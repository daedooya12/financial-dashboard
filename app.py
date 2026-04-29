import streamlit as st
import requests, json, os, io, zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="SK Square | 재무 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans KR', sans-serif;
    background: #F4F6FA;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2447 0%, #1A3A6B 60%, #1e4d8c 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E8EEF8 !important; }

[data-testid="stSidebar"] input[type="text"] {
    background: #FFFFFF !important;
    color: #1A3A6B !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    padding: 0.4rem 0.8rem !important;
}
[data-testid="stSidebar"] input[type="text"]::placeholder { color: #9CA3AF !important; }

[data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child {
    background: #FFFFFF !important;
    border-radius: 8px !important;
    border: none !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] span,
[data-testid="stSidebar"] div[data-baseweb="select"] div {
    color: #1A3A6B !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display: block !important; width: 100% !important;
    padding: 0.5rem 0.9rem !important; border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    background: rgba(255,255,255,0.06) !important;
    color: #C8D8F0 !important; font-size: 0.85rem !important;
    margin-bottom: 3px !important; cursor: pointer !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.15) !important; color: #fff !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] { display: none !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    color: inherit !important; font-size: 0.85rem !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: 100% !important;
    background: #3B82F6 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: #2563EB !important;
}

/* ── 메인 ── */
.main .block-container { padding: 1.5rem 2rem 3rem 2rem; max-width: 100%; }

.page-title { font-size: 1.6rem; font-weight: 700; color: #111827; margin-bottom: 0.2rem; }
.page-sub   { font-size: 0.82rem; color: #6B7280; margin-bottom: 1.5rem; }

.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 1.8rem; }
.kpi-card {
    background: white; border-radius: 14px;
    padding: 1.3rem 1.5rem;
    border-top: 4px solid #1A3A6B;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    position: relative; overflow: hidden;
}
.kpi-card::after {
    content: ''; position: absolute; right: -20px; top: -20px;
    width: 80px; height: 80px; border-radius: 50%;
    background: rgba(26,58,107,0.04);
}
.kpi-card.green  { border-top-color: #059669; }
.kpi-card.red    { border-top-color: #DC2626; }
.kpi-card.teal   { border-top-color: #0D9488; }
.kpi-card.amber  { border-top-color: #D97706; }
.kpi-label { font-size: 0.7rem; color: #9CA3AF; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px; }
.kpi-value { font-size: 1.6rem; font-weight: 700; color: #111827; line-height: 1; margin-bottom: 6px; }
.kpi-value.pos { color: #059669; }
.kpi-value.neg { color: #DC2626; }
.kpi-yoy  { font-size: 0.78rem; font-weight: 500; }
.kpi-yoy.pos { color: #059669; } .kpi-yoy.neg { color: #DC2626; }
.kpi-sub  { font-size: 0.72rem; color: #9CA3AF; margin-top: 3px; }

.section-hd {
    font-size: 0.75rem; font-weight: 700; color: #374151;
    text-transform: uppercase; letter-spacing: 0.07em;
    border-left: 3px solid #1A3A6B; padding-left: 10px;
    margin: 1.8rem 0 0.9rem 0;
}
.badge { display:inline-block; border-radius:4px; padding:3px 10px; font-size:0.72rem; font-weight:600; margin-right:5px; }
.badge-blue   { background:#DBEAFE; color:#1E40AF; }
.badge-yellow { background:#FEF3C7; color:#92400E; }
.badge-teal   { background:#CCFBF1; color:#0F766E; }
.badge-gray   { background:#F3F4F6; color:#374151; }

.chart-wrap { background: white; border-radius: 14px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1rem; }
.tbl-wrap   { background: white; border-radius: 14px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.tbl-note   { font-size: 0.7rem; color: #9CA3AF; margin-top: 0.8rem; }

.empty-state {
    text-align: center; padding: 5rem 2rem;
    color: #9CA3AF;
}
.empty-icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-title { font-size: 1.1rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem; }
.empty-sub { font-size: 0.85rem; }

.sidebar-label {
    font-size: 0.65rem; letter-spacing: 0.1em;
    color: #7B9EC4; font-weight: 600; margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)


# ── DART API ─────────────────────────────────────────────────
DART_BASE = "https://opendart.fss.or.kr/api"

def get_api_key():
    try:    return st.secrets["DART_API_KEY"]
    except: return os.environ.get("DART_API_KEY", "")

@st.cache_data(ttl=86400, show_spinner=False)
def load_corp_list(api_key):
    try:
        r    = requests.get(f"{DART_BASE}/corpCode.xml", params={"crtfc_key": api_key}, timeout=30)
        z    = zipfile.ZipFile(io.BytesIO(r.content))
        root = ET.fromstring(z.read("CORPCODE.xml"))
        corps = {}
        for item in root.findall("list"):
            name  = item.findtext("corp_name",  "").strip()
            code  = item.findtext("corp_code",  "").strip()
            stock = item.findtext("stock_code", "").strip()
            if name and code:
                corps[name] = {"corp_code": code, "stock_code": stock}
        return corps
    except:
        return {}

def search_corp(corps, query):
    q = query.strip()
    if not q: return []
    exact   = [(k, v) for k, v in corps.items() if k == q]
    partial = [(k, v) for k, v in corps.items() if q in k and k != q]
    return (exact + partial)[:10]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fs(api_key, corp_code, year, reprt_code, fs_div):
    try:
        r = requests.get(f"{DART_BASE}/fnlttSinglAcntAll.json", params={
            "crtfc_key": api_key, "corp_code": corp_code,
            "bsns_year": str(year), "reprt_code": reprt_code, "fs_div": fs_div
        }, timeout=30)
        d = r.json()
        if d.get("status") == "000":
            return d.get("list", [])
        return []
    except:
        return []


# ── 데이터 파싱 ───────────────────────────────────────────────
def parse_amount(s):
    """원 단위 문자열 → 억원 (소수점 1자리)"""
    if not s or str(s).strip() in ("", "-", "－", "N/A"): return None
    try:
        val = int(str(s).replace(",", "").strip())
        return round(val / 1e8, 1)
    except:
        return None

# 손익계산서 구분 키워드
IS_KEYWORDS = ["손익", "포괄손익"]

# EBITDA 계산을 위한 감가상각 계정 키워드
DEP_KEYWORDS = ["감가상각비", "상각비"]

def get_is_items(fs_list):
    """손익계산서 항목만 추출 (DART 원본 순서 유지)"""
    # 1순위: 순수 손익계산서 (포괄 제외)
    seen = set()
    items = []
    for item in fs_list:
        sj = item.get("sj_nm", "")
        if not any(kw in sj for kw in IS_KEYWORDS): continue
        if "포괄" in sj: continue
        acnt_nm  = item.get("account_nm", "").strip()
        acnt_id  = item.get("account_id", "")
        curr_amt = parse_amount(item.get("thstrm_amount"))
        prev_amt = parse_amount(item.get("frmtrm_amount"))
        if acnt_nm in seen: continue
        seen.add(acnt_nm)
        items.append({"account_nm": acnt_nm, "account_id": acnt_id, "curr": curr_amt, "prev": prev_amt})
    # 2순위: 손익계산서가 없으면 포괄손익계산서 사용 (일부 회사)
    if not items:
        for item in fs_list:
            sj = item.get("sj_nm", "")
            if not any(kw in sj for kw in IS_KEYWORDS): continue
            acnt_nm  = item.get("account_nm", "").strip()
            acnt_id  = item.get("account_id", "")
            curr_amt = parse_amount(item.get("thstrm_amount"))
            prev_amt = parse_amount(item.get("frmtrm_amount"))
            if acnt_nm in seen: continue
            seen.add(acnt_nm)
            items.append({"account_nm": acnt_nm, "account_id": acnt_id, "curr": curr_amt, "prev": prev_amt})
    return items

def get_cf_dep(fs_list):
    """현금흐름표에서 감가상각비 추출 (EBITDA용)"""
    for item in fs_list:
        sj   = item.get("sj_nm", "")
        acnt = item.get("account_nm", "").strip()
        if "현금" in sj and any(kw in acnt for kw in DEP_KEYWORDS):
            v = parse_amount(item.get("thstrm_amount"))
            if v is not None: return abs(v)
    return None

def find_amount(items, *keywords):
    """계정과목명에서 키워드 매칭으로 금액 추출"""
    for kw in keywords:
        for item in items:
            if item["account_nm"] == kw:
                return item["curr"]
    for kw in keywords:
        for item in items:
            if kw in item["account_nm"]:
                return item["curr"]
    return None


# ── KPI 추출 ──────────────────────────────────────────────────
def extract_kpis(years_data):
    """연도별 KPI 추출: 매출/영업이익/순이익/감가상각"""
    result = {}
    for yr, (items, dep) in years_data.items():
        rev = find_amount(items, "매출액", "영업수익", "수익(매출액)", "매출")
        op  = find_amount(items, "영업이익", "영업이익(손실)", "영업손익")
        net = find_amount(items, "당기순이익", "당기순이익(손실)", "당기순손실")
        ebt = find_amount(items, "법인세비용차감전순이익", "법인세비용차감전순이익(손실)", "법인세비용차감전순손실")
        result[yr] = {"rev": rev, "op": op, "net": net, "ebt": ebt, "dep": dep}
    return result


# ── 다연도 통합 테이블 ────────────────────────────────────────
def build_multi_year_table(years_data_dict, years):
    """
    연도별 IS 항목을 하나의 DataFrame으로 통합
    - 기준연도(최신) 계정과목을 행으로
    - 각 연도 금액 + YoY + CAGR 컬럼
    """
    # 최신 연도 기준 계정과목 목록
    latest_yr  = max(years)
    base_items = years_data_dict.get(latest_yr, ([], None))[0]
    acnt_names = [it["account_nm"] for it in base_items]

    # 각 연도별 계정과목→금액 딕셔너리
    yr_maps = {}
    for yr in years:
        items, _ = years_data_dict.get(yr, ([], None))
        yr_maps[yr] = {it["account_nm"]: it["curr"] for it in items}

    # DataFrame 구성
    records = []
    for acnt in acnt_names:
        row = {"계정과목": acnt}
        vals = []
        for yr in years:
            v = yr_maps[yr].get(acnt)
            row[str(yr)] = v
            vals.append(v)

        # YoY (전년 대비 %)
        for i in range(1, len(years)):
            cur = vals[i]; prv = vals[i-1]
            col = f"YoY {years[i]}"
            if cur is not None and prv and prv != 0:
                row[col] = round((cur - prv) / abs(prv) * 100, 1)
            else:
                row[col] = None

        # CAGR (전체 기간)
        n = len(years) - 1
        s, e = vals[0], vals[-1]
        if s and e and s != 0 and n > 0:
            try:    row["CAGR"] = round(((e / s) ** (1/n) - 1) * 100, 1)
            except: row["CAGR"] = None
        else:
            row["CAGR"] = None

        records.append(row)

    return pd.DataFrame(records)


# ── 스타일링 ──────────────────────────────────────────────────
def style_table(df, years):
    def fmt_val(v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
        return f"{v:,.1f}"

    def fmt_pct(v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
        sign = "▲ " if v > 0 else ("▼ " if v < 0 else "")
        return f"{sign}{abs(v):.1f}%"

    yr_cols  = [str(y) for y in years]
    yoy_cols = [f"YoY {y}" for y in years[1:]]
    cagr_col = "CAGR"

    def format_cell(val, col):
        if col in yr_cols:   return fmt_val(val)
        if col in yoy_cols:  return fmt_pct(val)
        if col == cagr_col:  return fmt_pct(val)
        return str(val) if val is not None else "—"

    # 표시용 df 생성
    display_df = df.copy()
    for col in display_df.columns:
        if col == "계정과목": continue
        display_df[col] = display_df.apply(lambda r: format_cell(r[col], col), axis=1)

    display_df = display_df.set_index("계정과목")

    # 스타일 함수
    def color_cell(val):
        if not isinstance(val, str) or val == "—": return ""
        if "▲" in val: return "color: #059669; font-weight: 500"
        if "▼" in val: return "color: #DC2626; font-weight: 500"
        # 수치 음수 처리
        try:
            num = float(val.replace(",", ""))
            if num < 0: return "color: #DC2626"
        except: pass
        return ""

    # 주요 계정 볼드 처리 키워드
    BOLD_KEYWORDS = ["매출액", "영업수익", "영업이익", "당기순이익", "당기순손실",
                     "법인세비용차감전", "매출총이익", "수익(매출액)"]

    def row_style(row):
        name = row.name
        is_bold = any(kw in name for kw in BOLD_KEYWORDS)
        base = "font-weight: 600; background: #F8FAFF;" if is_bold else ""
        return [base] * len(row)

    styled = (
        display_df.style
        .apply(row_style, axis=1)
        .map(color_cell)
        .set_properties(**{"font-size": "0.82rem", "padding": "6px 12px"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("background", "#1A3A6B"), ("color", "white"),
                ("font-size", "0.75rem"), ("font-weight", "600"),
                ("text-align", "center"), ("padding", "8px 12px"),
                ("white-space", "nowrap")
            ]},
            {"selector": "th.col_heading", "props": [("text-align", "center")]},
            {"selector": "th.row_heading", "props": [
                ("text-align", "left"), ("background", "#F8FAFF"),
                ("color", "#374151"), ("font-weight", "500")
            ]},
            {"selector": "td", "props": [("text-align", "right")]},
            {"selector": "td:first-child", "props": [("text-align", "left")]},
            {"selector": "tr:hover td", "props": [("background", "#EFF6FF !important")]},
        ])
    )
    return styled


# ── 차트 ─────────────────────────────────────────────────────
def make_chart(kpis, years):
    valid_years = [y for y in years if kpis.get(y, {}).get("rev") is not None]
    if not valid_years: return None

    rev  = [kpis[y]["rev"] or 0 for y in valid_years]
    op   = [kpis[y]["op"]  or 0 for y in valid_years]
    net  = [kpis[y]["net"] or 0 for y in valid_years]
    dep  = [kpis[y]["dep"] or 0 for y in valid_years]
    ebi  = [o + d for o, d in zip(op, dep)]
    yrs  = [str(y) for y in valid_years]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="매출", x=yrs, y=rev,
        marker_color="#1A3A6B", opacity=0.85, marker_line_width=0,
        text=[f"{v:,.0f}" for v in rev], textposition="outside",
        textfont=dict(size=10, color="#1A3A6B")))
    fig.add_trace(go.Bar(name="EBITDA", x=yrs, y=ebi,
        marker_color="#0D9488", opacity=0.85, marker_line_width=0,
        text=[f"{v:,.0f}" for v in ebi], textposition="outside",
        textfont=dict(size=10, color="#0D9488")))
    fig.add_trace(go.Bar(name="영업이익", x=yrs, y=op,
        marker_color=[("#DC2626" if v < 0 else "#059669") for v in op],
        opacity=0.85, marker_line_width=0,
        text=[f"{v:,.0f}" for v in op], textposition="outside",
        textfont=dict(size=10)))
    fig.add_trace(go.Scatter(name="당기순이익", x=yrs, y=net,
        mode="lines+markers",
        line=dict(color="#D97706", width=2.5, dash="dot"),
        marker=dict(size=9, color="#D97706", line=dict(color="white", width=2))))
    fig.update_layout(
        barmode="group", plot_bgcolor="white", paper_bgcolor="white",
        height=340, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right",
                    font=dict(size=11, family="Noto Sans KR"), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",", ticksuffix="억", gridcolor="#F3F4F6",
                   zeroline=True, zerolinecolor="#D1D5DB", tickfont=dict(size=11)),
        xaxis=dict(type="category", tickfont=dict(size=12)),
        font=dict(family="Noto Sans KR")
    )
    return fig


# ── 사이드바 ─────────────────────────────────────────────────
def render_sidebar():
    api_key = get_api_key()

    with st.sidebar:
        st.markdown("""
        <div style='padding:1.5rem 0 1rem 0;border-bottom:1px solid rgba(255,255,255,0.12);margin-bottom:1.2rem;'>
            <div style='font-size:0.62rem;letter-spacing:0.14em;color:#93B4D8;font-weight:700;margin-bottom:5px;'>SK SQUARE</div>
            <div style='font-size:1rem;font-weight:700;color:#FFF;line-height:1.35;'>투자분석<br>재무 대시보드</div>
            <div style='font-size:0.68rem;color:#7B9EC4;margin-top:5px;'>DART OpenAPI 기반</div>
        </div>
        """, unsafe_allow_html=True)

        if not api_key:
            st.markdown("""
            <div style='background:rgba(220,38,38,0.15);border:1px solid rgba(220,38,38,0.3);
            border-radius:8px;padding:10px 12px;font-size:0.78rem;color:#FCA5A5;'>
            ⚠️ DART API 키 미설정<br>
            <span style='font-size:0.72rem;opacity:0.8;'>Streamlit Secrets에<br>DART_API_KEY 추가 필요</span>
            </div>
            """, unsafe_allow_html=True)
            return None

        # 회사 검색
        st.markdown("<div class='sidebar-label'>🔍 COMPANY SEARCH</div>", unsafe_allow_html=True)
        query = st.text_input("", placeholder="회사명 입력 (예: 카카오)", key="query",
                              label_visibility="collapsed")

        selected_corp = None
        if query and len(query) >= 1:
            with st.spinner(""):
                corps = load_corp_list(api_key)
            results = search_corp(corps, query)
            if results:
                opt_labels = [f"{'📈' if v['stock_code'] else '🏢'} {n}" for n, v in results]
                chosen_idx = st.selectbox("", range(len(opt_labels)),
                    format_func=lambda i: opt_labels[i],
                    key="corp_sel", label_visibility="collapsed")
                selected_corp = results[chosen_idx]
            else:
                st.markdown("<div style='font-size:0.78rem;color:#F87171;'>검색 결과 없음</div>", unsafe_allow_html=True)

        # 조회 설정
        st.markdown("<div class='sidebar-label' style='margin-top:1rem;'>⚙️ SETTINGS</div>", unsafe_allow_html=True)

        fs_div_label = st.selectbox("재무제표 구분", ["연결 (CFS)", "개별 (OFS)"],
                                     key="fs_div", label_visibility="collapsed")
        fs_div = "CFS" if "CFS" in fs_div_label else "OFS"

        year_opts = [2025, 2024, 2023, 2022, 2021, 2020]
        sel_years = st.multiselect("조회 연도", year_opts,
                                   default=[2022, 2023, 2024, 2025],
                                   key="years", label_visibility="collapsed")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        search_clicked = st.button("📡 조회", use_container_width=True)

        if search_clicked and selected_corp and sel_years:
            corp_name, corp_info = selected_corp
            st.session_state.search_params = {
                "corp_name": corp_name,
                "corp_code": corp_info["corp_code"],
                "stock_code": corp_info["stock_code"],
                "fs_div": fs_div,
                "years": sorted(sel_years),
            }
            st.session_state.fs_data = None
            st.rerun()

        st.markdown("""
        <div style='margin-top:2rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.1);
        font-size:0.65rem;color:#4A6FA5;line-height:1.8;'>
        📌 사업보고서(연간) 기준<br>
        📌 단위: 억원
        </div>
        """, unsafe_allow_html=True)

    return api_key


# ── 메인 렌더링 ───────────────────────────────────────────────
def render_main(api_key):
    params = st.session_state.get("search_params")

    # 초기 화면
    if not params:
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-icon'>📊</div>
            <div class='empty-title'>SK Square 재무 분석 대시보드</div>
            <div class='empty-sub'>좌측 사이드바에서 회사명을 검색하고 조회 버튼을 눌러주세요</div>
        </div>
        """, unsafe_allow_html=True)
        return

    corp_name = params["corp_name"]
    corp_code = params["corp_code"]
    fs_div    = params["fs_div"]
    years     = params["years"]

    # ── 데이터 로드 ──
    if st.session_state.get("fs_data") is None:
        years_data = {}
        prog = st.progress(0, text=f"{corp_name} 재무데이터 로딩 중...")
        for i, yr in enumerate(years):
            prog.progress((i+1)/len(years), text=f"{yr}년 데이터 조회 중...")
            fs_list = fetch_fs(api_key, corp_code, yr, "11011", fs_div)
            if not fs_list and fs_div == "CFS":
                fs_list = fetch_fs(api_key, corp_code, yr, "11011", "OFS")
            items = get_is_items(fs_list)
            dep   = get_cf_dep(fs_list)
            years_data[yr] = (items, dep)
        prog.empty()
        st.session_state.fs_data = years_data
    else:
        years_data = st.session_state.fs_data

    kpis = extract_kpis(years_data)

    # ── 회사 헤더 ──
    listing = "상장 📈" if params.get("stock_code") else "비상장 🏢"
    std_label = "K-IFRS 연결" if fs_div == "CFS" else "K-GAAP 개별"
    yr_range  = f"{min(years)}~{max(years)}"

    st.markdown(f"<div class='page-title'>{corp_name}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<span class='badge badge-blue'>{listing}</span>"
        f"<span class='badge badge-teal'>{std_label}</span>"
        f"<span class='badge badge-gray'>사업보고서</span>"
        f"<span class='badge badge-gray'>{yr_range}</span>",
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── KPI 카드 ──
    latest = years[-1]; prev = years[-2] if len(years) >= 2 else None

    def yoy_fmt(curr, prev_val):
        if curr is None or prev_val is None or prev_val == 0: return None, None
        v = (curr - prev_val) / abs(prev_val) * 100
        return round(v, 1), "pos" if v >= 0 else "neg"

    def kpi_html(label, yr, val, yoy_val, yoy_cls, margin_label=None, margin_val=None, color="blue"):
        val_str = ("{:,.0f}억".format(val)) if val is not None else "—"
        val_cls = "neg" if (val is not None and val < 0) else "pos"
        yoy_str = ""
        if yoy_val is not None:
            arrow = "▲" if yoy_val > 0 else ("▼" if yoy_val < 0 else "")
            yoy_str = "<div class='kpi-yoy " + yoy_cls + "'>" + arrow + " " + "{:.1f}".format(abs(yoy_val)) + "% YoY</div>"
        margin_str = ""
        if margin_label and margin_val is not None:
            margin_str = "<div class='kpi-sub'>" + margin_label + ": " + "{:.1f}".format(margin_val) + "%</div>"
        card  = "<div class='kpi-card " + color + "'>"
        card += "<div class='kpi-label'>" + str(label) + " " + str(yr) + "</div>"
        card += "<div class='kpi-value " + val_cls + "'>" + val_str + "</div>"
        card += yoy_str + margin_str
        card += "</div>"
        return card

    k_latest = kpis.get(latest, {})
    k_prev   = kpis.get(prev, {}) if prev else {}

    rev_v  = k_latest.get("rev");  rev_p  = k_prev.get("rev")
    op_v   = k_latest.get("op");   op_p   = k_prev.get("op")
    net_v  = k_latest.get("net");  net_p  = k_prev.get("net")
    dep_v  = k_latest.get("dep", 0) or 0
    ebi_v  = (op_v + dep_v) if op_v is not None else None

    ebi_p_op  = k_prev.get("op")
    ebi_p_dep = k_prev.get("dep", 0) or 0
    ebi_p = (ebi_p_op + ebi_p_dep) if ebi_p_op is not None else None

    rev_yoy,  rev_cls  = yoy_fmt(rev_v,  rev_p)
    op_yoy,   op_cls   = yoy_fmt(op_v,   op_p)
    net_yoy,  net_cls  = yoy_fmt(net_v,  net_p)
    ebi_yoy,  ebi_cls  = yoy_fmt(ebi_v,  ebi_p)

    op_margin  = round(op_v  / rev_v * 100, 1) if op_v  and rev_v else None
    net_margin = round(net_v / rev_v * 100, 1) if net_v and rev_v else None
    ebi_margin = round(ebi_v / rev_v * 100, 1) if ebi_v and rev_v else None

    kpi_color = lambda v: "green" if v and v >= 0 else "red"

    html = "<div class='kpi-grid'>"
    html += kpi_html("매출",     latest, rev_v,  rev_yoy,  rev_cls,  color="blue")
    html += kpi_html("영업이익", latest, op_v,   op_yoy,   op_cls,   "영업이익률", op_margin,  kpi_color(op_v))
    html += kpi_html("EBITDA",   latest, ebi_v,  ebi_yoy,  ebi_cls,  "EBITDA margin", ebi_margin, "teal")
    html += kpi_html("당기순이익",latest, net_v, net_yoy,  net_cls,  "순이익률", net_margin, kpi_color(net_v))
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # ── 차트 ──
    st.markdown("<div class='section-hd'>추이 차트 | 단위: 억원</div>", unsafe_allow_html=True)
    fig = make_chart(kpis, years)
    if fig:
        st.markdown("<div class='chart-wrap'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 손익계산서 원본 테이블 ──
    st.markdown("<div class='section-hd'>손익계산서 | 단위: 억원 · DART 원본 계정 기준</div>", unsafe_allow_html=True)

    df = build_multi_year_table(years_data, years)
    if df.empty:
        st.warning("손익계산서 데이터를 불러오지 못했습니다.")
    else:
        n_years = len(years)
        # 컬럼 순서: 계정과목 | 연도들 | YoY들 | CAGR
        yr_cols  = [str(y) for y in years]
        yoy_cols = [f"YoY {y}" for y in years[1:]]
        ordered_cols = ["계정과목"] + yr_cols + yoy_cols + ["CAGR"]
        df = df[[c for c in ordered_cols if c in df.columns]]

        st.markdown("<div class='tbl-wrap'>", unsafe_allow_html=True)
        styled = style_table(df, years)
        # 행 수에 따라 높이 동적 조정
        h = min(max(len(df) * 36 + 60, 300), 700)
        st.dataframe(styled, use_container_width=True, height=h)
        st.markdown(
            f"<p class='tbl-note'>출처: DART OpenAPI 사업보고서 | {'연결' if fs_div=='CFS' else '개별'} 손익계산서 "
            f"| EBITDA = 영업이익 + 감가상각비(현금흐름표 기준) | YoY: 전년 대비 증감률 | CAGR: {min(years)}→{max(years)} 연평균 성장률</p>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ── 앱 실행 ───────────────────────────────────────────────────
def main():
    if "search_params" not in st.session_state:
        st.session_state.search_params = None
    if "fs_data" not in st.session_state:
        st.session_state.fs_data = None

    api_key = render_sidebar()
    if api_key:
        render_main(api_key)


if __name__ == "__main__":
    main()
