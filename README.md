# 금전지원 혜택 모아보기

사용자가 입력한 나이, 거주 지역, 관심 분야, 현재 상황을 기준으로 받을 수 있는 금전적 지원 혜택을 추천하는 Flask 웹 프로젝트입니다.

기존 버전은 공공기관 데이터 중심의 뼈대였고, 개선 버전은 발표/시연 완성도를 높이기 위해 통신사·카드사 샘플 데이터, 결과 필터, 키워드 검색, 추천 적합도, 추천 이유 뱃지, 중복 제거 통계, CSV 다운로드를 보강했습니다.

## 주요 기능

- 나이, 시/도, 시/군/구, 관심 분야, 현재 상황 입력
- 공공기관 API 호출 및 실패 시 샘플 데이터 대체
- 통신사/카드사 샘플 collector 연결
- 금전지원 성격의 혜택만 필터링
- 나이, 지역, 관심 분야, 상황, 금전지원 키워드 기반 추천 점수 계산
- 추천 적합도 퍼센트와 추천 이유 표시
- 출처/분야/키워드/정렬 필터 제공
- 검색 결과 CSV 다운로드
- 팀원이 collector만 교체해도 전체 화면에 자동 반영되는 구조

## 프로젝트 구조

```text
python_project1/
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
├─ requirements.txt
├─ .env.example
└─ README.md
```

## 실행 방법

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python project_app.py
```

실행 후 브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:5001/
```

PowerShell에서 가상환경 활성화가 막히면 아래 명령을 현재 터미널에서 한 번 실행한 뒤 다시 활성화합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\activate
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

## collector 교체 방법

통신사 또는 카드사 데이터를 실제 크롤링/API 결과로 바꾸려면 아래 파일의 함수 반환값만 교체하면 됩니다.

- `collectors/telecom_collector.py`
- `collectors/card_collector.py`

반환 형식은 다음과 같습니다.

```python
{
    "title": "혜택명",
    "provider": "제공 기관",
    "source_type": "공공기관 또는 통신사 또는 카드사",
    "category": "취업",
    "province": "전국",
    "district": "",
    "region": "전국",
    "money_type": "감면",
    "age_min": 19,
    "age_max": 34,
    "target": "청년",
    "summary": "혜택 설명",
    "url": "https://example.com",
    "matched_reason": "",
    "score": 0,
}
```

## 발표 설명 흐름

1. 사용자가 나이와 거주 지역, 관심 분야를 입력합니다.
2. 공공기관 API를 호출하고, 실패 시 샘플 정책 데이터로 대체합니다.
3. 통신사/카드사 collector 데이터를 함께 합칩니다.
4. 지원금, 응시료, 월세, 바우처, 환급 등 금전지원 키워드가 있는 혜택만 남깁니다.
5. 나이, 지역, 관심 분야, 현재 상황이 많이 맞는 순서로 추천 점수를 계산합니다.
6. 사용자는 출처, 분야, 키워드로 결과를 다시 필터링할 수 있습니다.
7. 추천 이유와 원문 링크를 확인하고, 결과를 CSV로 다운로드할 수 있습니다.

## 개선 포인트 요약

- 기존: 공공기관 중심, 통신사/카드사 비어 있음, 단순 결과 목록
- 개선: 3개 데이터 소스 표시, 추천 적합도 표시, 검색/필터 기능, UI 카드 개선, CSV 유지, 발표용 설명 강화
