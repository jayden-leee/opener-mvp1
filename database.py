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
