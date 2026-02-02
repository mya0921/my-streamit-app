import json
import math
import random
from datetime import date

import requests
import streamlit as st

# =========================================================
# Page
# =========================================================
st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="wide")

# =========================================================
# TMDB / OpenAI constants
# =========================================================
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_DETAIL_URL = "https://api.themoviedb.org/3/movie/{movie_id}"
TMDB_WATCH_PROVIDERS_LIST_URL = "https://api.themoviedb.org/3/watch/providers/movie"

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"

GENRE_IDS = {
    "액션": 28,
    "코미디": 35,
    "드라마": 18,
    "SF": 878,
    "로맨스": 10749,
    "판타지": 14,
}

# 추천 필터: 제작 대륙(원산지 국가코드 묶음)
CONTINENT_TO_COUNTRIES = {
    "전체": [],
    "아시아": [
        "KR", "JP", "CN", "TW", "HK", "SG", "TH", "VN", "PH", "ID", "MY", "IN",
        "AE", "SA", "IL", "TR", "IR",
    ],
    "유럽": [
        "GB", "FR", "DE", "IT", "ES", "NL", "BE", "SE", "NO", "DK", "FI", "IE", "PT", "PL", "CZ", "AT",
        "CH", "HU", "RO", "GR", "UA",
    ],
    "북미": ["US", "CA", "MX"],
    "남미": ["BR", "AR", "CL", "CO", "PE", "VE", "EC", "UY"],
    "아프리카": ["ZA", "EG", "NG", "KE", "MA", "TN", "DZ", "GH"],
    "오세아니아": ["AU", "NZ"],
}

# JustWatch 기준(OTT 필터) - 이 예시는 KR로 고정
WATCH_REGION = "KR"
LANGUAGE = "ko-KR"

# =========================================================
# UI Header
# =========================================================
st.title("🎬 나와 어울리는 영화는?")
st.write("7문항으로 취향을 분석하고, TMDB 후보 중에서 LLM이 **진짜 너가 좋아할 1편**을 최종 선정해줘요! 🍿✨")

if "seed" not in st.session_state:
    st.session_state.seed = random.randint(1, 10**9)

# =========================================================
# Sidebar (re-designed)
# =========================================================
with st.sidebar:
    st.header("🔑 API Keys")
    tmdb_key = st.text_input("TMDB API Key", type="password", placeholder="TMDB 키 입력")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="OpenAI 키 입력")

    st.divider()
    st.header("🎛️ 추천 필터")

    # 1) 대륙(제작 원산지)
    continent = st.selectbox("🌍 제작 대륙", list(CONTINENT_TO_COUNTRIES.keys()), index=0)

    # 2) OTT 선택(가능하면 TMDB에서 목록 불러오기)
    ott_name_to_id = {"전체(필터 없음)": None}

    if tmdb_key:
        try:
            # 제공자 목록 호출은 아래 캐시 함수에서
            pass
        except Exception:
            pass

    st.caption("📺 OTT는 한국(JustWatch) 기준으로 필터링됩니다.")
    ott_choice_placeholder = st.empty()  # provider 로드 후 교체

    # 3) 정렬/추천 기준
    st.subheader("📌 추천 기준")
    rec_mode = st.radio(
        "어떤 기준으로 추천할까요?",
        ["평점 중심(안정적)", "최신/연도 중심", "인기 중심(대중적)"],
        index=0,
    )

    # 연도 옵션(최신/연도 중심일 때만 의미 있음)
    year_now = date.today().year
    year_from = st.slider("연도 범위(시작)", 1980, year_now, max(2005, year_now - 10))
    year_to = st.slider("연도 범위(끝)", 1980, year_now, year_now)

    st.subheader("⚙️ 품질/다양성")
    include_adult = st.checkbox("성인 콘텐츠 포함", value=False)
    min_vote_count = st.slider("최소 투표 수(평점 안정성)", 0, 3000, 300, 50)
    max_movies = st.slider("추천 카드 개수", 5, 12, 6, 1)
    diversify = st.checkbox("다양하게 추천(결과 변주)", value=True)
    fetch_pages = st.slider("후보 페이지 수(다양성)", 1, 5, 3, 1)

    colA, colB = st.columns(2)
    with colA:
        if st.button("🎲 추천 새로고침"):
            st.session_state.seed = random.randint(1, 10**9)
    with colB:
        if st.button("🧹 캐시 초기화"):
            st.cache_data.clear()
            st.success("캐시를 지웠어요!")


# =========================================================
# TMDB cached calls
# =========================================================
@st.cache_data(ttl=60 * 10)
def tmdb_watch_providers_list(api_key: str, watch_region: str):
    params = {"api_key": api_key, "watch_region": watch_region}
    r = requests.get(TMDB_WATCH_PROVIDERS_LIST_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60 * 10)
def tmdb_discover(params: dict):
    r = requests.get(TMDB_DISCOVER_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60 * 60)
def tmdb_movie_detail(api_key: str, movie_id: int, language: str = LANGUAGE):
    url = TMDB_DETAIL_URL.format(movie_id=movie_id)
    params = {"api_key": api_key, "language": language}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def poster_url(poster_path: str | None):
    return (POSTER_BASE + poster_path) if poster_path else None


# =========================================================
# Load OTT providers into sidebar selectbox
# =========================================================
selected_provider_id = None
ott_choice = "전체(필터 없음)"
if tmdb_key:
    try:
        data = tmdb_watch_providers_list(tmdb_key, WATCH_REGION)
        providers = data.get("results", []) or []
        providers = sorted(providers, key=lambda x: x.get("display_priority", 9999))
        for p in providers:
            pid = p.get("provider_id")
            pname = p.get("provider_name")
            if pid and pname and pname not in ott_name_to_id:
                ott_name_to_id[pname] = pid
    except Exception:
        pass

with st.sidebar:
    # placeholder를 실제 selectbox로 교체
    ott_choice = ott_choice_placeholder.selectbox("📺 OTT 선택", list(ott_name_to_id.keys()), index=0)
    selected_provider_id = ott_name_to_id.get(ott_choice)
    if selected_provider_id:
        st.caption(f"선택 OTT: {ott_choice} (provider_id={selected_provider_id}, region={WATCH_REGION})")


# =========================================================
# Questions: 총 7개 (MBTI처럼 보이지 않게 2문항을 섞음)
# =========================================================
st.subheader("📝 7문항 취향 테스트")

questions = [
    ("1. 주말에 가장 하고 싶은 것은?", ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"]),
    ("2. 스트레스를 받으면 주로 어떻게 푸는 편이야?", ["혼자 정리하는 시간이 필요", "친구에게 얘기하며 푼다", "몸을 움직이며 푼다", "맛있는 걸 먹으며 기분 전환"]),
    ("3. 영화에서 가장 중요하게 보는 건?", ["감동과 여운", "박진감/스케일", "설정/아이디어", "웃음 포인트"]),
    ("4. 여행을 간다면 내 스타일은?", ["동선/일정을 꼼꼼히", "대략만 정하고 현지에서", "액티비티 위주로", "힐링/맛집/산책 위주로"]),
    ("5. 과제나 준비할 일이 생기면 나는?", ["미리미리 나눠서 해두는 편", "마감이 다가와야 집중이 된다", "일단 시작하고 흐름 타면 끝까지", "같이 할 사람을 모아 분위기 만들기"]),
    ("6. 새로운 콘텐츠를 볼 때 더 끌리는 건?", ["현실적으로 있을 법한 이야기", "완전히 새로운 세계/규칙이 있는 이야기", "관계/감정의 변화가 촘촘한 이야기", "가벼운 텐션으로 즐기는 이야기"]),
    ("7. 친구들이 나를 설명할 때 더 가까운 건?", ["차분하고 믿음직하다", "에너지가 있고 추진력이 있다", "생각이 많고 독특한 편이다", "분위기를 풀어주는 편이다"]),
]

# =========================================================
# Scoring (장르 6개 + 숨은 성향축 2개)
# - hidden axes:
#   social: -1(혼자) ~ +1(사교)  -> 코미디/액션 가중
#   imagination: -1(현실) ~ +1(상상) -> SF/판타지 가중
# =========================================================
def add_scores(score_dict: dict, adds: dict, weight: float = 1.0):
    for k, v in adds.items():
        score_dict[k] = score_dict.get(k, 0.0) + v * weight


# 장르 점수 맵 (각 선택지 -> 6장르 가중치 + 숨은축)
# 숨은축 키: "__social", "__imagination"
SCORE_MAP = {
    # Q1
    "집에서 휴식": {"드라마": 1.0, "로맨스": 0.5, "__social": -0.6, "__imagination": 0.0},
    "친구와 놀기": {"코미디": 1.0, "__social": +0.8, "__imagination": 0.0},
    "새로운 곳 탐험": {"액션": 1.0, "판타지": 0.2, "__social": +0.2, "__imagination": +0.2},
    "혼자 취미생활": {"SF": 0.8, "판타지": 0.6, "드라마": 0.2, "__social": -0.5, "__imagination": +0.7},

    # Q2
    "혼자 정리하는 시간이 필요": {"드라마": 0.8, "로맨스": 0.4, "__social": -0.7, "__imagination": 0.1},
    "친구에게 얘기하며 푼다": {"코미디": 0.7, "로맨스": 0.3, "__social": +0.8, "__imagination": 0.0},
    "몸을 움직이며 푼다": {"액션": 0.9, "__social": +0.2, "__imagination": 0.1},
    "맛있는 걸 먹으며 기분 전환": {"코미디": 0.8, "드라마": 0.2, "__social": +0.2, "__imagination": 0.0},

    # Q3
    "감동과 여운": {"드라마": 1.0, "로맨스": 0.7, "__social": 0.0, "__imagination": 0.0},
    "박진감/스케일": {"액션": 1.0, "SF": 0.4, "__social": +0.2, "__imagination": +0.2},
    "설정/아이디어": {"SF": 0.9, "판타지": 0.6, "__social": 0.0, "__imagination": +0.9},
    "웃음 포인트": {"코미디": 1.0, "__social": +0.4, "__imagination": 0.0},

    # Q4
    "동선/일정을 꼼꼼히": {"드라마": 0.4, "SF": 0.3, "__social": -0.1, "__imagination": 0.2},
    "대략만 정하고 현지에서": {"코미디": 0.6, "액션": 0.4, "__social": +0.2, "__imagination": 0.1},
    "액티비티 위주로": {"액션": 1.0, "__social": +0.2, "__imagination": 0.0},
    "힐링/맛집/산책 위주로": {"드라마": 0.8, "로맨스": 0.3, "__social": 0.0, "__imagination": 0.0},

    # Q5 (숨은 J/P 성향 느낌을 “티 안나게” 반영)
    "미리미리 나눠서 해두는 편": {"드라마": 0.3, "SF": 0.3, "__social": -0.1, "__imagination": 0.2},
    "마감이 다가와야 집중이 된다": {"액션": 0.3, "코미디": 0.3, "__social": +0.1, "__imagination": 0.0},
    "일단 시작하고 흐름 타면 끝까지": {"액션": 0.4, "SF": 0.2, "__social": 0.0, "__imagination": 0.2},
    "같이 할 사람을 모아 분위기 만들기": {"코미디": 0.6, "__social": +0.7, "__imagination": 0.0},

    # Q6 (숨은 S/N + F/T 느낌을 “티 안나게” 반영)
    "현실적으로 있을 법한 이야기": {"드라마": 0.7, "로맨스": 0.4, "__social": 0.0, "__imagination": -0.8},
    "완전히 새로운 세계/규칙이 있는 이야기": {"SF": 0.7, "판타지": 0.7, "__social": 0.0, "__imagination": +1.0},
    "관계/감정의 변화가 촘촘한 이야기": {"드라마": 0.8, "로맨스": 0.7, "__social": 0.1, "__imagination": -0.2},
    "가벼운 텐션으로 즐기는 이야기": {"코미디": 0.8, "액션": 0.2, "__social": +0.3, "__imagination": 0.0},

    # Q7
    "차분하고 믿음직하다": {"드라마": 0.6, "로맨스": 0.2, "__social": -0.2, "__imagination": 0.0},
    "에너지가 있고 추진력이 있다": {"액션": 0.8, "코미디": 0.3, "__social": +0.5, "__imagination": 0.1},
    "생각이 많고 독특한 편이다": {"SF": 0.6, "판타지": 0.5, "__social": -0.1, "__imagination": +0.6},
    "분위기를 풀어주는 편이다": {"코미디": 0.9, "__social": +0.8, "__imagination": 0.0},
}


def build_profile(answers: dict):
    # 장르 점수
    scores = {k: 0.0 for k in GENRE_IDS.keys()}
    # 숨은축
    axes = {"__social": 0.0, "__imagination": 0.0}

    for _, choice in answers.items():
        adds = SCORE_MAP.get(choice, {})
        # 장르
        add_scores(scores, {k: v for k, v in adds.items() if k in scores}, 1.0)
        # 축
        axes["__social"] += float(adds.get("__social", 0.0))
        axes["__imagination"] += float(adds.get("__imagination", 0.0))

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top1, top2 = ranked[0], ranked[1]
    mix = (top1[1] - top2[1]) <= 0.8 and top2[1] > 0

    genre_names = [top1[0], top2[0]] if mix else [top1[0]]

    # “MBTI 티 안나게” 설명용 라벨
    social_label = "사람이랑 같이 즐기는 쪽" if axes["__social"] > 0.6 else ("혼자 몰입하는 쪽" if axes["__social"] < -0.6 else "상황 따라 유연한 편")
    imag_label = "상상력/세계관 선호" if axes["__imagination"] > 0.6 else ("현실감/공감 선호" if axes["__imagination"] < -0.6 else "밸런스형")

    summary = (
        f"상위 장르: **{genre_names[0]}**" + (f", **{genre_names[1]}**" if mix else "")
        + f" · 취향 톤: **{social_label}**, **{imag_label}**"
    )
    return scores, axes, genre_names, summary


# =========================================================
# OpenAI: 최종 1편 선택
# =========================================================
def openai_pick_one_movie(openai_api_key: str, profile_summary: str, candidates: list[dict]) -> dict:
    instructions = (
        "너는 사용자의 취향 요약을 바탕으로 후보 영화 중 단 1편을 고르는 큐레이터다.\n"
        "반드시 후보 리스트 안에서만 선택해야 한다.\n"
        "출력은 JSON만: {\"movie_id\": <number>, \"title\": \"...\", \"reason\": \"...\"}\n"
        "reason는 2~3문장으로 간단히.\n"
        "추가 텍스트 금지."
    )

    payload = {"profile_summary": profile_summary, "candidates": candidates}

    body = {
        "model": "gpt-5-mini",
        "instructions": instructions,
        "input": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        "temperature": 0.3,
        "max_output_tokens": 260,
        "text": {"format": {"type": "text"}},
    }

    headers = {"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"}
    r = requests.post(OPENAI_RESPONSES_URL, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()

    out_text = ""
    for item in data.get("output", []) or []:
        if item.get("type") == "message":
            for c in item.get("content", []) or []:
                if c.get("type") == "output_text":
                    out_text += c.get("text", "")

    out_text = (out_text or "").strip()

    try:
        return json.loads(out_text)
    except Exception:
        l = out_text.find("{")
        rpos = out_text.rfind("}")
        if l != -1 and rpos != -1 and rpos > l:
            try:
                return json.loads(out_text[l : rpos + 1])
            except Exception:
                pass

    return {"movie_id": candidates[0]["id"], "title": candidates[0]["title"], "reason": "후보 중에서 전반적으로 취향 적합도와 대중 평가가 좋아 보여요."}


# =========================================================
# Rerank
# =========================================================
def rerank_movies(candidates: list[dict], user_genre_names: list[str]):
    votes = [float(m.get("vote_average") or 0.0) for m in candidates]
    pops = [float(m.get("popularity") or 0.0) for m in candidates]
    vcnt = [float(m.get("vote_count") or 0.0) for m in candidates]
    log_vcnt = [math.log(1 + x) for x in vcnt]

    nv = normalize(votes)
    npop = normalize(pops)
    nlog = normalize(log_vcnt)

    user_genre_ids = {GENRE_IDS[g] for g in user_genre_names if g in GENRE_IDS}

    scored = []
    for i, m in enumerate(candidates):
        g_ids = set(m.get("genre_ids") or [])
        match = len(g_ids & user_genre_ids)
        match_bonus = 0.10 * match

        score = 0.55 * nv[i] + 0.25 * nlog[i] + 0.20 * npop[i] + match_bonus
        scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


# =========================================================
# Render questions
# =========================================================
answers = {}
for q, opts in questions:
    answers[q] = st.radio(q, opts, key=q)

st.divider()


# =========================================================
# Result
# =========================================================
if st.button("결과 보기"):
    if not tmdb_key:
        st.error("사이드바에 TMDB API Key를 입력해주세요.")
        st.stop()
    if not openai_key:
        st.error("사이드바에 OpenAI API Key를 입력해주세요.")
        st.stop()

    # 1) 분석
    with st.spinner("분석 중..."):
        scores, axes, genre_names, profile_summary = build_profile(answers)

    with_genres = ",".join(str(GENRE_IDS[g]) for g in genre_names if g in GENRE_IDS)

    # 2) 제작 대륙 -> with_origin_country
    origin_countries = CONTINENT_TO_COUNTRIES.get(continent, [])
    with_origin_country = "|".join(origin_countries) if origin_countries else None

    # 3) OTT 필터
    with_watch_providers = str(selected_provider_id) if selected_provider_id else None
    with_watch_monetization_types = "flatrate" if selected_provider_id else None

    # 4) 추천 기준
    if rec_mode.startswith("평점"):
        sort_by = "vote_average.desc"
    elif rec_mode.startswith("인기"):
        sort_by = "popularity.desc"
    else:
        # 최신/연도 중심: 연도 필터 + 최신 정렬
        sort_by = "primary_release_date.desc"

    # 연도 범위
    # discover 파라미터는 release_date.gte / lte 를 지원하는 편이라 이쪽 사용
    date_gte = f"{min(year_from, year_to)}-01-01"
    date_lte = f"{max(year_from, year_to)}-12-31"

    # 5) 후보 수집
    seed = st.session_state.seed
    rng = random.Random(seed)
    base_page = rng.randint(1, 5) if diversify else 1

    candidates = []
    with st.spinner("TMDB에서 후보 영화를 찾는 중..."):
        try:
            for k in range(fetch_pages):
                page = base_page + k

                params = {
                    "api_key": tmdb_key,
                    "language": LANGUAGE,
                    "with_genres": with_genres,
                    "include_adult": include_adult,
                    "sort_by": sort_by,
                    "page": page,
                }

                # 평점 중심이면 표본 필터
                if sort_by.startswith("vote_average") and min_vote_count > 0:
                    params["vote_count.gte"] = min_vote_count

                # 연도 중심이면 연도 범위를 적극 적용
                if rec_mode.startswith("최신") or rec_mode.startswith("인기") or rec_mode.startswith("평점"):
                    # 연도 범위는 언제나 적용(사용자 요구: 연도별로 추천 옵션 포함)
                    params["primary_release_date.gte"] = date_gte
                    params["primary_release_date.lte"] = date_lte

                # 제작 대륙 필터
                if with_origin_country:
                    params["with_origin_country"] = with_origin_country

                # OTT 필터(한국 기준)
                if with_watch_providers:
                    params["watch_region"] = WATCH_REGION
                    params["with_watch_providers"] = with_watch_providers
                    params["with_watch_monetization_types"] = with_watch_monetization_types

                data = tmdb_discover(params)
                candidates.extend(data.get("results") or [])

        except requests.HTTPError as e:
            st.error(f"TMDB 요청 실패: {e}")
            st.stop()
        except requests.RequestException as e:
            st.error(f"네트워크 오류: {e}")
            st.stop()

    # 중복 제거
    uniq = {}
    for m in candidates:
        mid = m.get("id")
        if mid is not None:
            uniq[mid] = m
    candidates = list(uniq.values())

    if not candidates:
        st.info("조건에 맞는 영화가 없어요. (OTT/대륙/연도/투표수 조건을 완화해보세요)")
        st.stop()

    # 6) 리랭킹 + 상위 N개
    reranked = rerank_movies(candidates, genre_names)
    movies = reranked[:max_movies]

    # =========================================================
    # Result UI
    # =========================================================
    st.markdown(f"## ✨ 당신에게 딱인 장르는: **{genre_names[0]}**!")
    if len(genre_names) >= 2:
        st.caption(f"취향이 섞여 보여서 **{genre_names[0]} + {genre_names[1]}** 조합으로 추천했어요.")
    st.write(f"**분석 요약:** {profile_summary}")

    st.caption(
        "장르 점수: "
        + " · ".join([f"{g}={scores[g]:.1f}" for g in ["드라마", "로맨스", "액션", "코미디", "SF", "판타지"]])
    )

    applied = [f"with_genres={with_genres}", f"sort_by={sort_by}", f"years={year_from}-{year_to}"]
    if with_origin_country:
        applied.append(f"continent={continent}")
    if with_watch_providers:
        applied.append(f"OTT={ott_choice} (provider_id={with_watch_providers})")
    st.caption("적용 필터: " + " | ".join(applied))

    # =========================================================
    # LLM 최종 1편 선정 (후보 카드 중에서만)
    # =========================================================
    llm_candidates = []
    with st.spinner("LLM이 최종 1편을 고르는 중..."):
        for m in movies:
            llm_candidates.append(
                {
                    "id": int(m.get("id")),
                    "title": m.get("title") or "",
                    "overview": (m.get("overview") or "")[:800],
                    "vote_average": float(m.get("vote_average") or 0.0),
                    "vote_count": int(m.get("vote_count") or 0),
                    "release_date": m.get("release_date") or "",
                }
            )

        try:
            pick = openai_pick_one_movie(openai_key, profile_summary, llm_candidates)
        except Exception:
            pick = {"movie_id": llm_candidates[0]["id"], "title": llm_candidates[0]["title"], "reason": "후보 중에서 전반적으로 취향 적합도와 평가가 좋아 보여요."}

    picked_id = pick.get("movie_id")
    picked_title = pick.get("title", "")
    picked_reason = pick.get("reason", "")

    st.success(f"🎯 LLM 최종 추천: **{picked_title}**")
    st.write(picked_reason)

    st.divider()
    st.subheader("🍿 추천 후보 영화 (3열 카드)")

    cols = st.columns(3, gap="large")
    for i, m in enumerate(movies):
        col = cols[i % 3]
        movie_id = int(m.get("id"))
        title = m.get("title") or "제목 정보 없음"
        rating = float(m.get("vote_average") or 0.0)
        purl = poster_url(m.get("poster_path"))
        is_final = (picked_id == movie_id)

        with col:
            if purl:
                st.image(purl, use_container_width=True)
            else:
                st.info("포스터 없음")

            st.markdown(f"### ⭐ **{title}**" if is_final else f"**{title}**")
            st.write(f"⭐ 평점: **{rating:.1f}** / 10")

            with st.expander("상세 보기"):
                overview = m.get("overview") or "줄거리 정보가 없어요."
                release_date = m.get("release_date") or None

                try:
                    detail = tmdb_movie_detail(tmdb_key, movie_id, LANGUAGE)
                    overview = detail.get("overview") or overview
                    release_date = detail.get("release_date") or release_date
                    runtime = detail.get("runtime")
                    genres = detail.get("genres") or []
                    genres_text = ", ".join(g.get("name", "") for g in genres if g.get("name")) if genres else None
                except Exception:
                    runtime = None
                    genres_text = None

                st.write(overview)
                meta = []
                if release_date:
                    meta.append(f"개봉일: {release_date}")
                if runtime:
                    meta.append(f"러닝타임: {runtime}분")
                if genres_text:
                    meta.append(f"장르: {genres_text}")
                if meta:
                    st.caption(" · ".join(meta))

                if is_final:
                    st.markdown("**LLM이 이 영화를 고른 이유**")
                    st.write(picked_reason)

    st.divider()
    st.caption("💡 OTT 선택 후 결과가 적으면, 연도 범위를 넓히거나 최소 투표 수를 낮춰보세요.")
