# 금전지원 혜택 모아보기

사용자가 입력한 나이, 거주 지역, 관심 분야, 현재 상황을 기준으로 받을 수 있는 금전적 지원 혜택을 모아 보여주는 Flask 웹 프로젝트입니다.

현재 구현 범위는 공공기관 데이터 수집과 전체 웹앱 뼈대입니다. 통신사와 카드사 혜택 수집은 팀원이 같은 데이터 형식으로 연결할 수 있도록 함수 템플릿만 준비되어 있습니다.

## 주요 기능

- 시/도, 시/군/구, 나이, 관심 분야, 현재 상황 입력
- 공공기관 금전지원 혜택 수집
- API 키가 없거나 외부 요청이 실패할 때 샘플 데이터로 대체
- 금전지원 성격의 혜택만 필터링
- 조건이 많이 맞는 혜택을 우선 정렬
- 추천 이유 표시
- 검색 결과 CSV 다운로드
- 팀원용 통신사/카드사 collector 연결 구조 제공

## 프로젝트 구조

```text
python_project/
├─ project_app.py
├─ collectors/
│  ├─ public_policy_collector.py
│  ├─ telecom_collector.py
│  └─ card_collector.py
├─ services/
│  ├─ benefit_service.py
│  ├─ matcher.py
│  └─ money_filter.py
├─ data/
│  └─ sample_public_policies.csv
├─ templates/
│  └─ index.html
├─ static/
│  └─ style.css
├─ .env.example
└─ README.md
```

## 실행 방법

가상환경에 Flask, requests 등이 설치되어 있다면 아래 명령으로 실행합니다.

```powershell
python project_app.py
```

현재 개발 환경에서 기본 Python 명령이 잡히지 않는 경우에는 Codex 런타임 Python으로 실행할 수 있습니다.

```powershell
C:\Users\Win11Pro\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe project_app.py
```

실행 후 브라우저에서 접속합니다.

```text
http://127.0.0.1:5001/
```

## API 키 설정

API 키가 없어도 `data/sample_public_policies.csv` 샘플 데이터로 화면이 동작합니다.

실제 API를 연결하려면 `.env.example`을 참고해 프로젝트 루트에 `.env` 파일을 만들고 키를 입력합니다.

```env
GOV24_SERVICE_API_KEY=your_data_go_kr_api_key_here
GOV24_SERVICE_LIST_API_URL=https://api.odcloud.kr/api/gov24/v1/serviceList
GOV24_SERVICE_PAGE_SIZE=100

ONTONG_YOUTH_API_KEY=your_youthcenter_api_key_here
ONTONG_YOUTH_POLICY_API_URL=https://www.youthcenter.go.kr/opi/youthPlcyList.do
```

우선 연결 대상으로 생각한 API는 다음과 같습니다.

- 대한민국 공공서비스 정보 API
- 온통청년 청년정책 API

## 데이터 기준

이 프로젝트는 모든 혜택을 보여주지 않고, 금전적 지원 성격이 있는 혜택만 보여줍니다.

포함 예시:

- 지원금
- 현금성 수당
- 바우처
- 포인트
- 지역화폐
- 응시료 지원
- 교육비, 훈련비
- 교통비
- 월세, 주거비
- 장학금
- 대출이자 지원
- 환급, 감면, 면제

제외 예시:

- 단순 상담
- 멘토링
- 공간 대여
- 행사
- 채용 공고

관련 키워드는 `services/money_filter.py`에서 관리합니다.

## 공통 혜택 데이터 형식

모든 collector는 아래 형식의 `dict` 리스트를 반환하는 것을 목표로 합니다.

```python
{
    "title": "달서청년 자격증 응시료 지원사업",
    "provider": "대구광역시 달서구",
    "source_type": "공공기관",
    "category": "취업",
    "province": "대구",
    "district": "달서구",
    "region": "대구 달서구",
    "money_type": "비용지원",
    "age_min": 18,
    "age_max": 39,
    "target": "달서구 거주 미취업 청년",
    "summary": "자격시험 응시료를 지원하는 사업입니다.",
    "url": "https://www.dalseo.daegu.kr",
    "matched_reason": "",
    "score": 0,
}
```

`score`는 화면에 보여주지 않습니다. 내부에서 추천 결과를 정렬하기 위해서만 사용합니다.

## 팀원 작업 방법

통신사 혜택 담당자는 `collectors/telecom_collector.py`의 함수를 구현하면 됩니다.

```python
def get_telecom_benefits(user_profile):
    return []
```

카드사 혜택 담당자는 `collectors/card_collector.py`의 함수를 구현하면 됩니다.

```python
def get_card_benefits(user_profile):
    return []
```

두 함수 모두 `list[dict]` 형태로 혜택 데이터를 반환하면 `services/benefit_service.py`에서 자동으로 공공기관 데이터와 합쳐집니다.

예시:

```python
def get_telecom_benefits(user_profile):
    return [
        {
            "title": "청년 요금제 할인",
            "provider": "통신사명",
            "source_type": "통신사",
            "category": "통신",
            "province": "전국",
            "district": "",
            "region": "전국",
            "money_type": "감면",
            "age_min": 19,
            "age_max": 34,
            "target": "청년",
            "summary": "청년 대상 통신요금 할인 혜택입니다.",
            "url": "https://example.com",
            "matched_reason": "",
            "score": 0,
        }
    ]
```

## 주요 파일 설명

- `project_app.py`: Flask 실행 파일, 메인 화면과 CSV 다운로드 라우트
- `collectors/public_policy_collector.py`: 공공기관 API 호출, XML/JSON 파싱, 샘플 데이터 대체
- `services/benefit_service.py`: 공공/통신/카드 데이터 통합
- `services/matcher.py`: 사용자 조건과 혜택 조건 비교, 내부 정렬 점수 계산
- `services/money_filter.py`: 금전지원 키워드 필터
- `templates/index.html`: 웹 화면 구조
- `static/style.css`: 웹 화면 디자인
- `data/sample_public_policies.csv`: API 실패 시 사용하는 샘플 데이터

## 발표 설명 흐름

1. 사용자가 나이와 거주 지역을 입력한다.
2. 공공기관 API에서 혜택 데이터를 가져온다.
3. API 키가 없거나 실패하면 샘플 데이터로 대체한다.
4. 지원금, 응시료, 월세, 바우처 등 금전지원 키워드가 있는 혜택만 남긴다.
5. 지역, 나이, 관심 분야, 현재 상황이 많이 맞는 순서로 정렬한다.
6. 추천 이유와 원문 링크를 화면에 보여준다.
7. 필요하면 CSV로 다운로드한다.
