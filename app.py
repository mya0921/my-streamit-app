# app.py
# Daily Weaver
# 하루 기록 → 장기 서사 → 포트폴리오 자산화

import os
import json
import random
from datetime import datetime, date
from collections import Counter, defaultdict
import streamlit as st

# ==================================================
# 기본 설정
# ==================================================
APP_TITLE = "Daily Weaver"
DATA_DIR = "data"
PROFILE_PATH = f"{DATA_DIR}/profile.json"
ENTRIES_PATH = f"{DATA_DIR}/entries.jsonl"

st.set_page_config(APP_TITLE, "🧶", layout="wide")

# ==================================================
# 고정 데이터 (❗사용자 지정 그대로)
# ==================================================
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
]

# ==================================================
# 파일 유틸
# ==================================================
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

# ==================================================
# 날짜 파싱 (🔥 에러 원인 해결)
# ==================================================
def parse_entry_datetime(e):
    if "created" in e:
        return datetime.fromisoformat(e["created"])
    if "date" in e:
        return datetime.fromisoformat(e["date"] + "T00:00:00")
    return None

# ==================================================
# 세션 상태
# ==================================================
if "profile" not in st.session_state:
    st.session_state.profile = load_profile()

if "step" not in st.session_state:
    st.session_state.step = 1

if "style_mode" not in st.session_state:
    st.session_state.style_mode = STYLE_MODES[0]

if "answers" not in st.session_state:
    st.session_state.answers = {
        "emoji": None,
        "activities": [],
        "one_word": "",
        "moment": "",
        "growth": "",
        "special": ""
    }

# ==================================================
# 사이드바 — 주/월/연 분석
# ==================================================
with st.sidebar:
    st.markdown("## 📊 기록 분석")
    entries = read_entries()

    def group_by(entries, key):
        groups = defaultdict(list)
        for e in entries:
            dt = parse_entry_datetime(e)
            if dt is None:
                continue

            if key == "week":
                k = dt.strftime("%Y-W%U")
            elif key == "month":
                k = dt.strftime("%Y-%m")
            else:
                k = dt.strftime("%Y")

            groups[k].append(e)
        return groups

    if entries:
        for label, key in [("주간", "week"), ("월간", "month"), ("연간", "year")]:
            st.markdown(f"### {label} 요약")
            grouped = group_by(entries, key)
            latest = sorted(grouped.keys())[-1]

            acts, words = [], []
            for e in grouped[latest]:
                acts += e.get("answers", {}).get("activities", [])
                words.append(e.get("answers", {}).get("one_word", ""))

            if acts:
                st.write("활동:", ", ".join([a for a, _ in Counter(acts).most_common(3)]))
            if words:
                st.write("키워드:", ", ".join([w for w, _ in Counter(words).most_common(3)]))
    else:
        st.info("아직 기록이 없습니다.")

# ==================================================
# 온보딩
# ==================================================
if st.session_state.profile is None:
    st.markdown(f"# {APP_TITLE}")
    st.markdown("### 하루를 엮어, 미래를 만듭니다")

    name = st.text_input("이름")
    age = st.number_input("나이", 0, 120, step=1)
    gender = st.selectbox("성별", ["남성", "여성", "선택하지 않음"])
    job = st.text_input("직업")

    if st.button("시작하기"):
        st.session_state.profile = {
            "name": name,
            "age": age,
            "gender": gender,
            "job": job,
            "created": str(date.today())
        }
        save_profile(st.session_state.profile)
        st.experimental_rerun()

    st.stop()

# ==================================================
# 메인 기록 플로우
# ==================================================
st.markdown(f"# {APP_TITLE}")
st.markdown(f"**{st.session_state.profile['name']}님의 오늘**")

st.session_state.style_mode = st.selectbox("대화 스타일", STYLE_MODES)

step = st.session_state.step

# Step 1 — 이모지
if step == 1:
    st.markdown("### 지금 기분에 가장 가까운 이모지를 골라줘")
    cols = st.columns(5)
    for i, (emo, label) in enumerate(EMOJI_OPTIONS):
        if cols[i % 5].button(f"{emo}\n{label}"):
            st.session_state.answers["emoji"] = emo
            st.session_state.step = 2
            st.experimental_rerun()

# Step 2 — 행동
elif step == 2:
    st.markdown("### 오늘 어떤 행동을 했어?")
    st.session_state.answers["activities"] = st.multiselect(
        "", ACTIVITIES, default=st.session_state.answers["activities"]
    )
    if st.button("다음"):
        st.session_state.step = 3
        st.experimental_rerun()

# Step 3 — 한 단어
elif step == 3:
    st.markdown("### 오늘을 한 단어로 표현한다면?")
    st.session_state.answers["one_word"] = st.text_input("", st.session_state.answers["one_word"])
    if st.button("다음"):
        st.session_state.step = 4
        st.experimental_rerun()

# Step 4 — 순간
elif step == 4:
    st.markdown("### 가장 기억에 남는 순간은?")
    st.session_state.answers["moment"] = st.text_area("", st.session_state.answers["moment"])
    if st.button("다음"):
        st.session_state.step = 5
        st.experimental_rerun()

# Step 5 — 성장
elif step == 5:
    st.markdown("### 오늘의 경험에서 어떤 의미를 얻었어?")
    st.session_state.answers["growth"] = st.text_area("", st.session_state.answers["growth"])
    if st.button("다음"):
        st.session_state.step = 6
        st.experimental_rerun()

# Step 6 — 스페셜
elif step == 6:
    question = random.choice(SPECIAL_QUESTIONS)
    st.markdown(f"### ✨ {question}")
    st.session_state.answers["special"] = st.text_area("", st.session_state.answers["special"])

    if st.button("기록 저장"):
        append_entry({
            "created": datetime.now().isoformat(),
            "style_mode": st.session_state.style_mode,
            "answers": st.session_state.answers
        })

        st.session_state.step = 1
        st.session_state.answers = {
            "emoji": None,
            "activities": [],
            "one_word": "",
            "moment": "",
            "growth": "",
            "special": ""
        }
        st.experimental_rerun()
