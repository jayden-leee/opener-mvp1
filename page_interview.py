"""
pages/interview.py

수출 컨설턴트 AI와의 채팅 인터뷰 페이지.
대화를 통해 제품 정보를 수집하고, 완료 시 요약 카드를 표시합니다.
"""

import streamlit as st
import time

from eng_interviewer import (
    chat_with_consultant,
    detect_completion,
    strip_completion_marker,
    calc_progress,
    GREETING_MESSAGE,
    REQUIRED_FIELDS,
    FIELD_LABELS,
)


# ── 세션 초기화 ──────────────────────────────
def _init_session():
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": GREETING_MESSAGE}
        ]
    if "product_data" not in st.session_state:
        st.session_state.product_data = {}
    if "interview_done" not in st.session_state:
        st.session_state.interview_done = False
    if "thinking" not in st.session_state:
        st.session_state.thinking = False


# ── 요약 카드 렌더링 ─────────────────────────
def _render_summary_card(data: dict):
    """수집 완료된 제품 데이터를 구조화된 카드로 표시합니다."""

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #fff8f0 0%, #fff3e6 100%);
        border: 2px solid #C9973A;
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
    ">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:1.5rem;">
            <span style="font-size:2rem;">🎉</span>
            <div>
                <div style="font-size:1.3rem; font-weight:700; color:#8B3A3A;">
                    정보 수집 완료!
                </div>
                <div style="font-size:0.85rem; color:#8B6914; margin-top:2px;">
                    아래 정보로 라벨 번역 · 시장 분석 · 수출 서류 생성을 진행할 수 있습니다.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 핵심 정보 메트릭 행
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🍶 제품명", data.get("product_name", "—"))
    with col2:
        st.metric("🏷️ 주종", data.get("alcohol_type", "—"))
    with col3:
        alc = data.get("alcohol_pct", "—")
        st.metric("🔢 도수", alc if alc not in (None, "", "null") else "—")

    st.markdown("---")

    # 상세 정보 그리드
    left, right = st.columns(2)

    with left:
        st.markdown("#### 📝 제품 상세")

        flavor = data.get("flavor_profile", "—")
        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:1rem; margin-bottom:0.75rem; border:1px solid #E8DDD0;">
            <div style="font-size:0.75rem; color:#888; margin-bottom:4px; font-weight:500;">맛 · 향 프로파일</div>
            <div style="color:#2C1810;">{flavor}</div>
        </div>
        """, unsafe_allow_html=True)

        volume = data.get("volume", None)
        price  = data.get("price_range", "—")
        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:1rem; border:1px solid #E8DDD0;">
            <div style="font-size:0.75rem; color:#888; margin-bottom:4px; font-weight:500;">가격대</div>
            <div style="color:#2C1810;">{price}</div>
            {"<div style='font-size:0.8rem; color:#888; margin-top:6px;'>용량: " + volume + "</div>" if volume and volume not in ("null", "") else ""}
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("#### 🌏 수출 전략")

        countries = data.get("target_country", [])
        if isinstance(countries, str):
            countries = [countries]
        country_tags = "".join([
            f'<span style="background:#8B3A3A; color:white; padding:3px 12px; border-radius:99px; font-size:0.82rem; margin:2px; display:inline-block;">{c}</span>'
            for c in countries
        ])
        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:1rem; margin-bottom:0.75rem; border:1px solid #E8DDD0;">
            <div style="font-size:0.75rem; color:#888; margin-bottom:8px; font-weight:500;">타겟 국가</div>
            <div>{country_tags if country_tags else "—"}</div>
        </div>
        """, unsafe_allow_html=True)

        story = data.get("brand_story", "—")
        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:1rem; border:1px solid #E8DDD0;">
            <div style="font-size:0.75rem; color:#888; margin-bottom:4px; font-weight:500;">브랜드 스토리</div>
            <div style="color:#2C1810; line-height:1.6; font-size:0.9rem;">{story}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 다음 단계 CTA 버튼
    st.markdown("#### 🚀 다음 단계로 이동")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("🏷️ 라벨 번역 시작", use_container_width=True):
            st.session_state["product_data_for_next"] = data
            st.session_state["nav_target"] = "라벨 번역"
            st.rerun()
    with c2:
        if st.button("📊 시장 분석 시작", use_container_width=True):
            st.session_state["product_data_for_next"] = data
            st.session_state["nav_target"] = "시장 분석"
            st.rerun()
    with c3:
        if st.button("📄 수출 서류 생성", use_container_width=True):
            st.session_state["product_data_for_next"] = data
            st.session_state["nav_target"] = "수출 서류"
            st.rerun()
    with c4:
        if st.button("🔄 처음부터 다시", use_container_width=True, type="secondary"):
            for key in ["chat_messages", "product_data", "interview_done", "thinking"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # JSON 다운로드
    import json
    st.download_button(
        label="📥 JSON으로 저장",
        data=json.dumps(data, ensure_ascii=False, indent=2),
        file_name=f"{data.get('product_name', 'product')}_info.json",
        mime="application/json",
    )


# ── 진행률 사이드바 ──────────────────────────
def _render_progress_sidebar(data: dict):
    filled, total, missing = calc_progress(data)
    pct = int(filled / total * 100)

    with st.sidebar:
        st.markdown("---")
        st.markdown("**📋 정보 수집 현황**")
        st.progress(pct / 100, text=f"{filled}/{total} 항목 완료 ({pct}%)")

        if missing:
            st.markdown(
                "<div style='font-size:0.8rem; color:#888; margin-top:8px;'>남은 항목:</div>",
                unsafe_allow_html=True,
            )
            for label in missing:
                st.markdown(
                    f"<div style='font-size:0.82rem; padding:2px 0; color:#555;'>• {label}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.success("모든 정보 수집 완료! 🎉")


# ── 메인 렌더 함수 ────────────────────────────
def render():
    _init_session()

    # 페이지 헤더
    st.markdown(
        '<div class="page-header"><h1>💬 제품 정보 인터뷰</h1></div>',
        unsafe_allow_html=True,
    )
    st.caption("수출 컨설턴트 AI와 대화하며 제품 정보를 손쉽게 입력하세요.")

    # 진행률 사이드바
    _render_progress_sidebar(st.session_state.product_data)

    # ── 완료 화면 ──────────────────────────────
    if st.session_state.interview_done and st.session_state.product_data:
        # 마지막 대화까지 표시
        _render_chat_history()
        st.markdown("---")
        _render_summary_card(st.session_state.product_data)
        return

    # ── 채팅 UI ────────────────────────────────
    chat_area = st.container()

    with chat_area:
        _render_chat_history()

    # ── 입력창 ─────────────────────────────────
    if not st.session_state.interview_done:
        user_input = st.chat_input(
            "제품에 대해 자유롭게 말씀해 주세요...",
            disabled=st.session_state.thinking,
        )

        if user_input:
            # 사용자 메시지 추가
            st.session_state.chat_messages.append(
                {"role": "user", "content": user_input}
            )
            st.session_state.thinking = True
            st.rerun()

    # ── AI 응답 생성 (thinking 상태일 때) ──────
    if st.session_state.thinking:
        _generate_ai_response()


def _render_chat_history():
    """채팅 이력을 버블 형태로 렌더링합니다."""
    for msg in st.session_state.chat_messages:
        role    = msg["role"]
        content = msg["content"]

        # 완료 마커는 화면에서 숨김
        display_content = strip_completion_marker(content) if role == "assistant" else content

        if not display_content.strip():
            continue

        with st.chat_message(role, avatar="🍶" if role == "assistant" else "👤"):
            st.markdown(display_content)


def _generate_ai_response():
    """LLM을 호출하여 AI 응답을 생성하고 세션에 저장합니다."""
    with st.chat_message("assistant", avatar="🍶"):
        with st.spinner("컨설턴트가 답변을 작성 중입니다..."):
            # system 메시지 제외한 순수 대화 이력만 전달
            history = [
                m for m in st.session_state.chat_messages
                if m["role"] in ("user", "assistant")
            ]
            ai_response = chat_with_consultant(history)

    # 완료 여부 확인
    is_done, extracted_data = detect_completion(ai_response)

    # 메시지 저장
    st.session_state.chat_messages.append(
        {"role": "assistant", "content": ai_response}
    )

    # 완료 처리
    if is_done and extracted_data:
        st.session_state.product_data   = extracted_data
        st.session_state.interview_done = True

    st.session_state.thinking = False
    st.rerun()
