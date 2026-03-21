import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import TypedDict, List, Annotated, Union

# 1. 상태 정의 (혹시 이걸 찾고 있을 수 있습니다)
class InterviewerState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]
    current_step: str
    product_info: dict

# 2. 메인 함수 (대표님이 방금 보신 그 에러의 주인공!)
def chat_with_consultant(messages):
    try:
        if "OPENAI_API_KEY" not in st.secrets:
            return "OpenAI API 키가 없습니다. Secrets를 확인해주세요."
        
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
        system_msg = SystemMessage(content="당신은 전통주 수출 컨설턴트 '오프너'입니다.")
        response = llm.invoke([system_msg] + messages)
        return response.content
    except Exception as e:
        return f"연결 오류: {str(e)}"

# 3. 클래스 버전 (보험용)
class EnglishInterviewer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    def ask_question(self, chat_history):
        return chat_with_consultant(chat_history)

# 4. 모든 종류의 별명(Alias) - 설계도가 어떤 이름을 불러도 다 대답하게 함
Interviewer = EnglishInterviewer
EngInterviewer = EnglishInterviewer

# 5. 기타 필수 함수 및 클래스 (보험용)
def get_interviewer():
    return EnglishInterviewer()

def get_interview_graph():
    return None

class InterviewOutput(TypedDict):
    final_report: str
