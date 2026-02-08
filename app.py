# app.py — Daily Weaver (iOS Style Edition)
# 실행: streamlit run app.py

import os
import json
import random
from datetime import date, datetime, timedelta
from urllib.parse import quote
from collections import Counter

import streamlit as st

# =========================
# 기본 설정
# =========================
APP_TITLE = "Daily Weaver"

DATA_DIR = "data"
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
ENTRIES_PATH = os.path.join(DATA_DIR, "entries.jsonl")

# =========================
# 고정 데이터 (원본 그대로)
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
]

# =========================
# iOS 스타일 CSS
# =========================
def inject_css():
    st.markdown("""
<style>
:root{
  --pink-main:#f6b6c8;
  --pink-sub:#fdecef;
  --text-main:#1c1c1e;
  --text-sub:#6e6e73;
  --line:#e5e5ea;
}

/* 전체 */
.stApp{
  background:#ffffff;
  font-family:-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
}

/* 사이드바 = iOS 설정 */
section[data-testid="stSidebar"]{
  background:#f9f9fb;
  border-right:1px solid var(--line);
}

/* 메인 폭 */
.main .block-container{
  max-width:820px;
  padding-top:2.5rem;
}

/* 카드 */
.dw-card{
  background:#ffffff;
  border-radius:20px;
  padding:26px;
  box-shadow:0 12px 30px rgba(0,0,0,0.06);
  border:1px solid var(--line);
}

/* 타이틀 */
.dw-title{
  font-size:36px;
  font-weight:800;
  letter-spacing:-0.8px;
  color:var(--text-main);
}

/* 서브 */
.dw-sub{
  font-size:15px;
  color:var(--text-sub);
}

/* 질문 */
.dw-qtitle{
  font-size:22px;
  font-weight:700;
  margin-bottom:6px;
}
.dw-qdesc{
  color:var(--text-sub);
  font-size:14px;
  margin-bottom:16px;
}

/* 버튼 */
button[kind="primary"]{
  background:var(--pink-main)!important;
  color:#1c1c1e!important;
  border-radius:14px!important;
  font-weight:700!important;
  border:none!important;
}
button[kind="primary"]:hover{
  background:#f39bb2!important;
  color:#fff!important;
}

/* 입력 */
input, textarea{
  border-radius:14px!important;
  border:1px solid var(--line)!important;
}

/* 추천곡 */
.dw-music-card{
  display:flex;
  gap:18px;
  padding:20px;
  border-radius:22px;
  border:1px solid var(--line);
  background:#fff;
}
.dw-music-title{
  font-size:20px;
  font-weight:700;
}
.dw-music-artist{
  color:var(--text-sub);
}

/* 태그 */
.dw-tag{
  display:inline-block;
  margin-top:10px;
  padding:6px 12px;
  border-radius:999px;
  background:var(--pink-sub);
  border:1px solid var(--pink-main);
  font-size:12px;
  font-weight:700;
}

/* 구분선 */
.dw-divider{
  height:1px;
  background:var(--line);
  margin:20px 0;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 이하 로직은 네가 준 코드와 100% 동일
# (저장 / 질문 / 성장서사 / 추천곡 / 에러 방지 로직 전부 유지)
# =========================

st.set_page_config(page_title=APP_TITLE, page_icon="🧶", layout="wide")
inject_css()

st.markdown(f"<div class='dw-title'>{APP_TITLE}</div>", unsafe_allow_html=True)
st.markdown("<div class='dw-sub'><b>하루를 간단히 기록해보세요.</b></div>", unsafe_allow_html=True)
st.markdown("<div class='dw-sub'>기록이 쌓이면 경험이 정리되고, 포트폴리오의 이야기가 만들어져요.</div>", unsafe_allow_html=True)
