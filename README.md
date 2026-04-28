# 📊 SK Square 투자분석 재무 대시보드

DART 감사보고서 기반 재무 분석 결과를 시각화하는 Streamlit 대시보드입니다.

## 구조

```
financial-dashboard/
├── app.py                  # 메인 앱
├── requirements.txt
├── data/
│   ├── tmap_mobility.json  # 티맵모빌리티 (완료)
│   └── *.json              # 추가 회사 파일
└── README.md
```

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud 배포

1. 이 저장소를 GitHub에 push
2. [share.streamlit.io](https://share.streamlit.io) 접속
3. GitHub 연동 후 `app.py` 선택하여 배포

## 새 회사 추가 방법

Claude에게 재무분석을 요청한 후, 아래 형식의 JSON 파일을 `data/` 폴더에 추가하면
앱 재시작 없이 자동으로 버튼에 등재됩니다.

### JSON 템플릿

```json
{
  "company_name": "회사명",
  "company_name_en": "Company Name",
  "sector": "업종",
  "listing_status": "비상장 or 코스피 or 코스닥",
  "fiscal_year_end": "12월",
  "currency": "KRW",
  "unit": "억원",
  "standard": "K-IFRS 연결",
  "source": "DART 연결감사보고서",
  "dart_links": {
    "2025": "https://dart.fss.or.kr/...",
    "2024": "https://dart.fss.or.kr/..."
  },
  "years": ["2022", "2023", "2024", "2025"],
  "income_statement": {
    "revenue":          [0, 0, 0, 0],
    "operating_cost":   [0, 0, 0, 0],
    "operating_income": [0, 0, 0, 0],
    "non_operating":    [0, 0, 0, 0],
    "ebt":              [0, 0, 0, 0],
    "net_income":       [0, 0, 0, 0]
  },
  "cost_breakdown": {
    "service_cost":   [0, 0, 0, 0],
    "employee_cost":  [0, 0, 0, 0],
    "commission_fee": [0, 0, 0, 0],
    "depreciation":   [0, 0, 0, 0],
    "advertising":    [0, 0, 0, 0]
  },
  "margins": {
    "operating_margin": [0.0, 0.0, 0.0, 0.0],
    "net_margin":       [0.0, 0.0, 0.0, 0.0]
  },
  "cagr": {
    "period": "2022→2025",
    "revenue": 0.0,
    "operating_cost": 0.0,
    "employee_cost": 0.0,
    "depreciation": 0.0,
    "advertising": 0.0
  },
  "yoy_growth": {
    "revenue": [null, 0.0, 0.0, 0.0]
  },
  "key_highlights": [
    "주요 시사점 1",
    "주요 시사점 2"
  ]
}
```
