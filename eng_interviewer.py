import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# ==========================================
# 1. 설계도가 애타게 찾던 '상수(이름)'들
# ==========================================
GREETING_MESSAGE = "안녕하세요! 전통주 수출 컨설턴트 오프너입니다. 대표님의 멋진 제품을 해외에 알리기 위해 몇 가지 질문을 드릴게요. 먼저, **제품의 이름과 주종(탁주, 약주 등)**을 말씀해 주시겠어요?"

REQUIRED_FIELDS = [
    "product_name", "alcohol_type", "alcohol_pct", "flavor_profile", 
    "volume", "price_range", "target_country", "brand_story"
]

FIELD_LABELS = {
    "product_name": "제품명",
    "alcohol_type": "주종",
    "alcohol_pct": "알코올 도수",
    "flavor_profile": "맛과 향",
    "volume": "용량",
    "price_range": "가격대",
    "target_country": "타겟 국가",
    "brand_story": "브랜드 스토리"
}

# ==========================================
# 2. 설계도에 딱 맞춘 '핵심 일꾼' 함수들
# ==========================================

def chat_with_consultant(history):
    """AI와 대화하는 메인 엔진"""
    try:
        if "OPENAI_API_KEY" not in st.secrets:
            return "오류: OpenAI API 키가 설정되지 않았습니다."
        
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
        
        # 시스템 메시지 (AI의 역할 부여)
        messages = [SystemMessage(content="당신은 친절한 전통주 수출 컨설턴트입니다. 사용자가 답변하면 다음 정보를 자연스럽게 물어보세요.")]
        
        # Streamlit의 대화 기록을 Langchain 형식으로 변환 (설계도 맞춤형)
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
                
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"AI 연결 중 오류가 발생했습니다: {str(e)}"

def detect_completion(ai_response):
    """
    인터뷰 완료 여부 확인 (설계도가 2개의 값을 요구함)
    (완료여부, 추출된데이터딕셔너리) 를 반환
    """
    # 지금은 무조건 대화를 이어가도록 False 처리 (MVP 초기 설정)
    return False, {}

def strip_completion_marker(text):
    """불필요한 마커 제거"""
    if not text: return ""
    return text.replace("[DONE]", "").strip()

def calc_progress(data):
    """
    진척도 계산 (설계도가 '채워진수, 전체수, 남은항목' 3개를 요구함)
    """
    if not data:
        return 0, len(REQUIRED_FIELDS), [FIELD_LABELS[f] for f in REQUIRED_FIELDS]
        
    filled = 0
    missing_labels = []
    
    for field in REQUIRED_FIELDS:
        if data.get(field):
            filled += 1
        else:
            missing_labels.append(FIELD_LABELS[field])
            
    return filled, len(REQUIRED_FIELDS), missing_labels
