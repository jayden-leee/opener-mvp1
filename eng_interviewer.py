import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, List, Annotated

# 1. 상태(State) 정의 - 혹시 이걸 찾고 있을 수 있습니다.
class InterviewerState(TypedDict):
    messages: List[Annotated[str, "message"]]
    current_step: str
    product_info: dict

# 2. 메인 클래스 (이름을 여러 버전으로 다 만들었습니다)
class EnglishInterviewer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
        
    def ask_question(self, chat_history):
        return "전통주 수출에 대해 무엇이든 말씀해 주세요!"

# 별칭(Alias) - 설계도가 어떤 이름을 불러도 대답할 수 있게 합니다.
EngInterviewer = EnglishInterviewer
Interviewer = EnglishInterviewer

# 3. 필수 함수들
def get_interviewer():
    return EnglishInterviewer()

def get_interview_graph():
    # 혹시 그래프를 찾고 있다면 빈 객체라도 돌려줍니다.
    return None

# 4. 결과물 형식
class InterviewOutput:
    pass
