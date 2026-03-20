"""
오프너(Opener) - 전통주 수출용 AI SaaS MVP
메인 애플리케이션 진입점  v0.5.0 (flat layout)
"""

# ── sys.path 고정 ─────────────────────────────────────────────────────────────
# 어떤 폴더에서 실행해도 app.py가 있는 디렉토리를 Python 경로에 추가합니다.
# 예: cd /home/user && streamlit run files/app.py  → files/ 가 path에 들어감
import sys, os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
from dotenv import load_dotenv
import os
import uuid

# 환경변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="오프너(Opener) — 전통주 수출 AI",
    page_icon="🍶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 세션 ID 초기화 (사용자 구분용) ──────────────
if "_session_id" not in st.session_state:
    st.session_state["_session_id"] = str(uuid.uuid4())

# ── 커스텀 CSS ───────────────────────────────────
from util_styles import load_css
load_css()

# ── 인터뷰 완료 후 자동 DB 저장 ─────────────────
# interview.py에서 interview_done이 새로 True가 된 직후 한 번만 실행
if (
    st.session_state.get("interview_done")
    and st.session_state.get("product_data")
    and not st.session_state.get("_product_saved_id")
):
    from database import save_product
    pid = save_product(
        st.session_state["product_data"],
        session_id=st.session_state["_session_id"],
    )
    st.session_state["_product_saved_id"] = pid

# ── 제안서 완료 후 자동 DB 저장 ─────────────────
if (
    st.session_state.get("proposal_pdf_bytes")
    and st.session_state.get("proposal_cold_email")
    and not st.session_state.get("_proposal_saved_id")
):
    from database import save_full_pipeline
    result = save_full_pipeline(
        product_data=st.session_state.get("product_data", {}),
        buyer_intel=st.session_state.get("proposal_target_buyer") or {},
        cold_email=st.session_state.get("proposal_cold_email", {}),
        pitch_deck=st.session_state.get("proposal_pitch_deck", {}),
        pdf_bytes=st.session_state.get("proposal_pdf_bytes"),
        session_id=st.session_state["_session_id"],
    )
    st.session_state["_proposal_saved_id"] = result.get("proposal_id")
    st.session_state["_buyer_saved_id"]    = result.get("buyer_id")

# ── nav_target 리다이렉트 ────────────────────────
if "nav_target" in st.session_state:
    target = st.session_state.pop("nav_target")
    from util_navigation import PAGES
    page_values = list(PAGES.values())
    if target in page_values:
        st.session_state["_nav_index"] = page_values.index(target)

# ── 네비게이션 ───────────────────────────────────
from util_navigation import render_sidebar
page = render_sidebar()

# ── DB 연결 상태 사이드바 표시 ───────────────────
from database import is_connected
with st.sidebar:
    st.markdown("---")
    if is_connected():
        st.markdown(
            '<div style="font-size:0.72rem;color:#1e7e34;text-align:center;">'
            '🟢 Supabase 연결됨</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:0.72rem;color:#aaa;text-align:center;">'
            '⚪ DB 미연결 (로컬 모드)</div>',
            unsafe_allow_html=True,
        )

# ── 페이지 라우팅 ────────────────────────────────
if page == "홈":
    from page_home import render
    render()

elif page in ("제품 인터뷰", "💬 제품 인터뷰"):
    from page_interview import render
    render()

elif page == "바이어 발굴":
    from page_buyer_hunter import render
    render()

elif page == "제안서 생성":
    from page_proposal_generator import render
    render()

elif page == "라벨 번역":
    from page_label_translator import render
    render()

elif page == "시장 분석":
    from page_market_analysis import render
    render()

elif page == "수출 서류":
    from page_export_docs import render
    render()

elif page == "설정":
    from page_settings import render
    render()

# ── 전역 피드백 위젯 (하단 고정) ────────────────
st.markdown("---")
from util_feedback_widget import render_feedback_widget
render_feedback_widget(
    page_context=page,
    proposal_id=st.session_state.get("_proposal_saved_id"),
    show_stats=False,
)
