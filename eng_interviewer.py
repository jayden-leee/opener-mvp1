import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import TypedDict, List, Annotated, Union, Any

# 1. 상태(State) 정의
class InterviewerState(TypedDict):
    messages: List[Any]
    current_step: str
    product_info: dict

# 2. 메인 대화 함수 (chat_with_consultant)
def chat_with_consultant(messages):
    try:
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
        system_msg = SystemMessage(content="당신은 전통주 수출 컨설턴트입니다. 친절하게 상담을 진행하세요.")
        response = llm.invoke([system_msg] + messages)
        return response.content
    except Exception as e:
        return f"AI 연결 에러: {str(e)}"

# 3. ★이번 에러의 핵심: 인터뷰 완료 감지 함수★
def detect_completion(messages):
    """
    AI가 대화 내용을 보고 인터뷰를 마쳐도 될지 판단합니다.
    지금은 MVP 단계이므로, 일단 False를 돌려주어 대화가 계속되게 합니다.
    """
    # 대화가 너무 길어지거나 특정 키워드가 나오면 True를 반환하도록 나중에 확장 가능합니다.
    return False

# 4. 클래스 버전 인터페이스 (보험용)
class EnglishInterviewer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    def ask_question(self, chat_history):
        return chat_with_consultant(chat_history)

# 별칭(Alias) 설정
EngInterviewer = EnglishInterviewer
Interviewer = EnglishInterviewer

# 5. 필수 함수들
def get_interviewer():
    return EnglishInterviewer()

def get_interview_graph():
    return None

# 6. 출력 형식 정의
class InterviewOutput(TypedDict):
    final_report: str
