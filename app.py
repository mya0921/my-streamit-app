# app.py — Daily Weaver (Final Integrated Version)
# Streamlit / No External API

import os, json, random
from datetime import date, datetime, timedelta
from collections import Counter
from urllib.parse import quote
import streamlit as st

# ======================================================
# 기본 설정
# ======================================================
APP_TITLE = "Daily Weaver"
DATA_DIR = "data"
PROFILE_PATH = f"{DATA_DIR}/profile.json"
ENTRIES_PATH = f"{DATA_DIR}/entries.jsonl"

# ======================================================
# 디자인 시스템 (Soft Pink + Apple/Toss)
# ======================================================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: "Pretendard", -apple-system, sans-serif;
        background: #FFFFFF;
        color: #1A1A1B;
    }

    .main .block-container {
        max-width: 720px;
        padding-top: 4.5rem;
    }

    .dw-title {
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .dw-sub {
        color: #6B7684;
        font-size: 16px;
        margin-top: 6px;
    }

    .dw-card {
        background: #FFFFFF;
        border: 1px solid #F2F4F6;
        border-radius: 24px;
        padding: 26px;
        margin-top: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.04);
    }

    /* 버튼 */
    div.stButton > button {
        width: 100%;
        background: #F6B6C8 !important;
        border-radius: 16px !important;
        border: none !important;
        color: #2F2F2F !important;
        font-weight: 700 !important;
        padding: 12px 0 !important;
    }

    div.stButton > button:hover {
        background: #F48FB1 !important;
        color: white !important;
    }

    input, textarea {
        border-radius: 14px !important;
        background: #F9FAFB !important;
        border: 1px solid #E5E8EB !important;
    }

    /* 음악 카드 */
    .music-card {
        display: flex;
        gap: 18px;
        align-items: center;
        background: #111;
        color: white;
        padding: 22px;
        border-radius: 26px;
        margin-top: 24px;
    }

    .music-title {
        font-size: 18px;
        font-weight: 700;
    }

    .music-artist {
        font-size: 14px;
        color: #B5B5B5;
        margin-top: 4px;
    }

    .music-tag {
        display: inline-block;
        margin-top: 10px;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        background: #F6B6C8;
        color: #222;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

# ======================================================
# 데이터 저장/로드
# ======================================================
def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_profile():
    if os.path.exists(PROFILE_PATH):
        return json.load(open(PROFILE_PATH, encoding="utf-8"))
    return None

def save_profile(p):
    ensure_dir()
    json.dump(p, open(PROFILE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def append_entry(e):
    ensure_dir()
    with open(ENTRIES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def read_entries():
    if not os.path.exists(ENTRIES_PATH): return []
    return [json.loads(l) for l in open(ENTRIES_PATH, encoding="utf-8") if l.strip()]

# ======================================================
# 음악 추천 고도화 (API 없음)
# ======================================================
SONGS = {
    "comfort": [("Love Poem","아이유"), ("Breathe","이하이")],
    "focus": [("Experience","Einaudi"), ("Time","Hans Zimmer")],
    "reset": [("Good Days","SZA"), ("Palette","아이유")],
    "sentimental": [("밤편지","아이유"), ("Someone Like You","Adele")],
    "energetic": [("Dynamite","BTS"), ("New Rules","Dua Lipa")]
}

def spotify_url(t,a):
    return f"https://open.spotify.com/search/{quote(t+' '+a)}"

def infer_tag(entries, today_ans):
    score = Counter()
    for e in entries[-7:]:
        w = e["answers"]["one_word"]
        if any(k in w for k in ["힘듦","우울","침잠"]): score["comfort"]+=2
        if any(k in w for k in ["집중","몰입"]): score["focus"]+=2
    if "공부" in today_ans["activities"]: score["focus"]+=2
    if today_ans["one_word"] in ["리셋","정리"]: score["reset"]+=3
    return score.most_common(1)[0][0] if score else "sentimental"

# ======================================================
# 앱 시작
# ======================================================
st.set_page_config(APP_TITLE, "🧶", "centered")
inject_css()

if "step" not in st.session_state: st.session_state.step = 0
if "profile" not in st.session_state: st.session_state.profile = load_profile()
if "answers" not in st.session_state:
    st.session_state.answers = {"mood":"","activities":[],"one_word":"","best":"","growth":""}

# ======================================================
# 사이드바 – 성장 & 포트폴리오
# ======================================================
with st.sidebar:
    st.markdown("### 🧶 Daily Weaver")
    entries = read_entries()

    st.caption("기록은 감정 정리가 아니라\n**경험을 구조화하는 도구**입니다.")
    st.divider()

    st.metric("총 기록", f"{len(entries)}일")
    st.metric("이번 주", f"{len([e for e in entries if (datetime.now()-datetime.fromisoformat(e['date'])).days<7])}회")

    st.divider()
    st.markdown("#### ✍ 포트폴리오 활용 힌트")
    st.caption(
        "- 반복 키워드 → 나의 강점\n"
        "- 성장 포인트 → 변화 서사\n"
        "- 활동 패턴 → 직무 적합성"
    )

# ======================================================
# 메인 플로우
# ======================================================
if st.session_state.step == 0:
    st.markdown('<div class="dw-title">오늘을 엮어볼까요?</div>', unsafe_allow_html=True)
    st.markdown('<div class="dw-sub">기록이 쌓이면 당신만의 서사가 됩니다.</div>', unsafe_allow_html=True)
    if st.button("기록 시작하기"):
        st.session_state.step = 1
        st.rerun()

elif st.session_state.step == 1:
    st.markdown('<div class="dw-card">', unsafe_allow_html=True)
    st.subheader("오늘을 한 단어로 말한다면?")
    w = st.text_input("단어", placeholder="예: 버팀, 리셋, 몰입", label_visibility="collapsed")
    if st.button("다음") and w:
        st.session_state.answers["one_word"] = w
        st.session_state.step = 2
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == 2:
    st.markdown('<div class="dw-card">', unsafe_allow_html=True)
    st.subheader("가장 기억에 남는 순간은?")
    b = st.text_area("순간", label_visibility="collapsed")
    if st.button("기록 완료") and b:
        st.session_state.answers["best"] = b
        st.session_state.step = 3
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == 3:
    tag = infer_tag(read_entries(), st.session_state.answers)
    song = random.choice(SONGS[tag])

    entry = {
        "date": date.today().isoformat(),
        "answers": st.session_state.answers
    }
    append_entry(entry)

    st.markdown('<div class="dw-title">오늘의 기록이 완성됐어요.</div>', unsafe_allow_html=True)
    st.markdown(f"**{st.session_state.answers['one_word']}**이라는 단어가 잘 어울리는 하루였네요.")

    st.markdown(f"""
    <div class="music-card">
        <img src="https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=140&h=140&fit=crop" style="border-radius:16px;">
        <div>
            <div class="music-title">{song[0]}</div>
            <div class="music-artist">{song[1]}</div>
            <div class="music-tag">{tag}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.link_button("Spotify에서 듣기", spotify_url(song[0], song[1]))
    if st.button("처음으로"):
        st.session_state.step = 0
        st.rerun()
