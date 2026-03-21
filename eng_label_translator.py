import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

# ==========================================
# 1. 지원 언어 목록 (설계도 요구 사항)
# ==========================================
SUPPORTED_LANGUAGES = {
    "영어 (English)": "en",
    "일본어 (日本語)": "ja",
    "중국어 간체 (简体中文)": "zh-CN",
    "베트남어 (Tiếng Việt)": "vi",
    "프랑스어 (Français)": "fr"
}

# ==========================================
# 2. 라벨 텍스트 분석 일꾼
# ==========================================
def analyze_label_text(text):
    """
    사용자가 입력한 라벨 텍스트(문자열)를 분석하여 항목별 JSON(딕셔너리)으로 구조화합니다.
    """
    try:
        if "OPENAI_API_KEY" not in st.secrets:
            return {"error": "API 키가 설정되지 않았습니다."}
            
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"], temperature=0.1) # 정확도를 위해 온도 낮춤
        
        sys_msg = SystemMessage(content="""
        당신은 주류 라벨 분석 전문가입니다. 사용자가 입력한 난잡한 라벨 텍스트에서 주요 정보를 추출하여 반드시 아래 JSON 형식으로만 응답하세요.
        {
            "product_name": "제품명",
            "alcohol_type": "주종 (예: 탁주, 약주, 소주 등)",
            "alcohol_pct": "알코올 도수 (%)",
            "volume": "용량 (ml 등)",
            "ingredients": "원재료명 목록",
            "manufacturer": "제조사명",
            "other_info": "기타 경고 문구 등"
        }
        """)
        user_msg = HumanMessage(content=f"원본 라벨 텍스트:\n{text}")
        
        response = llm.invoke([sys_msg, user_msg])
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
        
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# 3. 라벨 번역 일꾼
# ==========================================
def translate_label(analyzed_data, target_lang_code, target_market):
    """
    구조화된 라벨 데이터를 대상 국가 언어로 번역합니다.
    """
    try:
        if "error" in analyzed_data:
            return {"error": "분석된 데이터에 오류가 있어 번역을 진행할 수 없습니다."}
            
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"], temperature=0.3)
        
        sys_msg = SystemMessage(content=f"""
        당신은 주류 라벨 번역 및 현지화 전문가입니다. 
        주어진 라벨 정보를 대상 언어 코드({target_lang_code})로 번역하세요.
        단순 번역을 넘어, 대상 시장({target_market})의 주류 라벨링 표기법이나 규정 뉘앙스에 맞게 다듬어 주시면 좋습니다.
        결과는 반드시 아래 JSON 형식으로 반환하세요.
        {{
            "Translated_Product_Name": "번역된 제품명",
            "Translated_Alcohol_Type": "번역된 주종",
            "Translated_Alcohol_Pct": "번역된 도수 (예: ABV 14%)",
            "Translated_Volume": "번역된 용량",
            "Translated_Ingredients": "번역된 원재료명",
            "Translated_Manufacturer": "번역된 제조사명",
            "Regulatory_Notes": "이 시장에 수출할 때 라벨에 필수로 추가해야 할 현지 규정/경고문구 (해당 언어로 작성)"
        }}
        """)
        
        # 분석된 JSON 데이터를 문자열로 변환해서 전달
        user_msg = HumanMessage(content=f"분석된 라벨 데이터:\n{json.dumps(analyzed_data, ensure_ascii=False)}")
        
        response = llm.invoke([sys_msg, user_msg])
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
        
    except Exception as e:
        return {"error": str(e)}
