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
}


def get_dashboard_data(args):
    user_profile = build_user_profile(args)

    public_benefits, public_status = get_public_policy_benefits(user_profile)
    telecom_benefits = get_telecom_benefits(user_profile)
    card_benefits = get_card_benefits(user_profile)

    all_benefits = public_benefits + telecom_benefits + card_benefits
    money_benefits = filter_money_supports(all_benefits)
    ranked_benefits = rank_benefits(money_benefits, user_profile)

    source_statuses = [
        public_status,
        _team_status("통신사 혜택", telecom_benefits),
        _team_status("카드사 혜택", card_benefits),
    ]

    return {
        "user_profile": user_profile,
        "benefits": ranked_benefits,
        "source_statuses": source_statuses,
        "stats": build_stats(ranked_benefits, source_statuses, len(all_benefits)),
        "download_query": urlencode(user_profile),
    }


def build_user_profile(args):
    return {
        "age": str(args.get("age") or DEFAULT_PROFILE["age"]).strip(),
        "province": str(args.get("province") or DEFAULT_PROFILE["province"]).strip(),
        "district": str(args.get("district") or DEFAULT_PROFILE["district"]).strip(),
        "interest": str(args.get("interest") or DEFAULT_PROFILE["interest"]).strip(),
        "status": str(args.get("status") or DEFAULT_PROFILE["status"]).strip(),
    }


def build_stats(benefits, source_statuses, collected_count):
    source_counts = Counter(benefit.get("source_type", "기타") for benefit in benefits)
    category_counts = Counter(benefit.get("category", "기타") for benefit in benefits)
    money_type_counts = Counter(benefit.get("money_type", "금전지원") for benefit in benefits)

    return {
        "total": len(benefits),
        "collected_total": collected_count,
        "sources": dict(source_counts),
        "categories": dict(category_counts),
        "money_types": dict(money_type_counts),
        "active_sources": sum(
            1
            for status in source_statuses
            if status.get("ok") or status.get("used_sample")
        ),
        "sample_mode": any(status.get("used_sample") for status in source_statuses),
    }


def _team_status(name, benefits):
    if benefits:
        return {
            "name": name,
            "ok": True,
            "used_sample": False,
            "message": f"{name} 데이터 {len(benefits)}건이 연결되었습니다.",
        }
    return {
        "name": name,
        "ok": False,
        "used_sample": False,
        "message": "팀원 데이터 연결 예정입니다.",
    }
