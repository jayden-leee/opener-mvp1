import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import TypedDict, List, Annotated, Union, Any

# 1. 상태(State) 정의
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

# 3. 이번 에러의 주인공: 완료 감지 및 마커 제거 함수
def detect_completion(messages):
    # 인터뷰 완료 여부를 판단 (임시로 False)
    return False

def strip_completion_marker(text):
    """
    답변에서 불필요한 마커를 제거하는 청소부 함수입니다.
    """
    if not text: return ""
    return text.replace("[DONE]", "").replace("<|endoftext|>", "").strip()

# 4. 클래스 버전 인터페이스 (보험용)
class EnglishInterviewer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    def ask_question(self, chat_history):
        return chat_with_consultant(chat_history)

# 별칭(Alias) 설정 - 어떤 이름을 불러도 대답하게 함
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
