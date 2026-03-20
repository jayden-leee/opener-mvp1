"""
pages/label_translator.py
전통주 라벨 번역 페이지
"""

import streamlit as st
from eng_label_translator import (
    analyze_label_text,
    translate_label,
    SUPPORTED_LANGUAGES,
)


def render():
    st.markdown('<div class="page-header"><h1>🏷️ 라벨 번역</h1></div>', unsafe_allow_html=True)
    st.write("전통주 라벨을 입력하면 AI가 수출 대상국 언어로 번역합니다.")

    st.markdown("---")

    # 입력 섹션
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.subheader("📥 원본 라벨 입력")

        input_method = st.radio(
            "입력 방식",
            ["텍스트 직접 입력", "이미지 업로드 (OCR)"],
            horizontal=True,
        )

        if input_method == "텍스트 직접 입력":
            label_text = st.text_area(
                "라벨 텍스트",
                height=250,
                placeholder="예)\n산사춘\n알코올 14%\n원재료: 쌀, 산사, 정제수\n용량: 375ml\n제조: (주)배상면주가",
            )
        else:
            uploaded = st.file_uploader("라벨 이미지 업로드", type=["jpg", "jpeg", "png"])
            label_text = ""
            if uploaded:
                st.image(uploaded, caption="업로드된 라벨", use_column_width=True)
                st.info("🔄 OCR 기능은 추후 업데이트 예정입니다.")

        # 번역 옵션
        st.markdown("**번역 설정**")
        target_lang_label = st.selectbox("대상 언어", list(SUPPORTED_LANGUAGES.keys()))
        target_market = st.text_input("수출 대상 시장", placeholder="예: 미국, 일본, 중국")

        analyze_btn = st.button("🔍 분석 & 번역", use_container_width=True)

    with col_out:
        st.subheader("📤 번역 결과")

        if analyze_btn:
            if not label_text.strip():
                st.warning("라벨 텍스트를 입력해주세요.")
                return

            with st.spinner("AI가 라벨을 분석 중입니다..."):
                analyzed = analyze_label_text(label_text)

            if "error" in analyzed and analyzed.get("error"):
                st.error(f"분석 실패: {analyzed.get('error')}")
                return

            st.success("✅ 분석 완료")
            with st.expander("원본 분석 결과 보기"):
                st.json(analyzed)

            target_lang_code = SUPPORTED_LANGUAGES[target_lang_label]

            with st.spinner(f"{target_lang_label}로 번역 중..."):
                translated = translate_label(analyzed, target_lang_code, target_market or "일반 수출")

            if "error" in translated:
                st.error(f"번역 실패: {translated.get('error')}")
                return

            st.markdown("### 번역 결과")
            for key, value in translated.items():
                if key not in ("error", "response"):
                    st.markdown(f"**{key}:** {value}")

            # 복사용 JSON
            with st.expander("JSON 데이터 다운로드"):
                import json
                st.download_button(
                    "📥 JSON 다운로드",
                    data=json.dumps(translated, ensure_ascii=False, indent=2),
                    file_name="translated_label.json",
                    mime="application/json",
                )

        else:
            st.info("왼쪽에서 라벨 텍스트를 입력하고 '분석 & 번역' 버튼을 누르세요.")
