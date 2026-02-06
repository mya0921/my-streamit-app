import streamlit as st
import json
import os
import random
from datetime import date
from urllib.parse import quote

APP_TITLE = "Daily Weaver"
PROFILE_PATH = "data/profile.json"

# -------------------------
# Fixed sets
# -------------------------
STYLE_MODES = ["친한친구", "반려동물", "공식적", "코치", "작가"]

EMOJI_FACE = [
    ("😀", "기쁨"), ("🙂", "평온"), ("😐", "무덤덤"), ("😔", "우울"), ("😢", "슬픔"),
    ("😭", "벅참"), ("😡", "분노"), ("😤", "답답"), ("😴", "피곤"), ("😬", "불안"),
]
EMOJI_SYMBOL = [
    ("☀️", "맑음"), ("🌙", "감성"), ("🌧️", "침잠"), ("🌿", "안정"), ("🔥", "열정"),
    ("⚡", "긴장"), ("🧊", "냉정"), ("🌊", "출렁임"), ("🫧", "가벼움"), ("🌸", "따뜻함"),
]

EMOTION_CHECKS = ["평온","기쁨","설렘","뿌듯","불안","답답","우울","분노","피곤","무기력"]
ACTIVITY_CHECKS = ["공부","업무","운동","휴식","약속","창작","정리","이동","소비","회복"]

# TODO: 질문 150개는 question_bank.json으로 분리 추천
SPECIAL_QUESTIONS = [
    "오늘 하루를 색깔로 표현한다면 어떤 색인가요?",
    "오늘 하루가 영화라면 제목은 무엇인가요?",
    "오늘 하루를 이모지 세 개로 표현한다면 무엇인가요?",
    # ... 여기에 150개 질문 전체를 넣거나, 파일에서 로드
]

# -------------------------
# Utils: profile persistence
# -------------------------
def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_profile(profile: dict):
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

def profile_display_line(p: dict) -> str:
    parts = [p.get("name", "")]
    if p.get("age") is not None:
        parts.append(f"{p['age']}세")
    if p.get("gender"):
        parts.append(p["gender"])
    if p.get("job"):
        parts.append(p["job"])
    return " · ".join([x for x in parts if x])

# -------------------------
# App state init
# -------------------------
def init_state():
    if "style_mode" not in st.session_state:
        st.session_state.style_mode = "친한친구"
    if "profile" not in st.session_state:
        st.session_state.profile = load_profile()
    if "editing_profile" not in st.session_state:
        st.session_state.editing_profile = False

    if "chat_started" not in st.session_state:
        st.session_state.chat_started = False
    if "step" not in st.session_state:
        st.session_state.step = 0  # 0=대기, 1~6 질문, 7 완료

    if "today" not in st.session_state:
        st.session_state.today = date.today().isoformat()

    if "special_q" not in st.session_state:
        # 날짜 seed로 오늘 질문 고정
        random.seed(st.session_state.today)
        st.session_state.special_q = random.choice(SPECIAL_QUESTIONS)

    if "answers" not in st.session_state:
        st.session_state.answers = {}

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []

init_state()

# -------------------------
# Layout
# -------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🧶", layout="wide")
st.title("🧶 Daily Weaver")

# -------------------------
# Sidebar
# -------------------------
with st.sidebar:
    st.subheader("대화 스타일")
    st.session_state.style_mode = st.radio(
        "어떤 버전으로 이야기할까요?",
        STYLE_MODES,
        index=STYLE_MODES.index(st.session_state.style_mode),
        label_visibility="collapsed",
    )

    st.divider()
    st.subheader("내 프로필")
    if st.session_state.profile:
        st.caption(profile_display_line(st.session_state.profile))
        if st.button("프로필 수정", use_container_width=True):
            st.session_state.editing_profile = True
    else:
        st.caption("아직 프로필이 없어요.")
        if st.button("프로필 입력", use_container_width=True):
            st.session_state.editing_profile = True

    st.divider()
    st.subheader("성장서사 보기")
    tab_w, tab_m, tab_y = st.tabs(["주간", "월간", "연간"])
    with tab_w:
        st.caption("이번 주 요약(예시 UI)")
        # TODO: 주간 선택 UI + 요약 출력
    with tab_m:
        st.caption("이번 달 요약(예시 UI)")
        # TODO
    with tab_y:
        st.caption("올해 요약(예시 UI)")
        # TODO

# -------------------------
# Onboarding / Profile modal-ish
# -------------------------
def render_profile_form():
    st.markdown("### Daily Weaver에 오신 걸 환영해요")
    st.write("처음 한 번만 간단히 알려주면, 매일 기록이 더 자연스럽고 디테일해져요. 언제든 수정할 수 있어요.")
    st.info("프로필은 이 기기(로컬)에 저장되며, 원하면 언제든 지울 수 있어요.", icon="🔒")

    with st.form("profile_form", clear_on_submit=False):
        name = st.text_input("이름", value=(st.session_state.profile.get("name") if st.session_state.profile else ""))
        age = st.number_input("나이", min_value=0, max_value=120, value=int(st.session_state.profile.get("age", 20)) if st.session_state.profile else 20)
        gender = st.selectbox("성별", ["선택 안 함", "여성", "남성", "논바이너리", "기타"], index=0)
        job = st.text_input("직업", value=(st.session_state.profile.get("job") if st.session_state.profile else ""))

        col1, col2 = st.columns(2)
        submitted = col1.form_submit_button("저장", use_container_width=True)
        cancel = col2.form_submit_button("취소", use_container_width=True)

    if cancel:
        st.session_state.editing_profile = False
        st.rerun()

    if submitted:
        profile = {
            "name": name.strip() or "사용자",
            "age": int(age),
            "gender": "" if gender == "선택 안 함" else gender,
            "job": job.strip(),
        }
        save_profile(profile)
        st.session_state.profile = profile
        st.session_state.editing_profile = False
        st.success("저장했어요. 이제 오늘 기록을 시작해볼까요?")
        st.rerun()

# If no profile yet or editing, show onboarding and stop
if (st.session_state.profile is None) or st.session_state.editing_profile:
    render_profile_form()
    st.stop()

# -------------------------
# Main: chat start + step flow
# -------------------------
def push_app(msg: str):
    st.session_state.chat_log.append({"role": "app", "content": msg})

def push_user(msg: str):
    st.session_state.chat_log.append({"role": "user", "content": msg})

# Greeting (shown once)
if not st.session_state.chat_started and st.session_state.step == 0:
    p = st.session_state.profile
    st.info(f"{p.get('name','')}님, 오늘 기록을 시작하려면 한마디만 걸어주세요. 예: 시작하자", icon="🧶")

# Chat input trigger
user_msg = st.chat_input("여기에 한마디를 입력해 시작하세요")
if user_msg and not st.session_state.chat_started:
    st.session_state.chat_started = True
    st.session_state.step = 1
    push_user(user_msg)

    # style-based greeting (lightweight)
    name = st.session_state.profile.get("name", "사용자")
    if st.session_state.style_mode == "공식적":
        push_app(f"{name}님, 오늘의 기록을 시작하겠습니다.")
    elif st.session_state.style_mode == "반려동물":
        push_app(f"{name}님, 오늘도 만나서 반가워요 🐾 기록을 시작해볼까요.")
    else:
        push_app(f"{name}님, 오늘도 수고 많았어요. 이제 천천히 기록해볼까요.")
    st.rerun()

# Render chat log
for m in st.session_state.chat_log:
    with st.chat_message("assistant" if m["role"] == "app" else "user"):
        st.write(m["content"])

st.divider()

# Step UIs
step = st.session_state.step

def next_step():
    st.session_state.step += 1
    st.rerun()

if st.session_state.chat_started and step == 1:
    if "q1_shown" not in st.session_state:
        push_app("오늘의 기분은 어떤가요. 아래 이모티콘 중 가장 가까운 것을 골라주세요.")
        st.session_state.q1_shown = True
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        st.caption("얼굴")
        face_choice = st.radio("face", [f"{e} {t}" for e, t in EMOJI_FACE], label_visibility="collapsed")
    with c2:
        st.caption("상징")
        sym_choice = st.radio("symbol", [f"{e} {t}" for e, t in EMOJI_SYMBOL], label_visibility="collapsed")

    st.caption("추천: 얼굴 1개와 상징 1개를 모두 선택해 주세요.")
    if st.button("다음", type="primary"):
        st.session_state.answers["emoji_face"] = face_choice.split(" ")[0]
        st.session_state.answers["emoji_symbol"] = sym_choice.split(" ")[0]
        next_step()

elif st.session_state.chat_started and step == 2:
    if "q2_shown" not in st.session_state:
        push_app("오늘 하루는 무엇으로 채워졌나요. 해당하는 항목을 체크해 주세요.")
        st.session_state.q2_shown = True
        st.rerun()

    colA, colB = st.columns(2)
    with colA:
        st.caption("감정(복수 선택)")
        emotions = st.multiselect("emotions", EMOTION_CHECKS, label_visibility="collapsed")
    with colB:
        st.caption("행동(복수 선택)")
        acts = st.multiselect("acts", ACTIVITY_CHECKS, label_visibility="collapsed")

    if st.button("다음", type="primary"):
        st.session_state.answers["emotion_checks"] = emotions
        st.session_state.answers["activity_checks"] = acts
        next_step()

elif st.session_state.chat_started and step == 3:
    if "q3_shown" not in st.session_state:
        push_app("오늘 하루를 한 단어로 표현한다면 무엇인가요.")
        st.session_state.q3_shown = True
        st.rerun()

    one_word = st.text_input("한 단어", placeholder="예: 버팀, 리셋, 흐림, 반짝임")
    if st.button("다음", type="primary"):
        st.session_state.answers["one_word"] = one_word.strip()
        next_step()

elif st.session_state.chat_started and step == 4:
    if "q4_shown" not in st.session_state:
        push_app("오늘 가장 기억에 남는 순간은 무엇인가요. 떠오르는 장면을 자유롭게 적어주세요.")
        st.session_state.q4_shown = True
        st.rerun()

    best = st.text_area("기억에 남는 순간", height=160)
    if st.button("다음", type="primary"):
        st.session_state.answers["best_moment"] = best.strip()
        next_step()

elif st.session_state.chat_started and step == 5:
    if "q5_shown" not in st.session_state:
        push_app("오늘 새롭게 배우거나 성장한 점이 있나요. 작은 깨달음이어도 괜찮아요.")
        st.session_state.q5_shown = True
        st.rerun()

    growth = st.text_area("성장한 점", height=160)
    if st.button("다음", type="primary"):
        st.session_state.answers["growth"] = growth.strip()
        next_step()

elif st.session_state.chat_started and step == 6:
    if "q6_shown" not in st.session_state:
        push_app(f"오늘의 스페셜 질문이에요. {st.session_state.special_q}")
        st.session_state.q6_shown = True
        st.rerun()

    special_a = st.text_area("답변", height=140)
    if st.button("마무리", type="primary"):
        st.session_state.answers["special_q"] = st.session_state.special_q
        st.session_state.answers["special_answer"] = special_a.strip()
        next_step()

elif st.session_state.chat_started and step == 7:
    # Closing message (template MVP)
    p = st.session_state.profile
    a = st.session_state.answers

    name = p.get("name", "사용자")
    one_word = a.get("one_word", "").strip()
    best = a.get("best_moment", "").strip()
    growth = a.get("growth", "").strip()

    if st.session_state.style_mode == "공식적":
        closing = f"{name}님, 오늘 기록을 마쳤습니다. 오늘의 핵심 단어는 '{one_word}'였고, 가장 인상 깊은 순간은 '{best[:40]}...'입니다. 오늘의 배움으로 '{growth[:40]}...'을 남겨주신 점이 좋습니다."
    elif st.session_state.style_mode == "반려동물":
        closing = f"{name}님, 오늘도 정말 수고했어요 🐾 '{one_word}' 같은 하루였고, '{best[:40]}...' 장면이 마음에 남아요. '{growth[:40]}...' 이 기록은 내일의 {name}님을 더 편하게 해줄 거예요."
    else:
        closing = f"{name}님, 오늘은 '{one_word}'라는 단어가 잘 어울리는 날이었어요. 특히 '{best[:50]}...' 그 순간이 오래 남을 것 같아요. 오늘도 수고 많았고, '{growth[:50]}...'을 적어둔 것만으로도 충분히 멋져요."

    push_app(closing)

    # Song recommendation (MVP: curated tag -> search link)
    # 아주 단순: 감정/행동 기반으로 키워드 정해서 검색 링크
    mood_hint = (a.get("emoji_symbol") or "") + " " + (one_word or "")
    query = quote(mood_hint.strip() or "lofi chill")
    spotify_url = f"https://open.spotify.com/search/{query}"

    with st.chat_message("assistant"):
        st.write("오늘의 추천곡을 골라봤어요.")
        st.markdown(f"[Spotify에서 열기]({spotify_url})")

    st.caption("다음 단계: 추천곡을 ‘곡명+아티스트’로 큐레이션하고, Spotify API로 track 링크를 정확히 붙일 수 있어요.")
