"""
utils/navigation.py
사이드바 네비게이션 컴포넌트
"""

import streamlit as st


PAGES = {
    "🏠 홈":       "홈",
    "💬 제품 인터뷰": "제품 인터뷰",
    "🎯 바이어 발굴": "바이어 발굴",
    "🚀 제안서 생성": "제안서 생성",
    "🏷️ 라벨 번역": "라벨 번역",
    "📊 시장 분석": "시장 분석",
    "📄 수출 서류": "수출 서류",
    "⚙️ 설정":     "설정",
}

# 워크플로 단계 (홈 제외 메인 플로우 순서)
WORKFLOW_STEPS = ["제품 인터뷰", "바이어 발굴", "제안서 생성"]


def _workflow_badge(step_name: str, done: bool, active: bool) -> str:
    if done:
        bg, fg, prefix = "#e6f4ea", "#1e7e34", "✅"
    elif active:
        bg, fg, prefix = "#fff3cd", "#856404", "▶"
    else:
        bg, fg, prefix = "#f5f5f5", "#aaa", "○"
    return (
        f'<div style="background:{bg};color:{fg};border-radius:6px;'
        f'padding:4px 10px;font-size:0.78rem;margin-bottom:4px;">'
        f'{prefix} {step_name}</div>'
    )


def render_sidebar() -> str:
    page_keys   = list(PAGES.keys())
    default_idx = st.session_state.pop("_nav_index", 0)

    interview_done = bool(st.session_state.get("interview_done") and st.session_state.get("product_data"))
    buyers_ready   = bool(st.session_state.get("hunter_deep_dives"))
    proposal_done  = bool(st.session_state.get("proposal_pdf_bytes"))

    with st.sidebar:
        # ── 로고 ──
        st.markdown("""
            <div style="text-align:center; padding:1rem 0 1rem;">
                <div style="font-size:2.2rem;">🍶</div>
                <div style="font-size:1.35rem; font-weight:700; letter-spacing:0.05em;">오프너</div>
                <div style="font-size:0.72rem; opacity:0.6; margin-top:2px;">Opener — 전통주 수출 AI</div>
            </div>
        """, unsafe_allow_html=True)

        # ── 워크플로 진행 배지 ──
        st.markdown("""
            <div style="font-size:0.72rem; font-weight:600; color:#888;
                 letter-spacing:0.06em; margin-bottom:6px;">WORKFLOW</div>
        """, unsafe_allow_html=True)

        pname = st.session_state.get("product_data", {}).get("product_name", "")
        dive_count = len(st.session_state.get("hunter_deep_dives", {}))

        html_badges = ""
        html_badges += _workflow_badge(
            f"제품 인터뷰{f' — {pname}' if pname else ''}",
            done=interview_done, active=not interview_done
        )
        html_badges += _workflow_badge(
            f"바이어 발굴{f' — {dive_count}개 분석' if dive_count else ''}",
            done=buyers_ready, active=interview_done and not buyers_ready
        )
        html_badges += _workflow_badge(
            "제안서 생성" + (" — 완료!" if proposal_done else ""),
            done=proposal_done, active=buyers_ready and not proposal_done
        )
        st.markdown(html_badges, unsafe_allow_html=True)

        st.divider()

        # ── 메뉴 라디오 ──
        selected_label = st.radio(
            "메뉴",
            page_keys,
            index=default_idx,
            label_visibility="collapsed",
        )

        st.divider()

        st.markdown("""
            <div style="font-size:0.7rem; opacity:0.45; text-align:center;">
                MVP v0.4.0
            </div>
        """, unsafe_allow_html=True)

    return PAGES[selected_label]

