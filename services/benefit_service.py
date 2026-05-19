from collections import Counter
from urllib.parse import urlencode

from collectors.card_collector import get_card_benefits
from collectors.public_policy_collector import get_public_policy_benefits
from collectors.telecom_collector import get_telecom_benefits
from services.matcher import rank_benefits
from services.money_filter import filter_money_supports


DEFAULT_PROFILE = {
    "age": "24",
    "province": "대구",
    "district": "달서구",
    "interest": "취업",
    "status": "구직중",
    "source": "전체",
    "category": "전체",
    "keyword": "",
    "sort": "추천순",
}

SOURCE_OPTIONS = ["전체", "공공기관", "통신사", "카드사"]
CATEGORY_OPTIONS = ["전체", "취업", "주거", "금융", "교육", "문화", "생활지원", "통신", "금전지원"]
SORT_OPTIONS = ["추천순", "최신순", "이름순"]


def get_dashboard_data(args):
    user_profile = build_user_profile(args)

    public_benefits, public_status = get_public_policy_benefits(user_profile)
    telecom_benefits = get_telecom_benefits(user_profile)
    card_benefits = get_card_benefits(user_profile)

    collected_benefits = public_benefits + telecom_benefits + card_benefits
    deduped_benefits = _dedupe_benefits(collected_benefits)
    money_benefits = filter_money_supports(deduped_benefits)
    ranked_benefits = rank_benefits(money_benefits, user_profile)
    visible_benefits = apply_user_filters(ranked_benefits, user_profile)

    source_statuses = [
        public_status,
        _team_status("통신사 혜택", telecom_benefits),
        _team_status("카드사 혜택", card_benefits),
    ]

    return {
        "user_profile": user_profile,
        "benefits": visible_benefits,
        "source_statuses": source_statuses,
        "stats": build_stats(visible_benefits, source_statuses, len(collected_benefits), len(deduped_benefits)),
        "download_query": urlencode(user_profile),
        "source_options": SOURCE_OPTIONS,
        "category_options": CATEGORY_OPTIONS,
        "sort_options": SORT_OPTIONS,
    }


def build_user_profile(args):
    age = str(args.get("age") or DEFAULT_PROFILE["age"]).strip()
    if not age.isdigit():
        age = DEFAULT_PROFILE["age"]

    return {
        "age": age,
        "province": str(args.get("province") or DEFAULT_PROFILE["province"]).strip(),
        "district": str(args.get("district") or DEFAULT_PROFILE["district"]).strip(),
        "interest": str(args.get("interest") or DEFAULT_PROFILE["interest"]).strip(),
        "status": str(args.get("status") or DEFAULT_PROFILE["status"]).strip(),
        "source": _allowed(args.get("source"), SOURCE_OPTIONS, DEFAULT_PROFILE["source"]),
        "category": _allowed(args.get("category"), CATEGORY_OPTIONS, DEFAULT_PROFILE["category"]),
        "keyword": str(args.get("keyword") or DEFAULT_PROFILE["keyword"]).strip(),
        "sort": _allowed(args.get("sort"), SORT_OPTIONS, DEFAULT_PROFILE["sort"]),
    }


def apply_user_filters(benefits, user_profile):
    filtered = list(benefits)

    source = user_profile.get("source", "전체")
    if source != "전체":
        filtered = [benefit for benefit in filtered if benefit.get("source_type") == source]

    category = user_profile.get("category", "전체")
    if category != "전체":
        filtered = [benefit for benefit in filtered if benefit.get("category") == category]

    keyword = _normalize(user_profile.get("keyword"))
    if keyword:
        filtered = [benefit for benefit in filtered if keyword in _benefit_search_text(benefit)]

    sort = user_profile.get("sort", "추천순")
    if sort == "이름순":
        filtered.sort(key=lambda item: item.get("title", ""))
    elif sort == "최신순":
        # 현재 수집 데이터에는 공통 날짜 필드가 없으므로, 실제 API 연결 전까지는
        # 원본 수집 순서에 가까운 안정 정렬을 유지합니다.
        filtered.sort(key=lambda item: item.get("score", 0), reverse=True)
    else:
        filtered.sort(key=lambda item: item.get("score", 0), reverse=True)

    return filtered


def build_stats(benefits, source_statuses, collected_count, deduped_count):
    source_counts = Counter(benefit.get("source_type", "기타") for benefit in benefits)
    category_counts = Counter(benefit.get("category", "기타") for benefit in benefits)
    money_type_counts = Counter(benefit.get("money_type", "금전지원") for benefit in benefits)

    return {
        "total": len(benefits),
        "collected_total": collected_count,
        "deduped_total": deduped_count,
        "sources": dict(source_counts),
        "categories": dict(category_counts),
        "money_types": dict(money_type_counts),
        "active_sources": sum(1 for status in source_statuses if status.get("ok") or status.get("used_sample")),
        "sample_mode": any(status.get("used_sample") for status in source_statuses),
    }


def _team_status(name, benefits):
    if benefits:
        return {
            "name": name,
            "ok": True,
            "used_sample": False,
            "message": f"{name} 샘플 데이터 {len(benefits)}건이 연결되었습니다. 실제 API 또는 크롤링 결과로 교체할 수 있습니다.",
        }
    return {
        "name": name,
        "ok": False,
        "used_sample": False,
        "message": "팀원 데이터 연결 예정입니다.",
    }


def _dedupe_benefits(benefits):
    seen = set()
    deduped = []
    for benefit in benefits:
        key = (
            _normalize(benefit.get("title")),
            _normalize(benefit.get("provider")),
            _normalize(benefit.get("region")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(benefit)
    return deduped


def _allowed(value, options, default):
    value = str(value or "").strip()
    return value if value in options else default


def _benefit_search_text(benefit):
    return _normalize(
        " ".join(
            [
                str(benefit.get("title", "")),
                str(benefit.get("provider", "")),
                str(benefit.get("source_type", "")),
                str(benefit.get("category", "")),
                str(benefit.get("region", "")),
                str(benefit.get("target", "")),
                str(benefit.get("summary", "")),
                str(benefit.get("money_type", "")),
            ]
        )
    )


def _normalize(value):
    return str(value or "").replace(" ", "").lower()
