import streamlit as st
import requests

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="wide")

# -----------------------------
# TMDB constants
# -----------------------------
POSTER_BASE = "https://image.tmdb.org/t/p/w500"

GENRE_IDS = {
    "액션": 28,
    "코미디": 35,
    "드라마": 18,
    "SF": 878,
    "로맨스": 10749,
    "판타지": 14,
}

# 4개 성향(클러스터) -> (대표장르, 대표장르ID, 보조장르, 보조장르ID)
# - 로맨스/드라마 성향이면 드라마를 기본, 로맨스를 보조로 붙일 수 있게
# - SF/판타지 성향이면 SF를 기본, 판타지를 보조로 붙일 수 있게
CLUSTER_PROFILE = {
    "romance_drama": ("드라마", GENRE_IDS["드라마"], "로맨스", GENRE_IDS["로맨스"]),
    "action_adventure": ("액션", GENRE_IDS["액션"], None, None),
    "sf_fantasy": ("SF", GENRE_IDS["SF"], "판타지", GENRE_IDS["판타지"]),
    "comedy": ("코미디", GENRE_IDS["코미디"], None, None),
}

CLUSTER_REASON = {
    "romance_drama": "감정선과 여운을 중시하고, 차분하게 몰입하는 성향이 보여요.",
    "action_adventure": "활동적이고 도전적인 선택이 많아서, 빠른 전개와 스케일을 좋아할 가능성이 커요.",
    "sf_fantasy": "새로운 세계관/아이디어에 끌리는 선택이 많아, 상상력 자극 콘텐츠가 잘 맞아요.",
    "comedy": "가볍게 즐기고 웃는 포인트를 선택해서, 텐션 좋은 코미디가 찰떡이에요.",
}

# -----------------------------
# UI: Title / Intro / Sidebar
# -----------------------------
st.title("🎬 나와 어울리는 영화는?")
st.write("간단한 5문항으로 당신의 영화 취향을 분석하고, TMDB에서 딱 맞는 영화를 추천해드려요! 👀🍿")

with st.sidebar:
    st.header("🔑 TMDB 설정")
    api_key = st.text_input("TMDB API Key", type="password", placeholder="여기에 입력")

    st.divider()
    st.subheader("추천 옵션")
    language = st.selectbox("언어", ["ko-KR", "en-US"], index=0)
    region = st.selectbox("지역", ["KR", "US", "JP", "GB", "FR", "DE"], index=0)
    include_adult = st.checkbox("성인 콘텐츠 포함", value=False)

    # 추천 품질 고도화 옵션
    st.caption("추천 품질(선택): 평점 정렬 시 최소 투표 수 조건을 걸면 안정적인 작품이 더 나올 때가 많아요.")
    use_rating_sort = st.checkbox("인기 대신 평점 중심으로 추천", value=False)
    min_vote_count = st.slider("최소 투표 수(vote_count.gte)", min_value=0, max_value=2000, value=300, step=50)

    max_movies = st.slider("가져올 영화 개수", 5, 12, 5, 1)

st.divider()

# -----------------------------
# Questions
# -----------------------------
questions = [
    ("1. 주말에 가장 하고 싶은 것은?", ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"]),
    ("2. 스트레스 받으면?", ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"]),
    ("3. 영화에서 중요한 것은?", ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"]),
    ("4. 여행 스타일?", ["계획적", "즉흥적", "액티비티", "힐링"]),
    ("5. 친구 사이에서 나는?", ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"]),
]

# 각 선택지를 4개 성향 점수로 매핑
choice_to_cluster = {
    # Q1
    "집에서 휴식": "romance_drama",
    "친구와 놀기": "comedy",
    "새로운 곳 탐험": "action_adventure",
    "혼자 취미생활": "sf_fantasy",
    # Q2
    "혼자 있기": "romance_drama",
    "수다 떨기": "comedy",
    "운동하기": "action_adventure",
    "맛있는 거 먹기": "comedy",
    # Q3
    "감동 스토리": "romance_drama",
    "시각적 영상미": "action_adventure",
    "깊은 메시지": "sf_fantasy",
    "웃는 재미": "comedy",
    # Q4
    "계획적": "romance_drama",
    "즉흥적": "comedy",
    "액티비티": "action_adventure",
    "힐링": "romance_drama",
    # Q5
    "듣는 역할": "romance_drama",
    "주도하기": "action_adventure",
    "분위기 메이커": "comedy",
    "필요할 때 나타남": "sf_fantasy",
}

# -----------------------------
# Helpers: analysis & TMDB calls
# -----------------------------
def analyze_profile(answers: dict):
    """사용자 답변 -> 4개 성향 점수 -> (대표 클러스터, 보조 클러스터) 결정"""
    scores = {k: 0 for k in CLUSTER_PROFILE.keys()}
    for _, choice in answers.items():
        cluster = choice_to_cluster.get(choice)
        if cluster:
            scores[cluster] += 1

    # 정렬: 점수 내림차순
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_cluster, top_score = ranked[0]
    second_cluster, second_score = ranked[1]

    # 보조 장르를 붙일지(점수 차이가 1 이하이면 취향이 섞였다고 보고 2장르 조합)
    use_secondary_cluster = (top_score - second_score) <= 1 and second_score > 0

    return top_cluster, (second_cluster if use_secondary_cluster else None), scores


@st.cache_data(ttl=60 * 60)  # 1시간 캐시
def tmdb_discover(api_key: str, with_genres: str, language: str, region: str, include_adult: bool,
                  sort_by: str, min_vote_count: int, page: int = 1):
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": api_key,
        "with_genres": with_genres,
        "language": language,
        "region": region,
        "include_adult": include_adult,
        "page": page,
        "sort_by": sort_by,
    }
    # 평점 정렬일 때만 최소 투표 수 옵션을 의미 있게 적용
    if sort_by.startswith("vote_average") and min_vote_count > 0:
        params["vote_count.gte"] = min_vote_count

    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60 * 60)
def tmdb_movie_detail(api_key: str, movie_id: int, language: str):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": api_key, "language": language}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def poster_url(poster_path: str | None):
    if not poster_path:
        return None
    return POSTER_BASE + poster_path


def pick_genre_ids(top_cluster: str, second_cluster: str | None):
    """최대 2개 클러스터를 TMDB with_genres 문자열로 변환(예: '18,10749')"""
    primary_name, primary_id, primary_sub_name, primary_sub_id = CLUSTER_PROFILE[top_cluster]

    chosen_ids = [primary_id]
    chosen_names = [primary_name]

    # top_cluster 자체가 보조장르를 가질 수 있는 타입(드라마<->로맨스, SF<->판타지)
    # 점수가 확실히 높은 경우(단일 취향)에는 primary cluster 내부 보조장르를 살짝 섞어줄 수 있게 옵션처럼 적용
    # 여기서는 "대표+보조"를 기본으로 섞지 않고, 필요할 때만(secondary cluster 없음) 대표+내부보조를 사용.
    if second_cluster is None and primary_sub_id is not None:
        chosen_ids = [primary_id, primary_sub_id]
        chosen_names = [primary_name, primary_sub_name]

    # second_cluster가 있으면: 다른 성향의 대표 장르를 하나 더 섞음
    if second_cluster is not None:
        sec_name, sec_id, _, _ = CLUSTER_PROFILE[second_cluster]
        if sec_id not in chosen_ids:
            chosen_ids = [primary_id, sec_id]
            chosen_names = [primary_name, sec_name]

    return ",".join(str(x) for x in chosen_ids), chosen_names


def build_reason(overall_genres: list[str], profile_reason: str, movie: dict):
    """영화별 간단 추천 이유"""
    vote = float(movie.get("vote_average") or 0.0)
    popularity = float(movie.get("popularity") or 0.0)

    bits = []
    bits.append(f"당신의 취향( {', '.join(overall_genres)} )과 잘 맞는 장르 조합이에요.")
    if vote >= 7.5:
        bits.append("평점이 높은 편이라 만족도가 좋은 작품일 가능성이 커요.")
    if popularity >= 80:
        bits.append("현재 인기도가 높아서 많은 사람이 보고 있는 작품이에요.")
    bits.append(profile_reason)
    return " ".join(bits)


# -----------------------------
# Render radios
# -----------------------------
answers = {}
for q, opts in questions:
    answers[q] = st.radio(q, opts, key=q)

st.divider()

# -----------------------------
# Result button
# -----------------------------
if st.button("결과 보기"):
    if not api_key:
        st.error("사이드바에 TMDB API Key를 먼저 입력해주세요.")
        st.stop()

    sort_by = "vote_average.desc" if use_rating_sort else "popularity.desc"

    with st.spinner("분석 중..."):
        try:
            top_cluster, second_cluster, scores = analyze_profile(answers)
            profile_reason = CLUSTER_REASON[top_cluster]

            with_genres, genre_names = pick_genre_ids(top_cluster, second_cluster)

            data = tmdb_discover(
                api_key=api_key,
                with_genres=with_genres,
                language=language,
                region=region,
                include_adult=include_adult,
                sort_by=sort_by,
                min_vote_count=min_vote_count,
                page=1
            )
            movies = (data.get("results") or [])[:max_movies]

        except requests.HTTPError as e:
            st.error(f"TMDB 요청에 실패했어요. API Key/쿼리 파라미터를 확인해주세요.\n\n에러: {e}")
            st.stop()
        except requests.RequestException as e:
            st.error(f"네트워크 오류가 발생했어요.\n\n에러: {e}")
            st.stop()
        except Exception as e:
            st.error(f"알 수 없는 오류가 발생했어요.\n\n에러: {e}")
            st.stop()

    # 1) 결과 제목
    st.markdown(f"## ✨ 당신에게 딱인 장르는: **{genre_names[0]}**!")
    if len(genre_names) > 1:
        st.caption(f"취향이 섞여 보여서 **{genre_names[0]} + {genre_names[1]}** 조합으로 추천했어요.")

    st.caption(
        f"점수(성향): 드라마/로맨스={scores['romance_drama']} · "
        f"액션/어드벤처={scores['action_adventure']} · "
        f"SF/판타지={scores['sf_fantasy']} · "
        f"코미디={scores['comedy']}"
    )
    st.write(f"**추천 이유:** {profile_reason}")

    st.divider()
    st.subheader("🍿 추천 영화")

    if not movies:
        st.info("해당 조건에서 영화를 찾지 못했어요. (최소 투표 수/정렬 옵션을 바꿔보세요!)")
        st.stop()

    # 2) 영화 카드 3열 그리드
    cols = st.columns(3, gap="large")

    for i, m in enumerate(movies):
        col = cols[i % 3]

        movie_id = m.get("id")
        title = m.get("title") or "제목 정보 없음"
        rating = float(m.get("vote_average") or 0.0)
        purl = poster_url(m.get("poster_path"))

        with col:
            # 3) 카드 구성: 포스터 / 제목 / 평점
            if purl:
                st.image(purl, use_container_width=True)
            else:
                st.info("포스터 없음")

            st.markdown(f"**{title}**")
            st.write(f"⭐ 평점: **{rating:.1f}** / 10")

            # 4) 클릭(펼치기) 시 상세 정보
            with st.expander("상세 보기"):
                overview = m.get("overview") or "줄거리 정보가 없어요."

                # discover 결과 overview가 비어있는 경우가 종종 있어 detail로 보강
                release_date = None
                runtime = None
                genres_text = None

                if movie_id:
                    try:
                        detail = tmdb_movie_detail(api_key, int(movie_id), language)
                        overview = detail.get("overview") or overview
                        release_date = detail.get("release_date")
                        runtime = detail.get("runtime")
                        genres = detail.get("genres") or []
                        if genres:
                            genres_text = ", ".join(g.get("name", "") for g in genres if g.get("name"))
                    except Exception:
                        # 상세 호출 실패해도 UI는 유지
                        pass

                st.write(overview)

                meta_parts = []
                if release_date:
                    meta_parts.append(f"개봉일: {release_date}")
                if runtime:
                    meta_parts.append(f"러닝타임: {runtime}분")
                if genres_text:
                    meta_parts.append(f"장르: {genres_text}")
                if meta_parts:
                    st.caption(" · ".join(meta_parts))

                # 5) 영화별 추천 이유
                st.markdown("**이 영화를 추천하는 이유**")
                st.write(build_reason(genre_names, profile_reason, m))
