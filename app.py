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
# TMDB constants
# =========================================================
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_DETAIL_URL = "https://api.themoviedb.org/3/movie/{movie_id}"

GENRE_IDS = {
    "액션": 28,
    "코미디": 35,
    "드라마": 18,
    "SF": 878,
    "로맨스": 10749,
    "판타지": 14,
}


# =========================================================
# UI Header
# =========================================================
st.title("🎬 나와 어울리는 영화는?")
st.write("심리테스트 + (가벼운) MBTI 성향으로 당신에게 어울리는 영화를 TMDB에서 추천해드려요! 👀🍿")

# 세션 랜덤 시드(추천 다양성용)
if "seed" not in st.session_state:
    st.session_state.seed = random.randint(1, 10**9)


# =========================================================
# Sidebar (Basic / Advanced)
# =========================================================
with st.sidebar:
    st.header("🔑 TMDB 설정")
    api_key = st.text_input("TMDB API Key", type="password", placeholder="여기에 입력")

    st.divider()
    st.subheader("표시 설정 (번역/표기)")
    language = st.selectbox("언어(language)", ["ko-KR", "en-US", "ja-JP"], index=0)

    st.subheader("추천 필터 (결과에 실제로 영향)")
    watch_region = st.selectbox("국가/지역(watch_region)", ["KR", "US", "JP", "GB", "FR", "DE"], index=0)
    include_adult = st.checkbox("성인 콘텐츠 포함", value=False)

    with st.expander("고급 설정(정확도/다양성)"):
        st.caption("아래 옵션은 결과 목록 자체에 영향을 줍니다. (언어는 주로 번역/표기)")
        prefer_rating = st.checkbox("인기 대신 평점 중심(안정적 추천)", value=True)
        min_vote_count = st.slider("최소 투표 수(vote_count.gte)", 0, 3000, 300, 50)
        recent_years = st.slider("최근 N년 작품 선호(0=제한 없음)", 0, 30, 15, 1)

        use_providers = st.checkbox("OTT/시청 가능 제공자 필터 사용", value=False)
        provider_ids_text = st.text_input(
            "제공자 ID(쉼표로 구분)",
            placeholder="예: 8,119,337",
            help="TMDB 제공자(Watch Providers) ID를 쉼표로 입력하세요. (원하면 내가 ID 찾는 방법도 안내해줄게요)"
        )
        monetization = st.multiselect(
            "시청 형태(monetization types)",
            ["flatrate", "rent", "buy", "free", "ads"],
            default=["flatrate"],
            help="예: flatrate=구독형(OTT), rent/buy=대여/구매"
        )

        diversify = st.checkbox("다양하게 추천(같은 장르라도 결과가 바뀌게)", value=True)
        fetch_pages = st.slider("후보를 모을 페이지 수(많을수록 다양)", 1, 5, 3, 1)
        max_movies = st.slider("최종 추천 개수", 5, 12, 6, 1)

        colA, colB = st.columns(2)
        with colA:
            if st.button("🎲 추천 새로고침(랜덤)"):
                st.session_state.seed = random.randint(1, 10**9)
        with colB:
            if st.button("🧹 캐시 초기화"):
                st.cache_data.clear()
                st.success("캐시를 지웠어요!")


# =========================================================
# Questions (기존 5문항 + MBTI 8문항)
# =========================================================
st.subheader("📝 1) 심리테스트 (5문항)")

questions_core = [
    ("1. 주말에 가장 하고 싶은 것은?", ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"]),
    ("2. 스트레스 받으면?", ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"]),
    ("3. 영화에서 중요한 것은?", ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"]),
    ("4. 여행 스타일?", ["계획적", "즉흥적", "액티비티", "힐링"]),
    ("5. 친구 사이에서 나는?", ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"]),
]

st.subheader("🧩 2) MBTI 성향 (가볍게 8문항)")
st.caption("MBTI를 정확히 진단하기보다, 영화 취향을 더 정교하게 만들기 위한 보조 질문이에요.")

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


# =========================================================
# Scoring maps
# - 핵심: '장르 1개로 결정'이 아니라 '장르 가중치'를 누적 → Top2 조합 추천
# - MBTI 축은 장르 가중치 + 정렬/다양성에 영향을 주는 보너스로 사용
# =========================================================
def add_scores(score_dict: dict, adds: dict, weight: float = 1.0):
    for k, v in adds.items():
        score_dict[k] = score_dict.get(k, 0.0) + v * weight


# 6장르에 점수 누적
# (드라마/로맨스는 묶되 둘 다 점수 줄 수 있게 구성)
CORE_MAP = {
    # Q1
    "집에서 휴식": {"드라마": 1.0, "로맨스": 0.6},
    "친구와 놀기": {"코미디": 1.0},
    "새로운 곳 탐험": {"액션": 1.0, "판타지": 0.2},
    "혼자 취미생활": {"SF": 0.9, "판타지": 0.6, "드라마": 0.2},

    # Q2
    "혼자 있기": {"드라마": 0.9, "로맨스": 0.5},
    "수다 떨기": {"코미디": 1.0, "로맨스": 0.2},
    "운동하기": {"액션": 1.0},
    "맛있는 거 먹기": {"코미디": 0.9, "드라마": 0.2},

    # Q3
    "감동 스토리": {"드라마": 1.0, "로맨스": 0.8},
    "시각적 영상미": {"액션": 0.8, "SF": 0.7, "판타지": 0.5},
    "깊은 메시지": {"SF": 0.7, "드라마": 0.6},
    "웃는 재미": {"코미디": 1.0},

    # Q4
    "계획적": {"드라마": 0.5, "SF": 0.3},
    "즉흥적": {"코미디": 0.7, "액션": 0.5},
    "액티비티": {"액션": 1.0},
    "힐링": {"드라마": 0.9, "로맨스": 0.4},

    # Q5
    "듣는 역할": {"드라마": 0.7, "로맨스": 0.4},
    "주도하기": {"액션": 0.9, "SF": 0.3},
    "분위기 메이커": {"코미디": 1.0},
    "필요할 때 나타남": {"SF": 0.6, "판타지": 0.5, "액션": 0.2},
}

# MBTI는 장르 보정 + “추천 이유 문구”에 활용
MBTI_MAP = {
    # E/I
    "사람 만나면 충전된다": {"코미디": 0.6, "액션": 0.4},
    "혼자 있어야 회복된다": {"드라마": 0.6, "SF": 0.3},
    "대체로 먼저 말하는 편": {"코미디": 0.4, "액션": 0.4},
    "대체로 듣는 편": {"드라마": 0.5, "로맨스": 0.3},

    # S/N
    "현실적이고 공감되는 이야기": {"드라마": 0.6, "로맨스": 0.4},
    "상상력/세계관이 강한 이야기": {"SF": 0.6, "판타지": 0.5},
    "디테일한 장면/현실감": {"드라마": 0.4, "액션": 0.3},
    "메시지/상징/설정": {"SF": 0.5, "판타지": 0.4},

    # T/F
    "합리적으로 해결이 맞다": {"액션": 0.3, "SF": 0.3},
    "감정이 상하지 않게가 중요": {"드라마": 0.4, "로맨스": 0.5},
    "구성이 탄탄하고 완성도": {"SF": 0.3, "드라마": 0.3},
    "감정선/여운/공감": {"드라마": 0.4, "로맨스": 0.4},

    # J/P
    "미리 짜는 편": {"드라마": 0.2, "SF": 0.2},
    "그때그때 바꾸는 편": {"코미디": 0.3, "액션": 0.3},
    "마감 전 미리 끝낸다": {"드라마": 0.2},
    "몰아서 한 번에 한다": {"액션": 0.2, "코미디": 0.2},
}


def infer_mbti(answers_mbti: dict) -> str:
    """아주 가벼운 MBTI 추정(재미용)"""
    # 축별 점수: 첫 번째 선택지면 +1, 두 번째면 -1 식으로 단순화
    axes = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}

    # E/I
    for q in ["E/I-1. 에너지가 떨어질 때 나는…", "E/I-2. 모임에서 나는…"]:
        choice = answers_mbti.get(q)
        if choice in ["사람 만나면 충전된다", "대체로 먼저 말하는 편"]:
            axes["E"] += 1
        else:
            axes["I"] += 1

    # S/N
    for q in ["S/N-1. 더 끌리는 이야기 설정은?", "S/N-2. 영화 감상 후 기억에 남는 건?"]:
        choice = answers_mbti.get(q)
        if choice in ["현실적이고 공감되는 이야기", "디테일한 장면/현실감"]:
            axes["S"] += 1
        else:
            axes["N"] += 1

    # T/F
    for q in ["T/F-1. 갈등 장면에서 나는…", "T/F-2. 추천할 영화 기준은?"]:
        choice = answers_mbti.get(q)
        if choice in ["합리적으로 해결이 맞다", "구성이 탄탄하고 완성도"]:
            axes["T"] += 1
        else:
            axes["F"] += 1

    # J/P
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
    """장르 점수 + Top2 장르 + 설명 생성"""
    scores = {k: 0.0 for k in GENRE_IDS.keys()}

    for _, choice in answers_core.items():
        add_scores(scores, CORE_MAP.get(choice, {}), weight=1.0)

    for _, choice in answers_mbti.items():
        add_scores(scores, MBTI_MAP.get(choice, {}), weight=0.8)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top1, top2 = ranked[0], ranked[1]

    # 2nd 장르를 섞을지 결정 (점수 차가 작으면 혼합 추천)
    mix = (top1[1] - top2[1]) <= 0.8 and top2[1] > 0

    # 추천 장르 리스트
    if mix:
        genre_names = [top1[0], top2[0]]
    else:
        genre_names = [top1[0]]

    # 설명 문구
    mbti = infer_mbti(answers_mbti)
    reason_bits = []
    reason_bits.append(f"선호 장르 점수 상위: **{top1[0]}**" + (f", **{top2[0]}**" if mix else ""))
    reason_bits.append(f"MBTI 느낌은 **{mbti}** 쪽에 가까워 보여요(재미용).")

    # 간단한 성향 코멘트
    if "N" in mbti:
        reason_bits.append("세계관/설정형 콘텐츠 선호가 보여요.")
    if "F" in mbti:
        reason_bits.append("감정선/여운에 반응하는 편이에요.")
    if "E" in mbti:
        reason_bits.append("가볍고 텐션 있는 재미를 잘 즐길 가능성이 커요.")
    if "P" in mbti:
        reason_bits.append("즉흥/자극 포인트에 끌릴 때가 있어요.")

    return scores, genre_names, mbti, " ".join(reason_bits)


# =========================================================
# TMDB calls (cached)
# =========================================================
@st.cache_data(ttl=60 * 10)  # 10분 캐시 (옵션 바꿀 때 체감되게)
def tmdb_discover(
    api_key: str,
    with_genres: str,
    language: str,
    watch_region: str,
    include_adult: bool,
    sort_by: str,
    min_vote_count: int,
    min_release_date: str | None,
    with_watch_providers: str | None,
    with_watch_monetization_types: str | None,
    page: int,
):
    params = {
        "api_key": api_key,
        "with_genres": with_genres,
        "language": language,
        "include_adult": include_adult,
        "sort_by": sort_by,
        "page": page,
    }

    # 지역 필터(실제 추천 결과에 영향을 주려면 watch providers와 함께 쓰는 편이 체감 큼)
    # 그래도 watch_region은 provider 필터와 함께 쓰이므로 항상 전달
    params["watch_region"] = watch_region

    if sort_by.startswith("vote_average") and min_vote_count > 0:
        params["vote_count.gte"] = min_vote_count

    if min_release_date:
        params["primary_release_date.gte"] = min_release_date

    if with_watch_providers:
        params["with_watch_providers"] = with_watch_providers
    if with_watch_monetization_types:
        params["with_watch_monetization_types"] = with_watch_monetization_types

    r = requests.get(TMDB_DISCOVER_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60 * 60)
def tmdb_movie_detail(api_key: str, movie_id: int, language: str):
    url = TMDB_DETAIL_URL.format(movie_id=movie_id)
    params = {"api_key": api_key, "language": language}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def poster_url(poster_path: str | None):
    return (POSTER_BASE + poster_path) if poster_path else None


# =========================================================
# Reranking (후보 많이 가져와서 재정렬)
# =========================================================
def normalize(values):
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx - mn < 1e-9:
        return [0.5 for _ in values]
    return [(v - mn) / (mx - mn) for v in values]


def movie_relevance_score(movie: dict, user_genres: list[str]):
    """
    간단 리랭킹 점수:
    - vote_average(정규화) + log(vote_count)(정규화) + popularity(정규화) + 장르매칭 보너스
    - discover 결과는 장르ID 목록(genre_ids)이 들어있어서 매칭이 가능
    """
    # placeholder - 실제 정규화는 바깥에서 처리
    return 0.0


def rerank_movies(candidates: list[dict], user_genre_names: list[str]):
    # 1) 정규화 대상 추출
    votes = [float(m.get("vote_average") or 0.0) for m in candidates]
    pops = [float(m.get("popularity") or 0.0) for m in candidates]
    vcnt = [float(m.get("vote_count") or 0.0) for m in candidates]
    log_vcnt = [math.log(1 + x) for x in vcnt]

    nv = normalize(votes)
    np = normalize(pops)
    nl = normalize(log_vcnt)

    user_genre_ids = {GENRE_IDS[g] for g in user_genre_names if g in GENRE_IDS}

    scored = []
    for i, m in enumerate(candidates):
        g_ids = set(m.get("genre_ids") or [])
        match = len(g_ids & user_genre_ids)

        # 장르 조합 추천 시 더 잘 맞는 작품이 위로 오게 보너스
        match_bonus = 0.10 * match  # 0~0.2 정도

        # 기본 점수(가중치)
        score = (
            0.55 * nv[i] +        # 평점(정규화)
            0.25 * nl[i] +        # 투표수(로그 정규화)
            0.20 * np[i] +        # 인기도(정규화)
            match_bonus
        )
        scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


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
# Result button
# =========================================================
if st.button("결과 보기"):
    if not api_key:
        st.error("사이드바에 TMDB API Key를 먼저 입력해주세요.")
        st.stop()

    # 추천 파라미터 준비
    sort_by = "vote_average.desc" if (prefer_rating if "prefer_rating" in locals() else True) else "popularity.desc"

    # 최근 n년 필터
    min_release_date = None
    if "recent_years" in locals() and recent_years and recent_years > 0:
        today = date.today()
        min_release_date = date(today.year - recent_years, 1, 1).isoformat()

    # provider 필터 파싱
    with_watch_providers = None
    with_watch_monetization_types = None
    if "use_providers" in locals() and use_providers:
        raw = (provider_ids_text or "").strip()
        if raw:
            # 숫자만 뽑아 쉼표로 재구성
            ids = []
            for part in raw.split(","):
                part = part.strip()
                if part.isdigit():
                    ids.append(part)
            if ids:
                with_watch_providers = ",".join(ids)
                if monetization:
                    with_watch_monetization_types = ",".join(monetization)
        else:
            st.warning("제공자 필터를 켰다면, 제공자 ID를 입력해야 실제로 결과가 달라져요.")

    # 사용자 프로필 분석
    with st.spinner("분석 중..."):
        scores, genre_names, mbti, profile_reason = build_profile(answers_core, answers_mbti)

    # 장르 파라미터: Top1 or Top1+Top2
    with_genres = ",".join(str(GENRE_IDS[g]) for g in genre_names if g in GENRE_IDS)

    # 후보 모으기 (페이지 여러개 + (옵션) 랜덤 페이지)
    candidates = []
    seed = st.session_state.seed
    rng = random.Random(seed)

    pages_to_fetch = fetch_pages if "fetch_pages" in locals() else 3
    diversify_on = diversify if "diversify" in locals() else True

    # base page: 다양화면 1~5 랜덤, 아니면 1부터
    base_page = rng.randint(1, 5) if diversify_on else 1

    with st.spinner("TMDB에서 추천 후보를 찾는 중..."):
        try:
            for k in range(pages_to_fetch):
                page = base_page + k
                data = tmdb_discover(
                    api_key=api_key,
                    with_genres=with_genres,
                    language=language,
                    watch_region=watch_region,
                    include_adult=include_adult,
                    sort_by=sort_by,
                    min_vote_count=min_vote_count if "min_vote_count" in locals() else 300,
                    min_release_date=min_release_date,
                    with_watch_providers=with_watch_providers,
                    with_watch_monetization_types=with_watch_monetization_types,
                    page=page,
                )
                results = data.get("results") or []
                candidates.extend(results)

        except requests.HTTPError as e:
            st.error(f"TMDB 요청에 실패했어요. API Key/옵션을 확인해주세요.\n\n에러: {e}")
            st.stop()
        except requests.RequestException as e:
            st.error(f"네트워크 오류가 발생했어요.\n\n에러: {e}")
            st.stop()

    # 중복 제거(영화 id 기준)
    uniq = {}
    for m in candidates:
        mid = m.get("id")
        if mid is not None:
            uniq[mid] = m
    candidates = list(uniq.values())

    if not candidates:
        st.info("조건에 맞는 영화가 없어요. (투표수/최근연도/제공자 필터를 완화해보세요)")
        st.stop()

    # 리랭킹 후 상위 N개
    reranked = rerank_movies(candidates, genre_names)
    final_n = max_movies if "max_movies" in locals() else 6
    movies = reranked[:final_n]

    # =========================================================
    # Result UI
    # =========================================================
    st.markdown(f"## ✨ 당신에게 딱인 장르는: **{genre_names[0]}**!")
    if len(genre_names) >= 2:
        st.caption(f"취향이 섞여 보여서 **{genre_names[0]} + {genre_names[1]}** 조합으로 더 정확히 골랐어요.")
    st.caption(f"MBTI 느낌(재미용): **{mbti}**")
    st.write(f"**분석 요약:** {profile_reason}")

    # 점수 표시
    st.caption(
        "장르 점수: "
        + " · ".join([f"{g}={scores[g]:.1f}" for g in ["드라마", "로맨스", "액션", "코미디", "SF", "판타지"]])
    )

    # 적용된 필터 표시(체감 확인용)
    applied = [f"with_genres={with_genres}", f"watch_region={watch_region}", f"sort_by={sort_by}"]
    if min_release_date:
        applied.append(f"release>={min_release_date}")
    if sort_by.startswith("vote_average") and min_vote_count:
        applied.append(f"vote_count>={min_vote_count}")
    if with_watch_providers:
        applied.append(f"providers={with_watch_providers} ({with_watch_monetization_types or 'all'})")
    st.caption("적용 필터: " + " | ".join(applied))

    st.divider()
    st.subheader("🍿 추천 영화")

    # 3열 카드
    cols = st.columns(3, gap="large")

    for i, m in enumerate(movies):
        col = cols[i % 3]

        movie_id = m.get("id")
        title = m.get("title") or "제목 정보 없음"
        rating = float(m.get("vote_average") or 0.0)
        overview = m.get("overview") or "줄거리 정보가 없어요."
        purl = poster_url(m.get("poster_path"))

        # 간단 추천 이유
        why = []
        why.append(f"당신의 상위 장르(**{', '.join(genre_names)}**)와 잘 맞는 조합이에요.")
        if rating >= 7.5:
            why.append("평점이 높은 편이라 만족도가 높을 가능성이 커요.")
        vc = int(m.get("vote_count") or 0)
        if vc >= 1000:
            why.append("투표수가 충분해 안정적인 추천이에요.")
        why.append(f"MBTI 느낌(**{mbti}**) 기반으로 ‘몰입 포인트’가 맞을 확률이 있어요.")
        why_text = " ".join(why)

        with col:
            if purl:
                st.image(purl, use_container_width=True)
            else:
                st.info("포스터 없음")

            st.markdown(f"**{title}**")
            st.write(f"⭐ 평점: **{rating:.1f}** / 10")

            with st.expander("상세 보기"):
                # 필요할 때만 상세 호출(캐시됨)
                release_date = None
                runtime = None
                genres_text = None

                if movie_id:
                    try:
                        detail = tmdb_movie_detail(api_key, int(movie_id), language)
                        overview = detail.get("overview") or overview
                        release_date = detail.get("release_date")
                        runtime = detail.get("runtime")
                        g = detail.get("genres") or []
                        if g:
                            genres_text = ", ".join(x.get("name", "") for x in g if x.get("name"))
                    except Exception:
                        pass

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

                st.markdown("**이 영화를 추천하는 이유**")
                st.write(why_text)

    st.divider()
    st.caption("💡 팁: 결과가 너무 비슷하면 (1) ‘다양하게 추천’ 켜기 (2) 페이지 수 늘리기 (3) 제공자/최근 연도/투표수 조건 조절을 해보세요!")
