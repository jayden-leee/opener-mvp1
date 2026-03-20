"""
pages/buyer_hunter.py

🎯 바이어 발굴 엔진 (The Hunter)
Tavily 실시간 검색 → 바이어 리스트업 → 딥다이브 인텔리전스 카드
"""

from __future__ import annotations

import json
import streamlit as st
from eng_market_analyzer import (
    search_buyers,
    deep_dive_buyer,
    EXPORT_MARKETS,
)


# ─────────────────────────────────────────────
# 세션 초기화
# ─────────────────────────────────────────────

def _init():
    defaults = {
        "hunter_buyers":       [],      # 검색된 바이어 리스트
        "hunter_raw":          [],      # Tavily 원본 결과
        "hunter_selected":     set(),   # 선택된 바이어 인덱스
        "hunter_deep_dives":   {},      # company_name → deep dive 결과
        "hunter_searching":    False,
        "hunter_diving":       None,    # 딥다이브 중인 company_name
        "hunter_country":      "",
        "hunter_market_key":   "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
# 매칭 점수 색상
# ─────────────────────────────────────────────

def _score_color(score: int) -> str:
    if score >= 8:
        return "#1e7e34", "#e6f4ea"   # 초록
    elif score >= 6:
        return "#856404", "#fff3cd"   # 노랑
    else:
        return "#721c24", "#f8d7da"   # 빨강


def _score_label(score: int) -> str:
    if score >= 8: return "최적 매칭"
    if score >= 6: return "좋은 매칭"
    return "참고"


# ─────────────────────────────────────────────
# 바이어 카드
# ─────────────────────────────────────────────

def _render_buyer_card(idx: int, buyer: dict):
    """바이어 리스트 카드 하나를 렌더링합니다."""
    score     = buyer.get("match_score", 0)
    fg, bg    = _score_color(score)
    is_sel    = idx in st.session_state.hunter_selected
    has_dive  = buyer.get("company_name") in st.session_state.hunter_deep_dives

    border = "2px solid #8B3A3A" if is_sel else "1px solid #E8DDD0"
    shadow = "0 4px 16px rgba(139,58,58,0.15)" if is_sel else "0 2px 6px rgba(0,0,0,0.06)"

    st.markdown(f"""
    <div style="
        background:white; border:{border}; border-radius:14px;
        padding:1.1rem 1.3rem; margin-bottom:0.75rem;
        box-shadow:{shadow}; transition:all 0.2s;
    ">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="flex:1;">
                <div style="font-weight:700; font-size:1rem; color:#2C1810; margin-bottom:2px;">
                    {buyer.get('company_name','—')}
                    {"&nbsp;✅" if is_sel else ""}
                    {"&nbsp;🔍" if has_dive else ""}
                </div>
                <div style="font-size:0.8rem; color:#888; margin-bottom:6px;">
                    📍 {buyer.get('city','')}, {buyer.get('country','')} &nbsp;|&nbsp;
                    🏷️ {buyer.get('business_type','')} &nbsp;|&nbsp;
                    🍷 {buyer.get('specialty','')}
                </div>
                <div style="font-size:0.85rem; color:#444; line-height:1.5;">
                    {buyer.get('match_reason','—')}
                </div>
                {f'<div style="font-size:0.78rem; color:#8B3A3A; margin-top:6px;">🌐 {buyer.get("website","")}</div>' if buyer.get('website') else ''}
            </div>
            <div style="
                margin-left:1rem; text-align:center; min-width:64px;
                background:{bg}; color:{fg};
                border-radius:10px; padding:6px 10px;
                font-weight:700; font-size:1.1rem;
            ">
                {score}/10<br>
                <span style="font-size:0.68rem; font-weight:500;">{_score_label(score)}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 체크박스 + 딥다이브 버튼
    col_cb, col_btn, _ = st.columns([1, 2, 4])
    with col_cb:
        checked = st.checkbox(
            "선택",
            value=is_sel,
            key=f"chk_{idx}",
            label_visibility="collapsed",
        )
        if checked and idx not in st.session_state.hunter_selected:
            st.session_state.hunter_selected.add(idx)
            st.rerun()
        elif not checked and idx in st.session_state.hunter_selected:
            st.session_state.hunter_selected.discard(idx)
            st.rerun()

    with col_btn:
        dive_label = "🔍 딥다이브 완료" if has_dive else "🔬 딥다이브 분석"
        if st.button(dive_label, key=f"dive_{idx}", use_container_width=True):
            st.session_state.hunter_diving = buyer.get("company_name")
            st.rerun()


# ─────────────────────────────────────────────
# 딥다이브 인텔리전스 카드
# ─────────────────────────────────────────────

def _render_deep_dive_card(company_name: str, result: dict):
    """딥다이브 분석 결과를 상세 카드로 렌더링합니다."""
    fit   = result.get("fit_score", 0)
    fg, bg = _score_color(fit)

    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,#fdf8f2,#fff8f0);
        border:2px solid #C9973A; border-radius:16px;
        padding:1.5rem 2rem; margin:1rem 0;
    ">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:1rem;">
            <span style="font-size:1.8rem;">🎯</span>
            <div>
                <div style="font-size:1.2rem; font-weight:700; color:#8B3A3A;">
                    {company_name} — 인텔리전스 리포트
                </div>
                <div style="font-size:0.82rem; color:#8B6914;">
                    적합도 {fit}/10 &nbsp;·&nbsp; {result.get('fit_reason','—')}
                </div>
            </div>
            <div style="margin-left:auto; background:{bg}; color:{fg};
                border-radius:8px; padding:4px 14px; font-weight:700; font-size:1.1rem;">
                {fit}/10
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        # 기업 요약
        st.markdown("##### 🏢 기업 요약")
        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:1rem;
             border:1px solid #E8DDD0; margin-bottom:0.75rem; line-height:1.6; font-size:0.9rem;">
            {result.get('company_summary', '—')}
        </div>
        """, unsafe_allow_html=True)

        # Pain Points
        st.markdown("##### ⚡ 현재 고민 (Pain Points)")
        for pt in result.get("pain_points", []):
            st.markdown(f"""
            <div style="background:#fff3cd; border-left:3px solid #C9973A;
                 border-radius:0 8px 8px 0; padding:8px 12px; margin-bottom:6px; font-size:0.88rem;">
                {pt}
            </div>
            """, unsafe_allow_html=True)

        # 우리에게 기회
        st.markdown("##### 🚀 우리 제품의 기회")
        for opp in result.get("opportunities", []):
            st.markdown(f"""
            <div style="background:#e6f4ea; border-left:3px solid #1e7e34;
                 border-radius:0 8px 8px 0; padding:8px 12px; margin-bottom:6px; font-size:0.88rem;">
                {opp}
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        # 선호 키워드
        st.markdown("##### 🔑 선호 키워드")
        keywords = result.get("preferred_keywords", [])
        kw_html = " ".join([
            f'<span style="background:#8B3A3A; color:white; padding:3px 12px; '
            f'border-radius:99px; font-size:0.82rem; margin:2px; display:inline-block;">{k}</span>'
            for k in keywords
        ])
        st.markdown(f'<div style="margin-bottom:0.75rem;">{kw_html}</div>', unsafe_allow_html=True)

        # 의사결정자
        dm = result.get("decision_maker_hint", "")
        if dm:
            st.markdown("##### 👔 의사결정자 힌트")
            st.markdown(f"""
            <div style="background:white; border-radius:10px; padding:0.75rem 1rem;
                 border:1px solid #E8DDD0; font-size:0.88rem; margin-bottom:0.75rem;">
                {dm}
            </div>
            """, unsafe_allow_html=True)

        # 접근 전략
        st.markdown("##### 🗺️ 최적 접근 전략")
        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:1rem;
             border:1px solid #E8DDD0; line-height:1.7; font-size:0.88rem;">
            {result.get('approach_strategy', '—')}
        </div>
        """, unsafe_allow_html=True)

        # 주의사항
        red_flags = result.get("red_flags", [])
        if red_flags and red_flags[0]:
            st.markdown("##### 🚩 주의사항")
            for rf in red_flags:
                st.markdown(f"""
                <div style="background:#f8d7da; border-left:3px solid #dc3545;
                     border-radius:0 8px 8px 0; padding:8px 12px; margin-bottom:4px; font-size:0.85rem;">
                    {rf}
                </div>
                """, unsafe_allow_html=True)

    # JSON 내보내기
    st.download_button(
        "📥 인텔리전스 리포트 JSON 저장",
        data=json.dumps(result, ensure_ascii=False, indent=2),
        file_name=f"{company_name}_intelligence.json",
        mime="application/json",
        key=f"dl_{company_name}",
    )


# ─────────────────────────────────────────────
# 선택된 바이어 요약 사이드바
# ─────────────────────────────────────────────

def _render_selection_sidebar():
    buyers   = st.session_state.hunter_buyers
    selected = st.session_state.hunter_selected

    if not buyers:
        return

    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**🎯 선택된 바이어 ({len(selected)}개)**")

        if selected:
            for idx in sorted(selected):
                b = buyers[idx] if idx < len(buyers) else {}
                score = b.get("match_score", 0)
                fg, bg = _score_color(score)
                st.markdown(f"""
                <div style="background:{bg}; color:{fg}; border-radius:8px;
                     padding:6px 10px; margin-bottom:6px; font-size:0.82rem;">
                    <strong>{b.get('company_name','?')}</strong><br>
                    {b.get('city','')}, {b.get('country','')} &nbsp; {score}/10
                </div>
                """, unsafe_allow_html=True)

            # 전체 선택 초기화
            if st.button("선택 초기화", key="clear_sel"):
                st.session_state.hunter_selected = set()
                st.rerun()

            # 선택된 바이어 CSV 다운로드
            import csv, io
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=[
                "company_name","country","city","website","business_type","specialty","match_score","match_reason"
            ])
            writer.writeheader()
            for idx in sorted(selected):
                if idx < len(buyers):
                    writer.writerow({k: buyers[idx].get(k,"") for k in writer.fieldnames})

            st.download_button(
                "📥 선택 바이어 CSV",
                data=buf.getvalue(),
                file_name="selected_buyers.csv",
                mime="text/csv",
                key="dl_csv",
            )
        else:
            st.caption("바이어 카드에서 체크박스를 선택하세요.")


# ─────────────────────────────────────────────
# 메인 렌더
# ─────────────────────────────────────────────

def render():
    _init()
    _render_selection_sidebar()

    # ── 헤더 ──────────────────────────────────
    st.markdown(
        '<div class="page-header"><h1>🎯 바이어 발굴 (The Hunter)</h1></div>',
        unsafe_allow_html=True,
    )
    st.caption("Tavily AI 검색으로 타겟 국가의 유통사·수입사를 실시간 발굴하고, 딥다이브 분석으로 접근 전략을 수립합니다.")

    # ── 제품 정보 확인 ─────────────────────────
    product_data = st.session_state.get("product_data", {})
    if not product_data:
        st.warning(
            "⚠️ 제품 인터뷰를 먼저 완료해주세요. "
            "사이드바에서 '💬 제품 인터뷰'를 선택하거나 아래 버튼을 클릭하세요."
        )
        if st.button("💬 제품 인터뷰로 이동"):
            from util_navigation import PAGES
            st.session_state["_nav_index"] = list(PAGES.values()).index("제품 인터뷰")
            st.rerun()
        # 데모용 폴백 데이터
        product_data = {
            "product_name": "(데모) 화요 41",
            "alcohol_type": "증류식 소주",
            "flavor_profile": "깔끔하고 고급스러운 단맛, 긴 여운",
            "target_country": ["미국", "두바이"],
        }
        st.info("데모 데이터로 계속 진행합니다.")

    # 제품 정보 배지
    pname = product_data.get("product_name", "—")
    st.markdown(f"""
    <div style="background:#f0e8dc; border-radius:10px; padding:10px 16px;
         margin-bottom:1rem; display:inline-flex; align-items:center; gap:10px;">
        <span style="font-size:1.2rem;">🍶</span>
        <span style="color:#8B3A3A; font-weight:600;">{pname}</span>
        <span style="color:#888; font-size:0.85rem;">으로 바이어 탐색 중</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── 검색 설정 ──────────────────────────────
    st.subheader("🌍 검색 설정")

    col_mkt, col_query, col_btn = st.columns([2, 2, 1])

    with col_mkt:
        market_key = st.selectbox(
            "타겟 시장",
            list(EXPORT_MARKETS.keys()),
            index=0,
            key="hunter_market_select",
        )

    with col_query:
        # 국가명 자동 완성 + 커스텀 입력
        auto_country = market_key.split(" ", 1)[-1].replace("🇺🇸 ", "").replace("🇯🇵 ", "")
        country_input = st.text_input(
            "검색할 도시/국가 (영문)",
            value=st.session_state.get("hunter_country") or auto_country,
            placeholder="예: Dubai, UAE  /  London, UK  /  Tokyo, Japan",
            key="hunter_country_input",
        )

    with col_btn:
        st.markdown("<div style='margin-top:28px;'>", unsafe_allow_html=True)
        search_btn = st.button("🔍 검색 시작", use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 검색 실행 ──────────────────────────────
    if search_btn:
        if not country_input.strip():
            st.warning("검색할 국가/도시를 입력해주세요.")
        else:
            market_code = EXPORT_MARKETS.get(market_key, {}).get("code", "")
            st.session_state.hunter_country    = country_input.strip()
            st.session_state.hunter_market_key = market_key
            st.session_state.hunter_buyers     = []
            st.session_state.hunter_selected   = set()
            st.session_state.hunter_deep_dives = {}
            st.session_state.hunter_searching  = True
            st.rerun()

    # ── 검색 중 ────────────────────────────────
    if st.session_state.hunter_searching:
        country    = st.session_state.hunter_country
        market_key = st.session_state.hunter_market_key
        market_code = EXPORT_MARKETS.get(market_key, {}).get("code", "")

        with st.spinner(f"🌐 {country} 의 주류 유통사·수입사를 탐색 중입니다... (30초~1분 소요)"):
            progress_bar = st.progress(0, text="Tavily 검색 엔진 가동 중...")
            progress_bar.progress(20, text="검색 쿼리 실행 중...")

            buyers, raw = search_buyers(
                country=country,
                market_code=market_code,
                product_info=product_data,
            )

            progress_bar.progress(80, text="AI 분석 및 매칭 점수 계산 중...")
            progress_bar.progress(100, text="완료!")

        st.session_state.hunter_buyers    = buyers
        st.session_state.hunter_raw       = raw
        st.session_state.hunter_searching = False
        st.rerun()

    # ── 딥다이브 실행 ──────────────────────────
    if st.session_state.hunter_diving:
        company = st.session_state.hunter_diving
        buyers  = st.session_state.hunter_buyers
        target_buyer = next((b for b in buyers if b.get("company_name") == company), None)

        if target_buyer and company not in st.session_state.hunter_deep_dives:
            with st.spinner(f"🔬 {company} 딥다이브 분석 중... (20~40초 소요)"):
                dive_result = deep_dive_buyer(target_buyer, product_data)
            st.session_state.hunter_deep_dives[company] = dive_result

        st.session_state.hunter_diving = None
        st.rerun()

    # ── 결과 표시 ──────────────────────────────
    buyers = st.session_state.hunter_buyers

    if buyers:
        country = st.session_state.hunter_country

        # 통계 요약 행
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("발굴된 바이어", f"{len(buyers)}개")
        with col_s2:
            st.metric("선택된 바이어", f"{len(st.session_state.hunter_selected)}개")
        with col_s3:
            avg_score = sum(b.get("match_score", 0) for b in buyers) / len(buyers) if buyers else 0
            st.metric("평균 매칭 점수", f"{avg_score:.1f}/10")
        with col_s4:
            dive_count = len(st.session_state.hunter_deep_dives)
            st.metric("딥다이브 완료", f"{dive_count}개")

        st.markdown("---")
        st.subheader(f"📋 {country} 바이어 후보 리스트")
        st.caption("체크박스로 제안서를 보낼 바이어를 선택하고, 🔬 딥다이브로 상세 인텔리전스를 확인하세요.")

        # 정렬 옵션
        sort_opt = st.radio(
            "정렬",
            ["매칭 점수 높은 순", "이름 순"],
            horizontal=True,
            label_visibility="collapsed",
        )
        sorted_buyers = sorted(
            enumerate(buyers),
            key=lambda x: (-x[1].get("match_score", 0) if sort_opt.startswith("매칭") else x[1].get("company_name", "")),
        )

        # 바이어 카드 렌더링
        for orig_idx, buyer in sorted_buyers:
            _render_buyer_card(orig_idx, buyer)

        # ── 딥다이브 결과 표시 ──────────────────
        if st.session_state.hunter_deep_dives:
            st.markdown("---")
            st.subheader("🔬 딥다이브 인텔리전스 리포트")

            deep_dives = st.session_state.hunter_deep_dives
            if len(deep_dives) > 1:
                tab_names = list(deep_dives.keys())
                tabs = st.tabs(tab_names)
                for tab, cname in zip(tabs, tab_names):
                    with tab:
                        _render_deep_dive_card(cname, deep_dives[cname])
            else:
                cname, result = next(iter(deep_dives.items()))
                _render_deep_dive_card(cname, result)

    elif not st.session_state.hunter_searching:
        # 초기 안내
        st.markdown("""
        <div style="
            text-align:center; padding:3rem;
            background:#fdf8f2; border-radius:16px;
            border:2px dashed #E8DDD0; margin-top:1rem;
        ">
            <div style="font-size:3rem; margin-bottom:1rem;">🌐</div>
            <div style="font-size:1.1rem; font-weight:600; color:#8B3A3A; margin-bottom:0.5rem;">
                바이어를 찾을 준비가 됐습니다
            </div>
            <div style="color:#888; font-size:0.9rem;">
                타겟 시장과 국가/도시를 선택한 후<br>
                <strong>🔍 검색 시작</strong> 버튼을 눌러주세요.<br><br>
                <em>Tavily AI가 실시간으로 최적 바이어를 발굴합니다.</em>
            </div>
        </div>
        """, unsafe_allow_html=True)
