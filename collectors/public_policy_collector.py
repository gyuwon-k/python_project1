import csv
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = PROJECT_ROOT / "data" / "sample_public_policies.csv"

GOV24_SERVICE_LIST_URL = "https://api.odcloud.kr/api/gov24/v1/serviceList"
ONTONG_YOUTH_POLICY_URL = "https://www.youthcenter.go.kr/opi/youthPlcyList.do"
BOKJIRO_LOCAL_BASE_URL = "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations"
BOKJIRO_NATIONAL_BASE_URL = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001"


def get_public_policy_benefits(user_profile):
    env = _load_env()
    collected = []
    messages = []
    used_sample = False
    ok = False

    bokjiro_key = env.get("BOKJIRO_API_KEY") or env.get("PUBLIC_DATA_API_KEY")
    gov24_key = env.get("GOV24_SERVICE_API_KEY") or env.get("PUBLIC_DATA_API_KEY")
    youth_key = env.get("ONTONG_YOUTH_API_KEY")

    if bokjiro_key:
        try:
            collected.extend(_fetch_bokjiro_local_services(env, bokjiro_key, user_profile))
            ok = True
            messages.append("복지로 지자체 복지서비스 API를 호출했습니다.")
        except Exception as exc:
            messages.append(f"복지로 지자체 API 호출 실패: {exc}")

        try:
            collected.extend(_fetch_bokjiro_national_services(env, bokjiro_key, user_profile))
            ok = True
            messages.append("복지로 중앙부처 복지서비스 API를 호출했습니다.")
        except Exception as exc:
            messages.append(f"복지로 중앙부처 API 호출 실패: {exc}")

    if gov24_key:
        try:
            collected.extend(_fetch_gov24_services(env, gov24_key, user_profile))
            ok = True
            messages.append("대한민국 공공서비스 정보 API를 호출했습니다.")
        except Exception as exc:
            messages.append(f"공공서비스 API 호출 실패: {exc}")

    if youth_key:
        try:
            collected.extend(_fetch_youth_policies(env, youth_key, user_profile))
            ok = True
            messages.append("온통청년 API를 호출했습니다.")
        except Exception as exc:
            messages.append(f"온통청년 API 호출 실패: {exc}")

    sample_policies = _load_sample_policies()
    if not collected:
        collected = sample_policies
        used_sample = True
        messages.append("API 키가 없거나 수집 결과가 없어 샘플 데이터를 사용했습니다.")
    else:
        collected = _deduplicate_benefits(collected + sample_policies)
        messages.append("샘플 데이터도 함께 사용했습니다.")

    return collected, {
        "name": "공공기관 금전지원",
        "ok": ok,
        "used_sample": used_sample,
        "message": " ".join(messages),
    }


def _fetch_bokjiro_local_services(env, api_key, user_profile):
    base_url = env.get("BOKJIRO_LOCAL_BASE_URL", BOKJIRO_LOCAL_BASE_URL).rstrip("/")
    api_url = f"{base_url}/LcgvWelfarelist"
    page_size = int(env.get("BOKJIRO_PAGE_SIZE", "30"))
    params = {
        "serviceKey": api_key,
        "pageNo": 1,
        "numOfRows": page_size,
        "age": user_profile.get("age", ""),
        "ctpvNm": _province_full_name(user_profile.get("province", "")),
        "sggNm": user_profile.get("district", ""),
        "lifeArray": _life_cycle_code(user_profile.get("age")),
        "intrsThemaArray": _interest_theme_code(user_profile.get("interest")),
        "srchKeyCode": "003",
        "arrgOrd": "001",
    }
    raw_items = _request_xml_items(api_url, params)
    if not raw_items:
        raw_items = _request_xml_items(
            api_url,
            {
                "serviceKey": api_key,
                "pageNo": 1,
                "numOfRows": page_size,
                "ctpvNm": _province_full_name(user_profile.get("province", "")),
            },
        )
    if not raw_items:
        raw_items = _request_xml_items(
            api_url,
            {
                "serviceKey": api_key,
                "pageNo": 1,
                "numOfRows": page_size,
                "lifeArray": _life_cycle_code(user_profile.get("age")),
                "intrsThemaArray": _interest_theme_code(user_profile.get("interest")),
                "srchKeyCode": "003",
                "arrgOrd": "001",
            },
        )
    return [_normalize_bokjiro_service(item, user_profile, "지자체") for item in raw_items]


def _fetch_bokjiro_national_services(env, api_key, user_profile):
    base_url = env.get("BOKJIRO_NATIONAL_BASE_URL", BOKJIRO_NATIONAL_BASE_URL).rstrip("/")
    api_url = f"{base_url}/NationalWelfarelistV001"
    params = {
        "serviceKey": api_key,
        "callTp": "L",
        "pageNo": 1,
        "numOfRows": int(env.get("BOKJIRO_PAGE_SIZE", "30")),
        "srchKeyCode": "001",
        "age": user_profile.get("age", ""),
        "lifeArray": _life_cycle_code(user_profile.get("age")),
        "intrsThemaArray": _interest_theme_code(user_profile.get("interest")),
        "orderBy": "popular",
    }
    raw_items = _request_xml_items(api_url, params)
    return [_normalize_bokjiro_service(item, user_profile, "중앙부처") for item in raw_items]


def _request_xml_items(api_url, params):
    clean_params = {key: value for key, value in params.items() if value not in (None, "")}
    response = requests.get(api_url, params=clean_params, timeout=10)
    response.raise_for_status()
    return _extract_xml_items(response.text.strip())


def _fetch_gov24_services(env, api_key, user_profile):
    api_url = env.get("GOV24_SERVICE_LIST_API_URL", GOV24_SERVICE_LIST_URL)
    params = {
        "serviceKey": api_key,
        "page": 1,
        "perPage": int(env.get("GOV24_SERVICE_PAGE_SIZE", "100")),
        "returnType": "JSON",
    }
    response = requests.get(api_url, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()
    raw_items = _extract_json_items(payload)
    return [_normalize_gov24_service(item, user_profile) for item in raw_items]


def _fetch_youth_policies(env, api_key, user_profile):
    api_url = env.get("ONTONG_YOUTH_POLICY_API_URL", ONTONG_YOUTH_POLICY_URL)
    params = {
        "openApiVlak": api_key,
        "pageIndex": 1,
        "display": 50,
        "query": user_profile.get("interest", ""),
    }
    response = requests.get(api_url, params=params, timeout=10)
    response.raise_for_status()

    text = response.text.strip()
    if not text:
        return []

    if text.startswith("{") or text.startswith("["):
        raw_items = _extract_json_items(json.loads(text))
    else:
        raw_items = _extract_xml_items(text)

    return [_normalize_youth_policy(item, user_profile) for item in raw_items]


def _normalize_bokjiro_service(item, user_profile, provider_type):
    title = _pick(item, ["servNm", "serviceNm", "wlfareInfoNm", "서비스명", "title"])
    provider = _pick(
        item,
        ["jurMnofNm", "jurOrgNm", "ctpvNm", "sggNm", "소관기관명"],
    )
    summary = _pick(
        item,
        [
            "servDgst",
            "servDtlCn",
            "sprtCycNm",
            "서비스목적요약",
            "지원내용",
            "summary",
        ],
    )
    target = _pick(
        item,
        ["trgterIndvdlNmArray", "lifeNmArray", "sprtTrgtCn", "지원대상", "target"],
    )
    category = _pick(item, ["intrsThemaNmArray", "lifeNmArray", "서비스분야"]) or _infer_category(title, summary)
    region_text = " ".join(
        [
            _pick(item, ["ctpvNm", "시도명"]),
            _pick(item, ["sggNm", "시군구명"]),
            provider,
        ]
    ).strip()
    province, district = _extract_region(region_text, user_profile)
    url = _pick(item, ["servDtlLink", "servLink", "url", "상세조회URL"])
    age_min, age_max = _parse_age_range(" ".join([target, summary, title]))

    if provider_type == "중앙부처":
        province = "전국"
        district = ""

    return {
        "title": title or f"복지로 {provider_type} 복지서비스",
        "provider": provider or f"복지로 {provider_type}",
        "source_type": "공공기관",
        "category": category or "복지",
        "province": province,
        "district": district,
        "region": _format_region(province, district),
        "money_type": _infer_money_type(title, summary),
        "age_min": age_min,
        "age_max": age_max,
        "target": target or "복지서비스 대상자",
        "summary": summary or "복지로 API에서 수집한 복지서비스 정보입니다.",
        "url": url or "https://www.bokjiro.go.kr",
        "matched_reason": "",
        "score": 0,
    }


def _normalize_gov24_service(item, user_profile):
    title = _pick(
        item,
        ["서비스명", "서비스ID", "serviceName", "svcNm", "title", "name", "서비스명(국문)"],
    )
    provider = _pick(
        item,
        ["소관기관명", "부서명", "기관명", "provider", "orgNm", "jurMnofNm"],
    )
    summary = _pick(
        item,
        [
            "서비스목적요약",
            "서비스목적",
            "지원내용",
            "선정기준",
            "description",
            "summary",
            "svcPpo",
        ],
    )
    category = _pick(item, ["서비스분야", "분야", "category", "svcClsfNm"]) or _infer_category(title, summary)
    region_text = " ".join(
        [
            _pick(item, ["시도명", "시도", "지역", "region", "소관기관명"]),
            _pick(item, ["시군구명", "시군구", "district", "부서명"]),
        ]
    ).strip()
    province, district = _extract_region(region_text, user_profile)
    target = _pick(item, ["지원대상", "신청대상", "target", "sprtTrgtCn"]) or "일반 국민"
    url = _pick(item, ["상세조회URL", "온라인신청사이트URL", "url", "svcUrl"])
    age_min, age_max = _parse_age_range(" ".join([target, summary, title]))

    return {
        "title": title or "공공서비스",
        "provider": provider or "정부24",
        "source_type": "공공기관",
        "category": category or "금전지원",
        "province": province,
        "district": district,
        "region": _format_region(province, district),
        "money_type": _infer_money_type(title, summary),
        "age_min": age_min,
        "age_max": age_max,
        "target": target,
        "summary": summary or "정부24 공공서비스 정보 API에서 수집한 혜택입니다.",
        "url": url or "https://www.gov.kr/portal/rcvfvrSvc/main",
        "matched_reason": "",
        "score": 0,
    }


def _normalize_youth_policy(item, user_profile):
    title = _pick(item, ["plcyNm", "polyBizSjnm", "policyName", "title"])
    summary = _pick(
        item,
        ["plcyExplnCn", "polyItcnCn", "sporCn", "policyCn", "description", "summary"],
    )
    category = _pick(
        item,
        ["lclsfNm", "mclsfNm", "plcyKywdNm", "bizTycdSel", "category", "policyType"],
    )
    region_text = _pick(item, ["zipCd", "region", "sprvsnInstCdNm", "polyBizSecd"])
    province, district = _extract_region(region_text, user_profile)
    provider = _pick(
        item,
        ["sprvsnInstCdNm", "mngtMson", "operInstNm", "provider", "organName"],
    )
    target = _pick(
        item,
        ["sprtTrgtMinAge", "ageInfo", "target", "prcpCn", "empmSttsCn", "rqutPrdCn"],
    )
    url = _pick(item, ["aplyUrlAddr", "rqutUrla", "rfcSiteUrla1", "url"])
    age_text = " ".join(
        [
            _pick(item, ["sprtTrgtMinAge", "minAge"]),
            _pick(item, ["sprtTrgtMaxAge", "maxAge"]),
            _pick(item, ["ageInfo"]),
        ]
    )
    age_min, age_max = _parse_age_range(age_text)

    return {
        "title": title or "청년정책",
        "provider": provider or "온통청년",
        "source_type": "공공기관",
        "category": category or _infer_category(title, summary),
        "province": province,
        "district": district,
        "region": _format_region(province, district),
        "money_type": _infer_money_type(title, summary),
        "age_min": age_min,
        "age_max": age_max,
        "target": target or "청년",
        "summary": summary or "온통청년에서 제공하는 청년정책 정보입니다.",
        "url": url or "https://www.youthcenter.go.kr",
        "matched_reason": "",
        "score": 0,
    }


def _extract_json_items(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("data"),
        payload.get("items"),
        payload.get("item"),
        payload.get("result"),
        payload.get("response", {}).get("body", {}).get("items", {}).get("item")
        if isinstance(payload.get("response"), dict)
        else None,
        payload.get("youthPolicyList"),
        payload.get("youthPlcyList"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, dict):
            nested = _extract_json_items(candidate)
            if nested:
                return nested
    return []


def _extract_xml_items(xml_text):
    root = ET.fromstring(xml_text)
    item_nodes = []
    for tag in ("servList", "youthPolicy", "youthPlcy", "policy", "item", "row", "data"):
        item_nodes.extend(root.findall(f".//{tag}"))

    items = []
    for node in item_nodes:
        item = {}
        for child in list(node):
            item[_strip_namespace(child.tag)] = (child.text or "").strip()
        if item:
            items.append(item)
    return items


def _load_sample_policies():
    with SAMPLE_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    policies = []
    for row in rows:
        row["age_min"] = _to_int(row.get("age_min"))
        row["age_max"] = _to_int(row.get("age_max"))
        row["score"] = 0
        row["matched_reason"] = ""
        policies.append(row)
    return policies


def _deduplicate_benefits(benefits):
    deduplicated = []
    seen = set()
    for benefit in benefits:
        key = (
            benefit.get("title", "").strip(),
            benefit.get("provider", "").strip(),
            benefit.get("url", "").strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(benefit)
    return deduplicated


def _load_env():
    values = dict(os.environ)
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values


def _extract_region(text, user_profile):
    text = text or ""
    province = ""
    district = ""

    for candidate in _province_candidates():
        if candidate in text:
            province = candidate
            break

    district_match = re.search(r"([가-힣]+(?:시|군|구))", text)
    if district_match:
        district = district_match.group(1)

    return province or user_profile.get("province", "전국"), district


def _province_candidates():
    return [
        "서울",
        "부산",
        "대구",
        "인천",
        "광주",
        "대전",
        "울산",
        "세종",
        "경기",
        "강원",
        "충북",
        "충남",
        "전북",
        "전남",
        "경북",
        "경남",
        "제주",
    ]


def _province_full_name(province):
    names = {
        "서울": "서울특별시",
        "부산": "부산광역시",
        "대구": "대구광역시",
        "인천": "인천광역시",
        "광주": "광주광역시",
        "대전": "대전광역시",
        "울산": "울산광역시",
        "세종": "세종특별자치시",
        "경기": "경기도",
        "강원": "강원특별자치도",
        "충북": "충청북도",
        "충남": "충청남도",
        "전북": "전북특별자치도",
        "전남": "전라남도",
        "경북": "경상북도",
        "경남": "경상남도",
        "제주": "제주특별자치도",
    }
    return names.get(province, province)


def _life_cycle_code(age):
    age = _to_int(age)
    if age is None:
        return ""
    if age <= 6:
        return "001"
    if age <= 12:
        return "002"
    if age <= 18:
        return "003"
    if age <= 34:
        return "004"
    if age <= 64:
        return "005"
    return "006"


def _interest_theme_code(interest):
    codes = {
        "생활지원": "030",
        "주거": "040",
        "취업": "050",
        "일자리": "050",
        "문화": "060",
        "문화·여가": "060",
        "교육": "100",
        "금융": "130",
        "서민금융": "130",
    }
    return codes.get(interest, "")


def _format_region(province, district):
    if province and district:
        return f"{province} {district}"
    return province or district or "전국"


def _infer_category(title, summary):
    text = f"{title} {summary}"
    category_keywords = {
        "취업": ["취업", "구직", "자격증", "응시료", "면접", "일자리"],
        "주거": ["월세", "전세", "임대", "주거", "주택"],
        "금융": ["저축", "계좌", "대출", "이자", "자산"],
        "교육": ["교육", "훈련", "강의", "학습"],
        "문화": ["문화", "공연", "전시", "바우처"],
        "생활지원": ["수당", "급여", "지원금", "지역화폐", "포인트"],
    }
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "금전지원"


def _infer_money_type(title, summary):
    text = f"{title} {summary}"
    money_types = {
        "현금/수당": ["지원금", "현금", "수당", "급여", "장려금"],
        "비용지원": ["응시료", "교육비", "훈련비", "교통비", "월세", "주거비", "등록금"],
        "바우처/포인트": ["바우처", "포인트", "지역화폐", "이용권", "상품권"],
        "금융지원": ["대출", "이자", "저축", "계좌", "융자"],
        "환급": ["환급", "감면", "면제"],
    }
    for money_type, keywords in money_types.items():
        if any(keyword in text for keyword in keywords):
            return money_type
    return "금전지원"


def _pick(item, keys):
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _parse_age_range(text):
    numbers = [int(number) for number in re.findall(r"\d+", text or "")]
    if len(numbers) >= 2:
        plausible = [number for number in numbers if 0 < number <= 100]
        if len(plausible) >= 2:
            return min(plausible[:2]), max(plausible[:2])
    if len(numbers) == 1 and 0 < numbers[0] <= 100:
        return numbers[0], numbers[0]
    return None, None


def _strip_namespace(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _to_int(value):
    try:
        if value in (None, ""):
            return None
        return int(value)
    except ValueError:
        return None
