"""
pages/settings.py
API 키 및 앱 설정 페이지  (v0.5.0 — Supabase 설정 추가)
"""

import streamlit as st
import os
from database import is_connected, get_feedback_stats, get_recent_products, get_top_buyers


def render():
    st.markdown('<div class="page-header"><h1>⚙️ 설정</h1></div>', unsafe_allow_html=True)
    st.write("API 키, 모델, 데이터베이스 설정을 관리합니다.")
    st.markdown("---")

    tab_ai, tab_db, tab_stats, tab_info = st.tabs(["🤖 AI 설정", "🗄️ 데이터베이스", "📊 통계", "ℹ️ 앱 정보"])

    # ── AI 설정 탭 ─────────────────────────────────
    with tab_ai:
        st.subheader("🔑 AI API 키")
        st.info("API 키는 `.env` 파일 저장을 권장합니다. 아래는 현재 세션에만 적용됩니다.")

        col1, col2 = st.columns(2)
        with col1:
            openai_key = st.text_input("OpenAI API Key", type="password",
                                        value=os.getenv("OPENAI_API_KEY", ""), placeholder="sk-...")
            if st.button("OpenAI 저장 (세션)", key="save_oai"):
                os.environ["OPENAI_API_KEY"] = openai_key
                st.success("저장됨")

            tavily_key = st.text_input("Tavily API Key", type="password",
                                        value=os.getenv("TAVILY_API_KEY", ""), placeholder="tvly-...")
            if st.button("Tavily 저장 (세션)", key="save_tvly"):
                os.environ["TAVILY_API_KEY"] = tavily_key
                st.success("저장됨")

        with col2:
            anthropic_key = st.text_input("Anthropic API Key", type="password",
                                           value=os.getenv("ANTHROPIC_API_KEY", ""), placeholder="sk-ant-...")
            if st.button("Anthropic 저장 (세션)", key="save_ant"):
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                st.success("저장됨")

        st.markdown("---")
        st.subheader("🤖 기본 모델")
        provider = st.selectbox("프로바이더", ["openai", "anthropic"],
                                 index=0 if os.getenv("DEFAULT_LLM_PROVIDER","openai") == "openai" else 1)
        model_opts = {
            "openai":    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "anthropic": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        }
        model = st.selectbox("모델", model_opts[provider])
        if st.button("모델 저장 (세션)", key="save_model"):
            os.environ["DEFAULT_LLM_PROVIDER"] = provider
            os.environ["DEFAULT_MODEL"] = model
            st.success(f"{provider} / {model}")

    # ── DB 설정 탭 ──────────────────────────────────
    with tab_db:
        st.subheader("🗄️ Supabase 연결")

        connected = is_connected()
        if connected:
            st.success("🟢 Supabase 연결 중")
        else:
            st.warning("⚪ Supabase 미연결 — 로컬 모드로 실행 중")

        st.markdown("""
        **연결하는 방법:**
        1. [supabase.com](https://supabase.com) 에서 무료 프로젝트 생성
        2. Settings → API에서 `URL`과 `anon public key` 복사
        3. `.env` 파일에 아래 두 줄 추가
        """)

        col1, col2 = st.columns(2)
        with col1:
            sb_url = st.text_input("SUPABASE_URL", type="password",
                                    value=os.getenv("SUPABASE_URL",""),
                                    placeholder="https://xxxx.supabase.co")
        with col2:
            sb_key = st.text_input("SUPABASE_ANON_KEY", type="password",
                                    value=os.getenv("SUPABASE_ANON_KEY",""),
                                    placeholder="eyJhbGciOiJIUzI1NiIs...")

        if st.button("🔌 연결 테스트", key="test_db"):
            os.environ["SUPABASE_URL"]      = sb_url
            os.environ["SUPABASE_ANON_KEY"] = sb_key
            import database as db
            db._supabase_client = None  # 클라이언트 리셋
            if db.is_connected():
                st.success("✅ Supabase 연결 성공!")
            else:
                st.error("❌ 연결 실패. URL과 Key를 확인해주세요.")

        st.markdown("---")
        st.subheader("📋 DB 테이블 생성 SQL")
        st.caption("Supabase SQL Editor에서 아래 SQL을 실행하세요.")

        with st.expander("SQL 보기 / 복사"):
            st.code("""
-- 제품 정보
CREATE TABLE products (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id     TEXT,
  product_name   TEXT,
  alcohol_type   TEXT,
  flavor_profile TEXT,
  price_range    TEXT,
  target_country TEXT[],
  brand_story    TEXT,
  alcohol_pct    TEXT,
  volume         TEXT,
  raw_json       JSONB,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 바이어 분석
CREATE TABLE buyer_analyses (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id           UUID REFERENCES products(id),
  company_name         TEXT,
  country              TEXT,
  city                 TEXT,
  business_type        TEXT,
  match_score          INT DEFAULT 0,
  fit_score            INT DEFAULT 0,
  pain_points_json     JSONB,
  opportunities_json   JSONB,
  preferred_keywords   TEXT[],
  approach_strategy    TEXT,
  fit_reason           TEXT,
  deep_dive_json       JSONB,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- 제안서
CREATE TABLE proposals (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  buyer_analysis_id  UUID REFERENCES buyer_analyses(id),
  email_subject      TEXT,
  email_opener       TEXT,
  email_body_en      TEXT,
  email_body_ko      TEXT,
  pitch_headline     TEXT,
  pitch_hook         TEXT,
  pitch_closing_cta  TEXT,
  cold_email_json    JSONB,
  pitch_deck_json    JSONB,
  pdf_size_bytes     INT DEFAULT 0,
  created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- 피드백
CREATE TABLE feedback (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id  UUID REFERENCES proposals(id),
  session_id   TEXT,
  rating       INT NOT NULL CHECK (rating IN (0, 1)),
  comment      TEXT,
  page_context TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX ON products (created_at DESC);
CREATE INDEX ON buyer_analyses (product_id, fit_score DESC);
CREATE INDEX ON proposals (buyer_analysis_id);
CREATE INDEX ON feedback (proposal_id, rating);
            """, language="sql")

    # ── 통계 탭 ─────────────────────────────────────
    with tab_stats:
        st.subheader("📊 누적 데이터 통계")

        if not is_connected():
            st.info("Supabase 연결 후 실제 통계를 확인할 수 있습니다.")
            # 현재 세션 통계
            st.markdown("**현재 세션 현황**")
            c1, c2, c3 = st.columns(3)
            c1.metric("제품 인터뷰", "1" if st.session_state.get("interview_done") else "0")
            c2.metric("딥다이브 완료", str(len(st.session_state.get("hunter_deep_dives", {}))))
            c3.metric("제안서 생성", "1" if st.session_state.get("proposal_pdf_bytes") else "0")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**최근 제품**")
            products = get_recent_products(5)
            if products:
                for p in products:
                    st.markdown(f"- {p.get('product_name','—')} ({p.get('alcohol_type','—')})")
            else:
                st.caption("데이터 없음")

        with col2:
            st.markdown("**Top 바이어 (fit score)**")
            buyers = get_top_buyers(5)
            if buyers:
                for b in buyers:
                    st.markdown(f"- {b.get('company_name','—')} — {b.get('fit_score',0)}/10")
            else:
                st.caption("데이터 없음")

        st.markdown("---")
        stats = get_feedback_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 피드백", stats["total"])
        c2.metric("👍 좋아요", stats["likes"])
        c3.metric("👎 별로예요", stats["dislikes"])
        c4.metric("만족도", f"{stats['like_rate']}%")

    # ── 앱 정보 탭 ──────────────────────────────────
    with tab_info:
        st.subheader("ℹ️ 앱 정보")
        st.markdown("""
        | 항목 | 내용 |
        |------|------|
        | 버전 | MVP v0.5.0 |
        | 기술 스택 | Python 3.11 · Streamlit · OpenAI / Anthropic |
        | 데이터 | Supabase (PostgreSQL) |
        | 검색 | Tavily AI Search |
        | 차트 | matplotlib |
        | PDF | ReportLab |
        | 배포 | Docker + Cloud Run / Railway / Fly.io |
        | 문의 | opener@example.com |
        """)

