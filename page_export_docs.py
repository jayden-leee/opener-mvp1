"""
pages/export_docs.py
수출 서류 생성 페이지
"""

import streamlit as st
from eng_doc_generator import generate_document, generate_pdf_bytes, DOCUMENT_TYPES


def render():
    st.markdown('<div class="page-header"><h1>📄 수출 서류 자동 생성</h1></div>', unsafe_allow_html=True)
    st.write("제품 정보를 입력하면 수출에 필요한 서류 초안을 즉시 생성합니다.")

    st.markdown("---")

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.subheader("📋 정보 입력")

        doc_type = st.selectbox("생성할 서류 종류", list(DOCUMENT_TYPES.keys()))
        target_market = st.text_input("수출 대상 시장", placeholder="예: 미국, 일본")

        st.markdown("**제품 정보**")
        product_name = st.text_input("제품명")
        product_type = st.text_input("주종", placeholder="예: 증류식 소주")
        alcohol = st.text_input("알코올 도수", placeholder="예: 25%")
        volume = st.text_input("용량", placeholder="예: 375ml")
        ingredients = st.text_area("원재료", placeholder="쌀, 정제수, 입국 (한 줄에 하나씩)")

        st.markdown("**수출자/제조사 정보**")
        company = st.text_input("회사명")
        address = st.text_input("주소")
        contact = st.text_input("연락처")

        gen_btn = st.button("📝 서류 생성", use_container_width=True)

    with col_result:
        st.subheader("📄 생성된 서류")

        if gen_btn:
            if not product_name or not target_market:
                st.warning("제품명과 수출 대상 시장을 입력해주세요.")
                return

            product_info = {
                "name": product_name,
                "type": product_type,
                "alcohol": alcohol,
                "volume": volume,
                "ingredients": [i.strip() for i in ingredients.split("\n") if i.strip()],
            }
            exporter_info = {
                "company": company,
                "address": address,
                "contact": contact,
            }

            with st.spinner(f"{doc_type} 초안 생성 중..."):
                doc_content = generate_document(doc_type, product_info, target_market, exporter_info)

            if doc_content:
                st.success("✅ 서류 초안이 생성되었습니다.")
                st.markdown(doc_content)

                # 다운로드
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        "📥 텍스트 다운로드",
                        data=doc_content,
                        file_name=f"{doc_type.replace(' ', '_')}.md",
                        mime="text/markdown",
                    )
                with col_dl2:
                    pdf_bytes = generate_pdf_bytes(doc_content, doc_type)
                    st.download_button(
                        "📥 PDF 다운로드",
                        data=pdf_bytes,
                        file_name=f"{doc_type.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                    )
            else:
                st.error("서류 생성에 실패했습니다.")
        else:
            st.info("왼쪽에서 정보를 입력하고 '서류 생성' 버튼을 누르세요.")
