"""
utils/styles.py
오프너 Streamlit 앱의 커스텀 CSS 스타일
"""

import streamlit as st


CUSTOM_CSS = """
<style>
  /* ── 폰트 ── */
  @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700&family=Noto+Sans+KR:wght@300;400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
  }

  h1, h2, h3 {
    font-family: 'Noto Serif KR', serif;
  }

  /* ── 색상 테마 ── */
  :root {
    --color-primary: #8B3A3A;   /* 전통 자기 빨강 */
    --color-accent:  #C9973A;   /* 황금빛 */
    --color-bg:      #FDF8F2;   /* 한지 배경 */
    --color-text:    #2C1810;   /* 먹 색 */
    --color-border:  #E8DDD0;
  }

  /* ── 메인 컨테이너 ── */
  .block-container {
    padding-top: 2rem;
    max-width: 1100px;
  }

  /* ── 사이드바 ── */
  [data-testid="stSidebar"] {
    background-color: #2C1810;
  }
  [data-testid="stSidebar"] * {
    color: #FDF8F2 !important;
  }

  /* ── 카드 컴포넌트 ── */
  .opener-card {
    background: white;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(44, 24, 16, 0.06);
  }

  /* ── 배지 ── */
  .badge-pass   { background: #e6f4ea; color: #1e7e34; padding: 2px 10px; border-radius: 99px; font-size: 0.82rem; }
  .badge-warn   { background: #fff3cd; color: #856404; padding: 2px 10px; border-radius: 99px; font-size: 0.82rem; }
  .badge-fail   { background: #f8d7da; color: #721c24; padding: 2px 10px; border-radius: 99px; font-size: 0.82rem; }

  /* ── 버튼 ── */
  .stButton > button {
    background-color: var(--color-primary);
    color: white;
    border-radius: 8px;
    border: none;
    font-family: 'Noto Sans KR', sans-serif;
    font-weight: 500;
  }
  .stButton > button:hover {
    background-color: #6d2d2d;
    color: white;
  }

  /* ── 헤더 섹션 ── */
  .page-header {
    border-bottom: 2px solid var(--color-primary);
    padding-bottom: 0.75rem;
    margin-bottom: 2rem;
  }
  .page-header h1 { color: var(--color-primary); }
</style>
"""


def load_css():
    """Streamlit 앱에 커스텀 CSS를 주입합니다."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def card(content_fn):
    """카드 레이아웃 컨텍스트 매니저 대용 헬퍼"""
    st.markdown('<div class="opener-card">', unsafe_allow_html=True)
    content_fn()
    st.markdown('</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """규정 체크 결과를 HTML 배지로 반환합니다."""
    mapping = {
        "통과": ("badge-pass", "✅ 통과"),
        "주의": ("badge-warn", "⚠️ 주의"),
        "실패": ("badge-fail", "❌ 실패"),
    }
    cls, label = mapping.get(status, ("badge-warn", status))
    return f'<span class="{cls}">{label}</span>'
