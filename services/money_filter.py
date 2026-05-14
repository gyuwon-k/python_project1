MONEY_KEYWORDS = [
    "지원금",
    "현금",
    "수당",
    "급여",
    "장려금",
    "바우처",
    "포인트",
    "지역화폐",
    "상품권",
    "이용권",
    "응시료",
    "교육비",
    "훈련비",
    "교통비",
    "월세",
    "주거비",
    "등록금",
    "장학금",
    "이자",
    "대출",
    "융자",
    "환급",
    "감면",
    "면제",
]

EXCLUDE_KEYWORDS = [
    "상담",
    "멘토링",
    "공간",
    "시설",
    "행사",
    "공모전",
    "채용공고",
    "뉴스",
]


def filter_money_supports(benefits):
    filtered = []
    for benefit in benefits:
        if is_money_support(benefit):
            filtered.append(benefit)
    return filtered


def is_money_support(benefit):
    text = _search_text(benefit)
    has_money_keyword = any(keyword in text for keyword in MONEY_KEYWORDS)
    has_excluded_only = any(keyword in text for keyword in EXCLUDE_KEYWORDS)
    return has_money_keyword and not (has_excluded_only and not has_money_keyword)


def money_keyword_reason(benefit):
    text = _search_text(benefit)
    matched = [keyword for keyword in MONEY_KEYWORDS if keyword in text]
    if not matched:
        return ""
    return f"금전지원 키워드 포함: {', '.join(matched[:3])}"


def _search_text(benefit):
    return " ".join(
        [
            str(benefit.get("title", "")),
            str(benefit.get("category", "")),
            str(benefit.get("money_type", "")),
            str(benefit.get("target", "")),
            str(benefit.get("summary", "")),
        ]
    )
