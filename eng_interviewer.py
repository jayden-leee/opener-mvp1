import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import TypedDict, List, Annotated, Union, Any

# 1. 상태(State) 정의 - 모든 가능한 이름 다 넣었습니다.
class InterviewerState(TypedDict):
    messages: List[Any]
    current_step: str
    product_info: dict
    
class AgentState(TypedDict):
    messages: List[Any]

# 2. 메인 함수 - 대표님이 보셨던 그 'chat_with_consultant'
def chat_with_consultant(messages):
    try:
        llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
        system_msg = SystemMessage(content="당신은 전통주 수출 컨설턴트입니다.")
        response = llm.invoke([system_msg] + messages)
        return response.content
    except Exception as e:
        return f"에러 발생: {str(e)}"

# 3. 클래스 및 인터페이스 - 설계도가 부를만한 모든 이름들
class EnglishInterviewer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    def ask_question(self, chat_history):
        return chat_with_consultant(chat_history)

# 별명(Alias) - 설계도가 어떤 이름을 불러도 "나 여기 있어!"라고 대답합니다.
EngInterviewer = EnglishInterviewer
Interviewer = EnglishInterviewer
EnglishInterviewerClass = EnglishInterviewer

# 4. 필수 함수들
def get_interviewer():
    return EnglishInterviewer()

def get_interview_graph():
    return None

def create_interviewer():
    return EnglishInterviewer()

# 5. 출력 형식
class InterviewOutput(TypedDict):
    final_report: str
class InterviewerOutput(TypedDict):
    content: str
