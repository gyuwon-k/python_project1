def get_card_benefits(user_profile):
    """카드사/금융사 혜택 샘플 데이터입니다.

    실제 카드사 제휴 데이터나 크롤링 결과를 붙일 때도 같은 dict 구조를 유지하면
    서비스 레이어에서 자동으로 합쳐집니다.
    """
    return [
        {
            "title": "청년 교통비 캐시백 카드",
            "provider": "카드사 샘플",
            "source_type": "카드사",
            "category": "생활지원",
            "province": "전국",
            "district": "",
            "region": "전국",
            "money_type": "환급",
            "age_min": 19,
            "age_max": 34,
            "target": "대학생 및 사회초년생",
            "summary": "대중교통 이용금액 일부를 캐시백 형태로 환급해주는 샘플 카드 혜택입니다.",
            "url": "#",
            "matched_reason": "",
            "score": 0,
        },
        {
            "title": "자격증 응시료 할인 카드 혜택",
            "provider": "카드사 샘플",
            "source_type": "카드사",
            "category": "취업",
            "province": "전국",
            "district": "",
            "region": "전국",
            "money_type": "감면",
            "age_min": 18,
            "age_max": 39,
            "target": "구직중 청년",
            "summary": "어학시험, 한국사, 국가자격시험 결제 시 응시료 일부를 할인해주는 샘플 카드 혜택입니다.",
            "url": "#",
            "matched_reason": "",
            "score": 0,
        },
    ]
