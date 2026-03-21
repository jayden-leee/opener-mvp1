import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# 대표님! 에러가 났던 바로 그 '이름'입니다. 
def chat_with_consultant(messages):
    """
    AI 컨설턴트와 대화하는 핵심 함수입니다.
    """
    try:
        # 1. API 키 확인
        if "OPENAI_API_KEY" not in st.secrets:
            return "오류: OpenAI API 키가 설정되지 않았습니다. Secrets를 확인해주세요."

        # 2. AI 모델 초기화
        llm = ChatOpenAI(
            model="gpt-4o", 
            api_key=st.secrets["OPENAI_API_KEY"],
            temperature=0.7
        )

        # 3. 페르소나 설정 (전통주 수출 전문가)
        system_instruction = SystemMessage(content="""
        당신은 전통주 해외 수출 컨설턴트 '오프너'입니다. 
        사용자가 자신의 전통주 제품을 설명하면, 수출 제안서를 만들기 위해 필요한 정보들을 친절하게 물어봐주세요.
        전문적이면서도 격려하는 톤을 유지하세요.
        """)

        # 4. 전체 메시지 구성 (설정 + 대화 기록)
        full_messages = [system_instruction] + messages

        # 5. AI 답변 생성
        response = llm.invoke(full_messages)
        
        return response.content

    except Exception as e:
        return f"AI 연결 중 오류가 발생했습니다: {str(e)}"

# --- 아래는 혹시 모를 다른 에러 방지용 '보험' 코드들입니다 ---

class EnglishInterviewer:
    def ask_question(self, chat_history):
        return chat_with_consultant(chat_history)

def get_interviewer():
    return EnglishInterviewer()

class InterviewerState:
    pass
