"""
pages/market_analysis.py
수출 시장 분석 페이지
"""

import streamlit as st
from eng_market_analyzer import analyze_market, check_regulations, EXPORT_MARKETS
from util_styles import status_badge


def render():
    st.markdown('<div class="page-header"><h1>📊 시장 분석</h1></div>', unsafe_allow_html=True)
    st.write("수출 대상 시장의 규정, 기회, 도전 요인을 AI가 분석합니다.")

    st.markdown("---")

    with st.form("market_form"):
        st.subheader("제품 & 시장 정보 입력")
        col1, col2 = st.columns(2)

        with col1:
            product_name = st.text_input("제품명", placeholder="예: 화요 41")
            product_type = st.selectbox("주종", ["막걸리", "청주/약주", "증류식 소주", "일반 소주", "과실주", "기타"])
            # 💡 수정된 부분: 숫자 입력창, 0.1도 단위
            alcohol = st.number_input("알코올 도수 (%)", min_value=0.0, max_value=100.0, value=13.0, step=0.1, format="%.1f")

        with col2:
            target_market = st.selectbox("수출 목표 시장", list(EXPORT_MARKETS.keys()))
            volume = st.text_input("용량", placeholder="예: 375ml, 750ml")
            # 💡 수정된 부분: 10원 단위
            price_krw = st.number_input("국내 출고가 (원)", min_value=0, step=10, value=15000)

        submit = st.form_submit_button("🔍 분석 시작", use_container_width=True)

    if submit:
        product_info = {
            "name": product_name,
            "type": product_type,
            "alcohol": f"{alcohol}%",
            "volume": volume,
            "price_krw": price_krw,
        }
        market_data = EXPORT_MARKETS[target_market]

        tab1, tab2 = st.tabs(["📈 시장 분석", "✅ 규정 체크리스트"])

        with tab1:
            with st.spinner("시장 분석 중..."):
                result = analyze_market(product_info, target_market)

            if "error" in result:
                st.error(result["error"])
            else:
                score = result.get("opportunity_score", 0)
                col_score, col_summary = st.columns([1, 3])

                with col_score:
                    st.metric("기회 지수", f"{score} / 10")

                with col_summary:
                    st.markdown(f"**시장 요약**\n\n{result.get('market_summary', '')}")

                st.markdown("---")
                col_c, col_r = st.columns(2)
                with col_c:
                    st.markdown("**⚠️ 주요 도전 요인**")
                    for item in result.get("key_challenges", []):
                        st.markdown(f"- {item}")

                with col_r:
                    st.markdown("**💡 진출 전략 권고**")
                    for item in result.get("recommendations", []):
                        st.markdown(f"- {item}")

                st.markdown("---")
                st.markdown(f"**🎯 타겟 소비자:** {result.get('target_consumer', '')}")
                st.markdown(f"**💰 예상 현지 소비자가:** {result.get('estimated_price_range', '')}")

        with tab2:
            with st.spinner("규정 체크 중..."):
                checks = check_regulations(product_info, market_data.get("code", ""))

            for check in checks:
                badge_html = status_badge(check.get("status", "주의"))
                st.markdown(
                    f"{badge_html} &nbsp; **{check.get('item')}** — {check.get('detail', '')}",
                    unsafe_allow_html=True,
                )
