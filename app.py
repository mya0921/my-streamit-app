import streamlit as st
import requests

st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="centered")

# -----------------------------
# UI: Title / Intro / API Key
# -----------------------------
st.title("🎬 나와 어울리는 영화는?")
st.write("간단한 5문항으로 당신의 영화 취향을 분석하고, TMDB에서 딱 맞는 영화를 추천해드려요! 👀🍿")

with st.sidebar:
    st.header("🔑 TMDB 설정")
    api_key = st.text_input("TMDB API Key", type="password", placeholder="여기에 입력")

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

# 각 선택지를 "선호 장르"로 매핑 (요구사항: 4개 선택지 = 4개 장르 선호)
# 여기서는 4개 장르 축(로맨스/드라마, 액션/어드벤처, SF/판타지, 코미디)로 점수를 쌓고,
# 최종적으로 TMDB 장르 ID(드라마/액션/SF/코미디/로맨스/판타지) 중 하나를 고릅니다.
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
    "맛있는 거 먹기": "comedy",  # 코미디 성향(가벼운 즐거움)
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

# 최종 TMDB 장르 ID 매핑
GENRE_IDS = {
    "액션": 28,
    "코미디": 35,
    "드라마": 18,
    "SF": 878,
    "로맨스": 10749,
    "판타지": 14,
}

cluster_to_genre = {
    "romance_drama": ("드라마", 18),      # (장르명, ID)
    "action_adventure": ("액션", 28),
    "sf_fantasy": ("SF", 878),
    "comedy": ("코미디", 35),
}

cluster_reason = {
    "romance_drama": "감정선과 여운을 중시하고, 차분하게 몰입하는 성향이 보여요.",
    "action_adventure": "활동적이고 도전적인 선택이 많아서, 빠른 전개와 스케일을 좋아할 가능성이 커요.",
    "sf_fantasy": "새로운 세계관/아이디어에 끌리는 선택이 많아, 상상력 자극 콘텐츠가 잘 맞아요.",
    "comedy": "가볍게 즐기고 웃는 포인트를 선택해서, 텐션 좋은 코미디가 찰떡이에요.",
}

def analyze_genre(answers: dict):
    """사용자 답변 -> 4개 성향 점수 -> 대표 장르 결정"""
    scores = {
        "romance_drama": 0,
        "action_adventure": 0,
        "sf_fantasy": 0,
        "comedy": 0,
    }

    for _q, choice in answers.items():
        cluster = choice_to_cluster.get(choice)
        if cluster:
            scores[cluster] += 1

    # 동점 처리: 우선순위를 약간 부여하거나(여기서는 드라마>액션>SF>코미디),
    # 랜덤 대신 고정 우선순위로 결과가 안정적으로 나오게 처리
    priority = ["romance_drama", "action_adventure", "sf_fantasy", "comedy"]
    top_score = max(scores.values())
    top_clusters = [c for c, s in scores.items() if s == top_score]
    for p in priority:
        if p in top_clusters:
            top_cluster = p
            break

    genre_name, genre_id = cluster_to_genre[top_cluster]
    reason = cluster_reason[top_cluster]
    return genre_name, genre_id, scores, reason

def fetch_movies(api_key: str, genre_id: int, n: int = 5):
    """TMDB discover API로 장르 인기 영화 가져오기"""
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "page": 1,
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    return results[:n]

def poster_url(poster_path: str | None):
    if not poster_path:
        return None
    return "https://image.tmdb.org/t/p/w500" + poster_path

# -----------------------------
# Render Radios
# -----------------------------
answers = {}
for q, opts in questions:
    answers[q] = st.radio(q, opts, key=q)

st.divider()

# -----------------------------
# Result Button
# -----------------------------
if st.button("결과 보기"):
    if not api_key:
        st.error("사이드바에 TMDB API Key를 먼저 입력해주세요.")
        st.stop()

    with st.spinner("분석 중..."):
        try:
            genre_name, genre_id, scores, overall_reason = analyze_genre(answers)
            movies = fetch_movies(api_key, genre_id, n=5)
        except requests.HTTPError as e:
            st.error(f"TMDB 요청에 실패했어요. API Key가 올바른지 확인해주세요.\n\n에러: {e}")
            st.stop()
        except requests.RequestException as e:
            st.error(f"네트워크 오류가 발생했어요.\n\n에러: {e}")
            st.stop()
        except Exception as e:
            st.error(f"알 수 없는 오류가 발생했어요.\n\n에러: {e}")
            st.stop()

    st.subheader(f"🎯 당신에게 어울리는 장르: {genre_name}")
    st.caption(
        f"점수(성향): 드라마/로맨스={scores['romance_drama']} · "
        f"액션/어드벤처={scores['action_adventure']} · "
        f"SF/판타지={scores['sf_fantasy']} · "
        f"코미디={scores['comedy']}"
    )
    st.write(f"**추천 이유:** {overall_reason}")

    st.divider()
    st.subheader("🍿 추천 영화 TOP 5")

    if not movies:
        st.info("해당 장르에서 영화를 찾지 못했어요. 잠시 후 다시 시도해 주세요.")
    else:
        for m in movies:
            title = m.get("title") or m.get("name") or "제목 정보 없음"
            rating = m.get("vote_average", 0.0)
            overview = m.get("overview") or "줄거리 정보가 없어요."
            purl = poster_url(m.get("poster_path"))

            # 영화별 추천 이유(간단)
            per_movie_reason = (
                f"당신의 선택이 '{genre_name}' 성향과 잘 맞아, "
                f"대중적으로 인기(인기도 기준) 높은 작품 중에서 골랐어요."
            )

            with st.container():
                cols = st.columns([1, 2.2])
                with cols[0]:
                    if purl:
                        st.image(purl, use_container_width=True)
                    else:
                        st.info("포스터 없음")
                with cols[1]:
                    st.markdown(f"### {title}")
                    st.write(f"⭐ 평점: **{rating:.1f}** / 10")
                    st.write(overview)
                    st.caption(f"💡 이 영화를 추천하는 이유: {per_movie_reason}")

                st.divider()
