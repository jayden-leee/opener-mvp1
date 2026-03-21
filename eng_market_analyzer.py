import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

# ==========================================
# 1. 수출 시장 기본 데이터 (설계도 요구 사항)
# ==========================================
EXPORT_MARKETS = {
    "미국 (USA)": {"code": "US", "currency": "USD"},
    "일본 (Japan)": {"code": "JP", "currency": "JPY"},
    "베트남 (Vietnam)": {"code": "VN", "currency": "VND"},
    "홍콩 (Hong Kong)": {"code": "HK", "currency": "HKD"},
    "호주 (Australia)": {"code": "AU", "currency": "AUD"}
}

# ==========================================
# 2. 시장 분석 AI 엔진
# ==========================================
def analyze_market(product_info, target_market):
    """
    AI를 사용하여 제품 정보와 타겟 시장을 분석합니다.
    (설계도 요구: 딕셔너리 반환 - opportunity_score, market_summary, key_challenges, recommendations, target_consumer, estimated_price_range)
    """
    try:
        if "OPENAI_API_KEY" not in st.secrets:
            return {"error": "API 키가 설정되지 않았습니다. Secrets를 확인해주세요."}
            
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"], temperature=0.7)
        
        system_msg = SystemMessage(content="""
        당신은 전통주 수출 시장 분석 전문가입니다. 주어진 제품 정보와 타겟 시장을 분석하여 반드시 아래 JSON 형식으로만 답변하세요. 다른 말은 절대 덧붙이지 마세요.
        {
            "opportunity_score": 8,
            "market_summary": "이 시장은 최근 한국 전통주에 대한 관심이 높아지고 있습니다...",
            "key_challenges": ["높은 주류세", "콜드체인 유통망 확보 어려움"],
            "recommendations": ["프리미엄 한식당 중심의 B2B 영업", "SNS 인플루언서 활용"],
            "target_consumer": "K-Culture에 관심이 많은 2030 여성",
            "estimated_price_range": "현지 예상가 $20 - $30"
        }
        """)
        
        user_msg = HumanMessage(content=f"제품 정보: {product_info}\n타겟 시장: {target_market}")
        
        response = llm.invoke([system_msg, user_msg])
        
        # AI가 반환한 JSON 문자열을 파이썬 딕셔너리로 변환
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3] # 마크다운 코드 블록 제거
            
        return json.loads(content)
        
    except Exception as e:
        return {"error": f"시장 분석 중 오류가 발생했습니다: {str(e)}"}

# ==========================================
# 3. 규정 체크 로직
# ==========================================
def check_regulations(product_info, market_code):
    """
    제품 정보와 시장 코드를 바탕으로 주요 규정을 체크합니다.
    (설계도 요구: 리스트 안에 딕셔너리 반환 - status, item, detail)
    """
    checks = []
    
    # 예시 로직 (실제로는 더 복잡한 룰셋이나 AI를 적용할 수 있음)
    alcohol_pct = float(product_info.get('alcohol', '0%').replace('%', ''))
    
    # 1. 라벨링 규정 (기본)
    checks.append({
        "status": "성공", 
        "item": "라벨링", 
        "detail": f"{market_code} 현지 언어로 된 영양 성분 및 경고 문구 부착 필수"
    })
    
    # 2. 알코올 도수 관련
    if alcohol_pct > 20:
        checks.append({
            "status": "주의", 
            "item": "주류세", 
            "detail": "고도주로 분류되어 높은 주류세가 부과될 수 있습니다."
        })
    else:
        checks.append({
            "status": "성공", 
            "item": "주류세", 
            "detail": "저도주로 분류되어 비교적 유리한 세율 적용 가능"
        })
        
    # 3. 주종 관련 (막걸리 예시)
    if product_info.get('type') == '막걸리':
        checks.append({
            "status": "주의", 
            "item": "유통 기한", 
            "detail": "살균 막걸리가 아닐 경우 콜드체인(냉장 유통) 필수"
        })

    return checks
