"""
utils/prompts.py
오프너에서 사용하는 모든 LLM 프롬프트 템플릿 관리
"""

# ──────────────────────────────────────────
# 라벨 분석
# ──────────────────────────────────────────
LABEL_ANALYSIS_PROMPT = """
다음은 한국 전통주 제품 라벨의 원문 텍스트입니다.
이 텍스트에서 주요 정보를 추출하여 아래 JSON 형식으로 응답하세요.

[라벨 텍스트]
{label_text}

[응답 형식]
{{
  "product_name": "제품명",
  "type": "주종 (예: 막걸리, 청주, 소주, 약주, 증류식 소주)",
  "alcohol_content": "알코올 도수 (예: 13%)",
  "volume": "용량 (예: 750ml)",
  "ingredients": ["원재료1", "원재료2"],
  "manufacturer": "제조사명",
  "manufacturer_address": "제조사 주소",
  "best_before": "유통기한 정보",
  "storage": "보관 방법",
  "description": "제품 설명/특징 (2~3문장)"
}}
"""

# ──────────────────────────────────────────
# 라벨 번역
# ──────────────────────────────────────────
LABEL_TRANSLATE_PROMPT = """
다음은 한국 전통주 라벨 정보입니다.
이 정보를 {target_market} 시장에 맞게 {target_language} 언어로 번역하세요.
현지 주류 규정과 소비자 감성에 맞는 표현을 사용하세요.

[원본 라벨 데이터]
{label_data}

[응답 형식]
{{
  "product_name": "번역된 제품명",
  "type": "번역된 주종",
  "alcohol_content": "현지 표기 방식의 도수",
  "volume": "용량",
  "ingredients": ["번역된 원재료1", "번역된 원재료2"],
  "manufacturer": "제조사명 로마자/현지어 표기",
  "description": "번역된 제품 설명",
  "marketing_tagline": "현지 소비자를 위한 마케팅 문구 (1문장)",
  "compliance_notes": "현지 규정상 추가/수정 필요 사항"
}}
"""

# ──────────────────────────────────────────
# 시장 분석
# ──────────────────────────────────────────
MARKET_ANALYSIS_PROMPT = """
다음 한국 전통주 제품의 {market} 시장 진출 가능성을 분석해주세요.

[제품 정보]
{product_info}

[시장 기본 데이터]
{market_data}

[응답 형식]
{{
  "market_summary": "시장 현황 요약 (3~4문장)",
  "opportunity_score": 7,
  "opportunity_reason": "기회 요인 설명",
  "key_challenges": [
    "도전 요인 1",
    "도전 요인 2",
    "도전 요인 3"
  ],
  "recommendations": [
    "진출 전략 권고 1",
    "진출 전략 권고 2",
    "진출 전략 권고 3"
  ],
  "target_consumer": "주요 타겟 소비자층",
  "competitor_landscape": "경쟁 제품 현황",
  "estimated_price_range": "현지 예상 소비자가 범위"
}}
"""

# ──────────────────────────────────────────
# 규정 체크
# ──────────────────────────────────────────
REGULATION_CHECK_PROMPT = """
다음 전통주 제품이 {market_code} 시장 수출 규정을 충족하는지 검토해주세요.

[제품 정보]
{product_info}

각 규정 항목에 대해 "통과", "주의", "실패" 중 하나로 판단하고
JSON 배열로 응답하세요.

[응답 형식]
[
  {{
    "item": "규정 항목명",
    "status": "통과",
    "detail": "세부 설명"
  }},
  ...
]
"""

# ──────────────────────────────────────────
# 바이어 발굴 — 검색 결과 파싱
# ──────────────────────────────────────────
BUYER_PARSE_PROMPT = """
아래는 '{country}' 지역의 프리미엄 주류 유통사/수입사를 검색한 결과입니다.
각 결과에서 실제 기업 정보를 추출하여 JSON 배열로 정리해주세요.
중복은 제거하고, 명확히 주류 관련 기업인 것만 포함하세요.

[검색 결과]
{search_results}

[제품 정보 (매칭 참고용)]
{product_info}

[응답 형식 — JSON 배열]
[
  {{
    "company_name": "회사명 (영문)",
    "country": "국가",
    "city": "도시",
    "website": "웹사이트 URL (있으면)",
    "business_type": "유통사|수입사|소매체인|레스토랑체인|기타",
    "specialty": "전문 주류 카테고리 (예: Premium Spirits, Asian Beverages)",
    "match_reason": "이 제품과 맞는 이유 (1~2문장, 한국어)",
    "match_score": 8
  }},
  ...
]

최대 8개까지만 포함하세요. match_score는 1~10 정수입니다.
"""

# ──────────────────────────────────────────
# 바이어 딥 다이브 — 인텔리전스 분석
# ──────────────────────────────────────────
BUYER_DEEP_DIVE_PROMPT = """
아래는 '{company_name}' 기업에 대해 수집된 최신 정보입니다.
한국 전통주 수출 제안을 위해 이 기업을 심층 분석해주세요.

[수집된 정보]
{scraped_content}

[우리 제품 정보]
{product_info}

[분석 요청]
다음 JSON 형식으로 응답하세요:

{{
  "company_summary": "기업 소개 (2~3문장, 한국어)",
  "pain_points": [
    "현재 고민/니즈 1 (한국어, 구체적)",
    "현재 고민/니즈 2",
    "현재 고민/니즈 3"
  ],
  "opportunities": [
    "우리 제품으로 해결할 수 있는 기회 1",
    "기회 2"
  ],
  "preferred_keywords": ["바이어가 중시하는 키워드1", "키워드2", "키워드3", "키워드4"],
  "decision_maker_hint": "의사결정자 직책 추정 (예: Chief Buying Officer, Import Manager)",
  "approach_strategy": "이 바이어에게 접근하는 최적 전략 (3~4문장, 한국어)",
  "red_flags": ["주의해야 할 점 (있다면)"],
  "fit_score": 8,
  "fit_reason": "우리 제품과의 적합도 근거 (한국어, 2문장)"
}}
"""

# ──────────────────────────────────────────
# 수출 서류 생성
# ──────────────────────────────────────────
DOC_GENERATION_PROMPT = """
다음 정보를 바탕으로 {target_market} 수출용 [{document_type}] 초안을 작성해주세요.

[제품 정보]
{product_info}

[수출자/제조사 정보]
{exporter_info}

전문적이고 국제 표준에 맞는 형식으로 Markdown을 사용하여 작성하세요.
실제 수출 업무에 바로 활용 가능한 수준으로 작성해주세요.
"""

# ──────────────────────────────────────────
# 초개인화 콜드메일
# ──────────────────────────────────────────
COLD_EMAIL_PROMPT = """
다음 정보를 바탕으로 {company_name}에 보낼 초개인화 콜드메일을 작성하세요.

[우리 제품 정보]
{product_data}

[바이어 인텔리전스]
- 회사 Pain Points: {pain_points}
- 선호 키워드: {preferred_keywords}
- 접근 전략: {approach_strategy}
- 전체 분석: {buyer_intel}

[발신자 정보]
{sender_info}

[작성 원칙]
1. 첫 문장(오프너)은 바이어의 Pain Point를 정확히 저격해야 합니다.
2. 우리 제품이 그 Pain Point를 어떻게 해결하는지 구체적으로 연결하세요.
3. 선호 키워드를 자연스럽게 포함하세요.
4. 영어 본문은 200단어 이내, 친근하지만 전문적인 톤.
5. 한국어 참고 번역도 포함하세요.
6. 강력한 CTA(Call-to-Action)로 마무리하세요.

[응답 형식 — JSON]
{{
  "subject": "이메일 제목 (영문)",
  "opener_line": "첫 번째 오프너 문장 (영문, 바이어 Pain Point 저격)",
  "body_en": "영문 이메일 전체 본문 (인사 ~ 서명 제외 CTA 포함)",
  "body_ko": "한국어 참고 본문",
  "subject_alternatives": ["대안 제목 2", "대안 제목 3"]
}}
"""

# ──────────────────────────────────────────
# 맞춤형 피치덱 텍스트
# ──────────────────────────────────────────
PITCH_DECK_PROMPT = """
다음 정보를 바탕으로 {company_name}을 위한 맞춤형 제안서 피치덱 텍스트를 작성하세요.

[제품 정보]
{product_data}

[바이어 인텔리전스]
- 적합도: {fit_score}/10
- Pain Points: {pain_points}
- 기회 요인: {opportunities}
- 전체 분석: {buyer_intel}

[시장 분석]
{market_analysis}

[슬라이드 구성 요청]
아래 5개 슬라이드 구조로 작성하세요:
1. Problem (바이어의 Pain Point)
2. Solution (우리 제품으로 해결)
3. Product Story (제품 특징 + 브랜드 스토리)
4. Market Opportunity (시장 규모 + 트렌드)
5. Partnership Proposal (파트너십 제안 + 조건)

[응답 형식 — JSON]
{{
  "headline": "커버 슬라이드 한 줄 헤드라인 (임팩트 있게, 영문)",
  "hook": "프레젠테이션 오프너 문장 (한국어, 3문장)",
  "slides": [
    {{
      "title": "슬라이드 제목 (영문)",
      "bullets": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
      "speaker_note": "발표자 노트 (한국어, 2문장)"
    }}
  ],
  "closing_cta": "최종 CTA 문장 (영문, 행동을 유도하는 강한 문장)"
}}
"""
