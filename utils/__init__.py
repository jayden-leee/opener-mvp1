"""utils/ — 오프너 공통 유틸리티 패키지"""
from utils.navigation import PAGES, render_sidebar
from utils.feedback_widget import render_feedback_widget

__all__ = ["PAGES", "render_sidebar", "render_feedback_widget"]

"""
오프너(Opener) - 전통주 수출용 AI SaaS MVP
메인 애플리케이션 진입점  v0.5.0
"""

import streamlit as st
from dotenv import load_dotenv
import os
import uuid

# 환경변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="오프너(Opener) — 전통주 수출 AI",
    page_icon="🍶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 세션 ID 초기화 (사용자 구분용) ──────────────
if "_session_id" not in st.session_state:
    st.session_state["_session_id"] = str(uuid.uuid4())

# ── 커스텀 CSS ───────────────────────────────────
from utils.styles import load_css
load_css()

# ── 인터뷰 완료 후 자동 DB 저장 ─────────────────
# interview.py에서 interview_done이 새로 True가 된 직후 한 번만 실행
if (
    st.session_state.get("interview_done")
    and st.session_state.get("product_data")
    and not st.session_state.get("_product_saved_id")
):
    from database import save_product
    pid = save_product(
        st.session_state["product_data"],
        session_id=st.session_state["_session_id"],
    )
    st.session_state["_product_saved_id"] = pid

# ── 제안서 완료 후 자동 DB 저장 ─────────────────
if (
    st.session_state.get("proposal_pdf_bytes")
    and st.session_state.get("proposal_cold_email")
    and not st.session_state.get("_proposal_saved_id")
):
    from database import save_full_pipeline
    result = save_full_pipeline(
        product_data=st.session_state.get("product_data", {}),
        buyer_intel=st.session_state.get("proposal_target_buyer") or {},
        cold_email=st.session_state.get("proposal_cold_email", {}),
        pitch_deck=st.session_state.get("proposal_pitch_deck", {}),
        pdf_bytes=st.session_state.get("proposal_pdf_bytes"),
        session_id=st.session_state["_session_id"],
    )
    st.session_state["_proposal_saved_id"] = result.get("proposal_id")
    st.session_state["_buyer_saved_id"]    = result.get("buyer_id")

# ── nav_target 리다이렉트 ────────────────────────
if "nav_target" in st.session_state:
    target = st.session_state.pop("nav_target")
    from utils.navigation import PAGES
    page_values = list(PAGES.values())
    if target in page_values:
        st.session_state["_nav_index"] = page_values.index(target)

# ── 네비게이션 ───────────────────────────────────
from utils.navigation import render_sidebar
page = render_sidebar()

# ── DB 연결 상태 사이드바 표시 ───────────────────
from database import is_connected
with st.sidebar:
    st.markdown("---")
    if is_connected():
        st.markdown(
            '<div style="font-size:0.72rem;color:#1e7e34;text-align:center;">'
            '🟢 Supabase 연결됨</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:0.72rem;color:#aaa;text-align:center;">'
            '⚪ DB 미연결 (로컬 모드)</div>',
            unsafe_allow_html=True,
        )

# ── 페이지 라우팅 ────────────────────────────────
if page == "홈":
    from pages.home import render
    render()

elif page in ("제품 인터뷰", "💬 제품 인터뷰"):
    from pages.interview import render
    render()

elif page == "바이어 발굴":
    from pages.buyer_hunter import render
    render()

elif page == "제안서 생성":
    from pages.proposal_generator import render
    render()

elif page == "라벨 번역":
    from pages.label_translator import render
    render()

elif page == "시장 분석":
    from pages.market_analysis import render
    render()

elif page == "수출 서류":
    from pages.export_docs import render
    render()

elif page == "설정":
    from pages.settings import render
    render()

# ── 전역 피드백 위젯 (하단 고정) ────────────────
st.markdown("---")
from utils.feedback_widget import render_feedback_widget
render_feedback_widget(
    page_context=page,
    proposal_id=st.session_state.get("_proposal_saved_id"),
    show_stats=False,
)


"""
database.py  —  Supabase 연동 데이터 레이어

테이블 구조:
  ┌────────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
  │   products         │─1:N─│   buyer_analyses     │─1:1─│   proposals      │
  ├────────────────────┤     ├─────────────────────┤     ├──────────────────┤
  │ id (uuid PK)       │     │ id (uuid PK)         │     │ id (uuid PK)     │
  │ session_id         │     │ product_id (FK)      │     │ buyer_id (FK)    │
  │ product_name       │     │ company_name         │     │ cold_email_json  │
  │ alcohol_type       │     │ country              │     │ pitch_deck_json  │
  │ flavor_profile     │     │ fit_score            │     │ pdf_size_bytes   │
  │ price_range        │     │ pain_points_json     │     │ created_at       │
  │ target_country     │     │ opportunities_json   │     └──────────────────┘
  │ brand_story        │     │ approach_strategy    │
  │ alcohol_pct        │     │ deep_dive_json       │     ┌──────────────────┐
  │ volume             │     │ created_at           │     │   feedback       │
  │ raw_json           │     └─────────────────────┘     ├──────────────────┤
  │ created_at         │                                  │ id (uuid PK)     │
  └────────────────────┘                                  │ proposal_id (FK) │
                                                          │ rating (1=👍 0=👎)│
                                                          │ comment          │
                                                          │ page_context     │
                                                          │ created_at       │
                                                          └──────────────────┘

Supabase 미설치/미연결 시 → 모든 write는 조용히 스킵, read는 빈 리스트 반환.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Supabase 클라이언트 싱글턴
# ──────────────────────────────────────────────────────────

_supabase_client = None
_supabase_available = False


def _get_client():
    """Supabase 클라이언트를 반환합니다. 없으면 None."""
    global _supabase_client, _supabase_available

    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_ANON_KEY", "").strip()

    if not url or not key:
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(url, key)
        _supabase_available = True
        logger.info("Supabase 연결 성공: %s", url[:40])
        return _supabase_client
    except ImportError:
        logger.warning("supabase-py 미설치. `pip install supabase`")
        return None
    except Exception as e:
        logger.warning("Supabase 연결 실패: %s", e)
        return None


def is_connected() -> bool:
    """Supabase 연결 가능 여부를 반환합니다."""
    return _get_client() is not None


# ──────────────────────────────────────────────────────────
# 내부 헬퍼
# ──────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(obj: Any, max_depth: int = 6) -> Any:
    """
    JSON 직렬화 전 데이터를 정제합니다.
    - 바이트/바이너리 필드 제거
    - None → null 허용
    - 무한 중첩 방지
    - 긴 문자열 트리밍 (8KB)
    """
    if max_depth <= 0:
        return "[truncated]"
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, bytes):
        return f"[binary {len(obj)} bytes]"
    if isinstance(obj, str):
        return obj[:8192] if len(obj) > 8192 else obj
    if isinstance(obj, (list, tuple)):
        return [_clean(v, max_depth - 1) for v in obj]
    if isinstance(obj, dict):
        return {k: _clean(v, max_depth - 1) for k, v in obj.items() if k not in ("_binary", "pdf_bytes")}
    return str(obj)


def _to_json(obj: Any) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False)


def _safe_insert(table: str, payload: dict) -> Optional[dict]:
    """단일 레코드를 삽입하고 결과를 반환합니다. 실패 시 None."""
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.table(table).insert(payload).execute()
        rows = resp.data
        return rows[0] if rows else None
    except Exception as e:
        logger.error("DB insert 실패 [%s]: %s", table, e)
        return None


def _safe_upsert(table: str, payload: dict, on_conflict: str = "id") -> Optional[dict]:
    """upsert (insert or update)."""
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.table(table).upsert(payload, on_conflict=on_conflict).execute()
        rows = resp.data
        return rows[0] if rows else None
    except Exception as e:
        logger.error("DB upsert 실패 [%s]: %s", table, e)
        return None


# ──────────────────────────────────────────────────────────
# 1) 제품 정보 저장
# ──────────────────────────────────────────────────────────

def save_product(product_data: dict, session_id: Optional[str] = None) -> Optional[str]:
    """
    인터뷰로 수집한 제품 정보를 DB에 저장합니다.

    Returns:
        str | None : 생성된 product UUID (DB 미연결 시 임시 UUID 반환)
    """
    pid = str(uuid.uuid4())
    sid = session_id or str(uuid.uuid4())

    countries = product_data.get("target_country", [])
    if isinstance(countries, str):
        countries = [countries]

    payload = {
        "id":             pid,
        "session_id":     sid,
        "product_name":   str(product_data.get("product_name", ""))[:200],
        "alcohol_type":   str(product_data.get("alcohol_type", ""))[:100],
        "flavor_profile": str(product_data.get("flavor_profile", ""))[:500],
        "price_range":    str(product_data.get("price_range", ""))[:100],
        "target_country": countries,
        "brand_story":    str(product_data.get("brand_story", ""))[:2000],
        "alcohol_pct":    str(product_data.get("alcohol_pct", ""))[:20],
        "volume":         str(product_data.get("volume", ""))[:50],
        "raw_json":       _to_json(product_data),
        "created_at":     _now_iso(),
    }

    result = _safe_insert("products", payload)
    if result:
        logger.info("제품 저장 완료: %s (%s)", product_data.get("product_name"), pid)
    return pid


# ──────────────────────────────────────────────────────────
# 2) 바이어 분석 결과 저장
# ──────────────────────────────────────────────────────────

def save_buyer_analysis(
    buyer_intel: dict,
    product_id: Optional[str] = None,
) -> Optional[str]:
    """
    딥다이브 인텔리전스 분석 결과를 저장합니다.

    Returns:
        str | None : 생성된 buyer_analysis UUID
    """
    bid       = str(uuid.uuid4())
    meta      = buyer_intel.get("_buyer_meta", {})
    pa_points = buyer_intel.get("pain_points", [])
    opps      = buyer_intel.get("opportunities", [])

    payload = {
        "id":               bid,
        "product_id":       product_id,
        "company_name":     str(meta.get("company_name", ""))[:200],
        "country":          str(meta.get("country", ""))[:100],
        "city":             str(meta.get("city", ""))[:100],
        "business_type":    str(meta.get("business_type", ""))[:100],
        "match_score":      int(meta.get("match_score", 0)),
        "fit_score":        int(buyer_intel.get("fit_score", 0)),
        "pain_points_json": _to_json(pa_points),
        "opportunities_json": _to_json(opps),
        "preferred_keywords": buyer_intel.get("preferred_keywords", []),
        "approach_strategy": str(buyer_intel.get("approach_strategy", ""))[:2000],
        "fit_reason":        str(buyer_intel.get("fit_reason", ""))[:500],
        "deep_dive_json":    _to_json(_clean(buyer_intel)),
        "created_at":        _now_iso(),
    }

    result = _safe_insert("buyer_analyses", payload)
    if result:
        logger.info("바이어 분석 저장: %s (%s)", meta.get("company_name"), bid)
    return bid


# ──────────────────────────────────────────────────────────
# 3) 제안서 텍스트 저장
# ──────────────────────────────────────────────────────────

def save_proposal(
    cold_email: dict,
    pitch_deck: dict,
    buyer_analysis_id: Optional[str] = None,
    pdf_size_bytes: int = 0,
) -> Optional[str]:
    """
    생성된 제안서 텍스트(콜드메일 + 피치덱)를 저장합니다.
    PDF 바이너리는 저장하지 않고 크기만 기록합니다.

    Returns:
        str | None : 생성된 proposal UUID
    """
    prop_id = str(uuid.uuid4())

    payload = {
        "id":                  prop_id,
        "buyer_analysis_id":   buyer_analysis_id,
        "email_subject":       str(cold_email.get("subject", ""))[:500],
        "email_opener":        str(cold_email.get("opener_line", ""))[:500],
        "email_body_en":       str(cold_email.get("body_en", ""))[:5000],
        "email_body_ko":       str(cold_email.get("body_ko", ""))[:5000],
        "pitch_headline":      str(pitch_deck.get("headline", ""))[:300],
        "pitch_hook":          str(pitch_deck.get("hook", ""))[:1000],
        "pitch_closing_cta":   str(pitch_deck.get("closing_cta", ""))[:500],
        "cold_email_json":     _to_json(_clean(cold_email)),
        "pitch_deck_json":     _to_json(_clean(pitch_deck)),
        "pdf_size_bytes":      pdf_size_bytes,
        "created_at":          _now_iso(),
    }

    result = _safe_insert("proposals", payload)
    if result:
        logger.info("제안서 저장 완료: %s (PDF %d bytes)", prop_id, pdf_size_bytes)
    return prop_id


# ──────────────────────────────────────────────────────────
# 4) 피드백 저장
# ──────────────────────────────────────────────────────────

def save_feedback(
    rating: int,
    proposal_id: Optional[str] = None,
    page_context: str = "",
    comment: str = "",
    session_id: Optional[str] = None,
) -> Optional[str]:
    """
    사용자 피드백을 저장합니다.

    Args:
        rating       : 1 = 좋아요👍, 0 = 싫어요👎
        proposal_id  : 연결된 제안서 ID (없으면 None)
        page_context : 피드백이 발생한 페이지명
        comment      : 선택적 텍스트 코멘트
        session_id   : 세션 식별자

    Returns:
        str | None : 생성된 feedback UUID
    """
    fid = str(uuid.uuid4())
    payload = {
        "id":           fid,
        "proposal_id":  proposal_id,
        "session_id":   session_id or "",
        "rating":       int(rating),
        "comment":      str(comment)[:1000],
        "page_context": str(page_context)[:100],
        "created_at":   _now_iso(),
    }

    result = _safe_insert("feedback", payload)
    emoji = "👍" if rating == 1 else "👎"
    logger.info("피드백 저장: %s %s (page=%s)", emoji, fid, page_context)
    return fid


# ──────────────────────────────────────────────────────────
# 5) 통계 조회
# ──────────────────────────────────────────────────────────

def get_feedback_stats(proposal_id: Optional[str] = None) -> dict:
    """
    피드백 통계를 반환합니다.

    Returns:
        {"total": int, "likes": int, "dislikes": int, "like_rate": float}
    """
    client = _get_client()
    empty = {"total": 0, "likes": 0, "dislikes": 0, "like_rate": 0.0}
    if client is None:
        return empty

    try:
        q = client.table("feedback").select("rating")
        if proposal_id:
            q = q.eq("proposal_id", proposal_id)
        resp = q.execute()
        rows = resp.data or []
        total    = len(rows)
        likes    = sum(1 for r in rows if r.get("rating") == 1)
        dislikes = total - likes
        return {
            "total":     total,
            "likes":     likes,
            "dislikes":  dislikes,
            "like_rate": round(likes / total * 100, 1) if total else 0.0,
        }
    except Exception as e:
        logger.error("피드백 통계 조회 실패: %s", e)
        return empty


def get_recent_products(limit: int = 10) -> list[dict]:
    """최근 생성된 제품 목록을 반환합니다."""
    client = _get_client()
    if client is None:
        return []
    try:
        resp = (
            client.table("products")
            .select("id, product_name, alcohol_type, target_country, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        logger.error("제품 목록 조회 실패: %s", e)
        return []


def get_top_buyers(limit: int = 10) -> list[dict]:
    """fit_score 높은 바이어 분석 결과를 반환합니다."""
    client = _get_client()
    if client is None:
        return []
    try:
        resp = (
            client.table("buyer_analyses")
            .select("company_name, country, fit_score, match_score, created_at")
            .order("fit_score", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        logger.error("바이어 목록 조회 실패: %s", e)
        return []


# ──────────────────────────────────────────────────────────
# 6) 전체 파이프라인 저장 (편의 함수)
# ──────────────────────────────────────────────────────────

def save_full_pipeline(
    product_data: dict,
    buyer_intel: dict,
    cold_email: dict,
    pitch_deck: dict,
    pdf_bytes: Optional[bytes] = None,
    session_id: Optional[str] = None,
) -> dict:
    """
    제품 → 바이어 분석 → 제안서를 순서대로 저장하는 편의 함수.

    Returns:
        {
          "product_id":    str,
          "buyer_id":      str,
          "proposal_id":   str,
          "db_connected":  bool,
        }
    """
    sid = session_id or str(uuid.uuid4())

    product_id  = save_product(product_data, session_id=sid)
    buyer_id    = save_buyer_analysis(buyer_intel, product_id=product_id)
    proposal_id = save_proposal(
        cold_email=cold_email,
        pitch_deck=pitch_deck,
        buyer_analysis_id=buyer_id,
        pdf_size_bytes=len(pdf_bytes) if pdf_bytes else 0,
    )

    return {
        "product_id":   product_id,
        "buyer_id":     buyer_id,
        "proposal_id":  proposal_id,
        "db_connected": is_connected(),
        "session_id":   sid,
    }

version: "3.9"

services:
  opener:
    build: .
    image: opener:latest
    container_name: opener_app
    ports:
      - "8501:8501"
    env_file:
      - .env
    environment:
      - APP_ENV=production
      - MPLCONFIGDIR=/tmp/matplotlib
    volumes:
      # 로컬 개발 시 코드 마운트 (프로덕션에서는 제거)
      - .:/app
      - /app/__pycache__
      - /app/engine/__pycache__
      - /app/pages/__pycache__
      - /app/utils/__pycache__
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

  # 로컬 Supabase가 없을 때 테스트용 (선택)
  # supabase-local:
  #   image: supabase/postgres:15
  #   ports:
  #     - "5432:5432"
  #   environment:
  #     POSTGRES_PASSWORD: your_password

# =============================================
# 오프너(Opener) — Production Dockerfile
# =============================================
# 빌드:  docker build -t opener .
# 실행:  docker run -p 8501:8501 --env-file .env opener
# =============================================

# ── 1단계: 빌더 ─────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# 시스템 빌드 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 의존성 먼저 설치 (레이어 캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── 2단계: 런타임 ────────────────────────────
FROM python:3.11-slim AS runtime

# 한국어 폰트 + tesseract + 폰트 도구
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    tesseract-ocr \
    tesseract-ocr-kor \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 의존성 복사
COPY --from=builder /install /usr/local

# 앱 코드
WORKDIR /app
COPY . .

# Streamlit 설정
RUN mkdir -p /app/.streamlit
COPY .streamlit/config.toml /app/.streamlit/config.toml

# matplotlib 캐시 디렉토리
ENV MPLCONFIGDIR=/tmp/matplotlib
RUN mkdir -p /tmp/matplotlib

# 비루트 사용자 (보안)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /tmp/matplotlib
USER appuser

# 포트
EXPOSE 8501

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 실행
ENTRYPOINT ["streamlit", "run", "app.py", \
  "--server.port=8501", \
  "--server.address=0.0.0.0", \
  "--server.headless=true", \
  "--browser.gatherUsageStats=false"]

"""
utils/feedback_widget.py

앱 하단에 표시되는 "이 제안서가 마음에 드시나요?" 피드백 버튼 컴포넌트.
모든 페이지 하단에서 재사용 가능하며 DB 저장과 연동됩니다.
"""

from __future__ import annotations

import streamlit as st
from database import save_feedback, get_feedback_stats, is_connected


def render_feedback_widget(
    page_context: str = "",
    proposal_id: str | None = None,
    show_stats: bool = False,
):
    """
    좋아요/싫어요 피드백 버튼을 렌더링합니다.
    결과는 Supabase feedback 테이블에 저장됩니다.

    Args:
        page_context : 피드백이 발생한 페이지 이름
        proposal_id  : 연결된 제안서 ID (있으면 함께 저장)
        show_stats   : True이면 누적 피드백 통계도 표시
    """
    session_key_done    = f"fb_done_{page_context}"
    session_key_comment = f"fb_comment_{page_context}"

    # ── 이미 피드백 완료 ──────────────────────
    if st.session_state.get(session_key_done):
        rating = st.session_state.get(f"fb_rating_{page_context}", -1)
        emoji  = "👍" if rating == 1 else "👎"
        st.markdown(f"""
        <div style="
            display:flex; align-items:center; gap:10px;
            background:#f0faf0; border-radius:10px;
            padding:10px 16px; margin-top:1rem;
            border:1px solid #a8d5b1; font-size:0.88rem; color:#1e7e34;
        ">
            {emoji} &nbsp; 피드백 감사합니다! 서비스 개선에 반영하겠습니다.
        </div>
        """, unsafe_allow_html=True)
        return

    # ── 피드백 위젯 ───────────────────────────
    st.markdown("""
    <div style="
        border-top: 1px solid #E8DDD0;
        margin-top: 2rem; padding-top: 1rem;
    ">
    </div>
    """, unsafe_allow_html=True)

    col_msg, col_like, col_dislike, col_gap = st.columns([4, 1, 1, 2])

    with col_msg:
        st.markdown(
            '<div style="padding-top:6px; font-size:0.92rem; color:#555; font-weight:500;">'
            '이 결과가 도움이 되셨나요?'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_like:
        if st.button("👍 좋아요", key=f"like_{page_context}", use_container_width=True):
            _handle_feedback(1, page_context, proposal_id, session_key_done)

    with col_dislike:
        if st.button("👎 별로예요", key=f"dislike_{page_context}", use_container_width=True):
            _handle_feedback(0, page_context, proposal_id, session_key_done)

    # ── 선택적 통계 표시 ──────────────────────
    if show_stats and is_connected():
        stats = get_feedback_stats(proposal_id)
        if stats["total"] > 0:
            st.markdown(f"""
            <div style="font-size:0.78rem; color:#aaa; margin-top:6px; text-align:right;">
                누적: 👍 {stats['likes']}  👎 {stats['dislikes']}
                &nbsp;·&nbsp; 만족도 {stats['like_rate']}%
            </div>
            """, unsafe_allow_html=True)


def _handle_feedback(
    rating: int,
    page_context: str,
    proposal_id: str | None,
    session_key_done: str,
):
    """피드백을 저장하고 세션 플래그를 설정합니다."""
    session_id = st.session_state.get("_session_id", "")

    fid = save_feedback(
        rating=rating,
        proposal_id=proposal_id,
        page_context=page_context,
        session_id=session_id,
    )

    st.session_state[session_key_done]                     = True
    st.session_state[f"fb_rating_{page_context}"]          = rating
    st.session_state[f"fb_id_{page_context}"]              = fid

    if is_connected():
        st.toast("피드백이 저장되었습니다!", icon="✅")
    else:
        st.toast("피드백을 받았습니다! (DB 미연결)", icon="✅")

    st.rerun()

# 🍶 오프너(Opener) — 전통주 수출 AI SaaS

> 한국 전통주의 글로벌 진출을 돕는 **5단계 AI 수출 자동화 플랫폼**

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green)](https://supabase.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)

---

## 🚀 5단계 워크플로우

```
1단계·2단계  💬 제품 인터뷰   →  AI 컨설턴트와 대화, 제품 정보 자동 수집
3단계        🎯 바이어 발굴   →  Tavily AI 실시간 검색 + 딥다이브 인텔리전스
4단계        🚀 제안서 생성   →  콜드메일 + 피치덱 + 레이더 차트 + PDF
5단계        🗄️ 데이터 저장  →  Supabase DB 저장 + 피드백 수집
```

---

## ✨ 주요 기능

| 단계 | 기능 | 핵심 파일 |
|------|------|-----------|
| 1·2 | AI 인터뷰 채팅 (제품명/맛/가격/브랜드스토리 수집) | `engine/interviewer.py` |
| 3 | Tavily 실시간 바이어 검색 + Pain Point 딥다이브 | `engine/market_analyzer.py` |
| 4 | 초개인화 콜드메일 생성 (영문 + 한국어) | `engine/doc_generator.py` |
| 4 | 맞춤형 피치덱 텍스트 5-slide 구조 | `engine/doc_generator.py` |
| 4 | 맛 비교 레이더 차트 (matplotlib) | `engine/doc_generator.py` |
| 4 | 통합 PDF 제안서 자동 생성 (ReportLab) | `engine/doc_generator.py` |
| 5 | Supabase DB 자동 저장 + 피드백 수집 | `database.py` |
| + | 라벨 번역 (5개 언어) | `engine/label_translator.py` |
| + | 시장 분석 + 규정 체크 | `engine/market_analyzer.py` |
| + | 수출 서류 초안 (CO, COA, PDS 등) | `engine/doc_generator.py` |

---

## 📁 프로젝트 구조

```
opener/
├── app.py                        # 메인 진입점 + 전역 DB 저장 훅 + 피드백 위젯
├── database.py                   # Supabase CRUD 레이어 (오프라인 graceful fallback)
├── Dockerfile                    # 2-stage 프로덕션 빌드
├── docker-compose.yml
├── requirements.txt
├── .env.example                  # 환경변수 체크리스트
│
├── engine/
│   ├── llm_client.py             # OpenAI / Anthropic 멀티 프로바이더
│   ├── interviewer.py            # 멀티턴 인터뷰 + JSON 추출
│   ├── market_analyzer.py        # Tavily 검색 + 바이어 딥다이브
│   ├── label_translator.py       # 라벨 분석·번역
│   └── doc_generator.py          # 콜드메일·피치덱·레이더·PDF
│
├── pages/
│   ├── home.py                   # 4단계 워크플로우 홈
│   ├── interview.py              # 채팅 인터뷰 UI
│   ├── buyer_hunter.py           # 바이어 발굴 + 딥다이브 카드
│   ├── proposal_generator.py     # 제안서 생성 + 미리보기
│   ├── label_translator.py
│   ├── market_analysis.py
│   ├── export_docs.py
│   └── settings.py               # AI/DB/통계/앱정보 탭
│
└── utils/
    ├── navigation.py             # 사이드바 + 워크플로우 배지
    ├── prompts.py                # LLM 프롬프트 9개
    ├── styles.py                 # 전통주 테마 CSS
    └── feedback_widget.py        # 👍/👎 전역 피드백 위젯
```

---

## ⚡ 빠른 시작

### 로컬 실행

```bash
# 1. 클론
git clone https://github.com/your-org/opener.git && cd opener

# 2. 가상환경
python -m venv venv && source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 열어서 API 키 4개 입력 (아래 참고)

# 5. 실행
streamlit run app.py
# → http://localhost:8501
```

### Docker 실행

```bash
docker build -t opener .
docker run -p 8501:8501 --env-file .env opener
```

### docker-compose

```bash
docker-compose up -d
```

---

## 🔑 환경변수 체크리스트

| 변수 | 필수 | 발급처 | 설명 |
|------|------|--------|------|
| `OPENAI_API_KEY` | ✅ 필수* | platform.openai.com | GPT-4o |
| `ANTHROPIC_API_KEY` | ✅ 필수* | console.anthropic.com | Claude |
| `TAVILY_API_KEY` | 🟡 권장 | app.tavily.com | 바이어 검색 (월 1,000 무료) |
| `SUPABASE_URL` | 🟡 권장 | supabase.com | DB URL |
| `SUPABASE_ANON_KEY` | 🟡 권장 | supabase.com | DB 공개 키 |
| `DEFAULT_LLM_PROVIDER` | - | - | `openai` 또는 `anthropic` |
| `DEFAULT_MODEL` | - | - | `gpt-4o` 기본값 |

> *OpenAI 또는 Anthropic 중 하나만 있어도 실행 가능

---

## 🗄️ Supabase 테이블 설정

설정 → 데이터베이스 탭에서 SQL 자동 생성 버튼 제공.  
또는 아래 4개 테이블을 Supabase SQL Editor에서 직접 생성:

- `products` — 제품 인터뷰 데이터
- `buyer_analyses` — 바이어 딥다이브 결과
- `proposals` — 콜드메일 + 피치덱 텍스트
- `feedback` — 👍/👎 사용자 피드백

---

## 🌐 배포 가이드

| 플랫폼 | 명령 | 특징 |
|--------|------|------|
| **Railway** | `railway init && railway up` | Git 연동, 가장 간단 |
| **Fly.io** | `fly launch && fly deploy` | 글로벌 엣지, 무료 티어 |
| **Google Cloud Run** | `gcloud run deploy` | 서버리스, 트래픽 기반 과금 |
| **Render** | GitHub 연동 후 자동 배포 | 무료 티어 (슬립 있음) |

> 모든 플랫폼에서 환경변수를 대시보드 또는 CLI로 설정하세요.

---

## 🛣️ 로드맵

- [x] 1단계: 프로젝트 구조 설계
- [x] 2단계: AI 인터뷰 챗봇
- [x] 3단계: Tavily 바이어 발굴 + 딥다이브
- [x] 4단계: 제안서 PDF 자동 생성
- [x] 5단계: Supabase DB + 피드백 + Docker
- [ ] OCR 라벨 이미지 분석 (pytesseract)
- [ ] 다국어 UI (영어/일어 전환)
- [ ] 이메일 자동 발송 연동 (SendGrid)
- [ ] 바이어 CRM 대시보드
- [ ] Stripe 결제 연동 (SaaS 과금)

---

## 📄 라이선스

MIT License © 2025 Opener Team

# 오프너(Opener) — 의존 라이브러리  v0.5.0

# ── 핵심 프레임워크 ──
streamlit==1.35.0
python-dotenv==1.0.1

# ── AI / LLM ──
openai==1.30.0
anthropic==0.28.0
langchain==0.2.0
langchain-openai==0.1.8
langchain-anthropic==0.1.15

# ── 바이어 발굴 ──
tavily-python==0.3.9

# ── 데이터베이스 ──
supabase==2.4.3             # Supabase Python SDK (5단계)

# ── 차트 / 시각화 ──
matplotlib==3.9.0
numpy==1.26.4
plotly==5.22.0
altair==5.3.0

# ── PDF 생성 ──
reportlab==4.2.0
fpdf2==2.7.9

# ── 데이터 처리 ──
pandas==2.2.2
pydantic==2.7.1

# ── 이미지 처리 ──
Pillow==10.3.0
pytesseract==0.3.10

# ── 번역 ──
deep-translator==1.11.4

# ── HTTP ──
requests==2.32.3
httpx==0.27.0

# ── 유틸리티 ──
python-slugify==8.0.4

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

