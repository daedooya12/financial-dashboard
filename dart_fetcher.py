"""
DART OpenAPI 재무제표 자동 조회 모듈
사용법: streamlit run dart_fetcher.py
"""
import streamlit as st
import requests
import json
import os
import zipfile
import io
import xml.etree.ElementTree as ET

# ── DART API 설정 ─────────────────────────────────────────────
def get_api_key():
    """Streamlit secrets 또는 환경변수에서 API 키 로드"""
    try:
        return st.secrets["DART_API_KEY"]
    except:
        return os.environ.get("DART_API_KEY", "")

BASE_URL = "https://opendart.fss.or.kr/api"

# ── 1. 기업 코드 목록 다운로드 ────────────────────────────────
@st.cache_data(ttl=86400)
def get_corp_list(api_key):
    """전체 기업 코드 XML 다운로드 및 파싱"""
    url = f"{BASE_URL}/corpCode.xml?crtfc_key={api_key}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        return {}
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    xml_data = z.read("CORPCODE.xml")
    root = ET.fromstring(xml_data)
    corps = {}
    for item in root.findall("list"):
        name = item.findtext("corp_name", "").strip()
        code = item.findtext("corp_code", "").strip()
        stock = item.findtext("stock_code", "").strip()
        if name and code:
            corps[name] = {"corp_code": code, "stock_code": stock}
    return corps

def search_corp(corps, query):
    """회사명으로 기업 코드 검색"""
    query_norm = query.replace(" ", "").lower()
    if not query_norm:
        return []
    exact = []
    partial = []
    for k, v in corps.items():
        k_norm = k.replace(" ", "").lower()
        if k_norm == query_norm:
            exact.append((k, v))
        elif query_norm in k_norm:
            partial.append((k, v))
    return (exact + partial)[:10]

# ── 2. 재무제표 조회 ──────────────────────────────────────────
def get_financial_statement(api_key, corp_code, bsns_year, reprt_code="11011", fs_div="CFS"):
    """
    단일 재무제표 조회
    reprt_code: 11011=사업보고서, 11012=반기, 11013=1분기, 11014=3분기
    fs_div: CFS=연결, OFS=개별
    """
    url = f"{BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": api_key,
        "corp_code":  corp_code,
        "bsns_year":  str(bsns_year),
        "reprt_code": reprt_code,
        "fs_div":     fs_div,
    }
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}"
    data = resp.json()
    if data.get("status") != "000":
        return None, data.get("message", "API 오류")
    return data.get("list", []), None

# ── 3. 계정과목 파싱 ─────────────────────────────────────────
ACCOUNT_MAP = {
    # 손익계산서
    "매출액":               "revenue",
    "영업수익":             "revenue",
    "수익(매출액)":         "revenue",
    "매출원가":             "cogs",
    "매출총이익":           "gross_profit",
    "판매비와관리비":       "sga",
    "영업이익":             "operating_income",
    "영업이익(손실)":       "operating_income",
    "금융수익":             "financial_income",
    "금융비용":             "financial_expense",
    "기타수익":             "other_income",
    "기타비용":             "other_expense",
    "법인세비용차감전순이익": "ebt",
    "법인세비용차감전순이익(손실)": "ebt",
    "법인세비용":           "tax",
    "당기순이익":           "net_income",
    "당기순이익(손실)":     "net_income",
    "지배기업소유주지분":   "net_income_parent",
}

def parse_amount(val_str):
    """금액 문자열 → 억원 변환 (원 단위 입력)"""
    if not val_str or val_str.strip() in ("", "-", "－"):
        return None
    try:
        # 쉼표 제거 후 정수 변환
        val = int(val_str.replace(",", "").replace(" ", ""))
        # 원 → 억원
        return round(val / 100_000_000, 0)
    except:
        return None

def extract_pl(fs_list, year):
    """손익계산서 계정에서 주요 항목 추출"""
    result = {}
    for item in fs_list:
        acnt = item.get("account_nm", "").strip()
        sj   = item.get("sj_nm", "")  # 재무제표 구분
        # 손익계산서만
        if "손익" not in sj and "포괄" not in sj:
            continue
        key = ACCOUNT_MAP.get(acnt)
        if key and key not in result:
            # 당기 금액
            amt = parse_amount(item.get("thstrm_amount", ""))
            if amt is not None:
                result[key] = int(amt)
    return result

def extract_depreciation(fs_list):
    """주석 또는 현금흐름표에서 감가상각비 추출 (근사치)"""
    for item in fs_list:
        acnt = item.get("account_nm", "").strip()
        if "감가상각" in acnt and "무형" not in acnt:
            amt = parse_amount(item.get("thstrm_amount", ""))
            if amt is not None:
                return int(amt)
    return None

# ── 4. 연도별 수집 및 JSON 생성 ──────────────────────────────
def build_company_json(api_key, corp_name, corp_code, years, fs_div="CFS"):
    """여러 연도 재무제표 수집 → 대시보드 JSON 형식으로 변환"""
    all_data = {}
    errors   = []

    progress = st.progress(0)
    for i, year in enumerate(years):
        progress.progress((i + 1) / len(years), text=f"{year}년 데이터 조회 중...")
        fs_list, err = get_financial_statement(api_key, corp_code, year, fs_div=fs_div)
        if err:
            # 연결 실패 시 개별로 재시도
            fs_list, err2 = get_financial_statement(api_key, corp_code, year, fs_div="OFS")
            if err2:
                errors.append(f"{year}: {err}")
                continue
        pl = extract_pl(fs_list, year)
        dep = extract_depreciation(fs_list)
        if dep:
            pl["depreciation"] = dep
        all_data[year] = {"pl": pl, "fs_list": fs_list}

    progress.empty()
    if not all_data:
        return None, errors

    # JSON 구조 조립
    rev_list = [all_data.get(y, {}).get("pl", {}).get("revenue", 0) for y in years]
    op_list  = [all_data.get(y, {}).get("pl", {}).get("operating_income", 0) for y in years]
    net_list = [all_data.get(y, {}).get("pl", {}).get("net_income", 0) for y in years]
    ebt_list = [all_data.get(y, {}).get("pl", {}).get("ebt", 0) for y in years]
    dep_list = [all_data.get(y, {}).get("pl", {}).get("depreciation", 0) or 0 for y in years]

    # 영업비용 = 영업수익 - 영업손익
    op_cost_list = [r - o for r, o in zip(rev_list, op_list)]
    # 영업외손익 = EBT - 영업손익
    non_op_list = [e - o for e, o in zip(ebt_list, op_list)]
    # 이익률
    op_margin  = [round(o / r * 100, 1) if r else 0 for o, r in zip(op_list, rev_list)]
    net_margin = [round(n / r * 100, 1) if r else 0 for n, r in zip(net_list, rev_list)]

    # CAGR
    n = len(years) - 1
    def cagr(s, e):
        if not s or not e: return 0
        try: return round(((e / s) ** (1 / n) - 1) * 100, 1)
        except: return 0

    # 결정: 연결/개별
    standard = "K-IFRS 연결" if fs_div == "CFS" else "K-GAAP 개별"

    result = {
        "company_name":    corp_name,
        "company_name_en": corp_name,
        "sector":          "—",
        "listing_status":  "비상장",
        "fiscal_year_end": "12월",
        "currency":        "KRW",
        "unit":            "억원",
        "standard":        standard,
        "source":          "DART OpenAPI",
        "dart_links":      {},
        "years":           [str(y) for y in years],
        "income_statement": {
            "revenue":          rev_list,
            "operating_cost":   op_cost_list,
            "operating_income": op_list,
            "non_operating":    non_op_list,
            "ebt":              ebt_list,
            "net_income":       net_list,
        },
        "cost_breakdown": {
            "service_cost":   [0] * len(years),
            "employee_cost":  [0] * len(years),
            "commission_fee": [0] * len(years),
            "depreciation":   dep_list,
            "advertising":    [0] * len(years),
        },
        "margins": {
            "operating_margin": op_margin,
            "net_margin":       net_margin,
        },
        "cagr": {
            "period":       f"{years[0]}→{years[-1]}",
            "revenue":      cagr(rev_list[0], rev_list[-1]),
            "operating_cost": cagr(op_cost_list[0], op_cost_list[-1]),
            "employee_cost":  0,
            "depreciation":   cagr(dep_list[0], dep_list[-1]) if dep_list[0] else 0,
            "advertising":    0,
        },
        "yoy_growth": {
            "revenue": [None] + [
                round((rev_list[i] - rev_list[i-1]) / abs(rev_list[i-1]) * 100, 1)
                if rev_list[i-1] else None
                for i in range(1, len(years))
            ]
        },
        "key_highlights": [
            f"DART OpenAPI 자동 수집 ({years[0]}~{years[-1]})",
            f"매출 CAGR: {cagr(rev_list[0], rev_list[-1]):+.1f}% ({years[0]}→{years[-1]})",
            f"최근 영업이익률: {op_margin[-1]:.1f}% ({years[-1]})",
            f"최근 순이익: {net_list[-1]:,}억원 ({years[-1]})",
        ]
    }
    return result, errors


# ── 5. Streamlit UI ──────────────────────────────────────────
st.set_page_config(page_title="DART 자동 조회", page_icon="📡", layout="centered")

st.markdown("## 📡 DART 재무제표 자동 조회")
st.markdown("회사명을 검색하면 DART에서 재무제표를 자동으로 가져와 대시보드 JSON을 생성합니다.")

api_key = get_api_key()
if not api_key:
    st.error("API 키가 설정되지 않았습니다. Streamlit Secrets에 DART_API_KEY를 설정해주세요.")
    st.code('[secrets]\nDART_API_KEY = "your_api_key_here"', language="toml")
    st.stop()

# 기업 코드 로드
with st.spinner("기업 코드 목록 로딩 중..."):
    corps = get_corp_list(api_key)

if not corps:
    st.error("기업 코드 목록을 불러오지 못했습니다. API 키를 확인해주세요.")
    st.stop()

st.success(f"✅ {len(corps):,}개 기업 코드 로드 완료")

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("회사명 검색", placeholder="예: 티맵모빌리티, 십일번가")
with col2:
    fs_div = st.selectbox("재무제표 구분", ["CFS (연결)", "OFS (개별)"])
    fs_div_code = "CFS" if "CFS" in fs_div else "OFS"

year_options = list(range(2024, 2019, -1))
years = st.multiselect("조회 연도", year_options, default=[2022, 2023, 2024, 2025])
years = sorted(years)

if query:
    results = search_corp(corps, query)
    if not results:
        st.warning("검색 결과가 없습니다.")
    else:
        options = [f"{name} (corp_code: {info['corp_code']}, 상장: {'O' if info['stock_code'] else 'X'})"
                   for name, info in results]
        selected_opt = st.radio("검색 결과", options)
        selected_idx = options.index(selected_opt)
        selected_name, selected_info = results[selected_idx]

        # 섹터/상장 수동 입력
        col3, col4 = st.columns(2)
        with col3:
            sector = st.text_input("업종 (선택)", placeholder="예: 모빌리티 플랫폼")
        with col4:
            listing = st.selectbox("상장 여부", ["비상장", "코스피", "코스닥", "코넥스"])

        if st.button("🔍 재무제표 자동 조회 및 JSON 생성", type="primary"):
            if not years:
                st.error("연도를 선택해주세요.")
            else:
                with st.spinner("DART에서 데이터 가져오는 중..."):
                    result, errors = build_company_json(
                        api_key, selected_name,
                        selected_info["corp_code"],
                        years, fs_div_code
                    )

                if errors:
                    for e in errors:
                        st.warning(f"⚠️ {e}")

                if result:
                    # 섹터/상장 덮어쓰기
                    if sector:
                        result["sector"] = sector
                    result["listing_status"] = listing

                    st.success("✅ 조회 완료!")

                    # 미리보기
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("최근 매출", f"{result['income_statement']['revenue'][-1]:,}억")
                    with col_b:
                        st.metric("최근 영업손익", f"{result['income_statement']['operating_income'][-1]:,}억")
                    with col_c:
                        st.metric("최근 순이익", f"{result['income_statement']['net_income'][-1]:,}억")

                    # JSON 생성
                    json_str = json.dumps(result, ensure_ascii=False, indent=2)
                    file_name = selected_name.replace(" ", "_").replace("/", "_") + ".json"

                    st.download_button(
                        label=f"⬇️ {file_name} 다운로드",
                        data=json_str.encode("utf-8"),
                        file_name=file_name,
                        mime="application/json",
                    )

                    st.markdown("**생성된 JSON 미리보기:**")
                    st.json(result)
                else:
                    st.error("데이터를 가져오지 못했습니다.")

st.markdown("---")
st.markdown("""
**사용 방법:**
1. 회사명 검색 → 기업 선택
2. 연도 선택 (여러 개 가능)
3. 조회 버튼 클릭 → JSON 다운로드
4. 다운로드한 JSON을 `financial-dashboard/data/` 폴더에 업로드
""")
