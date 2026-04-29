import streamlit as st
import requests, json, os, io, zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    background: #F0F2F8;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2447 0%, #1A3A6B 60%, #1e4d8c 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E8EEF8 !important; }
[data-testid="stSidebar"] input[type="text"] {
    background: #FFFFFF !important; color: #1A3A6B !important;
    border: none !important; border-radius: 8px !important;
    font-size: 0.88rem !important;
}
[data-testid="stSidebar"] input[type="text"]::placeholder { color: #9CA3AF !important; }
[data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child {
    background: #FFFFFF !important; border-radius: 8px !important; border: none !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] span,
[data-testid="stSidebar"] div[data-baseweb="select"] div { color: #1A3A6B !important; }
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: 100% !important; background: #3B82F6 !important;
    color: #FFFFFF !important; border: none !important;
    border-radius: 8px !important; font-size: 0.85rem !important;
    font-weight: 600 !important; padding: 0.55rem 1rem !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover { background: #2563EB !important; }
.main .block-container { padding: 1.5rem 2rem 3rem 2rem; max-width: 100%; }

/* KPI */
.kpi-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 1rem; }
.kpi-grid-2 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 1.5rem; }
.kpi-card {
    background: white; border-radius: 12px; padding: 1.1rem 1.2rem;
    border-top: 3px solid #1A3A6B; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.kpi-card.green  { border-top-color: #059669; }
.kpi-card.red    { border-top-color: #DC2626; }
.kpi-card.teal   { border-top-color: #0D9488; }
.kpi-card.amber  { border-top-color: #D97706; }
.kpi-card.purple { border-top-color: #7C3AED; }
.kpi-card.gray   { border-top-color: #6B7280; }
.kpi-label { font-size: 0.68rem; color: #9CA3AF; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value { font-size: 1.35rem; font-weight: 700; color: #111827; line-height: 1; margin-bottom: 4px; }
.kpi-value.pos { color: #059669; } .kpi-value.neg { color: #DC2626; }
.kpi-yoy { font-size: 0.75rem; font-weight: 500; }
.kpi-yoy.pos { color: #059669; } .kpi-yoy.neg { color: #DC2626; }
.kpi-sub { font-size: 0.7rem; color: #9CA3AF; margin-top: 2px; }

.section-hd {
    font-size: 0.75rem; font-weight: 700; color: #374151;
    text-transform: uppercase; letter-spacing: 0.07em;
    border-left: 3px solid #1A3A6B; padding-left: 10px;
    margin: 1.8rem 0 0.9rem 0;
}
.section-hd.teal  { border-left-color: #0D9488; }
.section-hd.amber { border-left-color: #D97706; }

.badge { display:inline-block; border-radius:4px; padding:3px 10px; font-size:0.72rem; font-weight:600; margin-right:5px; }
.badge-blue   { background:#DBEAFE; color:#1E40AF; }
.badge-yellow { background:#FEF3C7; color:#92400E; }
.badge-teal   { background:#CCFBF1; color:#0F766E; }
.badge-gray   { background:#F3F4F6; color:#374151; }

.chart-wrap { background: white; border-radius: 14px; padding: 1.4rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1rem; }
.tbl-wrap   { background: white; border-radius: 14px; padding: 1.4rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1rem; }
.tbl-note   { font-size: 0.7rem; color: #9CA3AF; margin-top: 0.8rem; }
.page-title { font-size: 1.5rem; font-weight: 700; color: #111827; margin-bottom: 0.3rem; }
.empty-state { text-align: center; padding: 5rem 2rem; color: #9CA3AF; }
.empty-icon  { font-size: 3rem; margin-bottom: 1rem; }
.empty-title { font-size: 1.1rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem; }
.sidebar-label { font-size: 0.62rem; letter-spacing: 0.1em; color: #7B9EC4; font-weight: 700; margin-bottom: 5px; text-transform: uppercase; }
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
def fetch_fs_raw(api_key, corp_code, year, reprt_code, fs_div):
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

# ── 파싱 유틸 ─────────────────────────────────────────────────
def parse_amount(s):
    if not s or str(s).strip() in ("", "-", "－", "N/A"): return None
    try:
        return round(int(str(s).replace(",", "").strip()) / 1e8, 1)
    except:
        return None

def get_sj_items(fs_list, sj_keyword, exclude=None):
    """특정 재무제표 구분의 항목 추출 (DART 원본 순서 유지)"""
    seen, items = set(), []
    for item in fs_list:
        sj = item.get("sj_nm", "")
        if sj_keyword not in sj: continue
        if exclude and any(ex in sj for ex in exclude): continue
        acnt_nm = item.get("account_nm", "").strip()
        if acnt_nm in seen: continue
        seen.add(acnt_nm)
        items.append({
            "account_nm": acnt_nm,
            "account_id": item.get("account_id", ""),
            "curr":       parse_amount(item.get("thstrm_amount")),
            "prev":       parse_amount(item.get("frmtrm_amount")),
        })
    return items

def get_pl_items(fs_list):
    """손익계산서 항목 - 여러 sj_nm 패턴 대응"""
    # 우선순위: 손익계산서 > 포괄손익계산서 > 기타
    for keyword, excl in [
        ("손 익 계 산 서",   ["포괄"]),
        ("손익계산서",        ["포괄"]),
        ("포괄손익계산서",    []),
        ("포괄 손 익 계 산 서", []),
        ("손익",              []),
    ]:
        items = get_sj_items(fs_list, keyword, excl)
        if items:
            return items
    return []

def get_bs_items(fs_list):
    for keyword in ["재 무 상 태 표", "재무상태표", "대 차 대 조 표", "대차대조표"]:
        items = get_sj_items(fs_list, keyword)
        if items: return items
    return []

def get_cf_items(fs_list):
    for keyword in ["현 금 흐 름 표", "현금흐름표"]:
        items = get_sj_items(fs_list, keyword)
        if items: return items
    return []

def get_dep_from_cf(cf_items):
    """현금흐름표에서 감가상각비 추출"""
    for kw in ["감가상각비", "상각비"]:
        for it in cf_items:
            if kw in it["account_nm"] and "무형" not in it["account_nm"]:
                v = it["curr"]
                if v is not None: return abs(v)
    return 0.0

def find_val(items, *keywords):
    for kw in keywords:
        for it in items:
            if it["account_nm"].strip() == kw and it["curr"] is not None:
                return it["curr"]
    for kw in keywords:
        for it in items:
            if kw in it["account_nm"] and it["curr"] is not None:
                return it["curr"]
    return None

# ── 다연도 테이블 생성 ────────────────────────────────────────
def build_table(years_items, years, item_key="pl"):
    """연도별 항목 → 통합 DataFrame (YoY + CAGR 포함)"""
    latest_yr  = max(years)
    base_items = years_items.get(latest_yr, {}).get(item_key, [])
    if not base_items:
        # fallback: 데이터 있는 연도 기준
        for y in reversed(years):
            base_items = years_items.get(y, {}).get(item_key, [])
            if base_items: break
    acnt_names = [it["account_nm"] for it in base_items]

    yr_maps = {}
    for yr in years:
        items = years_items.get(yr, {}).get(item_key, [])
        yr_maps[yr] = {it["account_nm"]: it["curr"] for it in items}

    records = []
    for acnt in acnt_names:
        row  = {"계정과목": acnt}
        vals = []
        for yr in years:
            v = yr_maps[yr].get(acnt)
            row[str(yr)] = v
            vals.append(v)
        # YoY
        for i in range(1, len(years)):
            cur, prv = vals[i], vals[i-1]
            col = "YoY " + str(years[i])
            if cur is not None and prv and prv != 0:
                row[col] = round((cur - prv) / abs(prv) * 100, 1)
            else:
                row[col] = None
        # CAGR
        n = len(years) - 1
        s, e = vals[0], vals[-1]
        if s and e and s != 0 and n > 0:
            try:    row["CAGR"] = round(((e / s) ** (1/n) - 1) * 100, 1)
            except: row["CAGR"] = None
        else:
            row["CAGR"] = None
        records.append(row)

    return pd.DataFrame(records) if records else pd.DataFrame()

BOLD_KW = ["매출액", "영업수익", "수익(매출액)", "매출총이익", "영업이익",
           "영업이익(손실)", "당기순이익", "당기순이익(손실)", "당기순손실",
           "법인세비용차감전", "자산총계", "부채총계", "자본총계",
           "영업활동", "투자활동", "재무활동", "현금및현금성자산의"]

def style_df(df, years):
    def fv(v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
        return "{:,.1f}".format(v)
    def fp(v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
        arrow = "▲ " if v > 0 else ("▼ " if v < 0 else "")
        return arrow + "{:.1f}%".format(abs(v))

    yr_cols  = [str(y) for y in years]
    yoy_cols = ["YoY " + str(y) for y in years[1:]]

    disp = df.copy()
    for col in disp.columns:
        if col == "계정과목": continue
        if col in yr_cols:
            disp[col] = disp[col].apply(fv)
        else:
            disp[col] = disp[col].apply(fp)
    disp = disp.set_index("계정과목")

    def cc(val):
        if not isinstance(val, str) or val == "—": return "color:#D1D5DB" if val == "—" else ""
        if "▲" in val: return "color:#059669;font-weight:500"
        if "▼" in val: return "color:#DC2626;font-weight:500"
        try:
            num = float(val.replace(",", ""))
            if num < 0: return "color:#DC2626"
        except: pass
        return ""

    def cr(row):
        name = row.name
        if any(kw in name for kw in BOLD_KW):
            return ["font-weight:700;background:#F0F4FF"] * len(row)
        return [""] * len(row)

    return (
        disp.style
        .apply(cr, axis=1)
        .map(cc)
        .set_properties(**{"font-size": "0.82rem", "padding": "5px 10px"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("background", "#1A3A6B"), ("color", "white"),
                ("font-size", "0.73rem"), ("font-weight", "600"),
                ("text-align", "center"), ("padding", "8px 10px"),
                ("white-space", "nowrap"),
            ]},
            {"selector": "th.row_heading", "props": [
                ("text-align", "left"), ("background", "#F8FAFF"),
                ("color", "#374151"), ("font-weight", "500"),
                ("min-width", "180px"),
            ]},
            {"selector": "td", "props": [("text-align", "right")]},
            {"selector": "tr:hover td", "props": [("background", "#EFF6FF !important")]},
        ])
    )

# ── 차트 ─────────────────────────────────────────────────────
def make_summary_chart(kpis, years):
    valid = [y for y in years if kpis.get(y)]
    if not valid: return None
    yrs  = [str(y) for y in valid]
    rev  = [kpis[y].get("rev")  or 0 for y in valid]
    op   = [kpis[y].get("op")   or 0 for y in valid]
    net  = [kpis[y].get("net")  or 0 for y in valid]
    ebi  = [kpis[y].get("ebi")  or 0 for y in valid]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="매출", x=yrs, y=rev, marker_color="#1A3A6B", opacity=0.85,
        marker_line_width=0, text=["{:,.0f}".format(v) for v in rev],
        textposition="outside", textfont=dict(size=10, color="#1A3A6B")))
    fig.add_trace(go.Bar(name="EBITDA", x=yrs, y=ebi, marker_color="#0D9488", opacity=0.85,
        marker_line_width=0, text=["{:,.0f}".format(v) for v in ebi],
        textposition="outside", textfont=dict(size=10, color="#0D9488")))
    fig.add_trace(go.Bar(name="영업이익", x=yrs, y=op, opacity=0.85, marker_line_width=0,
        marker_color=["#DC2626" if v < 0 else "#059669" for v in op],
        text=["{:,.0f}".format(v) for v in op], textposition="outside", textfont=dict(size=10)))
    fig.add_trace(go.Scatter(name="당기순이익", x=yrs, y=net, mode="lines+markers",
        line=dict(color="#D97706", width=2.5, dash="dot"),
        marker=dict(size=9, color="#D97706", line=dict(color="white", width=2))))
    fig.update_layout(
        barmode="group", plot_bgcolor="white", paper_bgcolor="white",
        height=320, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right",
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",", ticksuffix="억", gridcolor="#F3F4F6",
                   zeroline=True, zerolinecolor="#D1D5DB", tickfont=dict(size=11)),
        xaxis=dict(type="category", tickfont=dict(size=12)),
        font=dict(family="Noto Sans KR"))
    return fig

# ── 사이드바 ─────────────────────────────────────────────────
def render_sidebar():
    api_key = get_api_key()
    with st.sidebar:
        st.markdown("""
        <div style='padding:1.4rem 0 1rem 0;border-bottom:1px solid rgba(255,255,255,0.12);margin-bottom:1.1rem;'>
            <div style='font-size:0.6rem;letter-spacing:0.14em;color:#93B4D8;font-weight:700;margin-bottom:4px;'>SK SQUARE</div>
            <div style='font-size:0.98rem;font-weight:700;color:#FFF;line-height:1.35;'>투자분석 재무 대시보드</div>
            <div style='font-size:0.67rem;color:#7B9EC4;margin-top:4px;'>DART OpenAPI 기반</div>
        </div>
        """, unsafe_allow_html=True)

        if not api_key:
            st.markdown("<div style='background:rgba(220,38,38,0.15);border:1px solid rgba(220,38,38,0.3);border-radius:8px;padding:10px;font-size:0.78rem;color:#FCA5A5;'>⚠️ DART_API_KEY 미설정</div>", unsafe_allow_html=True)
            return None

        st.markdown("<div class='sidebar-label'>🔍 Company Search</div>", unsafe_allow_html=True)

        # ── 검색어 입력 ──
        query = st.text_input("", placeholder="회사명 입력 (예: 카카오)",
                              key="query_input", label_visibility="collapsed")

        # 검색 결과
        corp_options = []
        if query and len(query.strip()) >= 1:
            with st.spinner(""):
                corps = load_corp_list(api_key)
            results = search_corp(corps, query.strip())
            if results:
                corp_options = results
                opt_labels = ["(" + ("📈" if v["stock_code"] else "🏢") + ") " + n for n, v in results]
                chosen_idx = st.selectbox("", range(len(opt_labels)),
                    format_func=lambda i: opt_labels[i],
                    key="corp_select", label_visibility="collapsed")
                selected_corp = results[chosen_idx]
            else:
                st.markdown("<div style='font-size:0.78rem;color:#F87171;padding:4px 0;'>검색 결과 없음</div>", unsafe_allow_html=True)
                selected_corp = None
        else:
            selected_corp = None

        st.markdown("<div class='sidebar-label' style='margin-top:0.9rem;'>⚙️ Settings</div>", unsafe_allow_html=True)

        fs_div_label = st.selectbox("", ["연결 (CFS)", "개별 (OFS)"],
                                    key="fs_div_sel", label_visibility="collapsed")
        fs_div = "CFS" if "CFS" in fs_div_label else "OFS"

        year_opts = [2025, 2024, 2023, 2022, 2021, 2020]
        sel_years = st.multiselect("", year_opts, default=[2022, 2023, 2024, 2025],
                                   key="year_sel", label_visibility="collapsed")

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        search_btn = st.button("📡  재무제표 조회", use_container_width=True)

        if search_btn:
            if not selected_corp:
                st.error("회사를 선택해주세요.")
            elif not sel_years:
                st.error("연도를 선택해주세요.")
            else:
                corp_name, corp_info = selected_corp
                # ── 핵심: 새 검색 시 기존 캐시 완전 초기화 ──
                st.session_state.search_params = {
                    "corp_name":  corp_name,
                    "corp_code":  corp_info["corp_code"],
                    "stock_code": corp_info["stock_code"],
                    "fs_div":     fs_div,
                    "years":      sorted(sel_years),
                }
                st.session_state.fs_cache = {}   # 데이터 캐시 초기화
                st.rerun()

        st.markdown("""
        <div style='margin-top:1.5rem;padding-top:0.8rem;border-top:1px solid rgba(255,255,255,0.1);
        font-size:0.64rem;color:#4A6FA5;line-height:1.8;'>
        📌 사업보고서(연간) 기준<br>📌 단위: 억원<br>📌 BS / PL / CF 전체 표시
        </div>""", unsafe_allow_html=True)

    return api_key

# ── KPI 카드 HTML ─────────────────────────────────────────────
def make_kpi_card(label, val, yoy=None, sub=None, color="blue"):
    val_str = ("{:,.0f}억".format(val)) if val is not None else "—"
    val_cls = "neg" if (val is not None and val < 0) else "pos"
    yoy_html = ""
    if yoy is not None:
        arrow   = "▲" if yoy > 0 else ("▼" if yoy < 0 else "─")
        yoy_cls = "pos" if yoy > 0 else ("neg" if yoy < 0 else "")
        yoy_html = "<div class='kpi-yoy " + yoy_cls + "'>" + arrow + " " + "{:.1f}".format(abs(yoy)) + "% YoY</div>"
    sub_html = ("<div class='kpi-sub'>" + sub + "</div>") if sub else ""
    return (
        "<div class='kpi-card " + color + "'>"
        "<div class='kpi-label'>" + label + "</div>"
        "<div class='kpi-value " + val_cls + "'>" + val_str + "</div>"
        + yoy_html + sub_html +
        "</div>"
    )

def yoy_calc(cur, prv):
    if cur is None or prv is None or prv == 0: return None
    return round((cur - prv) / abs(prv) * 100, 1)

def pct_fmt(v, denom):
    if v is None or denom is None or denom == 0: return None
    return round(v / denom * 100, 1)

# ── 메인 렌더링 ───────────────────────────────────────────────
def render_main(api_key):
    params = st.session_state.get("search_params")
    if not params:
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-icon'>📊</div>
            <div class='empty-title'>SK Square 재무 분석 대시보드</div>
            <div class='empty-sub'>좌측에서 회사명을 검색하고 조회 버튼을 눌러주세요</div>
        </div>""", unsafe_allow_html=True)
        return

    corp_name = params["corp_name"]
    corp_code = params["corp_code"]
    fs_div    = params["fs_div"]
    years     = params["years"]

    # ── 데이터 로드 (session cache 사용) ──
    cache_key = corp_code + "_" + fs_div + "_" + "_".join(map(str, years))
    fs_cache  = st.session_state.get("fs_cache", {})

    if cache_key not in fs_cache:
        years_data = {}
        prog = st.progress(0, text=corp_name + " 데이터 로딩 중...")
        for i, yr in enumerate(years):
            prog.progress((i+1)/len(years), text=str(yr) + "년 조회 중...")
            raw = fetch_fs_raw(api_key, corp_code, yr, "11011", fs_div)
            # 연결 없으면 개별로 fallback
            if not raw and fs_div == "CFS":
                raw = fetch_fs_raw(api_key, corp_code, yr, "11011", "OFS")
            pl = get_pl_items(raw)
            bs = get_bs_items(raw)
            cf = get_cf_items(raw)
            dep = get_dep_from_cf(cf)
            years_data[yr] = {"pl": pl, "bs": bs, "cf": cf, "dep": dep, "raw": raw}
        prog.empty()
        fs_cache[cache_key] = years_data
        st.session_state.fs_cache = fs_cache
    else:
        years_data = fs_cache[cache_key]

    # ── KPI 추출 ──
    kpis = {}
    for yr in years:
        pl  = years_data[yr]["pl"]
        bs  = years_data[yr]["bs"]
        dep = years_data[yr]["dep"]
        rev = find_val(pl, "매출액", "영업수익", "수익(매출액)", "매출")
        op  = find_val(pl, "영업이익", "영업이익(손실)", "영업손익")
        net = find_val(pl, "당기순이익", "당기순이익(손실)", "당기순손실")
        ebt = find_val(pl, "법인세비용차감전순이익", "법인세비용차감전순이익(손실)", "법인세비용차감전순손실")
        gp  = find_val(pl, "매출총이익", "매출총손익")
        ta  = find_val(bs, "자산총계")
        tl  = find_val(bs, "부채총계")
        eq  = find_val(bs, "자본총계")
        ebi = (op + dep) if op is not None else None
        kpis[yr] = {"rev": rev, "op": op, "net": net, "ebt": ebt, "ebi": ebi,
                    "dep": dep, "gp": gp, "ta": ta, "tl": tl, "eq": eq}

    latest = years[-1]
    prev   = years[-2] if len(years) >= 2 else None
    kl     = kpis.get(latest, {})
    kp     = kpis.get(prev,   {}) if prev else {}

    rev_v  = kl.get("rev");  rev_p  = kp.get("rev")
    op_v   = kl.get("op");   op_p   = kp.get("op")
    net_v  = kl.get("net");  net_p  = kp.get("net")
    ebi_v  = kl.get("ebi");  ebi_p  = (kp.get("ebi"))
    ebt_v  = kl.get("ebt");  ebt_p  = kp.get("ebt")
    gp_v   = kl.get("gp");   gp_p   = kp.get("gp")
    ta_v   = kl.get("ta");   ta_p   = kp.get("ta")
    tl_v   = kl.get("tl")
    eq_v   = kl.get("eq");   eq_p   = kp.get("eq")
    dep_v  = kl.get("dep", 0) or 0

    # 파생 지표
    op_margin   = pct_fmt(op_v,  rev_v)
    gp_margin   = pct_fmt(gp_v,  rev_v)
    net_margin  = pct_fmt(net_v, rev_v)
    ebi_margin  = pct_fmt(ebi_v, rev_v)
    de_ratio    = round(tl_v / eq_v * 100, 1) if (tl_v and eq_v and eq_v != 0) else None
    roe         = pct_fmt(net_v, eq_v)
    roa         = pct_fmt(net_v, ta_v)
    asset_turn  = round(rev_v / ta_v, 2) if (rev_v and ta_v and ta_v != 0) else None

    # ── 헤더 ──
    listing   = "상장 📈" if params.get("stock_code") else "비상장 🏢"
    std_label = "K-IFRS 연결" if fs_div == "CFS" else "K-GAAP 개별"
    yr_range  = str(min(years)) + "~" + str(max(years))

    st.markdown("<div class='page-title'>" + corp_name + "</div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='badge badge-blue'>" + listing + "</span>"
        "<span class='badge badge-teal'>" + std_label + "</span>"
        "<span class='badge badge-gray'>사업보고서</span>"
        "<span class='badge badge-gray'>" + yr_range + "</span>",
        unsafe_allow_html=True)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Row 1: 핵심 손익 지표 (6개) ──
    st.markdown("<div class='section-hd'>핵심 손익 지표</div>", unsafe_allow_html=True)
    row1 = "<div class='kpi-grid'>"
    row1 += make_kpi_card("매출 " + str(latest),      rev_v, yoy_calc(rev_v, rev_p), sub="억원", color="blue")
    row1 += make_kpi_card("매출총이익 " + str(latest), gp_v,  yoy_calc(gp_v,  gp_p),
                          sub=("GP margin " + "{:.1f}".format(gp_margin) + "%") if gp_margin else None, color="blue")
    row1 += make_kpi_card("영업이익 " + str(latest),  op_v,  yoy_calc(op_v,  op_p),
                          sub=("OPM " + "{:.1f}".format(op_margin) + "%") if op_margin else None,
                          color="green" if (op_v and op_v >= 0) else "red")
    row1 += make_kpi_card("EBITDA " + str(latest),    ebi_v, yoy_calc(ebi_v, ebi_p),
                          sub=("margin " + "{:.1f}".format(ebi_margin) + "%") if ebi_margin else None, color="teal")
    row1 += make_kpi_card("세전이익 " + str(latest),  ebt_v, yoy_calc(ebt_v, ebt_p), color="amber")
    row1 += make_kpi_card("당기순이익 " + str(latest), net_v, yoy_calc(net_v, net_p),
                          sub=("NPM " + "{:.1f}".format(net_margin) + "%") if net_margin else None,
                          color="green" if (net_v and net_v >= 0) else "red")
    row1 += "</div>"
    st.markdown(row1, unsafe_allow_html=True)

    # ── Row 2: 재무건전성 지표 (4개) ──
    st.markdown("<div class='section-hd'>재무건전성 지표</div>", unsafe_allow_html=True)
    row2 = "<div class='kpi-grid-2'>"
    row2 += make_kpi_card("총자산 " + str(latest),  ta_v,  yoy_calc(ta_v,  ta_p),  color="gray")
    row2 += make_kpi_card("자본총계 " + str(latest), eq_v,  yoy_calc(eq_v,  eq_p),  color="gray")
    row2 += make_kpi_card("부채비율 " + str(latest),
                          de_ratio, None,
                          sub="부채/자본 ×100",
                          color="red" if (de_ratio and de_ratio > 200) else "gray")
    row2 += make_kpi_card("ROE " + str(latest),
                          None if roe is None else roe,
                          None,
                          sub=("순이익/자본 " + "{:.1f}".format(roe) + "%") if roe else None,
                          color="green" if (roe and roe > 0) else "red" if (roe and roe < 0) else "gray")
    row2 += "</div>"
    # 부채비율/ROE는 % 단위이므로 카드 값 표시 다르게 처리
    # 직접 HTML로 재구성
    de_str  = ("{:.1f}%".format(de_ratio)) if de_ratio is not None else "—"
    roe_str = ("{:.1f}%".format(roe))      if roe is not None      else "—"
    roa_str = ("{:.1f}%".format(roa))      if roa is not None      else "—"
    at_str  = ("{:.2f}x".format(asset_turn)) if asset_turn is not None else "—"
    de_color  = "red" if (de_ratio and de_ratio > 200) else "gray"
    roe_color = "green" if (roe and roe > 0) else ("red" if (roe and roe < 0) else "gray")

    row2b = "<div class='kpi-grid-2'>"
    row2b += make_kpi_card("총자산 " + str(latest), ta_v, yoy_calc(ta_v, ta_p), color="gray")
    row2b += make_kpi_card("자본총계 " + str(latest), eq_v, yoy_calc(eq_v, eq_p), color="gray")
    # 부채비율 카드 직접
    row2b += (
        "<div class='kpi-card " + de_color + "'>"
        "<div class='kpi-label'>부채비율 " + str(latest) + "</div>"
        "<div class='kpi-value'>" + de_str + "</div>"
        "<div class='kpi-sub'>부채/자본 × 100</div>"
        "</div>"
    )
    row2b += (
        "<div class='kpi-card " + roe_color + "'>"
        "<div class='kpi-label'>ROE / ROA " + str(latest) + "</div>"
        "<div class='kpi-value'>" + roe_str + "</div>"
        "<div class='kpi-sub'>ROA " + roa_str + " | 자산회전율 " + at_str + "</div>"
        "</div>"
    )
    row2b += "</div>"
    st.markdown(row2b, unsafe_allow_html=True)

    # ── 차트 ──
    st.markdown("<div class='section-hd'>수익성 추이 | 단위: 억원</div>", unsafe_allow_html=True)
    fig = make_summary_chart(kpis, years)
    if fig:
        st.markdown("<div class='chart-wrap'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 재무제표 테이블 3종 ──
    sections = [
        ("pl", "손익계산서 (P&L) | 단위: 억원 · DART 원본 계정", "section-hd"),
        ("bs", "재무상태표 (B/S) | 단위: 억원 · DART 원본 계정", "section-hd teal"),
        ("cf", "현금흐름표 (C/F) | 단위: 억원 · DART 원본 계정", "section-hd amber"),
    ]

    for key, title, hd_cls in sections:
        st.markdown("<div class='" + hd_cls + "'>" + title + "</div>", unsafe_allow_html=True)
        df = build_table(years_data, years, item_key=key)
        if df.empty:
            st.info(key.upper() + " 데이터를 불러오지 못했습니다.")
            continue
        yr_cols  = [str(y) for y in years]
        yoy_cols = ["YoY " + str(y) for y in years[1:]]
        cols     = ["계정과목"] + yr_cols + yoy_cols + ["CAGR"]
        df       = df[[c for c in cols if c in df.columns]]
        st.markdown("<div class='tbl-wrap'>", unsafe_allow_html=True)
        h = min(max(len(df) * 35 + 60, 250), 650)
        st.dataframe(style_df(df, years), use_container_width=True, height=h)
        std = "연결" if fs_div == "CFS" else "개별"
        st.markdown(
            "<p class='tbl-note'>출처: DART OpenAPI " + std + " " + key.upper() +
            " | YoY: 전년 대비 증감률 | CAGR: " + str(min(years)) + "→" + str(max(years)) + "</p>",
            unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ── 앱 실행 ───────────────────────────────────────────────────
def main():
    for key in ["search_params", "fs_cache"]:
        if key not in st.session_state:
            st.session_state[key] = None if key == "search_params" else {}

    api_key = render_sidebar()
    if api_key:
        render_main(api_key)

if __name__ == "__main__":
    main()
