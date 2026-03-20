"""
pages/home.py
오프너 홈 대시보드 — 4단계 워크플로우 안내
"""

import streamlit as st


def _nav(target: str):
    from util_navigation import PAGES
    st.session_state["_nav_index"] = list(PAGES.values()).index(target)
    st.rerun()


def render():
    st.markdown('<div class="page-header"><h1>🍶 오프너(Opener)</h1></div>', unsafe_allow_html=True)
    st.subheader("한국 전통주를 세계로 — AI 수출 지원 플랫폼")
    st.markdown("---")

    # ── 상태 읽기 ──────────────────────────────
    interview_done = bool(st.session_state.get("interview_done") and st.session_state.get("product_data"))
    product_data   = st.session_state.get("product_data", {})
    buyers_ready   = bool(st.session_state.get("hunter_deep_dives"))
    proposal_done  = bool(st.session_state.get("proposal_pdf_bytes"))
    pname          = product_data.get("product_name", "")

    # ── 4단계 워크플로우 타임라인 ───────────────
    st.markdown("#### 📍 수출 준비 워크플로우")

    steps = [
        {
            "num": "1", "icon": "💬", "title": "제품 인터뷰",
            "desc": "AI 컨설턴트와 5분 대화로\n제품 정보 자동 수집",
            "done": interview_done,
            "active": not interview_done,
            "btn": "인터뷰 시작", "target": "제품 인터뷰",
            "done_label": f"완료: {pname}" if pname else "완료",
        },
        {
            "num": "2", "icon": "🎯", "title": "바이어 발굴",
            "desc": "Tavily AI로 실시간 유통사 탐색\n딥다이브 인텔리전스 분석",
            "done": buyers_ready,
            "active": interview_done and not buyers_ready,
            "btn": "발굴 시작", "target": "바이어 발굴",
            "done_label": f"{len(st.session_state.get('hunter_deep_dives', {}))}개 분석 완료",
        },
        {
            "num": "3", "icon": "🚀", "title": "제안서 생성",
            "desc": "콜드메일 + 피치덱 +\n레이더 차트 + PDF 자동 생성",
            "done": proposal_done,
            "active": buyers_ready and not proposal_done,
            "btn": "생성 시작", "target": "제안서 생성",
            "done_label": "PDF 완성!",
        },
        {
            "num": "4", "icon": "📬", "title": "수출 서류",
            "desc": "원산지증명서·COA 등\n수출 서류 초안 자동 생성",
            "done": False,
            "active": proposal_done,
            "btn": "서류 생성", "target": "수출 서류",
            "done_label": "",
        },
    ]

    cols = st.columns(4, gap="small")
    for col, step in zip(cols, steps):
        with col:
            if step["done"]:
                border = "2px solid #1e7e34"
                bg     = "#f0faf0"
                icon_bg = "#1e7e34"
                tag = f'<span style="background:#e6f4ea;color:#1e7e34;font-size:0.72rem;border-radius:99px;padding:2px 8px;">✅ {step["done_label"]}</span>'
            elif step["active"]:
                border = "2px solid #8B3A3A"
                bg     = "#fff8f2"
                icon_bg = "#8B3A3A"
                tag = '<span style="background:#fff3cd;color:#856404;font-size:0.72rem;border-radius:99px;padding:2px 8px;">▶ 진행 중</span>'
            else:
                border = "1px solid #E8DDD0"
                bg     = "#fafafa"
                icon_bg = "#ccc"
                tag = '<span style="background:#f5f5f5;color:#aaa;font-size:0.72rem;border-radius:99px;padding:2px 8px;">대기 중</span>'

            st.markdown(f"""
            <div style="background:{bg};border:{border};border-radius:12px;
                 padding:1rem;height:180px;position:relative;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    <div style="background:{icon_bg};color:white;border-radius:50%;
                         width:28px;height:28px;display:flex;align-items:center;
                         justify-content:center;font-size:0.85rem;font-weight:700;flex-shrink:0;">
                        {step["num"]}
                    </div>
                    <span style="font-size:1.1rem;">{step["icon"]}</span>
                    <strong style="font-size:0.92rem;color:#2C1810;">{step["title"]}</strong>
                </div>
                <div style="font-size:0.8rem;color:#666;line-height:1.5;margin-bottom:8px;
                     white-space:pre-line;">{step["desc"]}</div>
                {tag}
            </div>
            """, unsafe_allow_html=True)

            # 버튼은 HTML 아래 별도 렌더 (Streamlit 버튼은 HTML 안에 못 넣음)
            if step["active"] or step["done"]:
                btn_label = "다시 시작" if step["done"] else f"→ {step['btn']}"
                btn_type  = "secondary" if step["done"] else "primary"
                if st.button(btn_label, key=f"hw_{step['num']}", use_container_width=True, type=btn_type):
                    _nav(step["target"])

    st.markdown("---")

    # ── 보조 기능 카드 ──────────────────────────
    st.markdown("#### 🔧 보조 도구")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div class="opener-card">
            <strong>🏷️ 라벨 번역</strong>
            <p style="font-size:0.85rem;color:#666;margin:4px 0 0;">
            전통주 라벨을 5개 언어로 자동 번역.<br>현지 규정 표현 자동 적용.
            </p>
        </div>""", unsafe_allow_html=True)
        if st.button("라벨 번역 →", key="h_label"):
            _nav("라벨 번역")

    with c2:
        st.markdown("""
        <div class="opener-card">
            <strong>📊 시장 분석</strong>
            <p style="font-size:0.85rem;color:#666;margin:4px 0 0;">
            수출 시장 규정·관세·트렌드<br>AI 즉시 분석.
            </p>
        </div>""", unsafe_allow_html=True)
        if st.button("시장 분석 →", key="h_market"):
            _nav("시장 분석")

    st.markdown("---")
    st.caption("💡 사이드바 워크플로우 배지로 진행 상황을 한눈에 확인하세요.")

