from services.money_filter import money_keyword_reason


def rank_benefits(benefits, user_profile):
    ranked = []
    for benefit in benefits:
        scored = dict(benefit)
        score, reasons = _score_benefit(scored, user_profile)
        if score <= 0:
            continue
        scored["score"] = score
        scored["matched_reason"] = ", ".join(reasons) or "입력 조건과 일부 관련이 있습니다."
        ranked.append(scored)

    return sorted(ranked, key=lambda item: item.get("score", 0), reverse=True)


def _score_benefit(benefit, user_profile):
    score = 0
    reasons = []
    age = _to_int(user_profile.get("age"))
    age_min = _to_int(benefit.get("age_min"))
    age_max = _to_int(benefit.get("age_max"))

    if age is not None:
        if age_min is not None and age < age_min:
            return 0, []
        if age_max is not None and age > age_max:
            return 0, []
        if age_min is not None or age_max is not None:
            score += 30
            reasons.append("나이 조건 일치")

    province = _normalize(user_profile.get("province"))
    district = _normalize(user_profile.get("district"))
    benefit_region = _normalize(benefit.get("region"))
    benefit_province = _normalize(benefit.get("province"))
    benefit_district = _normalize(benefit.get("district"))

    if district and (district in benefit_region or district in benefit_district):
        score += 40
        reasons.append("시군구 조건 일치")
    elif province and (province in benefit_region or province in benefit_province):
        score += 25
        reasons.append("시도 조건 일치")
    elif "전국" in benefit_region or benefit_region == "":
        score += 12
        reasons.append("전국 신청 가능")

    interest = _normalize(user_profile.get("interest"))
    searchable = _normalize(
        " ".join(
            [
                str(benefit.get("title", "")),
                str(benefit.get("category", "")),
                str(benefit.get("summary", "")),
            ]
        )
    )
    if interest and interest in searchable:
        score += 22
        reasons.append("관심 분야 일치")

    status = _normalize(user_profile.get("status"))
    target_text = _normalize(
        " ".join([str(benefit.get("target", "")), str(benefit.get("summary", ""))])
    )
    if status and status in target_text:
        score += 16
        reasons.append("현재 상황과 관련")

    money_reason = money_keyword_reason(benefit)
    if money_reason:
        score += 18
        reasons.append(money_reason)

    if benefit.get("source_type") == "공공기관":
        score += 10
        reasons.append("공공기관 정책")

    return score, reasons


def _normalize(value):
    return str(value or "").replace(" ", "").lower()


def _to_int(value):
    try:
        if value in (None, ""):
            return None
        return int(value)
    except ValueError:
        return None
