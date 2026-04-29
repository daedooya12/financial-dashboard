import streamlit as st
import json, os, glob, io, zipfile, requests
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
html, body, [class*="css"], .stApp { font-family:'Noto Sans KR',sans-serif; background:#F4F6FA; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0F2447 0%,#1A3A6B 60%,#1e4d8c 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color:#E8EEF8 !important; }

/* 라디오 */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display:block !important; width:100% !important;
    padding:0.5rem 0.9rem !important; border-radius:8px !important;
    border:1px solid rgba(255,255,255,0.15) !important;
    background:rgba(255,255,255,0.07) !important;
    color:#C8D8F0 !important; font-size:0.85rem !important;
    margin-bottom:3px !important; cursor:pointer !important; transition:all 0.2s !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background:rgba(255,255,255,0.18) !important; color:#FFFFFF !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] { display:none !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    color:inherit !important; font-size:0.85rem !important;
}

/* 사이드바 입력창 */
[data-testid="stSidebar"] input[type="text"] {
    background:rgba(255,255,255,0.1) !important;
    color:#FFFFFF !important; border:1px solid rgba(255,255,255,0.2) !important;
    border-radius:6px !important;
}
[data-testid="stSidebar"] input[type="text"]::placeholder { color:rgba(255,255,255,0.4) !important; }
[data-testid="stSidebar"] .stTextInput label { color:#93B4D8 !important; font-size:0.72rem !important; }
[data-testid="stSidebar"] .stSelectbox label { color:#93B4D8 !important; font-size:0.72rem !important; }
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width:100%; background:rgba(255,255,255,0.07) !important;
    color:#C8D8F0 !important; border:1px solid rgba(255,255,255,0.15) !important;
    border-radius:8px !important; font-size:0.85rem !important;
    transition:all 0.2s !important; margin-bottom:4px !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background:rgba(255,255,255,0.2) !important; color:#FFFFFF !important;
}

/* 메인 */
.main .block-container { padding:1.5rem 2rem 2rem 2rem; max-width:100%; }
.kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:1.5rem; }
.kpi-card { background:white; border-radius:12px; padding:1.2rem 1.4rem; border-top:4px solid #1A3A6B; box-shadow:0 1px 6px rgba(0,0,0,0.06); }
.kpi-card.green { border-top-color:#1A7F4B; }
.kpi-card.red   { border-top-color:#C0392B; }
.kpi-card.blue  { border-top-color:#1A3A6B; }
.kpi-label { font-size:0.72rem; color:#6B7280; font-weight:500; letter-spacing:0.04em; text-transform:uppercase; margin-bottom:6px; }
.kpi-value { font-size:1.55rem; font-weight:700; color:#111827; line-height:1.1; }
.kpi-value.pos { color:#1A7F4B; } .kpi-value.neg { color:#C0392B; }
.kpi-sub { font-size:0.75rem; color:#9CA3AF; margin-top:5px; }
.section-hd { font-size:0.8rem; font-weight:600; color:#374151; text-transform:uppercase; letter-spacing:0.06em; border-left:3px solid #1A3A6B; padding-left:10px; margin:1.6rem 0 0.8rem 0; }
.hl-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin-bottom:1rem; }
.hl-item { background:white; border-radius:8px; padding:0.7rem 1rem; font-size:0.82rem; color:#374151; border-left:3px solid #3B82F6; box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.badge { display:inline-block; border-radius:4px; padding:2px 9px; font-size:0.72rem; font-weight:500; margin-right:5px; }
.badge-blue   { background:#DBEAFE; color:#1E40AF; }
.badge-yellow { background:#FEF3C7; color:#92400E; }
.badge-gray   { background:#F3F4F6; color:#374151; }
.badge-green  { background:#DCFCE7; color:#166534; }
.src-note { font-size:0.7rem; color:#9CA3AF; margin-top:0.5rem; }
.chart-card { background:white; border-radius:12px; padding:1.2rem 1.2rem 0.5rem 1.2rem; box-shadow:0 1px 6px rgba(0,0,0,0.06); margin-bottom:1rem; }
.tbl-wrap { background:white; border-radius:12px; padding:1.2rem; box-shadow:0 1px 6px rgba(0,0,0,0.06); }
.divider { border:none; border-top:1px solid rgba(255,255,255,0.1); margin:1rem 0; }
</style>
""", unsafe_allow_html=True)


# ── DART API ─────────────────────────────────────────────────
DART_BASE = "https://opendart.fss.or.kr/api"

def get_api_key():
    try:
        return st.secrets["DART_API_KEY"]
    except:
        return os.environ.get("DART_API_KEY", "")

@st.cache_data(ttl=86400, show_spinner=False)
def load_corp_list(api_key):
    try:
        r = requests.get(f"{DART_BASE}/corpCode.xml", params={"crtfc_key": api_key}, timeout=30)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        root = ET.fromstring(z.read("CORPCODE.xml"))
        corps = {}
        for item in root.findall("list"):
            name = item.findtext("corp_name", "").strip()
            code = item.findtext("corp_code", "").strip()
            stock = item.findtext("stock_code", "").strip()
            if name and code:
                corps[name] = {"corp_code": code, "stock_code": stock}
        return corps
    except:
        return {}

def search_corp(corps, query):
    q = query.strip()
    if not q: return []
    exact = [(k, v) for k, v in corps.items() if k == q]
    partial = [(k, v) for k, v in corps.items() if q in k and k != q]
    return (exact + partial)[:8]

def fetch_fs(api_key, corp_code, year, fs_div="CFS"):
    try:
        r = requests.get(f"{DART_BASE}/fnlttSinglAcntAll.json", params={
            "crtfc_key": api_key, "corp_code": corp_code,
            "bsns_year": str(year), "reprt_code": "11011", "fs_div": fs_div
        }, timeout=30)
        d = r.json()
        if d.get("status") == "000":
            return d.get("list", []), None
        return None, d.get("message", "조회 실패")
    except Exception as e:
        return None, str(e)

ACNT_MAP = {
    "매출액": "revenue", "영업수익": "revenue", "수익(매출액)": "revenue",
    "영업이익": "operating_income", "영업이익(손실)": "operating_income",
    "법인세비용차감전순이익": "ebt", "법인세비용차감전순이익(손실)": "ebt",
    "법인세비용차감전순손실": "ebt",
    "당기순이익": "net_income", "당기순이익(손실)": "net_income", "당기순손실": "net_income",
    "법인세비용": "tax",
}

def parse_won(s):
    if not s or str(s).strip() in ("", "-", "－"): return None
    try: return round(int(str(s).replace(",", "")) / 1e8)
    except: return None

def extract_pl(fs_list):
    result = {}
    for item in fs_list:
        sj = item.get("sj_nm", "")
        if "손익" not in sj and "포괄" not in sj: continue
        acnt = item.get("account_nm", "").strip()
        key  = ACNT_MAP.get(acnt)
        if key and key not in result:
            amt = parse_won(item.get("thstrm_amount"))
            if amt is not None: result[key] = amt
    return result

def extract_dep(fs_list):
    """현금흐름표에서 감가상각비 추출"""
    for item in fs_list:
        acnt = item.get("account_nm", "").strip()
        if "감가상각" in acnt and "무형" not in acnt:
            amt = parse_won(item.get("thstrm_amount"))
            if amt is not None: return abs(amt)
    return 0

def build_json(corp_name, corp_code, years, fs_div, api_key, sector="—", listing="비상장"):
    all_pl, all_dep = {}, {}
    errors = []
    prog = st.progress(0, text="DART 조회 중...")
    for i, y in enumerate(years):
        prog.progress((i+1)/len(years), text=f"{y}년 데이터 조회 중...")
        fs, err = fetch_fs(api_key, corp_code, y, fs_div)
        if err or not fs:
            # 연결 실패 → 개별 재시도
            fs, err2 = fetch_fs(api_key, corp_code, y, "OFS" if fs_div == "CFS" else "CFS")
            if err2 or not fs:
                errors.append(f"{y}년: {err}")
                all_pl[y] = {}
                all_dep[y] = 0
                continue
        all_pl[y]  = extract_pl(fs)
        all_dep[y] = extract_dep(fs)
    prog.empty()

    def get(y, k): return all_pl.get(y, {}).get(k, 0) or 0

    rev  = [get(y, "revenue")          for y in years]
    op   = [get(y, "operating_income") for y in years]
    ebt  = [get(y, "ebt")              for y in years]
    net  = [get(y, "net_income")       for y in years]
    dep  = [all_dep.get(y, 0)          for y in years]
    cost = [r - o for r, o in zip(rev, op)]
    nop  = [e - o for e, o in zip(ebt, op)]
    op_m = [round(o/r*100,1) if r else 0 for o,r in zip(op, rev)]
    net_m= [round(n/r*100,1) if r else 0 for n,r in zip(net, rev)]

    n = len(years) - 1
    def cagr(s, e):
        if not s or not e: return 0
        try: return round(((e/s)**(1/n)-1)*100, 1)
        except: return 0

    return {
        "company_name": corp_name, "company_name_en": corp_name,
        "sector": sector, "listing_status": listing,
        "fiscal_year_end": "12월", "currency": "KRW", "unit": "억원",
        "standard": "K-IFRS 연결" if fs_div == "CFS" else "K-GAAP 개별",
        "source": "DART OpenAPI",
        "dart_links": {},
        "years": [str(y) for y in years],
        "income_statement": {
            "revenue": rev, "operating_cost": cost,
            "operating_income": op, "non_operating": nop,
            "ebt": ebt, "net_income": net,
        },
        "cost_breakdown": {
            "service_cost": [0]*len(years), "employee_cost": [0]*len(years),
            "commission_fee": [0]*len(years), "depreciation": dep, "advertising": [0]*len(years),
        },
        "margins": {"operating_margin": op_m, "net_margin": net_m},
        "cagr": {
            "period": f"{years[0]}→{years[-1]}",
            "revenue": cagr(rev[0], rev[-1]),
            "operating_cost": cagr(cost[0], cost[-1]),
            "employee_cost": 0, "depreciation": cagr(dep[0], dep[-1]) if dep[0] else 0, "advertising": 0,
        },
        "yoy_growth": {"revenue": [None] + [
            round((rev[i]-rev[i-1])/abs(rev[i-1])*100,1) if rev[i-1] else None
            for i in range(1, len(years))
        ]},
        "key_highlights": [
            f"DART OpenAPI 자동 수집 ({years[0]}~{years[-1]})",
            f"매출 CAGR: {cagr(rev[0], rev[-1]):+.1f}% ({years[0]}→{years[-1]})",
            f"최근 영업이익률: {op_m[-1]:.1f}% ({years[-1]})",
            f"최근 순이익: {net[-1]:,}억원 ({years[-1]})",
        ]
    }, errors


# ── 데이터 로드 ───────────────────────────────────────────────
@st.cache_data
def load_all_companies():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    companies = {}
    for f in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        with open(f, encoding="utf-8") as fp:
            d = json.load(fp)
        companies[os.path.basename(f).replace(".json", "")] = d
    return companies


# ── 유틸 ─────────────────────────────────────────────────────
def fmt(v):
    if v is None: return "—"
    return f"{v:,.0f}"

def fmtp(v, d=1):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    return f"{'+' if v>=0 else ''}{v:.{d}f}%"

def cagr_str(arr, n):
    try:
        s, e = arr[0], arr[-1]
        if not s or not e: return "—"
        v = ((e/s)**(1/n)-1)*100
        return f"{'+' if v>=0 else ''}{v:.1f}%"
    except: return "—"

def ebitda(inc, cb):
    return [inc["operating_income"][i] + cb["depreciation"][i] for i in range(len(inc["operating_income"]))]

def yoy_list(arr):
    r = [None]
    for i in range(1, len(arr)):
        p = arr[i-1]
        r.append(round((arr[i]-p)/abs(p)*100,1) if p else None)
    return r

COLORS = {
    "navy":"#1A3A6B","blue":"#3B82F6","teal":"#0D9488",
    "red":"#EF4444","amber":"#F59E0B","green":"#16A34A","lb":"#93C5FD"
}


# ── 차트 ─────────────────────────────────────────────────────
def chart_revenue(data):
    y = data["years"]; inc = data["income_statement"]
    rev, op, net = inc["revenue"], inc["operating_income"], inc["net_income"]
    ebi = ebitda(inc, data["cost_breakdown"])
    fig = go.Figure()
    for name, vals, color, txt_color in [
        ("영업수익", rev, COLORS["navy"], COLORS["navy"]),
        ("EBITDA",   ebi, COLORS["teal"], COLORS["teal"]),
        ("영업손익", op,  None,           None),
    ]:
        mc = [COLORS["red"] if v<0 else COLORS["green"] for v in vals] if color is None else color
        fig.add_trace(go.Bar(name=name, x=y, y=vals, marker_color=mc, marker_line_width=0,
            opacity=0.88, text=[f"{v:,}" for v in vals], textposition="outside",
            textfont=dict(size=10, color=txt_color or "#555")))
    fig.add_trace(go.Scatter(name="당기순이익", x=y, y=net, mode="lines+markers",
        line=dict(color=COLORS["amber"], width=2.5, dash="dot"),
        marker=dict(size=9, color=COLORS["amber"], line=dict(color="white", width=2))))
    fig.update_layout(barmode="group", plot_bgcolor="white", paper_bgcolor="white",
        height=360, margin=dict(l=0,r=0,t=20,b=0),
        legend=dict(orientation="h",y=1.01,x=1,xanchor="right",font=dict(size=11),bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",",ticksuffix="억",gridcolor="#F3F4F6",zeroline=True,zerolinecolor="#D1D5DB"),
        xaxis=dict(type="category"), font=dict(family="Noto Sans KR"))
    return fig

def chart_margin(data):
    y = data["years"]; inc = data["income_statement"]
    op_m = data["margins"]["operating_margin"]; net_m = data["margins"]["net_margin"]
    ebi  = ebitda(inc, data["cost_breakdown"]); rev = inc["revenue"]
    ebi_m = [round(e/r*100,1) if r else 0 for e,r in zip(ebi, rev)]
    fig = go.Figure()
    for name, vals, color, pos, fill in [
        ("EBITDA margin", ebi_m, COLORS["teal"], "top center", "tozeroy"),
        ("영업이익률", op_m, COLORS["navy"], "bottom center", None),
        ("순이익률",   net_m, COLORS["amber"], "top center", None),
    ]:
        kwargs = dict(fill=fill, fillcolor="rgba(13,148,136,0.07)") if fill else {}
        fig.add_trace(go.Scatter(name=name, x=y, y=vals, mode="lines+markers+text",
            line=dict(color=color, width=2.5, dash="dash" if name=="순이익률" else "solid"),
            marker=dict(size=8, color=color, line=dict(color="white", width=2)),
            text=[f"{v:.1f}%" for v in vals], textposition=pos,
            textfont=dict(size=10, color=color), **kwargs))
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=320,
        margin=dict(l=0,r=0,t=20,b=0),
        legend=dict(orientation="h",y=1.01,x=1,xanchor="right",font=dict(size=11),bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(ticksuffix="%",gridcolor="#F3F4F6",zeroline=True,zerolinecolor="#D1D5DB"),
        xaxis=dict(type="category"), font=dict(family="Noto Sans KR"))
    return fig

def chart_cost(data):
    y = data["years"]; cb = data["cost_breakdown"]
    keys   = ["service_cost","employee_cost","commission_fee","depreciation","advertising"]
    labels = ["용역원가","종업원급여","지급수수료","감가상각비","광고선전비"]
    colors = [COLORS["navy"],COLORS["blue"],COLORS["teal"],COLORS["lb"],COLORS["amber"]]
    fig = go.Figure()
    for k, label, color in zip(keys, labels, colors):
        fig.add_trace(go.Bar(name=label, x=y, y=cb[k], marker_color=color, marker_line_width=0))
    fig.update_layout(barmode="stack", plot_bgcolor="white", paper_bgcolor="white", height=320,
        margin=dict(l=0,r=0,t=20,b=0),
        legend=dict(orientation="h",y=1.01,x=1,xanchor="right",font=dict(size=11),bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",",ticksuffix="억",gridcolor="#F3F4F6"),
        xaxis=dict(type="category"), font=dict(family="Noto Sans KR"))
    return fig


# ── 손익 테이블 ───────────────────────────────────────────────
def pl_table(data):
    years = data["years"]; inc = data["income_statement"]
    cb = data["cost_breakdown"]; mar = data["margins"]
    n = len(years)-1
    ebi  = ebitda(inc, cb)
    rev  = inc["revenue"]
    ebi_m = [round(e/r*100,1) if r else 0 for e,r in zip(ebi,rev)]

    rows = [
        ("영업수익",            inc["revenue"],           False, True,  False),
        ("  용역원가",          cb["service_cost"],       False, False, True),
        ("  종업원급여",        cb["employee_cost"],      False, False, True),
        ("  지급수수료",        cb["commission_fee"],     False, False, True),
        ("  감가상각비",        cb["depreciation"],       False, False, True),
        ("  광고선전비",        cb["advertising"],        False, False, True),
        ("영업비용 합계",       inc["operating_cost"],    False, False, False),
        ("영업손익",            inc["operating_income"],  False, True,  False),
        ("  영업이익률 (%)",    mar["operating_margin"],  True,  False, True),
        ("EBITDA",              ebi,                      False, True,  False),
        ("  EBITDA margin (%)", ebi_m,                    True,  False, True),
        ("영업외손익",          inc["non_operating"],     False, False, False),
        ("법인세차감전손익",    inc["ebt"],               False, True,  False),
        ("당기순이익(손실)",    inc["net_income"],        False, True,  False),
        ("  순이익률 (%)",      mar["net_margin"],        True,  False, True),
    ]
    col_yoy  = [f"YoY {y}" for y in years[1:]]
    cagr_col = f"CAGR ({years[0]}→{years[-1]})"
    records, bolds, subs = [], [], []

    for label, vals, is_pct, bold, sub in rows:
        row = {"항목": label}
        for i, y in enumerate(years):
            row[y] = fmtp(vals[i]) if is_pct else fmt(vals[i])
        if is_pct:
            for cy in col_yoy: row[cy] = "—"
            row[cagr_col] = "—"
        else:
            yv = yoy_list(vals)
            for i, cy in enumerate(col_yoy): row[cy] = fmtp(yv[i+1])
            row[cagr_col] = cagr_str(vals, n)
        records.append(row); bolds.append(bold); subs.append(sub)

    df = pd.DataFrame(records).set_index("항목")

    def sc(v):
        if not isinstance(v, str) or v=="—": return "color:#D1D5DB" if v=="—" else ""
        s = v.strip()
        if s.startswith("-") or (s.startswith("(") and ")" in s): return "color:#C0392B;font-weight:500"
        if s.startswith("+"): return "color:#1A7F4B;font-weight:500"
        return ""

    def sr(row):
        i = list(df.index).index(row.name)
        if bolds[i]: return ["font-weight:600;background:#F0F4FF;color:#111827"]*len(row)
        if subs[i]:  return ["color:#6B7280;font-size:0.85em"]*len(row)
        return [""]*len(row)

    return df.style.apply(sr, axis=1).map(sc)


# ── 회사 페이지 렌더링 ────────────────────────────────────────
def render_company(data):
    years = data["years"]; inc = data["income_statement"]
    cb = data["cost_breakdown"]; mar = data["margins"]
    ebi = ebitda(inc, cb); rev = inc["revenue"]

    rl, rp = rev[-1], rev[-2]
    rev_yoy = (rl-rp)/abs(rp)*100 if rp else 0
    op_l  = inc["operating_income"][-1]
    net_l = inc["net_income"][-1]
    ebi_l = ebi[-1]
    ebi_m = round(ebi_l/rl*100,1) if rl else 0
    ly    = years[-1]
    dart_link = data.get("dart_links",{}).get(ly,"#")

    # 헤더
    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown(f"## {data['company_name']}")
        source_badge = f"<span class='badge badge-green'>DART API</span>" if data.get("source") == "DART OpenAPI" else ""
        st.markdown(
            f"<span class='badge badge-blue'>{data['sector']}</span>"
            f"<span class='badge badge-yellow'>{data['listing_status']}</span>"
            f"<span class='badge badge-gray'>{data['standard']}</span>"
            f"{source_badge}", unsafe_allow_html=True)
    with c2:
        if dart_link != "#":
            st.markdown(f"<div style='text-align:right;margin-top:1.2rem;'>"
                f"<a href='{dart_link}' target='_blank' style='font-size:0.78rem;color:#3B82F6;text-decoration:none;'>"
                f"📎 DART 원문 ({ly})</a></div>", unsafe_allow_html=True)

    # KPI
    def kc(v): return "green" if v>=0 else "red"
    kpis = [
        ("매출 "+ly,       fmt(rl)+"억",  f"YoY {rev_yoy:+.1f}%",                        "blue" if rev_yoy>=0 else "red"),
        ("영업손익 "+ly,   fmt(op_l)+"억", f"영업이익률 {mar['operating_margin'][-1]:.1f}%", kc(op_l)),
        ("EBITDA "+ly,     fmt(ebi_l)+"억",f"EBITDA margin {ebi_m:.1f}%",                kc(ebi_l)),
        ("당기순이익 "+ly, fmt(net_l)+"억",f"순이익률 {mar['net_margin'][-1]:.1f}%",       kc(net_l)),
    ]
    html = "<div class='kpi-grid'>"
    for label, val, sub, color in kpis:
        neg = val.startswith("-") or (val.startswith("(") and ")" in val)
        html += f"<div class='kpi-card {color}'><div class='kpi-label'>{label}</div><div class='kpi-value {'neg' if neg else 'pos'}'>{val}</div><div class='kpi-sub'>{sub}</div></div>"
    st.markdown(html+"</div>", unsafe_allow_html=True)

    # 차트
    st.markdown("<div class='section-hd'>Performance Summary</div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📊 수익 & 손익 추이","📉 이익률 추이","🗂 비용 구조"])
    with t1:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(chart_revenue(data), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with t2:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(chart_margin(data), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with t3:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(chart_cost(data), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 하이라이트
    st.markdown("<div class='section-hd'>Key Highlights</div>", unsafe_allow_html=True)
    hl_html = "<div class='hl-grid'>"
    for hl in data.get("key_highlights", []):
        hl_html += f"<div class='hl-item'>• {hl}</div>"
    st.markdown(hl_html+"</div>", unsafe_allow_html=True)

    # 테이블
    st.markdown("<div class='section-hd'>손익계산서 상세 | 단위: 억원</div>", unsafe_allow_html=True)
    st.markdown("<div class='tbl-wrap'>", unsafe_allow_html=True)
    st.dataframe(pl_table(data), use_container_width=True, height=545)
    st.markdown(f"<p class='src-note'>출처: {data['source']} | 단위: {data['unit']} | 기준: {data['standard']} | EBITDA = 영업손익 + 감가상각비</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── 사이드바 ─────────────────────────────────────────────────
def render_sidebar(companies):
    api_key = get_api_key()

    with st.sidebar:
        # 헤더
        st.markdown("""
        <div style='padding:1.5rem 0 1rem 0;border-bottom:1px solid rgba(255,255,255,0.12);margin-bottom:1rem;'>
            <div style='font-size:0.65rem;letter-spacing:0.12em;color:#93B4D8;font-weight:600;margin-bottom:4px;'>SK SQUARE</div>
            <div style='font-size:1rem;font-weight:700;color:#FFF;line-height:1.3;'>투자분석 재무 대시보드</div>
            <div style='font-size:0.68rem;color:#7B9EC4;margin-top:4px;'>DART 기반 · Claude 분석</div>
        </div>
        """, unsafe_allow_html=True)

        # ── 저장된 회사 목록 ──
        if companies:
            st.markdown("<div style='font-size:0.65rem;letter-spacing:0.1em;color:#7B9EC4;font-weight:600;margin-bottom:6px;'>포트폴리오 회사</div>", unsafe_allow_html=True)
            if "selected" not in st.session_state:
                st.session_state.selected = list(companies.keys())[0]
                st.session_state.view = "saved"

            keys   = list(companies.keys())
            labels = [companies[k]["company_name"] for k in keys]
            idx    = keys.index(st.session_state.selected) if st.session_state.selected in keys else 0

            selected_label = st.radio("", options=labels, index=idx, label_visibility="collapsed")
            new_key = keys[labels.index(selected_label)]
            if new_key != st.session_state.get("selected"):
                st.session_state.selected = new_key
                st.session_state.view = "saved"
                st.rerun()

        # ── 구분선 ──
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── DART 검색 ──
        st.markdown("<div style='font-size:0.65rem;letter-spacing:0.1em;color:#7B9EC4;font-weight:600;margin-bottom:8px;'>🔍 DART 재무제표 검색</div>", unsafe_allow_html=True)

        if not api_key:
            st.markdown("<div style='font-size:0.75rem;color:#F87171;padding:8px;background:rgba(255,0,0,0.1);border-radius:6px;'>⚠️ API 키 미설정<br>Streamlit Secrets에<br>DART_API_KEY 추가 필요</div>", unsafe_allow_html=True)
        else:
            query = st.text_input("회사명", placeholder="예: 카카오모빌리티", key="dart_query", label_visibility="collapsed")

            if query and len(query) >= 2:
                with st.spinner("검색 중..."):
                    corps = load_corp_list(api_key)
                results = search_corp(corps, query)

                if results:
                    opt_labels = [f"{n} {'📈' if v['stock_code'] else '🔒'}" for n, v in results]
                    chosen = st.selectbox("검색 결과", opt_labels, label_visibility="collapsed", key="dart_result")
                    chosen_idx = opt_labels.index(chosen)
                    chosen_name, chosen_info = results[chosen_idx]

                    c1, c2 = st.columns(2)
                    with c1:
                        fs_div = st.selectbox("구분", ["연결(CFS)","개별(OFS)"], label_visibility="collapsed", key="fs_div")
                        fs_code = "CFS" if "CFS" in fs_div else "OFS"
                    with c2:
                        sector = st.text_input("업종", placeholder="업종 입력", label_visibility="collapsed", key="sector_input")

                    year_opts = [2025, 2024, 2023, 2022, 2021, 2020]
                    sel_years = st.multiselect("조회 연도", year_opts, default=[2022,2023,2024,2025],
                                               label_visibility="collapsed", key="year_sel")

                    if st.button("📡 재무제표 조회", use_container_width=True):
                        if not sel_years:
                            st.error("연도를 선택해주세요.")
                        else:
                            years_sorted = sorted(sel_years)
                            result, errs = build_json(
                                chosen_name, chosen_info["corp_code"],
                                years_sorted, fs_code, api_key,
                                sector=sector or "—",
                                listing="상장" if chosen_info["stock_code"] else "비상장"
                            )
                            if errs:
                                for e in errs: st.warning(e)
                            if result:
                                st.session_state.dart_result_data = result
                                st.session_state.view = "dart"
                                st.rerun()
                else:
                    st.markdown("<div style='font-size:0.78rem;color:#F87171;'>검색 결과 없음</div>", unsafe_allow_html=True)

        # 하단 안내
        st.markdown("""
        <div style='margin-top:1.5rem;padding-top:0.8rem;border-top:1px solid rgba(255,255,255,0.08);'>
            <div style='font-size:0.65rem;color:#4A6FA5;line-height:1.7;'>
                💾 저장: JSON 다운로드 후<br>data/ 폴더 업로드
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── 메인 ─────────────────────────────────────────────────────
def main():
    companies = load_all_companies()

    if "view" not in st.session_state:
        st.session_state.view = "saved"

    render_sidebar(companies)

    view = st.session_state.get("view", "saved")

    if view == "dart" and st.session_state.get("dart_result_data"):
        data = st.session_state.dart_result_data
        render_company(data)

        # JSON 다운로드 버튼
        st.markdown("<div class='section-hd'>데이터 저장</div>", unsafe_allow_html=True)
        json_str  = json.dumps(data, ensure_ascii=False, indent=2)
        file_name = data["company_name"].replace(" ","_") + ".json"
        col1, col2 = st.columns([2,3])
        with col1:
            st.download_button(
                label=f"⬇️ {file_name} 다운로드",
                data=json_str.encode("utf-8"),
                file_name=file_name,
                mime="application/json",
                help="다운로드 후 GitHub data/ 폴더에 업로드하면 영구 저장됩니다"
            )
        with col2:
            st.markdown("<p style='font-size:0.8rem;color:#6B7280;margin-top:0.6rem;'>💡 다운로드 → GitHub data/ 폴더 업로드 → 앱 재배포 시 포트폴리오 목록에 자동 추가</p>", unsafe_allow_html=True)

    elif view == "saved" and companies:
        key  = st.session_state.get("selected", list(companies.keys())[0])
        render_company(companies[key])

    elif not companies:
        st.info("사이드바에서 DART 검색으로 회사를 조회해주세요.")


if __name__ == "__main__":
    main()
