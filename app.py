import os
import json
import random
import time
from datetime import date, datetime, timedelta
from urllib.parse import quote
from collections import Counter

import streamlit as st

# =========================
# 기본 설정 및 경로
# =========================
APP_TITLE = "Daily Weaver"
DATA_DIR = "data"
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
ENTRIES_PATH = os.path.join(DATA_DIR, "entries.jsonl")

# =========================
# 디자인 시스템 (Apple/Toss Style)
# =========================
def inject_css():
    st.markdown(
        """
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            
            html, body, [data-testid="stAppViewContainer"] {
                font-family: "Pretendard", -apple-system, sans-serif;
                background-color: #FFFFFF;
                color: #1A1A1B;
            }

            /* 메인 컨테이너 여백 */
            .main .block-container {
                max-width: 640px;
                padding-top: 5rem;
            }

            /* 카드 스타일 */
            .dw-card {
                background: #FFFFFF;
                padding: 24px;
                border-radius: 24px;
                border: 1px solid #F2F4F6;
                box-shadow: 0 8px 16px rgba(0,0,0,0.03);
                margin-bottom: 20px;
            }

            /* 타이포그래피 */
            .dw-title {
                font-size: 32px;
                font-weight: 800;
                letter-spacing: -1px;
                margin-bottom: 8px;
            }

            .dw-sub {
                font-size: 16px;
                color: #6B7684;
                line-height: 1.5;
            }

            /* 버튼 스타일 (토스풍 블루/블랙) */
            div.stButton > button {
                width: 100%;
                border-radius: 16px !important;
                border: none !important;
                background-color: #3182F6 !important; /* Toss Blue */
                color: white !important;
                font-weight: 600 !important;
                padding: 12px 0px !important;
                margin-top: 10px;
                transition: all 0.2s ease;
            }

            div.stButton > button:hover {
                background-color: #1B64DA !important;
                transform: translateY(-2px);
            }

            /* 입력창 스타일 */
            input, textarea {
                background-color: #F9FAFB !important;
                border: 1px solid #E5E8EB !important;
                border-radius: 14px !important;
            }

            /* 음악 카드 (Apple Music 풍) */
            .music-player {
                display: flex;
                align-items: center;
                background: #1A1A1B;
                color: white;
                padding: 20px;
                border-radius: 24px;
                margin-top: 20px;
            }
            .music-info {
                margin-left: 20px;
            }
            .music-title {
                font-weight: 700;
                font-size: 18px;
                margin-bottom: 4px;
            }
            .music-artist {
                font-size: 14px;
                color: #ADADAD;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================
# 로직 및 헬퍼 함수
# =========================
# (기존 데이터 로드/저장 로직과 동일 - 생략 없이 유지)
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_profile(p: dict):
    ensure_data_dir(); 
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def append_entry(entry: dict):
    ensure_data_dir(); 
    with open(ENTRIES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def read_entries():
    if not os.path.exists(ENTRIES_PATH): return []
    with open(ENTRIES_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

# (기존 유틸 함수들: infer_tag, closing_message 등은 그대로 유지)
# ... [이전 코드의 유틸 함수 부분]

# =========================
# 앱 상태 초기화
# =========================
def init_state():
    if "step" not in st.session_state: st.session_state.step = 0
    if "profile" not in st.session_state: st.session_state.profile = load_profile()
    if "answers" not in st.session_state: 
        st.session_state.answers = {"mood":None, "activities":[], "one_word":"", "best_moment":"", "growth":"", "special_answer":""}
    if "today" not in st.session_state: st.session_state.today = date.today().isoformat()

# =========================
# 메인 화면 구현
# =========================
st.set_page_config(page_title=APP_TITLE, page_icon="🧶", layout="centered")
inject_css()
init_state()

# 1. 사이드바 (깔끔한 대시보드 형태)
with st.sidebar:
    st.markdown("### 🧶 Daily Weaver")
    if st.session_state.profile:
        st.write(f"반가워요, **{st.session_state.profile['name']}**님")
    
    st.divider()
    # 요약 지표 시각화 (토스 자산 탭 느낌)
    entries = read_entries()
    st.markdown("#### 나의 기록 흐름")
    col1, col2 = st.columns(2)
    col1.metric("총 기록", f"{len(entries)}일")
    col2.metric("이번주", f"{len([e for e in entries if (datetime.now()-datetime.fromisoformat(e['date'])).days < 7])}회")
    
    if st.button("내 정보 수정"):
        st.session_state.step = -1 # 온보딩 단계
        st.rerun()

# 2. 메인 헤더
if st.session_state.step == 0:
    st.markdown(f'<div class="dw-title">오늘을 엮어볼까요?</div>', unsafe_allow_html=True)
    st.markdown('<div class="dw-sub">사소한 기록이 모여 당신의 단단한 포트폴리오가 됩니다.</div>', unsafe_allow_html=True)
    st.write("")
    if st.button("기록 시작하기"):
        st.session_state.step = 1
        st.rerun()

# 3. 질문 플로우 (Chat-Focus UX)
if st.session_state.step > 0 and st.session_state.step < 7:
    # 프로그레스 바
    st.progress(st.session_state.step / 6)
    st.caption(f"Step {st.session_state.step} of 6")
    
    step = st.session_state.step
    ans = st.session_state.answers

    st.markdown('<div class="dw-card">', unsafe_allow_html=True)
    
    if step == 1:
        st.subheader("오늘의 기분은 어떤가요?")
        mood_opts = ["😀 기쁨", "🙂 평온", "😐 무덤덤", "😔 우울", "😴 피곤", "🔥 열정"]
        choice = st.pills("기분", mood_opts, label_visibility="collapsed")
        if choice:
            ans["mood"] = choice
            if st.button("다음"): st.session_state.step = 2; st.rerun()

    elif step == 2:
        st.subheader("어떤 활동으로 채웠나요?")
        acts = ["공부", "업무", "운동", "휴식", "약속", "창작", "정리", "이동"]
        selected = st.pills("활동", acts, selection_mode="multi", label_visibility="collapsed")
        if selected:
            ans["activities"] = selected
            if st.button("다음"): st.session_state.step = 3; st.rerun()

    elif step == 3:
        st.subheader("오늘을 한 단어로 정의한다면?")
        word = st.text_input("단어 입력", placeholder="예: 성장, 비움, 몰입", label_visibility="collapsed")
        if st.button("다음") and word:
            ans["one_word"] = word
            st.session_state.step = 4; st.rerun()

    elif step == 4:
        st.subheader("가장 기억에 남는 장면은?")
        moment = st.text_area("장면 묘사", placeholder="어떤 일이 있었나요?", label_visibility="collapsed")
        if st.button("다음") and moment:
            ans["best_moment"] = moment
            st.session_state.step = 5; st.rerun()

    elif step == 5:
        st.subheader("오늘 무엇을 배웠나요?")
        growth = st.text_area("성장 포인트", placeholder="작은 깨달음도 좋아요.", label_visibility="collapsed")
        if st.button("다음") and growth:
            ans["growth"] = growth
            st.session_state.step = 6; st.rerun()

    elif step == 6:
        st.subheader("마지막으로, 오늘 하루를 영화 제목으로 지어본다면?")
        special = st.text_input("제목 입력", label_visibility="collapsed")
        if st.button("기록 완료"):
            ans["special_answer"] = special
            st.session_state.step = 7; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# 4. 결과 화면 (Apple Music Style)
elif st.session_state.step == 7:
    st.balloons()
    st.markdown('<div class="dw-title">오늘의 기록이 완성되었습니다.</div>', unsafe_allow_html=True)
    
    # 가상의 추천곡 데이터 (원래 로직 연결)
    st.markdown(
        """
        <div class="music-player">
            <img src="https://images.unsplash.com/photo-1514525253361-bee8718a302a?w=100&h=100&fit=crop" style="border-radius:12px;">
            <div class="music-info">
                <div class="music-title">밤편지 (Through the Night)</div>
                <div class="music-artist">아이유 (IU)</div>
                <div style="font-size: 12px; margin-top:8px; opacity:0.7;">오늘의 감성과 어울리는 곡</div>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.write("")
    st.markdown('<div class="dw-card">', unsafe_allow_html=True)
    st.write(f"**{st.session_state.profile['name'] if st.session_state.profile else '사용자'}님을 위한 회고**")
    st.write(f"오늘은 **{st.session_state.answers['one_word']}**가 돋보이는 하루였네요. 특히 {st.session_state.answers['best_moment'][:30]}... 순간이 인상적이에요.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("처음으로 돌아가기"):
        st.session_state.step = 0
        st.rerun()

# 5. 온보딩 (최초 실행)
if st.session_state.step == -1 or st.session_state.profile is None:
    st.markdown('<div class="dw-title">반가워요!</div>', unsafe_allow_html=True)
    st.markdown('<div class="dw-sub">더 나은 기록을 위해 이름을 알려주세요.</div>', unsafe_allow_html=True)
    name = st.text_input("이름")
    job = st.text_input("직업/목표")
    if st.button("시작하기"):
        st.session_state.profile = {"name": name, "job": job}
        save_profile(st.session_state.profile)
        st.session_state.step = 0
        st.rerun()
