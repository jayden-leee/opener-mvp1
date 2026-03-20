"""
utils/feedback_widget.py

앱 하단에 표시되는 "이 제안서가 마음에 드시나요?" 피드백 버튼 컴포넌트.
모든 페이지 하단에서 재사용 가능하며 DB 저장과 연동됩니다.
"""

from __future__ import annotations

import streamlit as st
from database import save_feedback, get_feedback_stats, is_connected


def render_feedback_widget(
    page_context: str = "",
    proposal_id: str | None = None,
    show_stats: bool = False,
):
    """
    좋아요/싫어요 피드백 버튼을 렌더링합니다.
    결과는 Supabase feedback 테이블에 저장됩니다.

    Args:
        page_context : 피드백이 발생한 페이지 이름
        proposal_id  : 연결된 제안서 ID (있으면 함께 저장)
        show_stats   : True이면 누적 피드백 통계도 표시
    """
    session_key_done    = f"fb_done_{page_context}"
    session_key_comment = f"fb_comment_{page_context}"

    # ── 이미 피드백 완료 ──────────────────────
    if st.session_state.get(session_key_done):
        rating = st.session_state.get(f"fb_rating_{page_context}", -1)
        emoji  = "👍" if rating == 1 else "👎"
        st.markdown(f"""
        <div style="
            display:flex; align-items:center; gap:10px;
            background:#f0faf0; border-radius:10px;
            padding:10px 16px; margin-top:1rem;
            border:1px solid #a8d5b1; font-size:0.88rem; color:#1e7e34;
        ">
            {emoji} &nbsp; 피드백 감사합니다! 서비스 개선에 반영하겠습니다.
        </div>
        """, unsafe_allow_html=True)
        return

    # ── 피드백 위젯 ───────────────────────────
    st.markdown("""
    <div style="
        border-top: 1px solid #E8DDD0;
        margin-top: 2rem; padding-top: 1rem;
    ">
    </div>
    """, unsafe_allow_html=True)

    col_msg, col_like, col_dislike, col_gap = st.columns([4, 1, 1, 2])

    with col_msg:
        st.markdown(
            '<div style="padding-top:6px; font-size:0.92rem; color:#555; font-weight:500;">'
            '이 결과가 도움이 되셨나요?'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_like:
        if st.button("👍 좋아요", key=f"like_{page_context}", use_container_width=True):
            _handle_feedback(1, page_context, proposal_id, session_key_done)

    with col_dislike:
        if st.button("👎 별로예요", key=f"dislike_{page_context}", use_container_width=True):
            _handle_feedback(0, page_context, proposal_id, session_key_done)

    # ── 선택적 통계 표시 ──────────────────────
    if show_stats and is_connected():
        stats = get_feedback_stats(proposal_id)
        if stats["total"] > 0:
            st.markdown(f"""
            <div style="font-size:0.78rem; color:#aaa; margin-top:6px; text-align:right;">
                누적: 👍 {stats['likes']}  👎 {stats['dislikes']}
                &nbsp;·&nbsp; 만족도 {stats['like_rate']}%
            </div>
            """, unsafe_allow_html=True)


def _handle_feedback(
    rating: int,
    page_context: str,
    proposal_id: str | None,
    session_key_done: str,
):
    """피드백을 저장하고 세션 플래그를 설정합니다."""
    session_id = st.session_state.get("_session_id", "")

    fid = save_feedback(
        rating=rating,
        proposal_id=proposal_id,
        page_context=page_context,
        session_id=session_id,
    )

    st.session_state[session_key_done]                     = True
    st.session_state[f"fb_rating_{page_context}"]          = rating
    st.session_state[f"fb_id_{page_context}"]              = fid

    if is_connected():
        st.toast("피드백이 저장되었습니다!", icon="✅")
    else:
        st.toast("피드백을 받았습니다! (DB 미연결)", icon="✅")

    st.rerun()
