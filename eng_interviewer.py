import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

class EngInterviewer:
    def __init__(self):
        # 스트림릿 세이브해둔 키 가져오기
        api_key = st.secrets["OPENAI_API_KEY"]
        self.llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
        
    def ask_question(self, chat_history):
        system_msg = SystemMessage(content="당신은 전통주 수출 컨설턴트입니다. 친절하게 인터뷰를 진행하세요.")
        response = self.llm.invoke([system_msg] + chat_history)
        return response.content

# 다른 파일에서 불러다 쓸 수 있게 내보내기
def get_interviewer():
    return EngInterviewer()
