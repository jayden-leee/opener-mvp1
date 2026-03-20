"""
pages/proposal_generator.py

🚀 4단계: 초개인화 제안서 자동 생성 UI
- 바이어 선택 → 콜드메일 + 피치덱 + 레이더 차트 + PDF 통합 생성
"""

from __future__ import annotations

import base64
import json
import time

import streamlit as st

from eng_doc_generator import (
    generate_cold_email,
    generate_pitch_deck_text,
    generate_flavor_radar_chart,
    generate_proposal_pdf,
)


# ─────────────────────────────────────────────
# 세션 초기화
# ─────────────────────────────────────────────

def _init():
    defaults = {
        "proposal_target_buyer": None,   # 선택된 바이어 딥다이브 결과
        "proposal_cold_email":   None,
        "proposal_pitch_deck":   None,
        "proposal_radar_png":    None,
        "proposal_pdf_bytes":    None,
        "proposal_generating":   False,
        "proposal_step":         0,      # 0=대기 1=콜드메일 2=피치덱 3=차트 4=PDF 5=완료
        "sender_info":           {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
# 진행 단계 표시
# ─────────────────────────────────────────────

STEPS = ["콜드메일", "피치덱", "레이더 차트", "PDF 조립"]

def _render_progress(step: int):
    cols = st.columns(len(STEPS))
    for i, (col, label) in enumerate(zip(cols, STEPS)):
        with col:
            if i < step:
                st.markdown(f"""
                <div style="text-align:center; background:#e6f4ea; border-radius:8px;
                     padding:6px; font-size:0.82rem; color:#1e7e34; font-weight:500;">
                    ✅ {label}
                </div>""", unsafe_allow_html=True)
            elif i == step:
                st.markdown(f"""
                <div style="text-align:center; background:#fff3cd; border-radius:8px;
                     padding:6px; font-size:0.82rem; color:#856404; font-weight:600;">
                    ⏳ {label}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align:center; background:#f5f5f5; border-radius:8px;
                     padding:6px; font-size:0.82rem; color:#aaa;">
                    ○ {label}
                </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 미리보기 렌더링
# ─────────────────────────────────────────────

def _render_cold_email_preview(email: dict):
    st.markdown("##### 📧 초개인화 콜드메일")

    st.markdown(f"""
    <div style="background:#f0f4ff; border-left:4px solid #4A4A8A;
         padding:10px 14px; border-radius:0 8px 8px 0; margin-bottom:8px;">
        <div style="font-size:0.75rem; color:#666; margin-bottom:2px;">SUBJECT</div>
        <div style="font-weight:600; color:#2C1810;">{email.get('subject','—')}</div>
    </div>
    """, unsafe_allow_html=True)

    opener = email.get("opener_line", "")
    if opener:
        st.markdown(f"""
        <div style="background:#fff3cd; border-left:4px solid #C9973A;
             padding:8px 14px; border-radius:0 8px 8px 0; margin-bottom:8px;
             font-size:0.88rem; font-style:italic; color:#5c4000;">
            "{opener}"
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📝 영문 본문 전체 보기"):
        st.text_area("English Body", value=email.get("body_en",""), height=220,
                     key="preview_email_en", label_visibility="collapsed")

    with st.expander("🇰🇷 한국어 참고본"):
        st.text_area("Korean Body", value=email.get("body_ko",""), height=200,
                     key="preview_email_ko", label_visibility="collapsed")

    alts = email.get("subject_alternatives", [])
    if alts:
        st.markdown("**대안 제목:**")
        for a in alts:
            st.markdown(f"- {a}")


def _render_pitch_deck_preview(deck: dict):
    st.markdown("##### 🎯 피치덱 슬라이드 스크립트")

    hook = deck.get("hook", "")
    if hook:
        st.markdown(f"""
        <div style="background:#fdf8f2; border:1px solid #C9973A; border-radius:8px;
             padding:12px 16px; margin-bottom:10px; font-size:0.9rem; color:#2C1810;
             line-height:1.6;">
            {hook}
        </div>
        """, unsafe_allow_html=True)

    slides = deck.get("slides", [])
    for i, slide in enumerate(slides, 1):
        with st.expander(f"Slide {i}: {slide.get('title','')}", expanded=(i <= 2)):
            for b in slide.get("bullets", []):
                st.markdown(f"• {b}")
            note = slide.get("speaker_note", "")
            if note:
                st.markdown(f"*💬 발표자 노트: {note}*")

    cta = deck.get("closing_cta", "")
    if cta:
        st.markdown(f"""
        <div style="background:#8B3A3A; color:white; border-radius:8px;
             padding:12px 16px; margin-top:8px; font-weight:600; font-size:0.92rem;">
            CTA: {cta}
        </div>
        """, unsafe_allow_html=True)


def _render_radar_preview(png_bytes: bytes, product_name: str):
    st.markdown("##### 📊 맛 비교 레이더 차트")
    st.image(png_bytes, caption=f"{product_name} vs. 경쟁 제품", use_column_width=False, width=380)

    # 이미지 다운로드
    st.download_button(
        "📥 차트 PNG 저장",
        data=png_bytes,
        file_name=f"{product_name}_flavor_radar.png",
        mime="image/png",
        key="dl_radar",
    )


# ─────────────────────────────────────────────
# 발신자 정보 폼
# ─────────────────────────────────────────────

def _render_sender_form() -> dict:
    st.markdown("#### 📋 발신자 / 회사 정보")
    st.caption("PDF 제안서 및 콜드메일에 표시됩니다.")

    saved = st.session_state.get("sender_info", {})

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("회사명", value=saved.get("company",""), placeholder="(주)한국양조")
        name    = st.text_input("담당자명", value=saved.get("name",""),    placeholder="김철수")
        title   = st.text_input("직함",   value=saved.get("title",""),   placeholder="수출팀장")
    with col2:
        email   = st.text_input("이메일", value=saved.get("email",""),   placeholder="export@brewery.kr")
        phone   = st.text_input("연락처", value=saved.get("phone",""),   placeholder="+82-10-XXXX-XXXX")
        website = st.text_input("웹사이트", value=saved.get("website",""), placeholder="https://brewery.kr")

    info = {"company":company,"name":name,"title":title,"email":email,"phone":phone,"website":website}
    st.session_state["sender_info"] = info
    return info


# ─────────────────────────────────────────────
# 바이어 선택 UI
# ─────────────────────────────────────────────

def _render_buyer_selector() -> tuple[dict | None, dict | None]:
    """
    hunter 세션에서 바이어 목록 + 딥다이브 결과를 읽어
    드롭다운으로 선택하게 합니다.

    Returns:
        (선택된 buyer_meta, 선택된 deep_dive_result)
    """
    buyers     = st.session_state.get("hunter_buyers", [])
    deep_dives = st.session_state.get("hunter_deep_dives", {})

    if not buyers:
        st.warning("⚠️ 먼저 **바이어 발굴** 페이지에서 바이어를 검색하고 딥다이브를 완료해주세요.")
        if st.button("🎯 바이어 발굴로 이동"):
            from util_navigation import PAGES
            st.session_state["_nav_index"] = list(PAGES.values()).index("바이어 발굴")
            st.rerun()
        return None, None

    # 딥다이브 완료된 바이어만 필터
    dive_ready = {b["company_name"]: b for b in buyers if b.get("company_name") in deep_dives}

    if not dive_ready:
        st.info("💡 바이어 발굴 페이지에서 **🔬 딥다이브 분석** 버튼을 눌러 바이어를 분석해주세요.")
        if st.button("🎯 바이어 발굴로 이동"):
            from util_navigation import PAGES
            st.session_state["_nav_index"] = list(PAGES.values()).index("바이어 발굴")
            st.rerun()
        return None, None

    options = list(dive_ready.keys())
    selected = st.selectbox(
        "제안서를 만들 바이어 선택",
        options,
        key="proposal_buyer_select",
    )

    if selected:
        buyer_meta = dive_ready[selected]
        intel      = deep_dives[selected]

        # 미니 카드
        score = buyer_meta.get("match_score", 0)
        fit   = intel.get("fit_score", 0)
        st.markdown(f"""
        <div style="background:white; border:1px solid #E8DDD0; border-radius:10px;
             padding:12px 16px; display:flex; gap:16px; align-items:center; margin-top:8px;">
            <div style="flex:1;">
                <div style="font-weight:700; color:#8B3A3A;">{selected}</div>
                <div style="font-size:0.82rem; color:#888; margin-top:2px;">
                    {buyer_meta.get('city','')}, {buyer_meta.get('country','')} &nbsp;·&nbsp;
                    {buyer_meta.get('business_type','')}
                </div>
            </div>
            <div style="text-align:center; background:#e6f4ea; border-radius:8px; padding:6px 12px;">
                <div style="font-size:1.1rem; font-weight:700; color:#1e7e34;">{fit}/10</div>
                <div style="font-size:0.72rem; color:#555;">적합도</div>
            </div>
            <div style="text-align:center; background:#fff3cd; border-radius:8px; padding:6px 12px;">
                <div style="font-size:1.1rem; font-weight:700; color:#856404;">{score}/10</div>
                <div style="font-size:0.72rem; color:#555;">매칭 점수</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        return buyer_meta, intel

    return None, None


# ─────────────────────────────────────────────
# 생성 파이프라인
# ─────────────────────────────────────────────

def _run_generation_pipeline(product_data: dict, buyer_intel: dict, sender_info: dict):
    """
    순차적으로 콜드메일 → 피치덱 → 레이더 → PDF를 생성합니다.
    각 단계마다 session_state를 업데이트하고 st.rerun()으로 진행률을 갱신합니다.
    """
    step = st.session_state.proposal_step

    if step == 0:
        _render_progress(0)
        with st.spinner("📧 초개인화 콜드메일 작성 중..."):
            email = generate_cold_email(product_data, buyer_intel, sender_info)
        st.session_state.proposal_cold_email = email
        st.session_state.proposal_step = 1
        st.rerun()

    elif step == 1:
        _render_progress(1)
        with st.spinner("🎯 맞춤형 피치덱 텍스트 작성 중..."):
            deck = generate_pitch_deck_text(product_data, buyer_intel)
        st.session_state.proposal_pitch_deck = deck
        st.session_state.proposal_step = 2
        st.rerun()

    elif step == 2:
        _render_progress(2)
        with st.spinner("📊 맛 비교 레이더 차트 생성 중..."):
            png = generate_flavor_radar_chart(product_data)
        st.session_state.proposal_radar_png = png
        st.session_state.proposal_step = 3
        st.rerun()

    elif step == 3:
        _render_progress(3)
        with st.spinner("📄 PDF 제안서 조립 중... (최종 단계)"):
            pdf = generate_proposal_pdf(
                product_data=product_data,
                buyer_intel=buyer_intel,
                cold_email=st.session_state.proposal_cold_email,
                pitch_deck=st.session_state.proposal_pitch_deck,
                radar_png=st.session_state.proposal_radar_png,
                sender_info=sender_info,
            )
        st.session_state.proposal_pdf_bytes = pdf
        st.session_state.proposal_step      = 4   # 완료
        st.session_state.proposal_generating = False
        st.rerun()


# ─────────────────────────────────────────────
# 완료 화면
# ─────────────────────────────────────────────

def _render_completed(product_data: dict, buyer_intel: dict):
    pname    = product_data.get("product_name", "—")
    buyer    = buyer_intel.get("_buyer_meta", {})
    company  = buyer.get("company_name", "바이어")

    # 성공 배너
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#e6f4ea,#f0faf0);
         border:2px solid #1e7e34; border-radius:14px; padding:1.5rem 2rem; margin-bottom:1.5rem;">
        <div style="font-size:1.4rem; font-weight:700; color:#1e7e34; margin-bottom:4px;">
            🎉 제안서 완성!
        </div>
        <div style="color:#555; font-size:0.9rem;">
            <strong>{pname}</strong> × <strong>{company}</strong>
            맞춤형 제안서가 모두 생성되었습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # PDF 다운로드 (대형 CTA)
    pdf_bytes = st.session_state.proposal_pdf_bytes
    if pdf_bytes:
        fname = f"{pname}_{company}_proposal.pdf".replace(" ", "_")
        col_dl, col_reset = st.columns([3, 1])
        with col_dl:
            st.download_button(
                label="📥  PDF 제안서 다운로드",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
        with col_reset:
            if st.button("🔄 다시 생성", use_container_width=True):
                for k in ["proposal_cold_email","proposal_pitch_deck",
                          "proposal_radar_png","proposal_pdf_bytes",
                          "proposal_step","proposal_generating","proposal_target_buyer"]:
                    st.session_state[k] = None if "bytes" in k or "email" in k or "deck" in k or "png" in k else 0
                st.session_state.proposal_generating = False
                st.rerun()

    st.markdown("---")

    # 탭으로 미리보기
    tab_email, tab_deck, tab_radar = st.tabs(["📧 콜드메일", "🎯 피치덱", "📊 레이더 차트"])

    with tab_email:
        email = st.session_state.proposal_cold_email
        if email:
            _render_cold_email_preview(email)

    with tab_deck:
        deck = st.session_state.proposal_pitch_deck
        if deck:
            _render_pitch_deck_preview(deck)

    with tab_radar:
        png = st.session_state.proposal_radar_png
        if png:
            _render_radar_preview(png, pname)

    # JSON 전체 내보내기
    all_data = {
        "product": product_data,
        "buyer": buyer,
        "cold_email": st.session_state.proposal_cold_email,
        "pitch_deck": st.session_state.proposal_pitch_deck,
    }
    with st.expander("📦 전체 데이터 JSON 내보내기"):
        st.download_button(
            "📥 JSON 저장",
            data=json.dumps(all_data, ensure_ascii=False, indent=2),
            file_name=f"{pname}_{company}_proposal_data.json",
            mime="application/json",
            key="dl_json_all",
        )


# ─────────────────────────────────────────────
# 메인 렌더
# ─────────────────────────────────────────────

def render():
    _init()

    st.markdown(
        '<div class="page-header"><h1>🚀 제안서 자동 생성</h1></div>',
        unsafe_allow_html=True,
    )
    st.caption("바이어 딥다이브 인텔리전스 + 제품 정보 → 초개인화 콜드메일 · 피치덱 · 레이더 차트 · PDF 통합 제안서")

    # ── 제품 정보 확인 ─────────────────────────
    product_data = st.session_state.get("product_data", {})
    if not product_data:
        st.warning("⚠️ 제품 인터뷰를 먼저 완료해주세요.")
        if st.button("💬 제품 인터뷰로 이동"):
            from util_navigation import PAGES
            st.session_state["_nav_index"] = list(PAGES.values()).index("제품 인터뷰")
            st.rerun()
        product_data = {
            "product_name": "(데모) 화요 41", "alcohol_type": "증류식 소주",
            "flavor_profile": "깔끔하고 고급스러운 단맛, 긴 여운",
            "brand_story": "경기도 여주 오천년 역사 쌀로 빚은 프리미엄 소주.",
            "price_range": "15,000원", "alcohol_pct": "41%", "volume": "375ml",
        }
        st.info("데모 데이터로 계속 진행합니다.")

    # ── 완료 화면 (이미 생성된 경우) ─────────────
    if st.session_state.proposal_step == 4 and st.session_state.proposal_pdf_bytes:
        buyer_intel = st.session_state.get("proposal_target_buyer") or {}
        if not buyer_intel:
            buyer_intel = {"_buyer_meta": {"company_name": "바이어"}}
        _render_completed(product_data, buyer_intel)
        return

    # ── 생성 중 ────────────────────────────────
    if st.session_state.proposal_generating:
        st.markdown("### ⚙️ 제안서 생성 중...")
        buyer_intel = st.session_state.proposal_target_buyer or {}
        sender_info = st.session_state.sender_info or {}
        _run_generation_pipeline(product_data, buyer_intel, sender_info)
        return

    # ── 설정 화면 ──────────────────────────────
    st.markdown("---")

    # 좌: 바이어 선택 + 발신자 정보 / 우: 데모 미리보기 안내
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.subheader("① 바이어 선택")
        buyer_meta, buyer_intel = _render_buyer_selector()

        st.markdown("---")
        sender_info = _render_sender_form()

        st.markdown("---")

        # 생성 버튼
        can_generate = bool(buyer_intel)
        if not can_generate:
            st.info("바이어 딥다이브 분석이 완료되어야 제안서를 생성할 수 있습니다.")

        if st.button(
            "🚀 제안서 생성하기",
            use_container_width=True,
            type="primary",
            disabled=not can_generate,
        ):
            st.session_state.proposal_target_buyer = buyer_intel
            st.session_state.proposal_step         = 0
            st.session_state.proposal_generating   = True
            st.rerun()

    with col_right:
        st.subheader("② 생성될 내용")
        st.markdown("""
        <div style="background:#fdf8f2; border-radius:12px; padding:1.2rem; border:1px solid #E8DDD0;">

        <div style="margin-bottom:10px;">
            <div style="font-weight:600; color:#8B3A3A; margin-bottom:4px;">📧 초개인화 콜드메일</div>
            <div style="font-size:0.85rem; color:#555; line-height:1.5;">
            바이어 Pain Point를 첫 문장에서 저격하는<br>
            영문 이메일 + 한국어 참고본 + 대안 제목 3개
            </div>
        </div>

        <div style="margin-bottom:10px;">
            <div style="font-weight:600; color:#8B3A3A; margin-bottom:4px;">🎯 맞춤형 피치덱</div>
            <div style="font-size:0.85rem; color:#555; line-height:1.5;">
            Problem → Solution → Product → Market → Partnership<br>
            5개 슬라이드 텍스트 + 발표자 노트
            </div>
        </div>

        <div style="margin-bottom:10px;">
            <div style="font-weight:600; color:#8B3A3A; margin-bottom:4px;">📊 맛 비교 레이더 차트</div>
            <div style="font-size:0.85rem; color:#555; line-height:1.5;">
            우리 제품 vs. 경쟁 제품 6축 맛 프로파일<br>
            matplotlib 고품질 PNG (PDF에 자동 삽입)
            </div>
        </div>

        <div>
            <div style="font-weight:600; color:#8B3A3A; margin-bottom:4px;">📄 통합 PDF 제안서</div>
            <div style="font-size:0.85rem; color:#555; line-height:1.5;">
            5개 섹션 완성본 PDF<br>
            다운로드 즉시 바이어에게 전송 가능
            </div>
        </div>

        </div>
        """, unsafe_allow_html=True)

        # 소요 시간 안내
        st.markdown("""
        <div style="background:#fff3cd; border-radius:8px; padding:10px 14px;
             margin-top:10px; font-size:0.82rem; color:#856404;">
            ⏱️ 예상 소요 시간: <strong>1~2분</strong><br>
            (LLM 호출 3회 + 차트 생성 + PDF 조립)
        </div>
        """, unsafe_allow_html=True)
