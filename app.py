import streamlit as st
import requests, os, io, zipfile
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"], .stApp { font-family:'Noto Sans KR',sans-serif; background:#F0F2F8; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0F2447 0%,#1A3A6B 60%,#1e4d8c 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color:#E8EEF8 !important; }
[data-testid="stSidebar"] input[type="text"] {
    background:#fff !important; color:#1A3A6B !important;
    border:none !important; border-radius:8px !important; font-size:0.88rem !important;
}
[data-testid="stSidebar"] input[type="text"]::placeholder { color:#9CA3AF !important; }
[data-testid="stSidebar"] div[data-baseweb="select"]>div:first-child {
    background:#fff !important; border-radius:8px !important; border:none !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] span,
[data-testid="stSidebar"] div[data-baseweb="select"] div { color:#1A3A6B !important; }
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width:100% !important; background:#3B82F6 !important; color:#fff !important;
    border:none !important; border-radius:8px !important;
    font-size:0.85rem !important; font-weight:600 !important; padding:0.55rem 1rem !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover { background:#2563EB !important; }

.main .block-container { padding:1.5rem 2rem 3rem 2rem; max-width:100%; }

.kpi-row { display:grid; gap:12px; margin-bottom:1rem; }
.kpi-row-6 { grid-template-columns:repeat(6,1fr); }
.kpi-row-4 { grid-template-columns:repeat(4,1fr); }
.kpi-card {
    background:white; border-radius:12px; padding:1.1rem 1.2rem;
    border-top:3px solid #1A3A6B; box-shadow:0 2px 8px rgba(0,0,0,0.06);
}
.kpi-card.blue   { border-top-color:#1A3A6B; }
.kpi-card.green  { border-top-color:#059669; }
.kpi-card.red    { border-top-color:#DC2626; }
.kpi-card.teal   { border-top-color:#0D9488; }
.kpi-card.amber  { border-top-color:#D97706; }
.kpi-card.purple { border-top-color:#7C3AED; }
.kpi-card.gray   { border-top-color:#6B7280; }
.kpi-label { font-size:0.67rem; color:#9CA3AF; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; margin-bottom:5px; }
.kpi-value { font-size:1.3rem; font-weight:700; color:#111827; line-height:1; margin-bottom:3px; }
.kpi-value.pos { color:#059669; } .kpi-value.neg { color:#DC2626; }
.kpi-yoy  { font-size:0.73rem; font-weight:500; }
.kpi-yoy.pos { color:#059669; } .kpi-yoy.neg { color:#DC2626; }
.kpi-sub  { font-size:0.68rem; color:#9CA3AF; margin-top:2px; }

.section-hd {
    font-size:0.74rem; font-weight:700; color:#374151;
    text-transform:uppercase; letter-spacing:0.07em;
    border-left:3px solid #1A3A6B; padding-left:10px;
    margin:1.8rem 0 0.8rem 0;
}
.section-hd.teal  { border-left-color:#0D9488; }
.section-hd.amber { border-left-color:#D97706; }

.badge { display:inline-block; border-radius:4px; padding:3px 10px; font-size:0.72rem; font-weight:600; margin-right:4px; }
.badge-blue   { background:#DBEAFE; color:#1E40AF; }
.badge-teal   { background:#CCFBF1; color:#0F766E; }
.badge-green  { background:#DCFCE7; color:#166534; }
.badge-yellow { background:#FEF3C7; color:#92400E; }
.badge-gray   { background:#F3F4F6; color:#374151; }

.chart-wrap { background:white; border-radius:14px; padding:1.4rem; box-shadow:0 2px 8px rgba(0,0,0,0.06); margin-bottom:1rem; }
.tbl-wrap   { background:white; border-radius:14px; padding:1.4rem; box-shadow:0 2px 8px rgba(0,0,0,0.06); margin-bottom:1rem; }
.tbl-note   { font-size:0.69rem; color:#9CA3AF; margin-top:0.7rem; }
.page-title { font-size:1.5rem; font-weight:700; color:#111827; margin-bottom:0.3rem; }
.empty-state { text-align:center; padding:5rem 2rem; color:#9CA3AF; }
.sidebar-lbl { font-size:0.62rem; letter-spacing:0.1em; color:#7B9EC4; font-weight:700; margin-bottom:5px; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DART API
# ─────────────────────────────────────────────
DART = "https://opendart.fss.or.kr/api"

def api_key():
    try:    return st.secrets["DART_API_KEY"]
    except: return os.environ.get("DART_API_KEY","")

@st.cache_data(ttl=86400, show_spinner=False)
def corp_list(key):
    try:
        r = requests.get(f"{DART}/corpCode.xml", params={"crtfc_key":key}, timeout=30)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        root = ET.fromstring(z.read("CORPCODE.xml"))
        out = {}
        for item in root.findall("list"):
            name  = item.findtext("corp_name","").strip()
            code  = item.findtext("corp_code","").strip()
            stock = item.findtext("stock_code","").strip()
            if name and code:
                out[name] = {"corp_code":code, "stock_code":stock}
        return out
    except:
        return {}

def search(corps, q):
    q = q.strip()
    if not q: return []
    exact   = [(k,v) for k,v in corps.items() if k==q]
    partial = [(k,v) for k,v in corps.items() if q in k and k!=q]
    return (exact+partial)[:10]

# ── 보고서 목록 조회 ──────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_report_list(key, corp_code, year):
    """해당 연도에 어떤 보고서가 있는지 조회"""
    results = {}
    # A: 감사보고서, B: 사업보고서 등 정기공시
    for pblntf_ty, label in [("A","감사보고서"), ("B","사업보고서")]:
        try:
            r = requests.get(f"{DART}/list.json", params={
                "crtfc_key": key, "corp_code": corp_code,
                "bgn_de": f"{year}0101", "end_de": f"{year+1}0630",
                "pblntf_ty": pblntf_ty, "page_count": "20"
            }, timeout=15)
            d = r.json()
            if d.get("status") == "000":
                items = d.get("list", [])
                # 사업보고서: "사업보고서" 포함, 감사보고서: "감사보고서" 포함
                for it in items:
                    nm = it.get("report_nm","")
                    rcp = it.get("rcept_no","")
                    if not rcp: continue
                    if "사업보고서" in nm and "사업" not in results:
                        results["사업보고서"] = rcp
                    if "감사보고서" in nm and "감사" not in results:
                        results["감사보고서"] = rcp
                    if "연결감사보고서" in nm and "연결감사" not in results:
                        results["연결감사보고서"] = rcp
        except:
            pass
    return results

# ── 재무제표 조회 (fnlttSinglAcntAll) ─────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_singl(key, corp_code, year, reprt_code, fs_div):
    try:
        r = requests.get(f"{DART}/fnlttSinglAcntAll.json", params={
            "crtfc_key":key, "corp_code":corp_code,
            "bsns_year":str(year), "reprt_code":reprt_code, "fs_div":fs_div
        }, timeout=30)
        d = r.json()
        if d.get("status") == "000":
            return d.get("list",[])
    except: pass
    return []

# ── 재무제표 조회 (rcpNo 기반 XBRL) ──────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_by_rcp(key, rcp_no, fs_div):
    """rcpNo로 직접 단일 회사 재무제표 조회"""
    for endpoint in ["fnlttSinglAcntAll.json", "fnlttXbrlAll.json"]:
        try:
            r = requests.get(f"{DART}/{endpoint}", params={
                "crtfc_key":key, "rcpNo":rcp_no, "fs_div":fs_div
            }, timeout=30)
            d = r.json()
            if d.get("status") == "000":
                data = d.get("list",[])
                if data: return data, endpoint
        except: pass
    return [], None

# ── 핵심: 스마트 조회 ─────────────────────────
def fetch_smart(key, corp_code, year, fs_div):
    """
    1) 사업보고서 있으면 → fnlttSinglAcntAll (11011)
    2) 없으면 감사보고서 rcpNo → fnlttSinglAcntAll / fnlttXbrlAll
    3) 연결/개별 모두 시도
    반환: (data, source_label)
    """
    fs_divs = [fs_div, "OFS" if fs_div=="CFS" else "CFS"]

    # 1) 사업보고서 기반 (fnlttSinglAcntAll)
    for fd in fs_divs:
        for rc in ["11011","11012","11013","11014"]:
            data = fetch_singl(key, corp_code, year, rc, fd)
            if data:
                return data, f"사업보고서({rc}/{fd})"

    # 2) 공시 목록에서 감사보고서 rcpNo 찾기
    report_map = get_report_list(key, corp_code, year)

    # 연결감사보고서 우선, 없으면 감사보고서
    rcp_no = report_map.get("연결감사보고서") or report_map.get("감사보고서")

    if rcp_no:
        for fd in fs_divs:
            data, ep = fetch_by_rcp(key, rcp_no, fd)
            if data:
                return data, f"감사보고서({rcp_no[:8]}…/{fd})"

    return [], "없음"


# ─────────────────────────────────────────────
#  파싱
# ─────────────────────────────────────────────
def to_억(s):
    if not s or str(s).strip() in ("","-","－","N/A"): return None
    try: return round(int(str(s).replace(",","").strip())/1e8, 1)
    except: return None

def extract_sj(raw, *keywords, exclude=None):
    """sj_nm 키워드로 항목 필터"""
    seen, out = set(), []
    for item in raw:
        sj = item.get("sj_nm","")
        if not any(kw in sj for kw in keywords): continue
        if exclude and any(ex in sj for ex in exclude): continue
        nm = item.get("account_nm","").strip()
        if nm in seen: continue
        seen.add(nm)
        out.append({
            "account_nm": nm,
            "account_id": item.get("account_id",""),
            "curr": to_억(item.get("thstrm_amount")),
            "prev": to_억(item.get("frmtrm_amount")),
        })
    return out

def get_pl(raw):
    # sj_nm 패턴을 우선순위대로 시도
    for kws, excl in [
        (["손 익 계 산 서","손익계산서"],            ["포괄"]),
        (["포괄손익계산서","포괄 손 익 계 산 서"],   []),
        (["손익"],                                    []),
    ]:
        items = extract_sj(raw, *kws, exclude=excl)
        if items: return items
    return []

def get_bs(raw):
    for kws in [
        ["재 무 상 태 표","재무상태표"],
        ["대 차 대 조 표","대차대조표"],
    ]:
        items = extract_sj(raw, *kws)
        if items: return items
    return []

def get_cf(raw):
    for kws in [["현 금 흐 름 표","현금흐름표"]]:
        items = extract_sj(raw, *kws)
        if items: return items
    return []

def find_val(items, *kws):
    for kw in kws:
        for it in items:
            if it["account_nm"]==kw and it["curr"] is not None: return it["curr"]
    for kw in kws:
        for it in items:
            if kw in it["account_nm"] and it["curr"] is not None: return it["curr"]
    return None

def get_dep(cf_items):
    for kw in ["감가상각비","상각비"]:
        for it in cf_items:
            if kw in it["account_nm"] and "무형" not in it["account_nm"]:
                v=it["curr"]
                if v is not None: return abs(v)
    return 0.0


# ─────────────────────────────────────────────
#  테이블
# ─────────────────────────────────────────────
BOLD_KW = [
    "매출액","영업수익","수익(매출액)","매출총이익","영업이익","영업이익(손실)",
    "당기순이익","당기순이익(손실)","당기순손실","법인세비용차감전",
    "자산총계","부채총계","자본총계","영업활동","투자활동","재무활동",
]

def build_table(years_data, years, key):
    latest = max(years)
    base   = years_data.get(latest,{}).get(key,[])
    if not base:
        for y in reversed(years):
            base = years_data.get(y,{}).get(key,[])
            if base: break
    acnts = [it["account_nm"] for it in base]
    maps  = {yr:{it["account_nm"]:it["curr"] for it in years_data.get(yr,{}).get(key,[])} for yr in years}

    rows=[]
    for ac in acnts:
        row={"계정과목":ac}
        vals=[]
        for yr in years:
            v=maps[yr].get(ac)
            row[str(yr)]=v; vals.append(v)
        for i in range(1,len(years)):
            c,p=vals[i],vals[i-1]
            row["YoY "+str(years[i])] = round((c-p)/abs(p)*100,1) if (c is not None and p and p!=0) else None
        n=len(years)-1; s,e=vals[0],vals[-1]
        row["CAGR"] = round(((e/s)**(1/n)-1)*100,1) if (s and e and s!=0 and n>0) else None
        rows.append(row)
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def style_table(df, years):
    def fv(v):
        if v is None or (isinstance(v,float) and np.isnan(v)): return "—"
        return "{:,.1f}".format(v)
    def fp(v):
        if v is None or (isinstance(v,float) and np.isnan(v)): return "—"
        arr="▲ " if v>0 else ("▼ " if v<0 else "")
        return arr+"{:.1f}%".format(abs(v))

    yr_cols = [str(y) for y in years]
    disp=df.copy()
    for col in disp.columns:
        if col=="계정과목": continue
        disp[col]=disp[col].apply(fv if col in yr_cols else fp)
    disp=disp.set_index("계정과목")

    def cc(v):
        if not isinstance(v,str) or v=="—": return "color:#D1D5DB" if v=="—" else ""
        if "▲" in v: return "color:#059669;font-weight:500"
        if "▼" in v: return "color:#DC2626;font-weight:500"
        try:
            if float(v.replace(",",""))<0: return "color:#DC2626"
        except: pass
        return ""

    def cr(row):
        if any(kw in row.name for kw in BOLD_KW):
            return ["font-weight:700;background:#F0F4FF"]*len(row)
        return [""]*len(row)

    return (disp.style.apply(cr,axis=1).map(cc)
        .set_properties(**{"font-size":"0.81rem","padding":"5px 10px"})
        .set_table_styles([
            {"selector":"th","props":[("background","#1A3A6B"),("color","white"),
             ("font-size","0.72rem"),("font-weight","600"),("text-align","center"),
             ("padding","8px 10px"),("white-space","nowrap")]},
            {"selector":"th.row_heading","props":[("text-align","left"),("background","#F8FAFF"),
             ("color","#374151"),("font-weight","500"),("min-width","180px")]},
            {"selector":"td","props":[("text-align","right")]},
            {"selector":"tr:hover td","props":[("background","#EFF6FF !important")]},
        ]))


# ─────────────────────────────────────────────
#  KPI 카드
# ─────────────────────────────────────────────
def kpi(label, val, yoy=None, sub=None, color="blue", pct=False):
    if pct:
        val_str = "{:.1f}%".format(val) if val is not None else "—"
        val_cls = "pos" if (val and val>0) else ("neg" if (val and val<0) else "")
    else:
        val_str = "{:,.0f}억".format(val) if val is not None else "—"
        val_cls = "neg" if (val is not None and val<0) else "pos"
    yoy_h=""
    if yoy is not None:
        arr="▲" if yoy>0 else ("▼" if yoy<0 else "─")
        yc ="pos" if yoy>0 else ("neg" if yoy<0 else "")
        yoy_h="<div class='kpi-yoy "+yc+"'>"+arr+" "+"{:.1f}".format(abs(yoy))+"% YoY</div>"
    sub_h=("<div class='kpi-sub'>"+sub+"</div>") if sub else ""
    return ("<div class='kpi-card "+color+"'>"
            "<div class='kpi-label'>"+label+"</div>"
            "<div class='kpi-value "+val_cls+"'>"+val_str+"</div>"
            +yoy_h+sub_h+"</div>")

def yoy_c(c,p):
    if c is None or p is None or p==0: return None
    return round((c-p)/abs(p)*100,1)

def pct_m(v,d):
    if v is None or d is None or d==0: return None
    return round(v/d*100,1)


# ─────────────────────────────────────────────
#  차트
# ─────────────────────────────────────────────
def make_chart(kpis_map, years):
    vy=[y for y in years if kpis_map.get(y,{}).get("rev") is not None]
    if not vy: return None
    yr=[str(y) for y in vy]
    rev=[kpis_map[y].get("rev") or 0 for y in vy]
    op =[kpis_map[y].get("op")  or 0 for y in vy]
    net=[kpis_map[y].get("net") or 0 for y in vy]
    ebi=[kpis_map[y].get("ebi") or 0 for y in vy]
    fig=go.Figure()
    fig.add_trace(go.Bar(name="매출",x=yr,y=rev,marker_color="#1A3A6B",opacity=0.85,
        marker_line_width=0,text=["{:,.0f}".format(v) for v in rev],
        textposition="outside",textfont=dict(size=10,color="#1A3A6B")))
    fig.add_trace(go.Bar(name="EBITDA",x=yr,y=ebi,marker_color="#0D9488",opacity=0.85,
        marker_line_width=0,text=["{:,.0f}".format(v) for v in ebi],
        textposition="outside",textfont=dict(size=10,color="#0D9488")))
    fig.add_trace(go.Bar(name="영업이익",x=yr,y=op,opacity=0.85,marker_line_width=0,
        marker_color=["#DC2626" if v<0 else "#059669" for v in op],
        text=["{:,.0f}".format(v) for v in op],textposition="outside",textfont=dict(size=10)))
    fig.add_trace(go.Scatter(name="당기순이익",x=yr,y=net,mode="lines+markers",
        line=dict(color="#D97706",width=2.5,dash="dot"),
        marker=dict(size=9,color="#D97706",line=dict(color="white",width=2))))
    fig.update_layout(
        barmode="group",plot_bgcolor="white",paper_bgcolor="white",
        height=320,margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h",y=1.02,x=1,xanchor="right",
                    font=dict(size=11),bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",",ticksuffix="억",gridcolor="#F3F4F6",
                   zeroline=True,zerolinecolor="#D1D5DB",tickfont=dict(size=11)),
        xaxis=dict(type="category",tickfont=dict(size=12)),
        font=dict(family="Noto Sans KR"))
    return fig


# ─────────────────────────────────────────────
#  사이드바
# ─────────────────────────────────────────────
def sidebar():
    key = api_key()
    with st.sidebar:
        st.markdown("""
        <div style='padding:1.4rem 0 1rem 0;border-bottom:1px solid rgba(255,255,255,0.12);margin-bottom:1.1rem;'>
            <div style='font-size:0.6rem;letter-spacing:0.14em;color:#93B4D8;font-weight:700;margin-bottom:4px;'>SK SQUARE</div>
            <div style='font-size:0.98rem;font-weight:700;color:#FFF;line-height:1.35;'>투자분석 재무 대시보드</div>
            <div style='font-size:0.67rem;color:#7B9EC4;margin-top:4px;'>DART OpenAPI 기반</div>
        </div>""", unsafe_allow_html=True)

        if not key:
            st.markdown("<div style='background:rgba(220,38,38,0.15);border:1px solid rgba(220,38,38,0.3);border-radius:8px;padding:10px;font-size:0.78rem;color:#FCA5A5;'>⚠️ DART_API_KEY 미설정</div>", unsafe_allow_html=True)
            return None

        st.markdown("<div class='sidebar-lbl'>🔍 Company Search</div>", unsafe_allow_html=True)
        query = st.text_input("", placeholder="회사명 입력", key="q", label_visibility="collapsed")

        selected = None
        if query and len(query.strip()) >= 1:
            corps = corp_list(key)
            results = search(corps, query.strip())
            if results:
                labels = [("(📈) " if v["stock_code"] else "(🏢) ")+n for n,v in results]
                idx = st.selectbox("", range(len(labels)), format_func=lambda i:labels[i],
                                   key="sel", label_visibility="collapsed")
                selected = results[idx]
            else:
                st.markdown("<div style='font-size:0.78rem;color:#F87171;'>검색 결과 없음</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-lbl' style='margin-top:0.9rem;'>⚙️ Settings</div>", unsafe_allow_html=True)
        fs_label = st.selectbox("", ["연결 우선 (CFS→OFS)", "개별 우선 (OFS→CFS)"],
                                key="fs", label_visibility="collapsed")
        fs_div = "CFS" if "CFS" in fs_label else "OFS"

        year_opts = [2025,2024,2023,2022,2021,2020]
        sel_years = st.multiselect("", year_opts, default=[2022,2023,2024,2025],
                                   key="yrs", label_visibility="collapsed")

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        btn = st.button("📡  재무제표 조회", use_container_width=True)

        if btn:
            if not selected: st.error("회사를 선택해주세요."); return key
            if not sel_years: st.error("연도를 선택해주세요."); return key
            name, info = selected
            st.session_state.params = {
                "name": name, "corp_code": info["corp_code"],
                "stock_code": info["stock_code"],
                "fs_div": fs_div, "years": sorted(sel_years),
            }
            st.session_state.cache = {}
            st.rerun()

        st.markdown("""
        <div style='margin-top:1.5rem;padding-top:0.8rem;border-top:1px solid rgba(255,255,255,0.1);
        font-size:0.63rem;color:#4A6FA5;line-height:1.9;'>
        📌 사업보고서 우선 조회<br>
        📌 없으면 감사보고서 자동 전환<br>
        📌 연결→개별 자동 fallback<br>
        📌 단위: 억원
        </div>""", unsafe_allow_html=True)
    return key


# ─────────────────────────────────────────────
#  메인
# ─────────────────────────────────────────────
def main_view(key):
    params = st.session_state.get("params")
    if not params:
        st.markdown("""
        <div class='empty-state'>
            <div style='font-size:3rem;margin-bottom:1rem;'>📊</div>
            <div style='font-size:1.1rem;font-weight:600;color:#374151;margin-bottom:0.5rem;'>SK Square 재무 분석 대시보드</div>
            <div style='font-size:0.85rem;'>좌측에서 회사명을 검색하고 조회 버튼을 눌러주세요</div>
        </div>""", unsafe_allow_html=True)
        return

    name      = params["name"]
    corp_code = params["corp_code"]
    fs_div    = params["fs_div"]
    years     = params["years"]

    # ── 캐시 키: 검색 파라미터 조합 ──────────
    ckey = f"{corp_code}_{fs_div}_{'_'.join(map(str,years))}"
    cache = st.session_state.get("cache", {})

    if ckey not in cache:
        ydata = {}
        sources = {}
        prog = st.progress(0, text=f"{name} 데이터 로딩 중...")
        for i, yr in enumerate(years):
            prog.progress((i+1)/len(years), text=f"{yr}년 조회 중...")
            raw, src = fetch_smart(key, corp_code, yr, fs_div)
            pl  = get_pl(raw)
            bs  = get_bs(raw)
            cf  = get_cf(raw)
            dep = get_dep(cf)
            ydata[yr]   = {"pl":pl,"bs":bs,"cf":cf,"dep":dep,"raw":raw}
            sources[yr] = src
        prog.empty()
        cache[ckey] = {"ydata":ydata,"sources":sources}
        st.session_state.cache = cache
    else:
        ydata   = cache[ckey]["ydata"]
        sources = cache[ckey]["sources"]

    # ── 조회 소스 표시 ───────────────────────
    src_info = " | ".join([f"{y}: {sources.get(y,'—')}" for y in years])

    # ── KPI 수집 ────────────────────────────
    kpis_map = {}
    for yr in years:
        pl  = ydata[yr]["pl"]
        bs  = ydata[yr]["bs"]
        dep = ydata[yr]["dep"]
        rev = find_val(pl,"매출액","영업수익","수익(매출액)","매출")
        op  = find_val(pl,"영업이익","영업이익(손실)","영업손익")
        net = find_val(pl,"당기순이익","당기순이익(손실)","당기순손실")
        ebt = find_val(pl,"법인세비용차감전순이익","법인세비용차감전순이익(손실)","법인세비용차감전순손실")
        gp  = find_val(pl,"매출총이익","매출총손익")
        ta  = find_val(bs,"자산총계")
        tl  = find_val(bs,"부채총계")
        eq  = find_val(bs,"자본총계")
        ebi = (op+dep) if op is not None else None
        kpis_map[yr]={"rev":rev,"op":op,"net":net,"ebt":ebt,"gp":gp,"ebi":ebi,
                      "dep":dep,"ta":ta,"tl":tl,"eq":eq}

    latest = years[-1]
    prev   = years[-2] if len(years)>=2 else None
    kl = kpis_map.get(latest,{})
    kp = kpis_map.get(prev,{}) if prev else {}

    rev_v=kl.get("rev"); rev_p=kp.get("rev")
    op_v =kl.get("op");  op_p =kp.get("op")
    net_v=kl.get("net"); net_p=kp.get("net")
    ebt_v=kl.get("ebt"); ebt_p=kp.get("ebt")
    gp_v =kl.get("gp");  gp_p =kp.get("gp")
    ebi_v=kl.get("ebi"); ebi_p=kp.get("ebi")
    ta_v =kl.get("ta");  ta_p =kp.get("ta")
    tl_v =kl.get("tl")
    eq_v =kl.get("eq");  eq_p =kp.get("eq")

    op_m   = pct_m(op_v,  rev_v)
    gp_m   = pct_m(gp_v,  rev_v)
    net_m  = pct_m(net_v, rev_v)
    ebi_m  = pct_m(ebi_v, rev_v)
    de     = round(tl_v/eq_v*100,1) if (tl_v and eq_v and eq_v!=0) else None
    roe    = pct_m(net_v, eq_v)
    roa    = pct_m(net_v, ta_v)
    at_    = round(rev_v/ta_v,2) if (rev_v and ta_v and ta_v!=0) else None

    # ── 헤더 ────────────────────────────────
    listing  = "상장 📈" if params.get("stock_code") else "비상장 🏢"
    std      = "K-IFRS 연결" if fs_div=="CFS" else "K-GAAP 개별"
    yr_range = f"{min(years)}~{max(years)}"

    st.markdown(f"<div class='page-title'>{name}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<span class='badge badge-blue'>{listing}</span>"
        f"<span class='badge badge-teal'>{std}</span>"
        f"<span class='badge badge-gray'>사업보고서/감사보고서</span>"
        f"<span class='badge badge-gray'>{yr_range}</span>",
        unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.68rem;color:#9CA3AF;margin:6px 0 0 0;'>조회 소스: {src_info}</p>",
                unsafe_allow_html=True)
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── KPI Row 1: 손익 6개 ─────────────────
    st.markdown("<div class='section-hd'>핵심 손익 지표</div>", unsafe_allow_html=True)
    r1 = "<div class='kpi-row kpi-row-6'>"
    r1 += kpi("매출 "+str(latest),      rev_v, yoy_c(rev_v,rev_p), color="blue")
    r1 += kpi("매출총이익 "+str(latest), gp_v,  yoy_c(gp_v,gp_p),
              sub=f"GP margin {gp_m:.1f}%" if gp_m else None, color="blue")
    r1 += kpi("영업이익 "+str(latest),   op_v,  yoy_c(op_v,op_p),
              sub=f"OPM {op_m:.1f}%" if op_m else None,
              color="green" if (op_v and op_v>=0) else "red")
    r1 += kpi("EBITDA "+str(latest),     ebi_v, yoy_c(ebi_v,ebi_p),
              sub=f"margin {ebi_m:.1f}%" if ebi_m else None, color="teal")
    r1 += kpi("세전이익 "+str(latest),   ebt_v, yoy_c(ebt_v,ebt_p), color="amber")
    r1 += kpi("당기순이익 "+str(latest), net_v, yoy_c(net_v,net_p),
              sub=f"NPM {net_m:.1f}%" if net_m else None,
              color="green" if (net_v and net_v>=0) else "red")
    r1 += "</div>"
    st.markdown(r1, unsafe_allow_html=True)

    # ── KPI Row 2: 재무건전성 4개 ───────────
    st.markdown("<div class='section-hd'>재무건전성 지표</div>", unsafe_allow_html=True)
    de_str  = f"{de:.1f}%"   if de  is not None else "—"
    roe_str = f"{roe:.1f}%"  if roe is not None else "—"
    roa_str = f"{roa:.1f}%"  if roa is not None else "—"
    at_str  = f"{at_:.2f}x"  if at_ is not None else "—"
    de_c    = "red" if (de and de>200) else "gray"
    roe_c   = "green" if (roe and roe>0) else ("red" if (roe and roe<0) else "gray")

    r2 = "<div class='kpi-row kpi-row-4'>"
    r2 += kpi("총자산 "+str(latest),   ta_v, yoy_c(ta_v,ta_p), color="gray")
    r2 += kpi("자본총계 "+str(latest), eq_v, yoy_c(eq_v,eq_p), color="gray")
    r2 += (f"<div class='kpi-card {de_c}'>"
           f"<div class='kpi-label'>부채비율 {latest}</div>"
           f"<div class='kpi-value'>{de_str}</div>"
           f"<div class='kpi-sub'>부채 / 자본 × 100</div></div>")
    r2 += (f"<div class='kpi-card {roe_c}'>"
           f"<div class='kpi-label'>ROE / ROA {latest}</div>"
           f"<div class='kpi-value'>{roe_str}</div>"
           f"<div class='kpi-sub'>ROA {roa_str} | 자산회전율 {at_str}</div></div>")
    r2 += "</div>"
    st.markdown(r2, unsafe_allow_html=True)

    # ── 차트 ────────────────────────────────
    st.markdown("<div class='section-hd'>수익성 추이 | 단위: 억원</div>", unsafe_allow_html=True)
    fig = make_chart(kpis_map, years)
    if fig:
        st.markdown("<div class='chart-wrap'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 재무제표 3종 ─────────────────────────
    tables = [
        ("pl", "손익계산서 (P&L)",  "section-hd"),
        ("bs", "재무상태표 (B/S)",  "section-hd teal"),
        ("cf", "현금흐름표 (C/F)",  "section-hd amber"),
    ]
    for tkey, title, hd_cls in tables:
        st.markdown(f"<div class='{hd_cls}'>{title} | 단위: 억원 · DART 원본 계정</div>",
                    unsafe_allow_html=True)
        df = build_table(ydata, years, tkey)
        if df.empty:
            st.info(f"{tkey.upper()} 데이터를 불러오지 못했습니다.")
            continue
        yr_cols  = [str(y) for y in years]
        yoy_cols = ["YoY "+str(y) for y in years[1:]]
        cols     = ["계정과목"]+yr_cols+yoy_cols+["CAGR"]
        df       = df[[c for c in cols if c in df.columns]]
        st.markdown("<div class='tbl-wrap'>", unsafe_allow_html=True)
        h = min(max(len(df)*35+60,250),650)
        st.dataframe(style_table(df,years), use_container_width=True, height=h)
        std2 = "연결" if fs_div=="CFS" else "개별"
        st.markdown(
            f"<p class='tbl-note'>출처: DART OpenAPI {std2} {tkey.upper()} | "
            f"YoY: 전년 대비 증감률 | CAGR: {min(years)}→{max(years)}</p>",
            unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 디버그 ───────────────────────────────
    with st.expander("🔧 DEBUG", expanded=False):
        st.markdown(f"**corp_code:** `{corp_code}` | **fs_div 설정:** `{fs_div}`")
        for yr in years:
            raw = ydata.get(yr,{}).get("raw",[])
            sj  = sorted(set(it.get("sj_nm","") for it in raw)) if raw else []
            pl_cnt = len(ydata[yr]["pl"]); bs_cnt = len(ydata[yr]["bs"]); cf_cnt = len(ydata[yr]["cf"])
            st.markdown(f"**{yr}**: 소스=`{sources.get(yr,'—')}` | 총{len(raw)}건 | PL:{pl_cnt} BS:{bs_cnt} CF:{cf_cnt}")
            if sj: st.markdown("sj_nm: " + " / ".join([repr(s) for s in sj]))


# ─────────────────────────────────────────────
#  실행
# ─────────────────────────────────────────────
def main():
    for k,v in [("params",None),("cache",{})]:
        if k not in st.session_state:
            st.session_state[k] = v
    key = sidebar()
    if key:
        main_view(key)

if __name__ == "__main__":
    main()
