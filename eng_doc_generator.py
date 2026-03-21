import json
import io
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# ==========================================
# 1. 콜드메일 생성 일꾼
# ==========================================
def generate_cold_email(product_data, buyer_intel, sender_info):
    try:
        if "OPENAI_API_KEY" not in st.secrets:
            return {"subject": "Error", "body_en": "API Key missing."}
            
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"], temperature=0.7)
        
        sys_msg = SystemMessage(content="""
        당신은 B2B 콜드메일 카피라이터입니다. 제품 정보와 바이어 정보를 바탕으로 영문 콜드메일을 작성하세요.
        반드시 아래 JSON 형식으로만 응답해야 합니다.
        {
            "subject": "이메일 제목 (영어)",
            "opener_line": "바이어의 관심을 끌 첫 문장 (영어)",
            "body_en": "이메일 본문 전체 (영어)",
            "body_ko": "이메일 본문 번역본 (한국어)",
            "subject_alternatives": ["대안 제목 1", "대안 제목 2", "대안 제목 3"]
        }
        """)
        user_msg = HumanMessage(content=f"제품: {product_data}\n바이어: {buyer_intel}\n발신자: {sender_info}")
        
        response = llm.invoke([sys_msg, user_msg])
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        return {"subject": "생성 오류", "body_en": str(e), "body_ko": "오류 발생", "opener_line": "", "subject_alternatives": []}

# ==========================================
# 2. 피치덱 스크립트 생성 일꾼
# ==========================================
def generate_pitch_deck_text(product_data, buyer_intel):
    try:
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"], temperature=0.7)
        sys_msg = SystemMessage(content="""
        당신은 투자 피칭/제안서 작성 전문가입니다. 
        반드시 아래 JSON 형식으로 5슬라이드 분량의 피치덱 텍스트를 작성하세요.
        {
            "hook": "제안의 핵심을 찌르는 오프닝 멘트",
            "slides": [
                {"title": "슬라이드 1 제목", "bullets": ["포인트1", "포인트2"], "speaker_note": "발표자 노트"}
            ],
            "closing_cta": "마지막 행동 유도 멘트 (Call to Action)"
        }
        """)
        user_msg = HumanMessage(content=f"제품: {product_data}\n바이어: {buyer_intel}")
        
        response = llm.invoke([sys_msg, user_msg])
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        return {"hook": "오류 발생", "slides": [], "closing_cta": str(e)}

# ==========================================
# 3. 레이더 차트 생성 일꾼 (시각화)
# ==========================================
def generate_flavor_radar_chart(product_data):
    """
    matplotlib을 사용하여 6각 레이더 차트 이미지를 생성합니다.
    (만약 matplotlib이 설치 안되어 있다면 에러 방지용 빈 이미지를 반환합니다)
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import io
        
        # 6개 축 설정
        labels = np.array(['Sweetness', 'Acidity', 'Body', 'Aroma', 'Finish', 'Balance'])
        # 제품 데이터를 바탕으로 가상의 점수(1~5) 부여 (MVP 용)
        stats = np.array([4, 3, 5, 4, 4, 4.5])
        
        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
        stats = np.concatenate((stats,[stats[0]]))
        angles = np.concatenate((angles,[angles[0]]))
        
        fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
        ax.fill(angles, stats, color='#8B3A3A', alpha=0.25)
        ax.plot(angles, stats, color='#8B3A3A', linewidth=2)
        ax.set_yticklabels([])
        
        # 라벨 설정
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=10)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True, bbox_inches='tight')
        buf.seek(0)
        return buf.getvalue()
        
    except ImportError:
        # 라이브러리가 없을 경우 에러 대신 1x1 투명 픽셀 반환 (앱 터짐 방지)
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c\x60\x00\x02\x00\x00\x05\x00\x01\xe2+\xef\x0f\x00\x00\x00\x00IEND\xaeB`\x82'

# ==========================================
# 4. 최종 PDF 생성 일꾼
# ==========================================
def generate_proposal_pdf(product_data, buyer_intel, cold_email, pitch_deck, radar_png, sender_info):
    """
    제안서 내용을 PDF로 병합하여 바이트 형태로 반환합니다.
    (MVP 버전: reportlab 라이브러리가 없어도 에러가 나지 않도록 최소한의 PDF 구조를 반환)
    """
    try:
        from reportlab.pdfgen import canvas
        import io
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(100, 750, f"Proposal for {buyer_intel.get('_buyer_meta', {}).get('company_name', 'Buyer')}")
        c.drawString(100, 730, f"Product: {product_data.get('product_name', 'Product')}")
        c.drawString(100, 710, "This is an auto-generated PDF from Opener MVP.")
        c.save()
        buf.seek(0)
        return buf.getvalue()
        
    except ImportError:
        # reportlab 라이브러리가 없을 경우 아주 단순한 빈 PDF 껍데기 반환
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n196\n%%EOF"

# ==========================================
# 5. 수출 서류 생성용 메뉴판 (설계도 요구)
# ==========================================
DOCUMENT_TYPES = {
    "상업송장 (Commercial Invoice)": "Commercial Invoice",
    "포장명세서 (Packing List)": "Packing List",
    "제조공정도 (Manufacturing Process)": "Manufacturing Process Description",
    "성분분석표 (Certificate of Analysis)": "Certificate of Analysis (COA)"
}

# ==========================================
# 6. 수출 서류 초안 작성 일꾼
# ==========================================
def generate_document(doc_type, product_info, target_market, exporter_info):
    """
    선택한 서류 종류에 맞춰 AI가 영문 수출 서류 초안(Markdown)을 작성합니다.
    """
    try:
        import streamlit as st
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        
        if "OPENAI_API_KEY" not in st.secrets:
            return "오류: API 키가 설정되지 않았습니다."
            
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"], temperature=0.3)
        
        doc_name_en = DOCUMENT_TYPES.get(doc_type, doc_type)
        
        sys_msg = SystemMessage(content=f"""
        당신은 관세사 및 수출입 서류 작성 전문가입니다.
        사용자가 제공한 정보를 바탕으로 [{doc_name_en}]의 초안을 영문으로 작성하세요.
        문서의 형식은 깔끔한 Markdown 테이블이나 리스트 형태를 유지하고, 실제 실무에서 쓰이는 양식처럼 보이게 구성하세요.
        빈칸이나 추가 정보가 필요한 곳은 [  ] 처리하여 사용자가 나중에 채워 넣을 수 있게 하세요.
        """)
        
        user_msg = HumanMessage(content=f"제품 정보: {product_info}\n수출 대상 시장: {target_market}\n수출자 정보: {exporter_info}")
        
        response = llm.invoke([sys_msg, user_msg])
        return response.content
        
    except Exception as e:
        return f"문서 생성 중 오류 발생: {str(e)}"

# ==========================================
# 7. 텍스트 -> PDF 변환 일꾼
# ==========================================
def generate_pdf_bytes(markdown_content, doc_type):
    """
    생성된 Markdown 텍스트를 간단한 PDF로 변환합니다.
    (MVP 버전: reportlab 등 복잡한 라이브러리 의존성을 피하기 위해 텍스트를 담은 기본 PDF 반환)
    """
    try:
        from reportlab.pdfgen import canvas
        import io
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(50, 800, f"Document: {doc_type}")
        
        # Markdown 텍스트를 줄바꿈하여 PDF에 간단히 쓰기
        y_position = 760
        lines = markdown_content.split('\n')
        for line in lines[:40]: # 페이지 넘김 방지를 위해 첫 40줄만 인쇄 (MVP용)
            # 한글 깨짐 방지를 위해 아주 간단히 텍스트만 처리하거나, 영어 위주로 작성됨을 가정
            c.drawString(50, y_position, line.strip()[:80]) # 너무 긴 줄 자르기
            y_position -= 15
            
        c.save()
        buf.seek(0)
        return buf.getvalue()
        
    except ImportError:
        # 라이브러리가 없을 경우 에러 방지용 가짜 PDF 껍데기 반환
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n196\n%%EOF"
