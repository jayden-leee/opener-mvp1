import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import TypedDict, List, Annotated, Union, Any

# 1. 상태(State) 및 타입 정의
class InterviewerState(TypedDict):
    messages: List[Any]
    current_step: str
    product_info: dict

# 2. 메인 대화 함수
def chat_with_consultant(messages):
    try:
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
        system_msg = SystemMessage(content="당신은 전통주 수출 컨설턴트입니다.")
        response = llm.invoke([system_msg] + messages)
        return response.content
    except Exception as e:
        return f"AI 연결 에러: {str(e)}"

# 3. 이번 에러의 주인공: 진척도 계산 함수
def calc_progress(messages):
    """
    대화 길이를 보고 진행률(0~100)을 대략적으로 계산합니다.
    """
    if not messages: return 0
    # 메시지 10개 정도면 완료(100%)라고 가정하고 계산
    progress = min(len(messages) * 10, 100)
    return progress

# 4. 필수 유틸리티 함수들 (완료 감지, 마커 제거 등)
def detect_completion(messages):
    return False

def strip_completion_marker(text):
    if not text: return ""
    return text.replace("[DONE]", "").strip()

# 5. 클래스 인터페이스 및 별칭 (설계도가 부를 수 있는 모든 이름)
class EnglishInterviewer:
    def __init__(self):
        if "OPENAI_API_KEY" in st.secrets:
            self.llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    def ask_question(self, chat_history):
        return chat_with_consultant(chat_history)

Interviewer = EnglishInterviewer
EngInterviewer = EnglishInterviewer

# 6. 필수 함수들 (보험용)
def get_interviewer():
    return EnglishInterviewer()

def get_interview_graph():
    return None

def reset_interview():
    st.session_state.messages = []
    
class InterviewOutput(TypedDict):
    final_report: str
