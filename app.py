# app.py
import streamlit as st
import json, os, random
from datetime import date, datetime
from urllib.parse import quote

APP_TITLE = "Daily Weaver"
DATA_DIR = "data"
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
ENTRIES_PATH = os.path.join(DATA_DIR, "entries.jsonl")

# -----------------------------
# UI THEME (White base + light pink accent)
# -----------------------------
def inject_css():
    st.markdown(
        """
<style>
    .stApp { background: #ffffff; }
    section[data-testid="stSidebar"]{
        background: #ffffff;
        border-right: 1px solid #f1f1f1;
    }
    .main .block-container{
        max-width: 860px;
        padding-top: 2.2rem;
    }

    /* Card */
    .dw-card{
        background: #ffffff;
        border: 1px solid #f2f2f2;
        border-radius: 18px;
        padding: 22px 22px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    .dw-title{
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    .dw-sub{
        color: #666;
        margin-bottom: 16px;
        font-size: 15px;
    }
    .dw-chip{
        display: inline-block;
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid #eaeaea;
        background: #fff;
        margin: 6px 8px 0 0;
        font-size: 14px;
        user-select: none;
    }
    .dw-chip-on{
        border: 1px solid #f6b6c8;
        background: #fff0f5;
        font-weight: 700;
    }

    /* Primary button */
    button[kind="primary"]{
        background: #f6b6c8 !important;
        color: #3a3a3a !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 800 !important;
        padding: 0.55rem 1rem !important;
    }
    button[kind="primary"]:hover{
        background: #f48fb1 !important;
        color: #ffffff !important;
    }

    /* Inputs */
    input, textarea{
        border-radius: 12px !important;
    }

    /* Radio horizontal spacing a bit nicer */
    div[role="radiogroup"]{
        gap: 10px;
    }

    /* Spotify card */
    .dw-music{
        display: flex;
        gap: 16px;
        align-items: center;
        padding: 16px;
        border-radius: 18px;
        border: 1px solid #f2f2f2;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    .dw-music img{
        border-radius: 12px;
    }
    .dw-music-title{
        font-size: 18px;
        font-weight: 800;
        margin: 0;
    }
    .dw-music-artist{
        color: #666;
        margin: 4px 0 0 0;
    }
</style>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Fixed Sets
# -----------------------------
STYLE_MODES = ["친한친구", "반려동물", "차분한 비서", "인생의 멘토", "감성 에디터"]

# Emoji options: 얼굴 10 + 상징 10 (이모지+단어 묶어서 보여주기)
EMOJI_OPTIONS = [
    ("😀", "기쁨"), ("🙂", "평온"), ("😐", "무덤덤"), ("😔", "우울"), ("😢", "슬픔"),
    ("😭", "벅참"), ("😡", "분노"), ("😤", "답답"), ("😴", "피곤"), ("😬", "불안"),
    ("☀️", "맑음"), ("🌙", "감성"), ("🌧️", "침잠"), ("🌿", "안정"), ("🔥", "열정"),
    ("⚡", "긴장"), ("🧊", "냉정"), ("🌊", "출렁임"), ("🫧", "가벼움"), ("🌸", "따뜻함"),
]

# 행동 10개만
ACTIVITIES = ["공부", "업무", "운동", "휴식", "약속", "창작", "정리", "이동", "소비", "회복"]

# 스페셜 질문(예시 일부) — 여기에 150개를 넣거나 파일에서 로드하면 됨
SPECIAL_QUESTIONS = [
    "오늘 하루를 색으로 표현한다면 어떤 색인가요?",
    "오늘 하루가 영화라면 제목은 무엇인가요?",
    "오늘 하루를 이모지 세 개로 표현한다면 무엇인가요?",
    "오늘 기분을 음료로 표현한다면 무엇인가요?",
    "오늘 하루가 드라마라면 부제는 무엇인가요?",
    "오늘 하루를 광고 문구로 만든다면 무엇인가요?",
    "오늘 하루가 카페라면 분위기는 어떤가요?",
    "오늘 하루가 선물이라면 포장지는 어떤 모습인가요?",
]

# 추천곡(Spotify API 없이): 태그별 큐레이션 + 커버 URL + Spotify search 링크
# 커버는 일단 "데모 이미지"로 시작해도 되고, 실제 앨범 커버 URL로 교체하면 됨.
SONGS = {
    "comfort": [
        {
            "title": "Love Poem",
            "artist": "아이유",
            "cover_url": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=400&q=60",
        },
        {
            "title": "Breathe",
            "artist": "이하이",
            "cover_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=400&q=60",
        },
    ],
    "chill": [
        {
            "title": "Sunday Morning",
            "artist": "Maroon 5",
            "cover_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=400&q=60",
        },
        {
            "title": "Some",
            "artist": "소유 & 정기고",
            "cover_url": "https://images.unsplash.com/photo-1521337706264-a414f153a5f5?auto=format&fit=crop&w=400&q=60",
        },
    ],
    "energetic": [
        {
            "title": "Dynamite",
            "artist": "BTS",
            "cover_url": "https://images.unsplash.com/photo-1524678606370-a47ad25cb82a?auto=format&fit=crop&w=400&q=60",
        },
        {
            "title": "New Rules",
            "artist": "Dua Lipa",
            "cover_url": "https://images.unsplash.com/photo-1521337581100-8ca9a73a5f79?auto=format&fit=crop&w=400&q=60",
        },
    ],
    "focus": [
        {
            "title": "Experience",
            "artist": "Ludovico Einaudi",
            "cover_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?auto=format&fit=crop&w=400&q=60",
        },
        {
            "title": "Time",
            "artist": "Hans Zimmer",
            "cover_url": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=400&q=60",
        },
    ],
    "reset": [
        {
            "title": "On The Ground",
            "artist": "ROSÉ",
            "cover_url": "https://images.unsplash.com/photo-1520975661595-6453be3f7070?auto=format&fit=crop&w=400&q=60",
        },
        {
            "title": "Good Days",
            "artist": "SZA",
            "cover_url": "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=400&q=60",
        },
    ],
    "sentimental": [
        {
            "title": "밤편지",
            "artist": "아이유",
            "cover_url": "https://images.unsplash.com/photo-1514119412350-e174d90d280e?auto=format&fit=crop&w=400&q=60",
        },
        {
            "title": "Someone Like You",
            "artist": "Adele",
            "cover_url": "https://images.unsplash.com/photo-1499415479124-43c32433a620?auto=format&fit=crop&w=400&q=60",
        },
    ],
}

# -----------------------------
# Persistence
# -----------------------------
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_profile(p):
    ensure_data_dir()
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def append_entry(entry: dict):
    ensure_data_dir()
    with open(ENTRIES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def read_entries():
    if not os.path.exists(ENTRIES_PATH):
        return []
    out = []
    with open(ENTRIES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

# -----------------------------
# State
# -----------------------------
def init_state():
    if "style_mode" not in st.session_state:
        st.session_state.style_mode = "친한친구"

    if "profile" not in st.session_state:
        st.session_state.profile = load_profile()

    if "show_onboarding" not in st.session_state:
        st.session_state.show_onboarding = (st.session_state.profile is None)

    if "today" not in st.session_state:
        st.session_state.today = date.today().isoformat()

    if "special_q" not in st.session_state:
        random.seed(st.session_state.today)
        st.session_state.special_q = random.choice(SPECIAL_QUESTIONS)

    if "step" not in st.session_state:
        st.session_state.step = 0  # 0 대기, 1~6 질문, 7 완료

    if "chat_started" not in st.session_state:
        st.session_state.chat_started = False

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []

    if "answers" not in st.session_state:
        st.session_state.answers = {
            "mood": None,
            "activities": [],
            "one_word": "",
            "best_moment": "",
            "growth": "",
            "special_answer": "",
        }

def push_app(msg: str):
    st.session_state.chat_log.append({"role": "app", "content": msg})

def push_user(msg: str):
    st.session_state.chat_log.append({"role": "user", "content": msg})

# -----------------------------
# Helpers: recommendation + closing message
# -----------------------------
def infer_tag(mood_label: str, activities: list[str], one_word: str) -> str:
    # 아주 단순 규칙 기반 (MVP)
    mood_text = (mood_label or "") + " " + (one_word or "")
    mood_text = mood_text.lower()

    # emoji hint via label keywords
    if any(k in mood_text for k in ["우울", "슬픔", "침잠", "벅참"]):
        return "comfort"
    if any(k in mood_text for k in ["감성", "따뜻함", "출렁임", "밤", "편지"]):
        return "sentimental"
    if any(k in mood_text for k in ["열정", "긴장", "맑음"]):
        return "energetic"
    if any(k in mood_text for k in ["냉정", "무덤덤", "리셋"]):
        return "reset"

    # activity hint
    if ("공부" in activities) or ("업무" in activities):
        return "focus"
    if ("휴식" in activities) or ("회복" in activities):
        return "chill"

    return "chill"

def pick_song(tag: str) -> dict:
    pool = SONGS.get(tag) or SONGS["chill"]
    # deterministic-ish per day
    seed = st.session_state.today + tag
    random.seed(seed)
    return random.choice(pool)

def spotify_search_url(title: str, artist: str) -> str:
    q = quote(f"{title} {artist}".strip())
    return f"https://open.spotify.com/search/{q}"

def shorten(text: str, n=44) -> str:
    t = (text or "").strip().replace("\n", " ")
    return t if len(t) <= n else t[:n] + "…"

def closing_message(style_mode: str, name: str, one_word: str, best: str, growth: str, mood: str) -> str:
    # 답변 기반으로 매일 다르게(씨드) — 과장 X, 2~3문장, 마지막 응원
    seed = st.session_state.today + (one_word or "") + (mood or "")
    random.seed(seed)

    best_s = shorten(best, 36)
    growth_s = shorten(growth, 36)

    cheers = [
        "오늘도 정말 수고했어요.",
        "오늘 기록을 남긴 것만으로도 충분히 잘한 일이에요.",
        "내일은 조금 더 편안한 하루가 되길 바라요.",
        "오늘의 당신에게 박수를 보내요.",
        "오늘도 잘 버텼어요.",
    ]
    cheer = random.choice(cheers)

    if style_mode == "친한친구":
        lines = [
            f"오늘은 ‘{one_word}’라는 단어가 참 잘 어울리는 하루였어요.",
            f"특히 {best_s} 그 장면이 오래 남을 것 같아요.",
            cheer,
        ]
    elif style_mode == "반려동물":
        lines = [
            f"{name}님, 오늘 기록 남겨줘서 고마워요 🐾",
            f"‘{one_word}’ 같은 하루였지만 {growth_s} 이 마음을 남긴 게 멋져요.",
            cheer,
        ]
    elif style_mode == "차분한 비서":
        lines = [
            f"오늘의 기록을 정리하면 핵심 단어는 ‘{one_word}’입니다.",
            f"인상적인 순간은 {best_s}이며, 배움은 {growth_s}로 요약됩니다.",
            cheer,
        ]
    elif style_mode == "인생의 멘토":
        lines = [
            f"오늘을 ‘{one_word}’로 정리한 감각이 아주 정확해요.",
            f"{growth_s}을 발견한 것은 앞으로의 방향을 바꿀 수 있어요.",
            cheer,
        ]
    else:  # 감성 에디터
        lines = [
            f"오늘은 ‘{one_word}’라는 단어가 하루를 조용히 감싸고 있었어요.",
            f"{best_s} 그 장면이 한 장의 사진처럼 남아 있네요.",
            cheer,
        ]
    return " ".join(lines[:3])

# -----------------------------
# Page
# -----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🧶", layout="wide")
inject_css()
init_state()

# Sidebar
with st.sidebar:
    st.subheader("대화 스타일")
    st.session_state.style_mode = st.radio(
        "오늘은 어떤 분위기로 기록할까요",
        STYLE_MODES,
        index=STYLE_MODES.index(st.session_state.style_mode),
        label_visibility="collapsed",
    )

    st.divider()
    st.subheader("성장서사 보기")
    wtab, mtab, ytab = st.tabs(["주간", "월간", "연간"])

    # (MVP) 샘플 출력 템플릿 — 실제 집계는 entries 기반으로 확장
    with wtab:
        st.caption("이번 주를 한눈에 정리해요.")
        st.markdown("- 🌿 이번 주 테마: ‘정리와 회복’")
        st.markdown("**요약 표(예시)**")
        st.table({"항목": ["기록일수", "대표 활동", "핵심 단어"], "내용": ["5일", "업무 · 회복", "버팀 · 리셋"]})
        st.markdown("**포트폴리오/자소서 틀(예시)**")
        st.markdown("- 상황: \n- 행동: \n- 결과/변화: ")

    with mtab:
        st.caption("이번 달의 흐름을 잡아드려요.")
        st.markdown("- 🌸 이번 달 테마: ‘리듬 만들기’")
        st.table({"항목": ["기록일수", "대표 활동", "핵심 단어"], "내용": ["18일", "공부 · 업무", "집중 · 페이스"]})

    with ytab:
        st.caption("올해의 큰 줄기를 확인해요.")
        st.markdown("- 🌙 올해의 키워드: ‘확장’")
        st.table({"항목": ["기록월", "대표 활동", "반복 감정"], "내용": ["12개월", "업무 · 성장", "불안 → 뿌듯"]})

# Main Title
st.markdown('<div class="dw-title">Daily Weaver</div>', unsafe_allow_html=True)

# -----------------------------
# Onboarding (compact + pretty)
# -----------------------------
if st.session_state.show_onboarding:
    st.markdown('<div class="dw-card">', unsafe_allow_html=True)
    st.markdown('<div class="dw-sub">오늘 하루를 가볍게 남겨볼까요.</div>', unsafe_allow_html=True)

    with st.form("profile_form", clear_on_submit=False):
        c1, c2 = st.columns([1.2, 1])
        with c1:
            name = st.text_input("이름", placeholder="예: 연세")
        with c2:
            age = st.number_input("나이", min_value=0, max_value=120, value=20, step=1)

        c3, c4 = st.columns([1, 1.2])
        with c3:
            gender = st.selectbox("성별", ["선택 안 함", "여성", "남성"])
        with c4:
            job = st.text_input("직업", placeholder="예: 대학생, 기획자, 개발자")

        colA, colB = st.columns(2)
        save = colA.form_submit_button("저장하고 시작", type="primary", use_container_width=True)
        skip = colB.form_submit_button("다음에 입력", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if skip:
        st.session_state.profile = {"name": "사용자", "age": None, "gender": "선택 안 함", "job": ""}
        save_profile(st.session_state.profile)
        st.session_state.show_onboarding = False
        st.rerun()

    if save:
        p = {
            "name": (name.strip() if name.strip() else "사용자"),
            "age": int(age),
            "gender": gender,
            "job": job.strip(),
        }
        st.session_state.profile = p
        save_profile(p)
        st.session_state.show_onboarding = False
        st.rerun()

    st.stop()

# -----------------------------
# Chat start
# -----------------------------
p = st.session_state.profile
name = p.get("name", "사용자")

if not st.session_state.chat_started and st.session_state.step == 0:
    st.markdown(
        '<div class="dw-card"><div class="dw-sub">'
        '오늘 기록을 시작하려면 한마디만 입력해 주세요.<br/>예: “시작하자”, “오늘 기록할래”'
        '</div></div>',
        unsafe_allow_html=True,
    )

user_msg = st.chat_input("여기에 한마디를 입력해 시작하세요")
if user_msg and not st.session_state.chat_started:
    st.session_state.chat_started = True
    st.session_state.step = 1
    push_user(user_msg)

    if st.session_state.style_mode == "차분한 비서":
        push_app(f"{name}님, 오늘의 기록을 시작하겠습니다.")
    elif st.session_state.style_mode == "반려동물":
        push_app(f"{name}님, 반가워요 🐾 오늘 기록을 시작해볼까요.")
    elif st.session_state.style_mode == "인생의 멘토":
        push_app(f"{name}님, 오늘도 한 걸음 나아가 봅시다. 기록을 시작할게요.")
    elif st.session_state.style_mode == "감성 에디터":
        push_app(f"{name}님, 오늘의 장면들을 한 줄씩 엮어볼까요.")
    else:
        push_app(f"{name}님, 오늘도 수고 많았어요. 천천히 기록해볼까요.")
    st.rerun()

# Render chat log
for m in st.session_state.chat_log:
    with st.chat_message("assistant" if m["role"] == "app" else "user"):
        st.write(m["content"])

st.write("")
st.divider()

# -----------------------------
# Steps
# -----------------------------
def next_step():
    st.session_state.step += 1
    st.rerun()

step = st.session_state.step
a = st.session_state.answers

# Step 1: Mood emoji (horizontal pill-ish)
if st.session_state.chat_started and step == 1:
    if "q1" not in st.session_state:
        push_app("오늘의 기분은 어떤가요.\n지금 마음과 가장 가까운 것을 골라주세요.")
        st.session_state.q1 = True
        st.rerun()

    opts = [f"{e} {t}" for e, t in EMOJI_OPTIONS]

    # TOSS-ish horizontal: use radio(horizontal=True)
    choice = st.radio(
        "오늘의 기분",
        opts,
        horizontal=True,
        label_visibility="collapsed",
        index=0 if a["mood"] is None else max(0, opts.index(a["mood"]))
    )
    st.markdown("<div class='dw-sub'>선택된 항목은 다음 요약과 추천곡에 반영돼요.</div>", unsafe_allow_html=True)

    if st.button("다음", type="primary"):
        a["mood"] = choice
        next_step()

# Step 2: Activities (10, multi, horizontal-ish)
elif st.session_state.chat_started and step == 2:
    if "q2" not in st.session_state:
        push_app("오늘 하루는 무엇으로 채워졌나요.\n해당하는 항목을 모두 선택해 주세요.")
        st.session_state.q2 = True
        st.rerun()

    st.markdown("<div class='dw-sub'>복수 선택이 가능해요.</div>", unsafe_allow_html=True)

    # If st.pills exists, use it for best UX; fallback to multiselect
    selected = a["activities"]

    if hasattr(st, "pills"):
        selected = st.pills(
            "오늘 한 일",
            ACTIVITIES,
            selection_mode="multi",
            default=selected,
            label_visibility="collapsed",
        )
    else:
        # fallback: multiselect (not perfect horizontal, but stable)
        selected = st.multiselect("오늘 한 일", ACTIVITIES, default=selected, label_visibility="collapsed")

    if st.button("다음", type="primary"):
        a["activities"] = selected
        next_step()

# Step 3: One word
elif st.session_state.chat_started and step == 3:
    if "q3" not in st.session_state:
        push_app("오늘 하루를 한 단어로 표현한다면 무엇인가요.\n딱 떠오르는 단어 하나만 적어주세요.")
        st.session_state.q3 = True
        st.rerun()

    one = st.text_input("한 단어", value=a["one_word"], placeholder="예: 버팀, 리셋, 반짝임, 흐림", label_visibility="collapsed")
    if st.button("다음", type="primary"):
        a["one_word"] = one.strip()
        next_step()

# Step 4: Best moment
elif st.session_state.chat_started and step == 4:
    if "q4" not in st.session_state:
        push_app("오늘 가장 기억에 남는 순간은 무엇인가요.\n떠오르는 장면을 짧게 적어도 괜찮아요.")
        st.session_state.q4 = True
        st.rerun()

    best = st.text_area("기억에 남는 순간", value=a["best_moment"], height=160, placeholder="예: 퇴근길에 들었던 노래, 누군가의 한마디, 혼자 웃었던 순간…", label_visibility="collapsed")
    if st.button("다음", type="primary"):
        a["best_moment"] = best.strip()
        next_step()

# Step 5: Growth
elif st.session_state.chat_started and step == 5:
    if "q5" not in st.session_state:
        push_app("오늘 새롭게 배우거나 성장한 점이 있나요.\n작은 깨달음도 충분히 의미 있어요.")
        st.session_state.q5 = True
        st.rerun()

    g = st.text_area("성장/배움", value=a["growth"], height=160, placeholder="예: 감정을 말로 정리하는 방법, 나의 패턴, 사람과의 거리감…", label_visibility="collapsed")
    if st.button("다음", type="primary"):
        a["growth"] = g.strip()
        next_step()

# Step 6: Special Q
elif st.session_state.chat_started and step == 6:
    if "q6" not in st.session_state:
        push_app(f"오늘의 스페셜 질문이에요.\n{st.session_state.special_q}")
        st.session_state.q6 = True
        st.rerun()

    sp = st.text_area("스페셜 질문 답변", value=a["special_answer"], height=140, label_visibility="collapsed")
    if st.button("기록 마무리", type="primary"):
        a["special_answer"] = sp.strip()
        next_step()

# Done
elif st.session_state.chat_started and step == 7:
    # closing message (dynamic)
    mood_label = a["mood"] or ""
    one_word = a["one_word"] or "기록"
    best = a["best_moment"]
    growth = a["growth"]
    style = st.session_state.style_mode

    closing = closing_message(style, name, one_word, best, growth, mood_label)
    push_app(closing)

    # pick song without Spotify API
    tag = infer_tag(mood_label, a["activities"], one_word)
    song = pick_song(tag)
    url = spotify_search_url(song["title"], song["artist"])

    # persist entry
    entry = {
        "date": st.session_state.today,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "profile": st.session_state.profile,
        "style_mode": style,
        "answers": {
            "mood": mood_label,
            "activities": a["activities"],
            "one_word": one_word,
            "best_moment": best,
            "growth": growth,
            "special_q": st.session_state.special_q,
            "special_answer": a["special_answer"],
        },
        "song": {
            "tag": tag,
            "title": song["title"],
            "artist": song["artist"],
            "cover_url": song["cover_url"],
            "spotify_url": url,
        },
    }
    append_entry(entry)

    # Render assistant message + music card
    with st.chat_message("assistant"):
        st.write(closing)
        st.write("")
        st.markdown("**오늘의 추천곡은 이 노래예요.**")
        st.caption("오늘의 분위기와 가장 잘 어울리는 곡을 골라봤어요.")

        st.markdown(
            f"""
<div class="dw-music">
    <img src="{song["cover_url"]}" width="92" height="92" />
    <div>
        <p class="dw-music-title">{song["title"]}</p>
        <p class="dw-music-artist">{song["artist"]}</p>
    </div>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.link_button("Spotify에서 듣기", url)

    # Reset button
    st.write("")
    if st.button("오늘 기록 다시 하기", use_container_width=True):
        st.session_state.step = 0
        st.session_state.chat_started = False
        st.session_state.chat_log = []
        st.session_state.answers = {
            "mood": None,
            "activities": [],
            "one_word": "",
            "best_moment": "",
            "growth": "",
            "special_answer": "",
        }
        # re-roll special q for tomorrow only; keep today's stable
        st.rerun()

# If finished step not yet moved to 7 (advance)
# After step 6 submission, next_step() already sets 7 and reruns.

