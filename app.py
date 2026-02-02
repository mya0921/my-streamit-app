import streamlit as st

st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="centered")

st.title("🎬 나와 어울리는 영화는?")
st.write("간단한 5문항으로 당신의 영화 취향을 알아보고, 어떤 영화가 어울리는지 찾아봐요! 👀🍿")

st.divider()

# 질문/선택지 데이터
questions = [
    ("1. 주말에 가장 하고 싶은 것은?",
     ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"]),
    ("2. 스트레스 받으면?",
     ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"]),
    ("3. 영화에서 중요한 것은?",
     ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"]),
    ("4. 여행 스타일?",
     ["계획적", "즉흥적", "액티비티", "힐링"]),
    ("5. 친구 사이에서 나는?",
     ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"]),
]

answers = {}

# 5개 질문을 st.radio로 표시
for q, opts in questions:
    answers[q] = st.radio(q, opts, key=q)

st.divider()

# 결과 보기 버튼
if st.button("결과 보기"):
    st.subheader("분석 중...")
