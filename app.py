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
SPECIAL_HISTORY_PATH = os.path.join(DATA_DIR, "special_history.json")

ASSET_LOGO = None


# =========================
# 고정 데이터
# =========================
STYLE_MODES = ["친한친구", "반려동물", "차분한 비서", "인생의 멘토", "감성 에디터"]
STYLE_EMOJI = {
    "친한친구": "💬",
    "반려동물": "🐾",
    "차분한 비서": "🗂️",
    "인생의 멘토": "🧭",
    "감성 에디터": "📝",
}
STYLE_OPTIONS = [f"{STYLE_EMOJI[s]} {s}" for s in STYLE_MODES]

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
    "오늘 하루에 제목을 붙인다면 어떤 제목이 어울리나요?",
    "오늘 가장 마음에 남은 말 한마디가 있다면 무엇인가요?",
    "오늘 나를 가장 지탱해준 것은 무엇이었나요?",
    "오늘 가장 나답다고 느낀 순간은 언제였나요?",
    "오늘의 나에게 점수를 준다면 몇 점인가요?",
    "오늘은 어떤 감정이 가장 오래 머물렀나요?",
    "오늘 내가 가장 잘한 선택은 무엇이었나요?",
    "오늘 하루가 한 장의 사진이라면 어떤 장면인가요?",
    "오늘의 나는 어떤 날씨 같았나요?",
    "오늘 내 마음을 가장 잘 표현하는 노래 제목은 무엇인가요?",
    "오늘 가장 후회되는 순간이 있다면 무엇인가요?",
    "오늘 가장 감사했던 순간은 무엇이었나요?",
    "오늘 하루를 한 문장으로 요약한다면?",
    "오늘 내가 나를 칭찬해주고 싶은 이유는 무엇인가요?",
    "오늘 내가 놓치고 싶지 않은 순간은 무엇인가요?",
    "오늘은 어떤 사람으로 기억되고 싶나요?",
    "오늘 나를 가장 흔든 사건은 무엇이었나요?",
    "오늘은 어떤 색감의 하루였나요? (파스텔/모노톤/네온 등)",
    "오늘 내 마음에 가장 가까운 단어는 무엇인가요?",
    "오늘 하루를 물건 하나로 표현한다면 무엇인가요?",
    "오늘 하루가 여행지라면 어디일까요?",
    "오늘 하루를 만약 그림으로 그린다면 어떤 스타일일까요?",
    "오늘 내가 더 잘하고 싶었던 것은 무엇인가요?",
    "오늘 내가 가장 많이 했던 생각은 무엇인가요?",
    "오늘 나를 웃게 만든 건 무엇이었나요?",
    "오늘 하루는 어떤 향이 날까요?",
    "오늘의 나에게 필요한 한마디는 무엇인가요?",
    "오늘 하루를 만약 일기 제목으로 붙이면?",
    "오늘은 어떤 순간이 가장 뿌듯했나요?",
    "오늘 하루는 어떤 감정으로 시작했고 어떤 감정으로 끝났나요?",
    "오늘은 어떤 순간이 가장 나를 위로했나요?",
    "오늘 하루를 다시 산다면 가장 먼저 바꾸고 싶은 건 무엇인가요?",
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


# =========================
# CSS (iMessage + Apple Music)
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

  --accent: #F7B6C8;
  --accent-strong: #F48FB1;
  --accent-soft: rgba(247,182,200,0.18);

  --you-top: #FBE1E8;
  --you-bottom: #F7C8D6;
  --bubble-you: linear-gradient(180deg, var(--you-top) 0%, var(--you-bottom) 100%);
  --bubble-you-text: #111;

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

/* content area */
.main .block-container{
  max-width: 980px;
  padding-top: 1.1rem;
  padding-bottom: 6.2rem;
}

/* sidebar glass */
section[data-testid="stSidebar"]{
  background: rgba(255,255,255,0.58) !important;
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-right: 1px solid rgba(60,60,67,0.10) !important;
}
section[data-testid="stSidebar"] .block-container{ padding-top: 1.1rem; }
section[data-testid="stSidebar"] h3{
  font-size: 14px !important;
  font-weight: 900 !important;
  letter-spacing: -0.2px;
  color: rgba(60,60,67,0.92);
  margin-bottom: 0.6rem;
}
section[data-testid="stSidebar"] hr{
  border: none;
  height: 1px;
  background: rgba(60,60,67,0.10);
  margin: 0.9rem 0;
}
section[data-testid="stSidebar"] div[role="radiogroup"]{
  padding: 8px 10px;
  border-radius: 16px;
  background: rgba(255,255,255,0.55);
  border: 1px solid rgba(60,60,67,0.10);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  padding: 8px 8px;
  border-radius: 12px;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
  background: rgba(247,182,200,0.12);
}

/* profile chip */
.dw-profile-chip{
  display:flex;
  align-items:center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 18px;
  border: 1px solid rgba(60,60,67,0.10);
  background: rgba(255,255,255,0.55);
}
.dw-avatar{
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: radial-gradient(circle at 30% 30%, rgba(247,182,200,1) 0%, rgba(247,182,200,0.35) 55%, rgba(255,255,255,0) 75%);
  border: 1px solid rgba(244,143,177,0.18);
  box-shadow: 0 10px 18px rgba(244,143,177,0.10);
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight: 900;
  color: rgba(60,60,67,0.92);
}
.dw-profile-name{
  font-weight: 900;
  letter-spacing: -0.2px;
  font-size: 13px;
  margin: 0;
}
.dw-profile-meta{
  font-size: 12px;
  color: rgba(60,60,67,0.72);
  margin: 2px 0 0 0;
}

/* Tabs pink */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"]{
  color: rgba(244,143,177,1) !important;
}
.stTabs [data-baseweb="tab-highlight"]{
  background-color: rgba(244,143,177,1) !important;
}

/* header */
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

/* chat */
.dw-chat{ padding: 12px 8px; }
.dw-row{ display:flex; margin: 10px 0; }
.dw-row.them{ justify-content:flex-start; }
.dw-row.you{ justify-content:flex-end; }

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

/* assistant bubble */
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

/* user bubble */
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

/* fixed composer */
.dw-fixed-composer{
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 14px 18px 18px 18px;
  background: rgba(245,245,247,0.70);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-top: 1px solid rgba(60,60,67,0.12);
  z-index: 9999;
}
.dw-fixed-inner{
  max-width: 980px;
  margin: 0 auto;
  display:flex;
  gap: 10px;
  align-items:flex-end;
}

/* inputs */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stMultiSelect div[data-baseweb="select"] > div,
.stSelectbox div[data-baseweb="select"] > div{
  border-radius: 16px !important;
  border: 1px solid rgba(60,60,67,0.18) !important;
  background: rgba(255,255,255,0.92) !important;
}
.stTextArea textarea:focus{
  outline: none !important;
  border-color: rgba(247,182,200,0.65) !important;
  box-shadow: 0 0 0 4px var(--accent-soft) !important;
}

/* buttons */
button[kind="primary"],
div[data-testid="stFormSubmitButton"] button{
  background: linear-gradient(180deg, rgba(251,225,232,1) 0%, rgba(247,200,214,1) 100%) !important;
  color: #111 !important;
  border: none !important;
  border-radius: 999px !important;
  font-weight: 900 !important;
  padding: 0.62rem 1.05rem !important;
  box-shadow: 0 12px 26px rgba(244,143,177,0.18) !important;
}

/* =====================================================
   MUSIC: 여백 완전 제거 + glossy album cover
   ===================================================== */

/* wrap 자체를 없애서 bubble 내부 padding만 남게 */
.dw-music-wrap{
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
}

/* 카드도 그냥 딱 붙게 */
.dw-music-card{
  display:flex;
  gap: 12px;
  align-items:center;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}

/* glossy cover */
.dw-cover-wrap{
  position: relative;
  width: 140px;
  height: 140px;
  border-radius: 26px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 18px 34px rgba(0,0,0,0.22);
  border: 1px solid rgba(255,255,255,0.55);
}

.dw-cover{
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 26px;
  display:block;
}

/* glossy shine overlay */
.dw-cover-wrap:after{
  content:"";
  position:absolute;
  top: -30%;
  left: -30%;
  width: 160%;
  height: 90%;
  background: linear-gradient(
    135deg,
    rgba(255,255,255,0.75) 0%,
    rgba(255,255,255,0.25) 25%,
    rgba(255,255,255,0.08) 45%,
    rgba(255,255,255,0.00) 60%
  );
  transform: rotate(-12deg);
  pointer-events:none;
  opacity: 0.75;
}

/* bottom glow */
.dw-cover-wrap:before{
  content:"";
  position:absolute;
  bottom:-40px;
  left:-20px;
  width: 200px;
  height: 140px;
  background: radial-gradient(circle, rgba(247,182,200,0.55) 0%, rgba(247,182,200,0.00) 70%);
  filter: blur(12px);
  opacity: 0.85;
  pointer-events:none;
}

.dw-music-title{
  font-size: 16px;
  font-weight: 900;
  margin: 0;
  letter-spacing: -0.2px;
}
.dw-music-artist{
  font-size: 13px;
  color: rgba(60,60,67,0.70);
  margin: 4px 0 0 0;
}

.dw-open-row{
  margin-top: 10px;
  display:flex;
  justify-content: space-between;
  align-items:center;
  gap: 10px;
}
.dw-open-text{
  font-size: 13px;
  font-weight: 900;
  color: rgba(60,60,67,0.88);
}
.dw-open-btn{
  text-decoration:none;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width: 38px;
  height: 32px;
  border-radius: 12px;
  background: rgba(247,182,200,0.18);
  border: 1px solid rgba(247,182,200,0.40);
  box-shadow: 0 10px 18px rgba(244,143,177,0.10);
  font-size: 16px;
}
.dw-open-btn:hover{
  background: rgba(247,182,200,0.28);
}
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
# 스페셜 질문 중복 방지
# =========================
def load_special_history():
    if os.path.exists(SPECIAL_HISTORY_PATH):
        try:
            with open(SPECIAL_HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_special_history(history: dict):
    ensure_data_dir()
    with open(SPECIAL_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def pick_special_question_unique(today_str: str, avoid_days: int = 14) -> str:
    history = load_special_history()

    if today_str in history:
        return history[today_str]

    today_date = datetime.fromisoformat(today_str).date()
    recent_dates = [(today_date - timedelta(days=i)).isoformat() for i in range(1, avoid_days + 1)]

    recent_used = set()
    for d in recent_dates:
        if d in history:
            recent_used.add(history[d])

    pool = [q for q in SPECIAL_QUESTIONS if q not in recent_used]
    if not pool:
        pool = SPECIAL_QUESTIONS[:]

    seed_val = int(today_str.replace("-", ""))
    random.seed(seed_val)
    chosen = random.choice(pool)

    history[today_str] = chosen

    cleaned = {}
    for k, v in history.items():
        try:
            kd = datetime.fromisoformat(k).date()
            if (today_date - kd).days <= 60:
                cleaned[k] = v
        except Exception:
            continue

    save_special_history(cleaned)
    return chosen


# =========================
# 유틸
# =========================
def spotify_search_url(title: str, artist: str) -> str:
    q = quote(f"{title} {artist}".strip())
    return f"https://open.spotify.com/search/{q}"

def shorten(text: str, n=40) -> str:
    t = (text or "").strip().replace("\n", " ")
    return t if len(t) <= n else t[:n] + "…"

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
    random.seed(st.session_state.today + tag)
    return random.choice(pool)

def closing_message(style_mode: str, name: str, one_word: str, best: str, growth: str) -> str:
    best_s = shorten(best, 36)
    growth_s = shorten(growth, 36)

    random.seed(st.session_state.today + (one_word or "") + best_s)

    cheers = [
        "오늘도 정말 수고했어요.",
        "오늘 하루를 기록한 것만으로도 충분히 잘한 일이에요.",
        "내일은 조금 더 편안한 하루가 되길 바라요.",
        "오늘의 당신에게 박수를 보내요.",
        "오늘도 잘 버텼어요.",
    ]
    cheer = random.choice(cheers)

    if style_mode == "친한친구":
        return f"오늘은 **{one_word}**라는 단어가 딱 어울리는 하루였어. 특히 {best_s} 그 장면이 오래 남을 것 같아. {cheer}"
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
# 성장서사
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
        st.session_state.special_q = pick_special_question_unique(st.session_state.today, avoid_days=14)

    if "step" not in st.session_state:
        st.session_state.step = 0

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
# iMessage-style renderer
# =========================
def render_chat():
    st.markdown('<div class="dw-chat">', unsafe_allow_html=True)

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


# =========================
# Sidebar
# =========================
with st.sidebar:
    st.subheader("대화 스타일")
    current_label = f"{STYLE_EMOJI[st.session_state.style_mode]} {st.session_state.style_mode}"
    idx = STYLE_OPTIONS.index(current_label) if current_label in STYLE_OPTIONS else 0
    chosen_label = st.radio(
        "오늘은 어떤 분위기로 기록할까요",
        STYLE_OPTIONS,
        index=idx,
        label_visibility="collapsed",
    )
    st.session_state.style_mode = chosen_label.split(" ", 1)[1]

    st.divider()
    st.subheader("내 프로필")

    prof = st.session_state.profile or {}
    name = prof.get("name", "사용자")
    job = prof.get("job", "")
    age = prof.get("age", None)
    gender = prof.get("gender", "선택 안 함")

    meta_parts = []
    if isinstance(age, int) and age > 0:
        meta_parts.append(f"{age}세")
    if gender and gender != "선택 안 함":
        meta_parts.append(gender)
    if job:
        meta_parts.append(job)
    meta = " · ".join(meta_parts) if meta_parts else "프로필을 설정해 주세요"

    initial = (name[:1] if name else "U")
    st.markdown(
        f"""
<div class="dw-profile-chip">
  <div class="dw-avatar">{initial}</div>
  <div>
    <p class="dw-profile-name">{name}</p>
    <p class="dw-profile-meta">{meta}</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

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


# =========================
# Header
# =========================
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
    st.markdown("### 프로필 설정")
    with st.form("profile_form", clear_on_submit=False):
        current = st.session_state.profile or {}

        name = st.text_input("이름", value=current.get("name", ""), placeholder="예: 연세")
        age_val = current.get("age")
        age = st.number_input("나이", min_value=0, max_value=120, value=int(age_val) if isinstance(age_val, int) else 20, step=1)
        gender = st.selectbox("성별", ["선택 안 함", "여성", "남성"],
                              index=["선택 안 함", "여성", "남성"].index(current.get("gender", "선택 안 함")))
        job = st.text_input("직업", value=current.get("job", ""), placeholder="예: 대학생, 기획자, 개발자")

        colA, colB = st.columns(2)
        save = colA.form_submit_button("저장", type="primary", use_container_width=True)
        cancel = colB.form_submit_button("취소", use_container_width=True)

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


# =========================
# 첫 시작
# =========================
if not st.session_state.chat_started and st.session_state.step == 0:
    st.session_state.chat_started = True
    profile = st.session_state.profile or {}
    name = profile.get("name", "사용자")
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
    st.session_state.step = 1
    st.rerun()


# =========================
# Step UI
# =========================
step = st.session_state.step
a = st.session_state.answers


# =========================
# Fixed Composer (iMessage)
# =========================
st.markdown('<div class="dw-fixed-composer">', unsafe_allow_html=True)
st.markdown('<div class="dw-fixed-inner">', unsafe_allow_html=True)

if step == 1:
    options = [f"{e} {t}" for e, t in EMOJI_OPTIONS]
    chosen = choose_single_pills("mood", options, key="mood_choice")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("전송", key="send_step1", type="primary"):
        a["mood"] = chosen
        push_user(chosen)
        push_app("오늘 하루는 무엇으로 채워졌나요? 오늘 한 일을 모두 선택해 주세요.")
        next_step()

elif step == 2:
    selected = choose_multi_pills("activities", ACTIVITIES, key="activity_choice")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("전송", key="send_step2", type="primary"):
        a["activities"] = selected
        text = ", ".join(selected) if selected else "(선택 없음)"
        push_user(text)
        push_app("한 단어로 오늘을 표현한다면 무엇인가요? 딱 떠오르는 단어 하나만 적어주세요.")
        next_step()

elif step == 3:
    msg = st.text_area("", placeholder="한 단어를 입력해 주세요…", key="msg_step3", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("➤", key="send_step3", type="primary"):
        if msg.strip():
            a["one_word"] = msg.strip()
            push_user(a["one_word"])
            push_app("가장 기억에 남는 순간은 무엇인가요? 떠오르는 장면을 자유롭게 적어주세요.")
            next_step()

    st.markdown("</div>", unsafe_allow_html=True)

elif step == 4:
    msg = st.text_area("", placeholder="기억에 남는 순간을 적어 주세요…", key="msg_step4", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("➤", key="send_step4", type="primary"):
        if msg.strip():
            a["best_moment"] = msg.strip()
            push_user(a["best_moment"])
            push_app("새롭게 배우거나 성장한 점이 있나요? 작은 깨달음도 충분히 의미 있어요.")
            next_step()

    st.markdown("</div>", unsafe_allow_html=True)

elif step == 5:
    msg = st.text_area("", placeholder="오늘 성장한 점을 적어 주세요…", key="msg_step5", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("➤", key="send_step5", type="primary"):
        if msg.strip():
            a["growth"] = msg.strip()
            push_user(a["growth"])
            push_app(f"오늘의 스페셜 질문이에요.\n{st.session_state.special_q}")
            next_step()

    st.markdown("</div>", unsafe_allow_html=True)

elif step == 6:
    msg = st.text_area("", placeholder="답을 적어 주세요…", key="msg_step6", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("완료", key="send_step6", type="primary"):
        a["special_answer"] = msg.strip()
        push_user(a["special_answer"] if a["special_answer"] else "(빈 값)")
        next_step()

    st.markdown("</div>", unsafe_allow_html=True)

elif step == 7:
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("다시 하기", key="reset_btn", type="primary"):
        st.session_state.step = 0
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

        if "special_q" in st.session_state:
            del st.session_state.special_q

        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Final step: Music bubble push
# =========================
if step == 7:
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

    if not st.session_state.final_pushed:
        music_html = f"""
<b>{closing}</b><br/><br/>

<div class="dw-music-wrap">
  <div class="dw-music-card">
    <div class="dw-cover-wrap">
      <img class="dw-cover" src="{song["cover_url"]}" />
    </div>

    <div style="flex:1;">
      <p class="dw-music-title">{song["title"]}</p>
      <p class="dw-music-artist">{song["artist"]}</p>

      <div class="dw-open-row">
        <div class="dw-open-text">Spotify에서 바로 감상하기</div>
        <a class="dw-open-btn" href="{link}" target="_blank" title="Spotify 열기">🎧</a>
      </div>
    </div>
  </div>
</div>
        """.strip()

        push_app(music_html)
        st.session_state.final_pushed = True
        st.rerun()
