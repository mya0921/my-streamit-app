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
# Constants
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

# 대륙(제작) 옵션: TMDB의 with_origin_country(ISO 3166-1)로 필터링
# ※ 현실적으로 “대륙=국가코드 묶음”이라 100% 완벽하진 않지만, 체감 필터로는 충분히 좋아요.
CONTINENT_TO_COUNTRIES = {
    "전체": [],
    "아시아": [
        "KR", "JP", "CN", "TW", "HK", "SG", "TH", "VN", "PH", "ID", "MY", "IN", "PK", "BD", "LK",
        "AE", "SA", "IL", "TR", "IR",
    ],
    "유럽": [
        "GB", "FR", "DE", "IT", "ES", "NL", "BE", "SE", "NO", "DK", "FI", "IE", "PT", "PL", "CZ", "AT",
        "CH", "HU", "RO", "GR", "UA",
    ],
    "북미": ["US", "CA", "MX"],
    "남미": ["BR", "AR", "CL", "CO", "PE", "VE", "EC", "UY", "PY", "BO"],
    "아프리카": ["ZA", "EG", "NG", "KE", "MA", "TN", "DZ", "GH", "ET"],
    "오세아니아": ["AU", "NZ"],
}

# 한국(JustWatch) 기준으로 OTT 제공자 필터를 걸기 위해 watch_region은 고정
# (원하면 나중에 “시청 국가”도 옵션으로 분리해줄 수 있어요)
WATCH_REGION = "KR"
DEFAULT_LANGUAGE = "ko-KR"

# =========================================================
# Header
# =========================================================
st.title("🎬 나와 어울리는 영화는?")
st.write("심리테스트 + MBTI 성향을 바탕으로 TMDB에서 후보를 뽑고, 마지막에 LLM이 **진짜 너가 좋아할 1편**을 골라줘요! 🍿✨")

if "seed" not in st.session_state:
    st.session_state.seed = random.randint(1, 10**9)

# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.header("🔑 API 키")
    tmdb_key = st.text_input("TMDB API Key", type="password", placeholder="TMDB 키 입력")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="OpenAI 키 입력")

    st.divider()
    st.header("🌍 제작 대륙(원산지) 필터")
    continent = st.selectbox("제작된 대륙", list(CONTINENT_TO_COUNTRIES.keys()), index=0)
    st.caption("※ 제작국가(원산지) 기준 필터예요. (시청 가능 지역/OTT와는 별개)")

    st.divider()
    st.header("📺 OTT 필터 (한국 기준)")
    st.caption("OTT 선택 시 **그 OTT에서 제공되는 영화만** 추천하도록 필터링해요. (JustWatch 데이터 기반)")

    st.divider()
    with st.expander("고급 설정(정확도/다양성)", expanded=True):
        include_adult = st.checkbox("성인 콘텐츠 포함", value=False)
        prefer_rating = st.checkbox("평점 중심(안정적 추천)", value=True)
        min_vote_count = st.slider("최소 투표 수(vote_count.gte)", 0, 3000, 300, 50)
        recent_years = st.slider("최근 N년 작품 선호(0=제한 없음)", 0, 30, 15, 1)

        diversify = st.checkbox("다양하게 추천(결과 변주)", value=True)
        fetch_pages = st.slider("후보를 모을 페이지 수", 1, 5, 3, 1)
        max_movies = st.slider("최종 추천 카드 개수", 5, 12, 6, 1)

        colA, colB = st.columns(2)
        with colA:
            if st.button("🎲 추천 새로고침"):
                st.session_state.seed = random.randint(1, 10**9)
        with colB:
            if st.button("🧹 캐시 초기화"):
                st.cache_data.clear()
                st.success("캐시를 지웠어요!")


# =========================================================
# Helpers
# =========================================================
def poster_url(poster_path: str | None):
    return (POSTER_BASE + poster_path) if poster_path else None


def normalize(values):
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx - mn < 1e-9:
        return [0.5 for _ in values]
    return [(v - mn) / (mx - mn) for v in values]


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
        match_bonus = 0.10 * match  # 장르 매칭 보너스

        score = (
            0.55 * nv[i] +
            0.25 * nlog[i] +
            0.20 * npop[i] +
            match_bonus
        )
        scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def add_scores(score_dict: dict, adds: dict, weight: float = 1.0):
    for k, v in adds.items():
        score_dict[k] = score_dict.get(k, 0.0) + v * weight


# =========================================================
# Questions & Scoring
# =========================================================
st.subheader("📝 1) 심리테스트 (5문항)")
questions_core = [
    ("1. 주말에 가장 하고 싶은 것은?", ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"]),
    ("2. 스트레스 받으면?", ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"]),
    ("3. 영화에서 중요한 것은?", ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"]),
    ("4. 여행 스타일?", ["계획적", "즉흥적", "액티비티", "힐링"]),
    ("5. 친구 사이에서 나는?", ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"]),
]

st.subheader("🧩 2) MBTI 성향 (8문항)")
st.caption("MBTI를 딱 16타입으로 확정하려는 목적이 아니라, 취향을 더 정교하게 만드는 보조 정보예요.")

questions_mbti = [
    ("E/I-1. 에너지가 떨어질 때 나는…", ["사람 만나면 충전된다", "혼자 있어야 회복된다"]),
    ("E/I-2. 모임에서 나는…", ["대체로 먼저 말하는 편", "대체로 듣는 편"]),
    ("S/N-1. 더 끌리는 이야기 설정은?", ["현실적이고 공감되는 이야기", "상상력/세계관이 강한 이야기"]),
    ("S/N-2. 영화 감상 후 기억에 남는 건?", ["디테일한 장면/현실감", "메시지/상징/설정"]),
    ("T/F-1. 갈등 장면에서 나는…", ["합리적으로 해결이 맞다", "감정이 상하지 않게가 중요"]),
    ("T/F-2. 추천할 영화 기준은?", ["구성이 탄탄하고 완성도", "감정선/여운/공감"]),
    ("J/P-1. 계획 스타일은?", ["미리 짜는 편", "그때그때 바꾸는 편"]),
    ("J/P-2. 여행/과제 진행은?", ["마감 전 미리 끝낸다", "몰아서 한 번에 한다"]),
]

CORE_MAP = {
    "집에서 휴식": {"드라마": 1.0, "로맨스": 0.6},
    "친구와 놀기": {"코미디": 1.0},
    "새로운 곳 탐험": {"액션": 1.0, "판타지": 0.2},
    "혼자 취미생활": {"SF": 0.9, "판타지": 0.6, "드라마": 0.2},

    "혼자 있기": {"드라마": 0.9, "로맨스": 0.5},
    "수다 떨기": {"코미디": 1.0, "로맨스": 0.2},
    "운동하기": {"액션": 1.0},
    "맛있는 거 먹기": {"코미디": 0.9, "드라마": 0.2},

    "감동 스토리": {"드라마": 1.0, "로맨스": 0.8},
    "시각적 영상미": {"액션": 0.8, "SF": 0.7, "판타지": 0.5},
    "깊은 메시지": {"SF": 0.7, "드라마": 0.6},
    "웃는 재미": {"코미디": 1.0},

    "계획적": {"드라마": 0.5, "SF": 0.3},
    "즉흥적": {"코미디": 0.7, "액션": 0.5},
    "액티비티": {"액션": 1.0},
    "힐링": {"드라마": 0.9, "로맨스": 0.4},

    "듣는 역할": {"드라마": 0.7, "로맨스": 0.4},
    "주도하기": {"액션": 0.9, "SF": 0.3},
    "분위기 메이커": {"코미디": 1.0},
    "필요할 때 나타남": {"SF": 0.6, "판타지": 0.5, "액션": 0.2},
}

MBTI_MAP = {
    "사람 만나면 충전된다": {"코미디": 0.6, "액션": 0.4},
    "혼자 있어야 회복된다": {"드라마": 0.6, "SF": 0.3},
    "대체로 먼저 말하는 편": {"코미디": 0.4, "액션": 0.4},
    "대체로 듣는 편": {"드라마": 0.5, "로맨스": 0.3},

    "현실적이고 공감되는 이야기": {"드라마": 0.6, "로맨스": 0.4},
    "상상력/세계관이 강한 이야기": {"SF": 0.6, "판타지": 0.5},
    "디테일한 장면/현실감": {"드라마": 0.4, "액션": 0.3},
    "메시지/상징/설정": {"SF": 0.5, "판타지": 0.4},

    "합리적으로 해결이 맞다": {"액션": 0.3, "SF": 0.3},
    "감정이 상하지 않게가 중요": {"드라마": 0.4, "로맨스": 0.5},
    "구성이 탄탄하고 완성도": {"SF": 0.3, "드라마": 0.3},
    "감정선/여운/공감": {"드라마": 0.4, "로맨스": 0.4},

    "미리 짜는 편": {"드라마": 0.2, "SF": 0.2},
    "그때그때 바꾸는 편": {"코미디": 0.3, "액션": 0.3},
    "마감 전 미리 끝낸다": {"드라마": 0.2},
    "몰아서 한 번에 한다": {"액션": 0.2, "코미디": 0.2},
}


def infer_mbti(answers_mbti: dict) -> str:
    axes = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}

    for q in ["E/I-1. 에너지가 떨어질 때 나는…", "E/I-2. 모임에서 나는…"]:
        choice = answers_mbti.get(q)
        if choice in ["사람 만나면 충전된다", "대체로 먼저 말하는 편"]:
            axes["E"] += 1
        else:
            axes["I"] += 1

    for q in ["S/N-1. 더 끌리는 이야기 설정은?", "S/N-2. 영화 감상 후 기억에 남는 건?"]:
        choice = answers_mbti.get(q)
        if choice in ["현실적이고 공감되는 이야기", "디테일한 장면/현실감"]:
            axes["S"] += 1
        else:
            axes["N"] += 1

    for q in ["T/F-1. 갈등 장면에서 나는…", "T/F-2. 추천할 영화 기준은?"]:
        choice = answers_mbti.get(q)
        if choice in ["합리적으로 해결이 맞다", "구성이 탄탄하고 완성도"]:
            axes["T"] += 1
        else:
            axes["F"] += 1

    for q in ["J/P-1. 계획 스타일은?", "J/P-2. 여행/과제 진행은?"]:
        choice = answers_mbti.get(q)
        if choice in ["미리 짜는 편", "마감 전 미리 끝낸다"]:
            axes["J"] += 1
        else:
            axes["P"] += 1

    mbti = ""
    mbti += "E" if axes["E"] >= axes["I"] else "I"
    mbti += "S" if axes["S"] >= axes["N"] else "N"
    mbti += "T" if axes["T"] >= axes["F"] else "F"
    mbti += "J" if axes["J"] >= axes["P"] else "P"
    return mbti


def build_profile(answers_core: dict, answers_mbti: dict):
    scores = {k: 0.0 for k in GENRE_IDS.keys()}

    for _, choice in answers_core.items():
        add_scores(scores, CORE_MAP.get(choice, {}), weight=1.0)

    for _, choice in answers_mbti.items():
        add_scores(scores, MBTI_MAP.get(choice, {}), weight=0.8)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top1, top2 = ranked[0], ranked[1]
    mix = (top1[1] - top2[1]) <= 0.8 and top2[1] > 0

    genre_names = [top1[0], top2[0]] if mix else [top1[0]]

    mbti = infer_mbti(answers_mbti)
    reason_bits = []
    reason_bits.append(f"상위 장르: **{top1[0]}**" + (f", **{top2[0]}**" if mix else ""))
    reason_bits.append(f"MBTI 느낌(재미용): **{mbti}**")

    if "N" in mbti:
        reason_bits.append("세계관/설정형 선호가 보여요.")
    if "F" in mbti:
        reason_bits.append("감정선/여운에 반응하는 편이에요.")
    if "E" in mbti:
        reason_bits.append("가볍고 텐션 있는 재미를 잘 즐길 가능성이 커요.")
    if "P" in mbti:
        reason_bits.append("즉흥/자극 포인트에 끌릴 때가 있어요.")

    return scores, genre_names, mbti, " ".join(reason_bits)


# =========================================================
# TMDB API
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
def tmdb_movie_detail(api_key: str, movie_id: int, language: str = DEFAULT_LANGUAGE):
    url = TMDB_DETAIL_URL.format(movie_id=movie_id)
    params = {"api_key": api_key, "language": language}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


# =========================================================
# OpenAI: 최종 1편 선택
# =========================================================
def openai_pick_one_movie(openai_api_key: str, profile_summary: str, candidates: list[dict]) -> dict:
    """
    candidates: [{id,title,overview,vote_average,vote_count,release_date,genres_text}, ...]
    return: {"movie_id": int, "title": str, "reason": str}
    """
    system_instructions = (
        "너는 사용자의 성향(심리테스트/MBTI 요약)에 맞춰 영화 1편을 최종 선정하는 큐레이터야.\n"
        "반드시 후보 리스트 안에서만 1편을 고르고, 왜 그 영화가 사용자에게 '가장' 맞는지 간단명료하게 설명해.\n"
        "출력은 반드시 JSON만: {\"movie_id\": <number>, \"title\": \"...\", \"reason\": \"...\"}\n"
        "추가 텍스트/마크다운/코드블록 금지."
    )

    user_payload = {
        "profile_summary": profile_summary,
        "candidates": candidates,
        "selection_rules": [
            "후보 밖 영화는 절대 선택하지 말 것",
            "사용자의 성향과 감상 만족도를 최우선",
            "너무 장황하게 말하지 말고 핵심 이유 2~3문장",
        ],
    }

    body = {
        "model": "gpt-5-mini",
        "instructions": system_instructions,
        "input": [
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            }
        ],
        "temperature": 0.3,
        "max_output_tokens": 300,
        "text": {"format": {"type": "text"}},
    }

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }

    r = requests.post(OPENAI_RESPONSES_URL, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Responses API: output_text가 SDK 전용일 수 있어 안전하게 output에서 합치기
    out_text = ""
    try:
        for item in data.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        out_text += c.get("text", "")
    except Exception:
        out_text = ""

    out_text = (out_text or "").strip()

    # JSON 파싱(혹시 모델이 앞뒤로 텍스트를 붙이면, JSON 블록만 잘라서 시도)
    try:
        return json.loads(out_text)
    except Exception:
        # 가장 바깥 {...}만 추출
        l = out_text.find("{")
        rpos = out_text.rfind("}")
        if l != -1 and rpos != -1 and rpos > l:
            try:
                return json.loads(out_text[l : rpos + 1])
            except Exception:
                pass

    # 실패 시 fallback
    return {"movie_id": candidates[0]["id"], "title": candidates[0]["title"], "reason": "후보 중 가장 전반적 평판과 취향 적합도가 높아 보여요."}


# =========================================================
# Render questions
# =========================================================
answers_core = {}
for q, opts in questions_core:
    answers_core[q] = st.radio(q, opts, key=q)

st.divider()

answers_mbti = {}
for q, opts in questions_mbti:
    answers_mbti[q] = st.radio(q, opts, horizontal=True, key=q)

st.divider()

# =========================================================
# OTT 옵션: TMDB 키가 있어야 제공자 목록을 가져올 수 있음
# =========================================================
ott_name_to_id = {"전체(필터 없음)": None}
if tmdb_key:
    try:
        provider_data = tmdb_watch_providers_list(tmdb_key, WATCH_REGION)
        results = provider_data.get("results", []) or []

        # 사용자 UX: 구독형(플랫폼) 위주로 깔끔하게 보여주기 위해
        # display_priority 순 정렬 + 중복 제거
        results_sorted = sorted(results, key=lambda x: x.get("display_priority", 9999))
        for p in results_sorted:
            pid = p.get("provider_id")
            pname = p.get("provider_name")
            if pid and pname and pname not in ott_name_to_id:
                ott_name_to_id[pname] = pid
    except Exception:
        # 키가 틀리거나 네트워크 오류면 전체만 노출
        pass

with st.sidebar:
    ott_choice = st.selectbox("OTT 선택", list(ott_name_to_id.keys()), index=0)
    selected_provider_id = ott_name_to_id.get(ott_choice)
    if selected_provider_id:
        st.caption(f"선택한 OTT provider_id: {selected_provider_id} (watch_region={WATCH_REGION})")


# =========================================================
# Result
# =========================================================
if st.button("결과 보기"):
    if not tmdb_key:
        st.error("사이드바에 TMDB API Key를 입력해주세요.")
        st.stop()

    if not openai_key:
        st.error("사이드바에 OpenAI API Key를 입력해주세요. (LLM 최종 1편 선택에 필요)")
        st.stop()

    # 1) 사용자 프로필 분석
    with st.spinner("분석 중..."):
        scores, genre_names, mbti, profile_reason = build_profile(answers_core, answers_mbti)

    with_genres = ",".join(str(GENRE_IDS[g]) for g in genre_names if g in GENRE_IDS)

    # 2) 제작 대륙(원산지) -> with_origin_country 파라미터 구성
    origin_countries = CONTINENT_TO_COUNTRIES.get(continent, [])
    # TMDB 필터에서 OR는 보통 | 를 쓰는 경우가 많아서 파이프로 연결 (실패 시 자동으로 무시되도록 처리)
    with_origin_country = "|".join(origin_countries) if origin_countries else None

    # 3) OTT 필터 파라미터
    with_watch_providers = str(selected_provider_id) if selected_provider_id else None
    with_watch_monetization_types = "flatrate" if selected_provider_id else None

    # 4) discover 파라미터
    sort_by = "vote_average.desc" if prefer_rating else "popularity.desc"

    min_release_date = None
    if recent_years and recent_years > 0:
        today = date.today()
        min_release_date = date(today.year - recent_years, 1, 1).isoformat()

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
                    "language": DEFAULT_LANGUAGE,
                    "with_genres": with_genres,
                    "include_adult": include_adult,
                    "sort_by": sort_by,
                    "page": page,
                }

                # 평점 중심이면 표본 필터
                if sort_by.startswith("vote_average") and min_vote_count > 0:
                    params["vote_count.gte"] = min_vote_count

                # 최근 N년
                if min_release_date:
                    params["primary_release_date.gte"] = min_release_date

                # 제작 대륙(원산지) 필터
                if with_origin_country:
                    params["with_origin_country"] = with_origin_country

                # OTT 필터 (한국 기준)
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
        st.info("조건에 맞는 영화가 없어요. (OTT/대륙/투표수/최근연도 조건을 완화해보세요)")
        st.stop()

    # 6) 리랭킹 후 카드용 N개
    reranked = rerank_movies(candidates, genre_names)
    movies = reranked[:max_movies]

    # =========================================================
    # 결과 UI
    # =========================================================
    st.markdown(f"## ✨ 당신에게 딱인 장르는: **{genre_names[0]}**!")
    if len(genre_names) >= 2:
        st.caption(f"취향이 섞여 보여서 **{genre_names[0]} + {genre_names[1]}** 조합으로 후보를 골랐어요.")
    st.caption(f"MBTI 느낌(재미용): **{mbti}**")
    st.write(f"**분석 요약:** {profile_reason}")

    st.caption(
        "장르 점수: "
        + " · ".join([f"{g}={scores[g]:.1f}" for g in ["드라마", "로맨스", "액션", "코미디", "SF", "판타지"]])
    )

    applied = [f"with_genres={with_genres}", f"sort_by={sort_by}"]
    if with_origin_country:
        applied.append(f"with_origin_country={with_origin_country}")
    if min_release_date:
        applied.append(f"release>={min_release_date}")
    if sort_by.startswith("vote_average") and min_vote_count:
        applied.append(f"vote_count>={min_vote_count}")
    if with_watch_providers:
        applied.append(f"OTT={ott_choice} (provider_id={with_watch_providers}, region={WATCH_REGION})")
    st.caption("적용 필터: " + " | ".join(applied))

    # =========================================================
    # LLM 최종 1편 선정 (카드 후보 중에서만)
    # =========================================================
    # LLM 입력을 위해 후보를 조금 더 “사람 친화적”으로 정리
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
            pick = openai_pick_one_movie(
                openai_api_key=openai_key,
                profile_summary=f"{profile_reason} (상위 장르: {', '.join(genre_names)})",
                candidates=llm_candidates,
            )
        except requests.HTTPError as e:
            st.warning(f"OpenAI 호출 실패로, 기본 추천으로 대체했어요: {e}")
            pick = {"movie_id": llm_candidates[0]["id"], "title": llm_candidates[0]["title"], "reason": "가장 무난하게 잘 맞는 후보예요."}
        except Exception as e:
            st.warning(f"LLM 선택 중 문제가 생겨 기본 추천으로 대체했어요: {e}")
            pick = {"movie_id": llm_candidates[0]["id"], "title": llm_candidates[0]["title"], "reason": "가장 무난하게 잘 맞는 후보예요."}

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

            if is_final:
                st.markdown(f"### ⭐ **{title}**")
            else:
                st.markdown(f"**{title}**")

            st.write(f"⭐ 평점: **{rating:.1f}** / 10")

            with st.expander("상세 보기"):
                overview = m.get("overview") or "줄거리 정보가 없어요."
                release_date = m.get("release_date") or None

                # 상세 정보(캐시됨)
                try:
                    detail = tmdb_movie_detail(tmdb_key, movie_id, DEFAULT_LANGUAGE)
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
    st.caption("💡 팁: OTT를 선택했는데 결과가 비거나 너무 적으면, '최근 N년'이나 '최소 투표 수'를 낮춰보세요.")
