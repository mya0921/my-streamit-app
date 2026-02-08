# app.py — Daily Weaver (Streamlit, Spotify API 없이)
# 실행: streamlit run app.py

import os
import json
import random
from datetime import date, datetime, timedelta
from urllib.parse import quote
from collections import Counter

import streamlit as st


# =========================
# 기본 설정 / 경로
# =========================
APP_TITLE = "Daily Weaver"

DATA_DIR = "data"
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
ENTRIES_PATH = os.path.join(DATA_DIR, "entries.jsonl")

ASSET_LOGO = None  # 로고 쓰고 싶으면 경로 넣기


# =========================
# 고정 데이터
# =========================
STYLE_MODES = ["친한친구", "반려동물", "차분한 비서", "인생의 멘토", "감성 에디터"]

EMOJI_OPTIONS = [
    ("😀", "기쁨"), ("🙂", "평온"), ("😐", "무덤덤"), ("😔", "우울"), ("😢", "슬픔"),
    ("😭", "벅참"), ("😡", "분노"), ("😤", "답답"), ("😴", "피곤"), ("😬", "불안"),
    ("☀️", "맑음"), ("🌙", "감성"), ("🌧️", "침잠"), ("🌿", "안정"), ("🔥", "열정"),
    ("⚡", "긴장"), ("🧊", "냉정"), ("🌊", "출렁임"), ("🫧", "가벼움"), ("🌸", "따뜻함"),
]

ACTIVITIES = ["공부", "업무", "운동", "휴식", "약속", "창작", "정리", "이동", "소비", "회복"]

SPECIAL_QUESTIONS = [
    "오늘 하루를 색으로 표현한다면 어떤 색인가요?",
    "오늘 하루가 영화라면 제목은 무엇인가요?",
    "오늘 하루를 이모지 세 개로 표현한다면 무엇인가요?",
    "오늘 기분을 음식으로 표현한다면 무엇인가요?",
    "오늘 하루가 카페라면 분위기는 어떤가요?",
    "오늘 하루를 광고 문구로 만든다면 무엇인가요?",
    "오늘 하루가 선물이라면 포장지는 어떤 모습인가요?",
    "오늘 하루를 한 컷 만화로 그린다면 어떤 장면인가요?",
    # ... (150개로 확장)
]

SONGS = {
    "comfort": [
        {"title": "Love Poem", "artist": "아이유",
         "cover_url": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=900&q=60"},
        {"title": "Breathe", "artist": "이하이",
         "cover_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=900&q=60"},
    ],
    "chill": [
        {"title": "Sunday Morning", "artist": "Maroon 5",
         "cover_url": "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=900&q=60"},
        {"title": "Some", "artist": "소유 & 정기고",
         "cover_url": "https://images.unsplash.com/photo-1521337581100-8ca9a73a5f79?auto=format&fit=crop&w=900&q=60"},
    ],
    "energetic": [
        {"title": "Dynamite", "artist": "BTS",
         "cover_url": "https://images.unsplash.com/photo-1524678606370-a47ad25cb82a?auto=format&fit=crop&w=900&q=60"},
        {"title": "New Rules", "artist": "Dua Lipa",
         "cover_url": "https://images.unsplash.com/photo-1520975661595-6453be3f7070?auto=format&fit=crop&w=900&q=60"},
    ],
    "focus": [
        {"title": "Experience", "artist": "Ludovico Einaudi",
         "cover_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?auto=format&fit=crop&w=900&q=60"},
        {"title": "Time", "artist": "Hans Zimmer",
         "cover_url": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=900&q=60"},
    ],
    "reset": [
        {"title": "Good Days", "artist": "SZA",
         "cover_url": "https://images.unsplash.com/photo-1499415479124-43c32433a620?auto=format&fit=crop&w=900&q=60"},
        {"title": "On The Ground", "artist": "ROSÉ",
         "cover_url": "https://images.unsplash.com/photo-1521337706264-a414f153a5f5?auto=format&fit=crop&w=900&q=60"},
    ],
    "sentimental": [
        {"title": "밤편지", "artist": "아이유",
         "cover_url": "https://images.unsplash.com/photo-1521337706264-a414f153a5f5?auto=format&fit=crop&w=900&q=60"},
        {"title": "Someone Like You", "artist": "Adele",
         "cover_url": "https://images.unsplash.com/photo-1514119412350-e174d90d280e?auto=format&fit=crop&w=900&q=60"},
    ],
}

TAG_LABEL = {
    "comfort": "위로",
    "chill": "잔잔",
    "energetic": "에너지",
    "focus": "집중",
    "reset": "리셋",
    "sentimental": "감성",
}


# =========================
# 스타일(CSS): iMessage-like bubbles + 연핑크 더 연하게 + 음악 카드 버블용
# =========================
def inject_css():
    st.markdown(
        """
<style>
:root{
  --bg: #F5F5F7;
  --text: #111111;
  --muted: rgba(60,60,67,0.72);
  --hairline: rgba(60,60,67,0.12);

  /* Pink theme (soft) */
  --accent: #F7B6C8;
  --accent-strong: #F48FB1;
  --accent-soft: rgba(247,182,200,0.18);

  /* ✅ User bubble: 더 연하게 */
  --you-top: #FBE1E8;     /* very light pink */
  --you-bottom: #F7C8D6;  /* soft pink */
  --bubble-you: linear-gradient(180deg, var(--you-top) 0%, var(--you-bottom) 100%);
  --bubble-you-text: #111;

  /* Assistant bubble */
  --bubble-them: rgba(255,255,255,0.96);
  --bubble-them-text: #111;

  --bubble-shadow: 0 10px 26px rgba(0,0,0,0.08);
  --radius: 20px;
}

.stApp{
  background:
    radial-gradient(1100px 700px at 15% -10%, rgba(247,182,200,0.22) 0%, rgba(245,245,247,0) 60%),
    radial-gradient(900px 600px at 98% 12%, rgba(247,182,200,0.16) 0%, rgba(245,245,247,0) 55%),
    var(--bg) !important;
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
               "Apple SD Gothic Neo", "Pretendard", "Noto Sans KR", Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}

.main .block-container{
  max-width: 980px;
  padding-top: 1.3rem;
  padding-bottom: 2.6rem;
}

/* Sidebar glass */
section[data-testid="stSidebar"]{
  background: rgba(255,255,255,0.70) !important;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-right: 1px solid var(--hairline) !important;
}

/* Header */
.dw-header{ margin: 0 0 10px 0; }
.dw-title{
  font-size: 30px;
  font-weight: 900;
  letter-spacing: -0.7px;
  margin: 0 0 4px 0;
}
.dw-sub{
  font-size: 14px;
  color: var(--muted);
  margin: 0;
  line-height: 1.5;
}

/* Chat wrapper (no box) */
.dw-chat{
  padding: 10px 8px;
  border: none;
  background: transparent;
  box-shadow: none;
}

/* Rows */
.dw-row{ display:flex; margin: 10px 0; }
.dw-row.them{ justify-content:flex-start; }
.dw-row.you{ justify-content:flex-end; }

/* Bubble */
.dw-bubble{
  max-width: 78%;
  padding: 10px 12px;
  border-radius: var(--radius);
  box-shadow: var(--bubble-shadow);
  position: relative;
  word-break: break-word;
  line-height: 1.55;
  font-size: 15px;
}

/* Assistant bubble */
.dw-bubble.them{
  background: var(--bubble-them);
  color: var(--bubble-them-text);
  border: 1px solid rgba(60,60,67,0.10);
  border-bottom-left-radius: 8px;
}
.dw-bubble.them:after{
  content:"";
  position:absolute;
  left:-6px;
  bottom: 10px;
  width: 10px;
  height: 10px;
  background: var(--bubble-them);
  border-left: 1px solid rgba(60,60,67,0.10);
  border-bottom: 1px solid rgba(60,60,67,0.10);
  transform: rotate(45deg);
}

/* ✅ User bubble (lighter) */
.dw-bubble.you{
  background: var(--bubble-you);
  color: var(--bubble-you-text);
  border: 1px solid rgba(244,143,177,0.12);
  border-bottom-right-radius: 8px;
}
.dw-bubble.you:after{
  content:"";
  position:absolute;
  right:-6px;
  bottom: 10px;
  width: 10px;
  height: 10px;
  background: var(--you-bottom);
  border-right: 1px solid rgba(244,143,177,0.12);
  border-bottom: 1px solid rgba(244,143,177,0.12);
  transform: rotate(45deg);
}

/* Composer wrapper (no box) */
.dw-composer{
  margin-top: 12px;
  border: none;
  background: transparent;
  box-shadow: none;
  padding: 0;
}
.dw-hint{
  font-size: 13px;
  color: var(--muted);
  margin: 0 0 10px 2px;
}

/* Inputs */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stMultiSelect div[data-baseweb="select"] > div,
.stSelectbox div[data-baseweb="select"] > div{
  border-radius: 16px !important;
  border: 1px solid rgba(60,60,67,0.18) !important;
  background: rgba(255,255,255,0.92) !important;
  box-shadow: 0 1px 0 rgba(0,0,0,0.03);
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus{
  outline: none !important;
  border-color: rgba(247,182,200,0.65) !important;
  box-shadow: 0 0 0 4px var(--accent-soft) !important;
}

/* Buttons */
button[kind="primary"]{
  background: linear-gradient(180deg, rgba(251,225,232,1) 0%, rgba(247,200,214,1) 100%) !important;
  color: #111 !important;
  border: none !important;
  border-radius: 999px !important;
  font-weight: 900 !important;
  padding: 0.62rem 1.05rem !important;
  box-shadow: 0 12px 26px rgba(244,143,177,0.18) !important;
}
div.stButton > button:not([kind="primary"]){
  background: rgba(255,255,255,0.85) !important;
  border: 1px solid var(--hairline) !important;
  border-radius: 999px !important;
  font-weight: 800 !important;
  box-shadow: 0 10px 22px rgba(0,0,0,0.06) !important;
}

/* ✅ Music bubble content (inside assistant bubble) */
.dw-music-inbubble{
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(60,60,67,0.10);
}

.dw-music-card{
  display:flex;
  gap: 14px;
  align-items:center;
  padding: 10px;
  border-radius: 18px;
  border: 1px solid rgba(60,60,67,0.12);
  background: rgba(255,255,255,0.90);
  box-shadow: 0 12px 26px rgba(0,0,0,0.08);
}

/* ✅ Cover bigger */
.dw-cover{
  width: 160px;
  height: 160px;
  border-radius: 18px;
  object-fit: cover;
  border: 1px solid rgba(60,60,67,0.12);
  box-shadow: 0 12px 26px rgba(0,0,0,0.12);
}

.dw-music-title{ font-size: 18px; font-weight: 900; margin:0; letter-spacing:-0.2px; }
.dw-music-artist{ font-size: 14px; color: var(--muted); margin: 6px 0 0 0; }
.dw-tag{
  display:inline-block;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(247,182,200,0.9);
  background: rgba(247,182,200,0.18);
  font-weight: 900;
  color: rgba(60,60,67,0.95);
  margin-top: 10px;
}

/* Spacing */
div[data-testid="stMarkdown"]{ margin-bottom: 0.35rem; }
</style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# 저장/로드
# =========================
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_profile(p: dict):
    ensure_data_dir()
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def append_entry(entry: dict):
    ensure_data_dir()
    with open(ENTRIES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def read_entries() -> list[dict]:
    if not os.path.exists(ENTRIES_PATH):
        return []
    out = []
    with open(ENTRIES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# =========================
# 유틸
# =========================
def spotify_search_url(title: str, artist: str) -> str:
    q = quote(f"{title} {artist}".strip())
    return f"https://open.spotify.com/search/{q}"

def shorten(text: str, n=40) -> str:
    t = (text or "").strip().replace("\n", " ")
    return t if len(t) <= n else t[:n] + "…"

def today_seed() -> str:
    return st.session_state.today

def pick_today_special_question() -> str:
    random.seed(today_seed())
    return random.choice(SPECIAL_QUESTIONS)

def infer_tag(mood_text: str, activities: list[str], one_word: str) -> str:
    text = f"{mood_text} {one_word}".lower()

    if any(k in text for k in ["우울", "슬픔", "침잠", "벅참"]):
        return "comfort"
    if any(k in text for k in ["감성", "따뜻함", "출렁임", "밤"]):
        return "sentimental"
    if any(k in text for k in ["열정", "긴장", "맑음"]):
        return "energetic"
    if any(k in text for k in ["냉정", "무덤덤", "리셋"]):
        return "reset"
    if ("공부" in activities) or ("업무" in activities):
        return "focus"
    if ("휴식" in activities) or ("회복" in activities):
        return "chill"
    return "chill"

def pick_song(tag: str) -> dict:
    pool = SONGS.get(tag, SONGS["chill"])
    random.seed(today_seed() + tag)
    return random.choice(pool)

def closing_message(style_mode: str, name: str, one_word: str, best: str, growth: str) -> str:
    best_s = shorten(best, 36)
    growth_s = shorten(growth, 36)
    random.seed(today_seed() + (one_word or "") + best_s)

    cheers = [
        "오늘도 정말 수고했어요.",
        "오늘 하루를 기록한 것만으로도 충분히 잘한 일이에요.",
        "내일은 조금 더 편안한 하루가 되길 바라요.",
        "오늘의 당신에게 박수를 보내요.",
        "오늘도 잘 버텼어요.",
    ]
    cheer = random.choice(cheers)

    if style_mode == "친한친구":
        return f"오늘은 **{one_word}**라는 단어가 참 잘 어울리는 하루였어요. 특히 {best_s} 그 장면이 오래 남을 것 같아요. {cheer}"
    if style_mode == "반려동물":
        return f"{name}님, 오늘 기록 남겨줘서 고마워요 🐾 오늘은 **{one_word}** 같은 하루였네요. {growth_s} 이 마음을 남긴 게 멋져요. {cheer}"
    if style_mode == "차분한 비서":
        return f"{name}님, 오늘의 기록을 정리했습니다. 핵심 단어는 **{one_word}**이며, 기억에 남는 순간은 {best_s}입니다. 성장 포인트는 {growth_s}로 요약됩니다. {cheer}"
    if style_mode == "인생의 멘토":
        return f"오늘을 **{one_word}**로 정리한 감각이 정확해요. {growth_s}을 발견한 것은 앞으로의 방향을 바꿀 수 있어요. {cheer}"
    return f"오늘은 **{one_word}**라는 단어가 하루를 조용히 감싸고 있었어요. {best_s} 그 장면이 한 장의 사진처럼 남아 있네요. {cheer}"

def parse_entry_date(e: dict):
    d = e.get("date")
    if not d:
        return None
    try:
        return datetime.fromisoformat(d).date()
    except Exception:
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None

def filter_entries_last_days(entries: list[dict], days: int) -> list[dict]:
    today_ = datetime.fromisoformat(st.session_state.today).date()
    start = today_ - timedelta(days=days - 1)
    out = []
    for e in entries:
        ed = parse_entry_date(e)
        if ed and start <= ed <= today_:
            out.append(e)
    return out


# =========================
# 성장서사(주/월/년) 출력
# =========================
def show_growth_summary(entries: list[dict], title: str):
    if not entries:
        st.info("아직 기록이 없어요. 오늘의 기록을 먼저 남겨보세요.", icon="🧶")
        return

    moods, activities, words = [], [], []
    for e in entries:
        ans = e.get("answers", {})
        moods.append(ans.get("mood", ""))
        activities.extend(ans.get("activities", []))
        words.append(ans.get("one_word", ""))

    mood_top = [m for m, _ in Counter(moods).most_common(1)]
    act_top = [a for a, _ in Counter(activities).most_common(3)]
    word_top = [w for w, _ in Counter(words).most_common(3)]

    theme_emoji = "🌿"
    theme_line = "이번 기간은 기록이 ‘정리’로 연결되는 흐름이 보여요."
    if act_top:
        if "회복" in act_top or "휴식" in act_top:
            theme_emoji = "🌸"
            theme_line = "이번 기간은 회복과 리듬을 되찾는 장면이 많았어요."
        if "공부" in act_top or "업무" in act_top:
            theme_emoji = "📌"
            theme_line = "이번 기간은 몰입과 책임의 장면이 두드러져요."

    st.markdown(f"### {theme_emoji} {title}")

    table = {
        "항목": ["기록일수", "대표 활동", "핵심 단어", "대표 기분"],
        "내용": [
            f"{len(entries)}일",
            ", ".join(act_top) if act_top else "-",
            ", ".join([x for x in word_top if x]) if word_top else "-",
            mood_top[0] if mood_top else "-",
        ],
    }
    st.table(table)

    st.markdown("**이번 기간의 흐름**")
    st.write(f"- {theme_line}")
    if act_top:
        st.write(f"- 자주 등장한 활동은 **{', '.join(act_top)}**였어요.")
    if word_top and any(word_top):
        st.write(f"- 자주 등장한 단어는 **{', '.join([x for x in word_top if x])}**였어요.")

    st.markdown("**자소서·포트폴리오 소재 후보**")
    st.write("**소재 1**")
    st.write("- 상황: ")
    st.write("- 행동: ")
    st.write("- 결과/변화: ")

    st.write("**소재 2**")
    st.write("- 상황: ")
    st.write("- 행동: ")
    st.write("- 결과/변화: ")


# =========================
# 상태 초기화
# =========================
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
        st.session_state.special_q = pick_today_special_question()

    if "step" not in st.session_state:
        st.session_state.step = 0  # 0 대기, 1~6 질문, 7 완료

    if "chat_started" not in st.session_state:
        st.session_state.chat_started = False

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []

    if "final_pushed" not in st.session_state:
        st.session_state.final_pushed = False

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


# =========================
# iMessage-style chat renderer
# =========================
def render_chat():
    st.markdown('<div class="dw-chat">', unsafe_allow_html=True)

    if not st.session_state.chat_log:
        st.markdown('<div class="dw-hint">아래에 한마디 보내면 대화가 시작돼요.</div>', unsafe_allow_html=True)

    for m in st.session_state.chat_log:
        role = "them" if m["role"] == "app" else "you"
        content = (m.get("content") or "").replace("\n", "<br/>")
        st.markdown(
            f"""
<div class="dw-row {role}">
  <div class="dw-bubble {role}">{content}</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# 선택 UI
# =========================
def choose_single_pills(label: str, options: list[str], key: str):
    if hasattr(st, "pills"):
        return st.pills(label, options, selection_mode="single", default=st.session_state.get(key), key=key, label_visibility="collapsed")
    else:
        return st.radio(label, options, horizontal=True, key=key, label_visibility="collapsed")

def choose_multi_pills(label: str, options: list[str], key: str):
    if hasattr(st, "pills"):
        return st.pills(label, options, selection_mode="multi", default=st.session_state.get(key, []), key=key, label_visibility="collapsed")
    else:
        return st.multiselect(label, options, default=st.session_state.get(key, []), key=key, label_visibility="collapsed")

def next_step():
    st.session_state.step += 1
    st.rerun()


# =========================
# 앱 시작
# =========================
st.set_page_config(page_title=APP_TITLE, page_icon="🧶", layout="wide")
inject_css()
init_state()


# ---- Sidebar ----
with st.sidebar:
    st.subheader("대화 스타일")
    st.session_state.style_mode = st.radio(
        "오늘은 어떤 분위기로 기록할까요",
        STYLE_MODES,
        index=STYLE_MODES.index(st.session_state.style_mode),
        label_visibility="collapsed",
    )

    st.divider()
    st.subheader("내 프로필")
    prof = st.session_state.profile or {}
    prof_line = " · ".join([x for x in [
        prof.get("name", ""),
        (f"{prof.get('age')}세" if prof.get("age") not in [None, ""] else ""),
        (prof.get("gender") if prof.get("gender") not in [None, ""] else ""),
        prof.get("job", "")
    ] if x])
    if prof_line:
        st.caption(prof_line)
    if st.button("프로필 수정", use_container_width=True):
        st.session_state.show_onboarding = True
        st.rerun()

    st.divider()
    st.subheader("성장서사 보기")
    all_entries = read_entries()
    wtab, mtab, ytab = st.tabs(["주간", "월간", "연간"])
    with wtab:
        show_growth_summary(filter_entries_last_days(all_entries, 7), "이번 주 성장서사")
    with mtab:
        show_growth_summary(filter_entries_last_days(all_entries, 30), "이번 달 성장서사")
    with ytab:
        show_growth_summary(filter_entries_last_days(all_entries, 365), "올해 성장서사")


# ---- Main Header ----
if ASSET_LOGO and os.path.exists(ASSET_LOGO):
    st.image(ASSET_LOGO, width=160)

st.markdown(
    f"""
<div class="dw-header">
  <div class="dw-title">{APP_TITLE}</div>
  <div class="dw-sub"><b>하루를 간단히 기록해보세요.</b></div>
  <div class="dw-sub">기록이 쌓이면 경험이 정리되고, 포트폴리오의 이야기가 만들어져요.</div>
</div>
    """,
    unsafe_allow_html=True,
)


# =========================
# Onboarding
# =========================
if st.session_state.show_onboarding:
    st.markdown('<div class="dw-composer">', unsafe_allow_html=True)
    st.markdown('<div class="dw-hint"><b>처음 한 번만 입력</b>하면 더 자연스럽게 기록할 수 있어요. (사이드바에서 언제든 수정 가능)</div>', unsafe_allow_html=True)

    with st.form("profile_form", clear_on_submit=False):
        current = st.session_state.profile or {}
        c1, c2 = st.columns([1.3, 1])
        with c1:
            name = st.text_input("이름", value=current.get("name", ""), placeholder="예: 연세")
        with c2:
            age_val = current.get("age")
            age = st.number_input("나이", min_value=0, max_value=120, value=int(age_val) if isinstance(age_val, int) else 20, step=1)

        c3, c4 = st.columns([1, 1.3])
        with c3:
            gender = st.selectbox("성별", ["선택 안 함", "여성", "남성"],
                                  index=["선택 안 함", "여성", "남성"].index(current.get("gender", "선택 안 함")))
        with c4:
            job = st.text_input("직업", value=current.get("job", ""), placeholder="예: 대학생, 기획자, 개발자")

        colA, colB = st.columns(2)
        save = colA.form_submit_button("저장", type="primary", use_container_width=True)
        cancel = colB.form_submit_button("취소", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if cancel:
        if st.session_state.profile is None:
            st.session_state.profile = {"name": "사용자", "age": None, "gender": "선택 안 함", "job": ""}
            save_profile(st.session_state.profile)
        st.session_state.show_onboarding = False
        st.rerun()

    if save:
        p = {
            "name": name.strip() if name.strip() else "사용자",
            "age": int(age),
            "gender": gender,
            "job": job.strip(),
        }
        st.session_state.profile = p
        save_profile(p)
        st.session_state.show_onboarding = False
        st.rerun()

    st.stop()


# =========================
# Chat Area
# =========================
render_chat()
st.write("")


# =========================
# 대기 상태(채팅 시작)
# =========================
if not st.session_state.chat_started and st.session_state.step == 0:
    start_msg = st.chat_input("한마디만 보내서 기록을 시작해요 (예: 시작하자)")
    if start_msg:
        st.session_state.chat_started = True
        st.session_state.step = 1
        push_user(start_msg)

        name = (st.session_state.profile or {}).get("name", "사용자")
        mode = st.session_state.style_mode
        if mode == "차분한 비서":
            push_app(f"{name}님, 오늘의 기록을 시작하겠습니다.")
        elif mode == "반려동물":
            push_app(f"{name}님, 반가워요 🐾 오늘 기록을 시작해볼까요.")
        elif mode == "인생의 멘토":
            push_app(f"{name}님, 오늘도 한 걸음 나아가 봅시다. 기록을 시작할게요.")
        elif mode == "감성 에디터":
            push_app(f"{name}님, 오늘의 장면들을 조용히 엮어볼까요.")
        else:
            push_app(f"{name}님, 오늘도 수고 많았어요. 천천히 기록해볼까요.")

        push_app("오늘의 기분은 어떤가요? 지금 마음과 가장 가까운 걸 골라주세요.")
        st.rerun()

    st.stop()


# =========================
# 질문 플로우
# =========================
step = st.session_state.step
a = st.session_state.answers


# Step 1 — 기분 선택
if step == 1:
    st.markdown('<div class="dw-composer">', unsafe_allow_html=True)
    st.markdown('<div class="dw-hint">기분을 선택하고 <b>전송</b>하세요.</div>', unsafe_allow_html=True)

    options = [f"{e} {t}" for e, t in EMOJI_OPTIONS]
    chosen = choose_single_pills("mood", options, key="mood_choice")

    col1, col2 = st.columns([1, 1])
    send = col2.button("전송", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if send:
        a["mood"] = chosen
        push_user(chosen)
        push_app("오늘 하루는 무엇으로 채워졌나요? 오늘 한 일을 모두 선택해 주세요.")
        next_step()


# Step 2 — 활동 선택(복수)
elif step == 2:
    st.markdown('<div class="dw-composer">', unsafe_allow_html=True)
    st.markdown('<div class="dw-hint">오늘 한 일을 고르고 <b>전송</b>하세요. (복수 선택 가능)</div>', unsafe_allow_html=True)

    selected = choose_multi_pills("activities", ACTIVITIES, key="activity_choice")

    col1, col2 = st.columns([1, 1])
    send = col2.button("전송", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if send:
        a["activities"] = selected
        text = ", ".join(selected) if selected else "(선택 없음)"
        push_user(text)
        push_app("한 단어로 오늘을 표현한다면 무엇인가요? 딱 떠오르는 단어 하나만 적어주세요.")
        next_step()


# Step 3 — 한 단어(텍스트)
elif step == 3:
    msg = st.chat_input("한 단어를 보내주세요 (예: 버팀, 리셋, 반짝임)")
    if msg:
        a["one_word"] = msg.strip()
        push_user(a["one_word"] or "(빈 값)")
        push_app("가장 기억에 남는 순간은 무엇인가요? 떠오르는 장면을 자유롭게 적어주세요.")
        next_step()


# Step 4 — 베스트 모먼트(멀티라인)
elif step == 4:
    st.markdown('<div class="dw-composer">', unsafe_allow_html=True)
    st.markdown('<div class="dw-hint">장면을 적고 <b>전송</b>하세요. (길게 적어도 좋아요)</div>', unsafe_allow_html=True)

    best = st.text_area(
        "",
        value=a["best_moment"],
        height=140,
        placeholder="예: 퇴근길에 들었던 노래, 누군가의 한마디, 혼자 웃었던 순간…",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 1])
    send = col2.button("전송", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if send:
        a["best_moment"] = best.strip()
        push_user(a["best_moment"] if a["best_moment"] else "(빈 값)")
        push_app("새롭게 배우거나 성장한 점이 있나요? 작은 깨달음도 충분히 의미 있어요.")
        next_step()


# Step 5 — 성장(멀티라인)
elif step == 5:
    st.markdown('<div class="dw-composer">', unsafe_allow_html=True)
    st.markdown('<div class="dw-hint">성장 포인트를 적고 <b>전송</b>하세요.</div>', unsafe_allow_html=True)

    g = st.text_area(
        "",
        value=a["growth"],
        height=140,
        placeholder="예: 감정을 말로 정리하는 방법, 나의 패턴, 사람과의 거리감…",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 1])
    send = col2.button("전송", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if send:
        a["growth"] = g.strip()
        push_user(a["growth"] if a["growth"] else "(빈 값)")
        push_app(f"오늘의 스페셜 질문이에요.\n{st.session_state.special_q}")
        next_step()


# Step 6 — 스페셜(멀티라인)
elif step == 6:
    st.markdown('<div class="dw-composer">', unsafe_allow_html=True)
    st.markdown('<div class="dw-hint">답을 적고 <b>기록 마무리</b>를 눌러주세요.</div>', unsafe_allow_html=True)

    sp = st.text_area(
        "",
        value=a["special_answer"],
        height=120,
        placeholder="자유롭게 답해 주세요 :)",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 1])
    done = col2.button("기록 마무리", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if done:
        a["special_answer"] = sp.strip()
        push_user(a["special_answer"] if a["special_answer"] else "(빈 값)")
        next_step()


# Step 7 — 완료: 마무리 + 추천곡을 말풍선 안에
elif step == 7:
    profile = st.session_state.profile or {}
    name = profile.get("name", "사용자")

    mood = a["mood"] or ""
    one_word = a["one_word"] or "기록"
    best = a["best_moment"]
    growth = a["growth"]

    closing = closing_message(st.session_state.style_mode, name, one_word, best, growth)
    tag = infer_tag(mood, a["activities"], one_word)
    song = pick_song(tag)
    link = spotify_search_url(song["title"], song["artist"])

    entry = {
        "date": st.session_state.today,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "profile": profile,
        "style_mode": st.session_state.style_mode,
        "answers": {
            "mood": mood,
            "activities": a["activities"],
            "one_word": one_word,
            "best_moment": best,
            "growth": growth,
            "special_q": st.session_state.special_q,
            "special_answer": a["special_answer"],
        },
        "closing_message": closing,
        "song": {
            "tag": tag,
            "title": song["title"],
            "artist": song["artist"],
            "cover_url": song["cover_url"],
            "spotify_url": link,
        },
    }
    append_entry(entry)

    # ✅ 한 번만: "마무리 + 음악카드"를 하나의 말풍선(assistant)로 넣기
    if not st.session_state.final_pushed:
        music_html = f"""
<b>{closing}</b>
<div class="dw-music-inbubble">
  <div style="font-weight:900; margin-bottom:8px;">오늘의 추천곡 🎧</div>
  <div class="dw-music-card">
    <img class="dw-cover" src="{song["cover_url"]}" />
    <div>
      <p class="dw-music-title">{song["title"]}</p>
      <p class="dw-music-artist">{song["artist"]}</p>
      <div class="dw-tag">{TAG_LABEL.get(tag, tag)}</div>
      <div style="margin-top:10px;">
        <a href="{link}" target="_blank" style="text-decoration:none; font-weight:900; color: rgba(60,60,67,0.95);">
          Spotify에서 듣기 →
        </a>
      </div>
    </div>
  </div>
</div>
        """.strip()

        push_app(music_html)
        st.session_state.final_pushed = True
        st.rerun()

    # 다시하기 버튼만 아래에
    st.markdown('<div class="dw-composer">', unsafe_allow_html=True)
    if st.button("오늘 기록 다시 하기", use_container_width=True):
        st.session_state.step = 0
        st.session_state.chat_started = False
        st.session_state.chat_log = []
        st.session_state.final_pushed = False
        st.session_state.answers = {
            "mood": None,
            "activities": [],
            "one_word": "",
            "best_moment": "",
            "growth": "",
            "special_answer": "",
        }
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
