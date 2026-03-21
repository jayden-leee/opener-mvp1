import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 1. 인터뷰어 클래스 (이름을 여러 버전으로 준비했습니다)
class EnglishInterviewer:
    def __init__(self):
        if "OPENAI_API_KEY" not in st.secrets:
            st.error("OpenAI API Key가 설정되지 않았습니다.")
            return
        self.llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
        
    def ask_question(self, chat_history):
        system_msg = SystemMessage(content="당신은 전통주 수출 컨설턴트입니다. 친절하게 인터뷰를 진행하세요.")
        response = self.llm.invoke([system_msg] + chat_history)
        return response.content

# 혹시 다른 이름으로 부를까봐 별명을 지어둡니다.
EngInterviewer = EnglishInterviewer

# 2. 상태 관리용 함수 (보통 이게 필요합니다)
def get_interviewer():
    return EnglishInterviewer()

# 3. 빈 클래스 (에러 방지용)
class InterviewerState:
    pass
