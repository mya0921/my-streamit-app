# app.py
# Daily Weaver — Full Version
# 기록 → 분석 → 포트폴리오 연결까지 되는 개인 성장 앱

import os, json, random
from datetime import date, datetime, timedelta
from collections import Counter
from urllib.parse import quote
import streamlit as st

# ======================
# 기본 설정
# ======================
APP_TITLE = "Daily Weaver"
DATA_DIR = "data"
PROFILE_PATH = f"{DATA_DIR}/profile.json"
ENTRIES_PATH = f"{DATA_DIR}/entries.jsonl"

st.set_page_config(APP_TITLE, "🧶", layout="wide")

# ======================
# 스타일
# ======================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: Pretendard, -apple-system;
        background: #FFFFFF;
        color: #1A1A1B;
    }
    .main .block-container {
        max-width: 880px;
        padding-top: 3.5rem;
    }
    .title {
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -1px;
    }
    .subtitle {
        color: #6B7684;
        margin-bottom: 24px;
    }
    .card {
        background: white;
        border-radius: 24px;
        padding: 26px;
        border: 1px solid #F2F4F6;
        box-shadow: 0 8px 20px rgba(0,0,0,0.04);
        margin-bottom: 24px;
    }
    button[kind="primary"] {
        background: #F6B6C8 !important;
        color: #222 !important;
        border-radius: 16px !important;
        font-weight: 700 !important;
        border: none !important;
    }
    button[kind="primary"]:hover {
        background: #F48FB1 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_css()

# ======================
# 데이터 유틸
# ======================
def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_profile():
    if os.path.exists(PROFILE_PATH):
        return json.load(open(PROFILE_PATH, encoding="utf-8"))
    return None

def save_profile(p):
    ensure_dir()
    json.dump(p, open(PROFILE_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

def append_entry(e):
    ensure_dir()
    with open(ENTRIES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def read_entries():
    if not os.path.exists(ENTRIES_PATH):
        return []
    return [json.loads(l) for l in open(ENTRIES_PATH, encoding="utf-8") if l.strip()]

# ======================
# 세션 상태
# ======================
if "profile" not in st.session_state:
    st.session_state.profile = load_profile()

if "step" not in st.session_state:
    st.session_state.step = 0

if "answers" not in st.session_state:
    st.session_state.answers = {
        "mood": "",
        "activities": [],
        "one_word": "",
        "best_moment": "",
        "growth": "",
        "special": ""
    }

# ======================
# 사이드바 (포트폴리오 연계)
# ======================
with st.sidebar:
    st.markdown("## 📊 성장 & 포트폴리오")
    entries = read_entries()

    if entries:
        acts, words = [], []
        for e in entries:
            acts += e["answers"]["activities"]
            words.append(e["answers"]["one_word"])

        st.markdown("**자주 한 활동**")
        for a, c in Counter(acts).most_common(5):
            st.write(f"- {a} ({c})")

        st.markdown("**반복 키워드**")
        for w, c in Counter(words).most_common(5):
            st.write(f"- {w}")

        st.markdown("---")
        st.markdown("### ✍️ 자소서 힌트")
        st.write("""
- 문제 상황 → 해당 날짜 기록  
- 행동 → 선택한 활동  
- 변화 → 성장 질문 답변  
        """)
    else:
        st.info("아직 기록이 없어요.")

# ======================
# 온보딩 (개인정보)
# ======================
if st.session_state.profile is None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="title">Daily Weaver</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">당신의 하루를, 미래의 자산으로</div>', unsafe_allow_html=True)

    name = st.text_input("이름")
    role = st.selectbox("현재 단계", ["대학생", "취준생", "직장인"])
    goal = st.text_input("요즘 가장 중요한 목표는?")

    if st.button("시작하기", type="primary"):
        st.session_state.profile = {
            "name": name,
            "role": role,
            "goal": goal,
            "created": str(date.today())
        }
        save_profile(st.session_state.profile)
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ======================
# 질문 플로우
# ======================
QUESTIONS = [
    ("오늘 하루 기분은 어땠어?", "mood"),
    ("오늘 한 활동을 모두 골라줘", "activities"),
    ("오늘을 한 단어로 표현하면?", "one_word"),
    ("가장 기억에 남는 순간은?", "best_moment"),
    ("오늘의 경험에서 얻은 성장 포인트는?", "growth"),
]

ACTIVITY_OPTIONS = [
    "공부", "팀플", "발표", "면접 준비",
    "운동", "휴식", "사람 만남", "사이드 프로젝트"
]

SPECIAL_QUESTIONS = [
    "오늘의 선택이 1년 뒤의 나에게 어떤 영향을 줄까?",
    "오늘 가장 잘한 결정은 뭐였어?",
    "오늘의 경험을 자소서 문장으로 바꾼다면?"
]

st.markdown(f'<div class="title">안녕, {st.session_state.profile["name"]} 👋</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">오늘의 기록을 남겨보자</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)

step = st.session_state.step

if step < len(QUESTIONS):
    q, key = QUESTIONS[step]
    st.markdown(f"### {q}")

    if key == "activities":
        st.session_state.answers[key] = st.multiselect(
            "", ACTIVITY_OPTIONS, default=st.session_state.answers[key]
        )
    else:
        st.session_state.answers[key] = st.text_area(
            "", st.session_state.answers[key]
        )

    if st.button("다음", type="primary"):
        st.session_state.step += 1
        st.experimental_rerun()

elif step == len(QUESTIONS):
    q = random.choice(SPECIAL_QUESTIONS)
    st.markdown(f"### ✨ 스페셜 질문\n{q}")
    st.session_state.answers["special"] = st.text_area(
        "", st.session_state.answers["special"]
    )

    if st.button("기록 완료", type="primary"):
        entry = {
            "date": str(date.today()),
            "created": datetime.now().isoformat(),
            "answers": st.session_state.answers
        }
        append_entry(entry)
        st.session_state.step += 1
        st.experimental_rerun()

else:
    st.markdown("### 🎧 오늘의 무드 음악")
    mood = st.session_state.answers["mood"]
    keyword = quote(mood if mood else "집중")
    st.markdown(f"""
    <div style="padding:24px;border-radius:24px;background:#111;color:white">
        <div style="font-size:20px;font-weight:800">이런 분위기 어때?</div>
        <div style="margin-top:12px">
            <a href="https://www.youtube.com/results?search_query={keyword}+playlist"
               target="_blank" style="color:#F6B6C8;font-weight:700">
               🎵 유튜브 플레이리스트 열기
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("새 기록 쓰기"):
        st.session_state.step = 0
        st.session_state.answers = {
            "mood": "", "activities": [], "one_word": "",
            "best_moment": "", "growth": "", "special": ""
        }
        st.experimental_rerun()

st.markdown('</div>', unsafe_allow_html=True)
