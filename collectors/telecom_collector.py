def get_telecom_benefits(user_profile):
    """통신사/구독형 통신 혜택 샘플 데이터입니다.

    실제 크롤링 또는 API 연결 전에도 발표 화면에서 데이터 소스가 비어 보이지
    않도록, 공통 혜택 dict 형식에 맞춘 샘플 데이터를 반환합니다.
    """
    return [
        {
            "title": "청년 통신요금 할인 바우처",
            "provider": "통신사 샘플",
            "source_type": "통신사",
            "category": "생활지원",
            "province": "전국",
            "district": "",
            "region": "전국",
            "money_type": "감면",
            "age_min": 19,
            "age_max": 34,
            "target": "청년 및 대학생",
            "summary": "청년층의 통신비 부담을 줄이기 위해 월 통신요금 일부를 할인해주는 샘플 혜택입니다.",
            "url": "#",
            "matched_reason": "",
            "score": 0,
        },
        {
            "title": "취업준비생 데이터 추가 제공",
            "provider": "통신사 샘플",
            "source_type": "통신사",
            "category": "취업",
            "province": user_profile.get("province", "전국") or "전국",
            "district": "",
            "region": user_profile.get("province", "전국") or "전국",
            "money_type": "이용권",
            "age_min": 18,
            "age_max": 39,
            "target": "구직중 청년",
            "summary": "온라인 강의와 채용 사이트 이용이 많은 구직 청년에게 데이터 이용권을 제공하는 샘플 혜택입니다.",
            "url": "#",
            "matched_reason": "",
            "score": 0,
        },
    ]
