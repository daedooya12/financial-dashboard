import streamlit as st
import requests, os, io, zipfile, re, urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="SK Square | 재무 분석",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

/* ── 기본 ── */
html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans KR', sans-serif;
    background: #F0F2F8;
}

/* ── 반응형 ── */
@media (max-width: 768px) {
    .main .block-container { padding: 1rem !important; }
    .kpi-row-6 { grid-template-columns: repeat(2, 1fr) !important; }
    .kpi-row-4 { grid-template-columns: repeat(2, 1fr) !important; }
    .page-title { font-size: 1.2rem !important; }
}
@media (max-width: 480px) {
    .kpi-row-6, .kpi-row-4 { grid-template-columns: repeat(1, 1fr) !important; }
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2447 0%, #1A3A6B 100%);
}
[data-testid="stSidebar"] * { color: #E8EEF8 !important; }
[data-testid="stSidebar"] input[type="text"] {
    background: #fff !important; color: #1A3A6B !important;
    border: none !important; border-radius: 8px !important;
    font-size: .85rem !important;
}
[data-testid="stSidebar"] input[type="text"]::placeholder { color: #9CA3AF !important; }
[data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child {
    background: #fff !important; border-radius: 8px !important; border: none !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] span,
[data-testid="stSidebar"] div[data-baseweb="select"] div { color: #1A3A6B !important; }
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: 100% !important; background: #3B82F6 !important;
    color: #fff !important; border: none !important; border-radius: 8px !important;
    font-size: .85rem !important; font-weight: 600 !important; margin-top: 4px !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover { background: #2563EB !important; }
[data-testid="stSidebar"] .stRadio label {
    color: #C8D8F0 !important; font-size: .85rem !important;
}

/* ── 메인 ── */
.main .block-container { padding: 1.5rem 2rem 3rem; max-width: 100%; }

/* KPI */
.kpi-row  { display: grid; gap: 12px; margin-bottom: 1rem; }
.kpi-row-6 { grid-template-columns: repeat(6, 1fr); }
.kpi-row-4 { grid-template-columns: repeat(4, 1fr); }
.kpi-card {
    background: #fff; border-radius: 12px;
    padding: 1rem 1.1rem; border-top: 3px solid #1A3A6B;
    box-shadow: 0 1px 6px rgba(0,0,0,.07);
}
.kpi-card.blue   { border-top-color: #1A3A6B; }
.kpi-card.green  { border-top-color: #059669; }
.kpi-card.red    { border-top-color: #DC2626; }
.kpi-card.teal   { border-top-color: #0D9488; }
.kpi-card.amber  { border-top-color: #D97706; }
.kpi-card.gray   { border-top-color: #6B7280; }
.kpi-label { font-size: .66rem; color: #9CA3AF; font-weight: 600;
             letter-spacing: .05em; text-transform: uppercase; margin-bottom: 4px; }
.kpi-value { font-size: 1.25rem; font-weight: 700; color: #111; line-height: 1; margin-bottom: 2px; }
.kpi-value.pos { color: #059669; } .kpi-value.neg { color: #DC2626; }
.kpi-yoy  { font-size: .72rem; font-weight: 500; }
.kpi-yoy.pos { color: #059669; } .kpi-yoy.neg { color: #DC2626; }
.kpi-sub  { font-size: .67rem; color: #9CA3AF; margin-top: 2px; }

/* 섹션 헤더 */
.sec { font-size: .72rem; font-weight: 700; color: #374151;
       text-transform: uppercase; letter-spacing: .07em;
       border-left: 3px solid #1A3A6B; padding-left: 9px;
       margin: 1.6rem 0 .7rem; }
.sec.teal  { border-left-color: #0D9488; }
.sec.amber { border-left-color: #D97706; }

/* 뱃지 */
.badge { display:inline-block; border-radius:4px; padding:2px 9px;
         font-size:.7rem; font-weight:600; margin-right:4px; }
.b-blue   { background:#DBEAFE; color:#1E40AF; }
.b-teal   { background:#CCFBF1; color:#0F766E; }
.b-yellow { background:#FEF3C7; color:#92400E; }
.b-gray   { background:#F3F4F6; color:#374151; }
.b-green  { background:#DCFCE7; color:#166534; }

/* 카드 래퍼 */
.card { background:#fff; border-radius:14px; padding:1.3rem;
        box-shadow:0 1px 6px rgba(0,0,0,.07); margin-bottom:1rem; }

.tbl-note { font-size:.67rem; color:#9CA3AF; margin-top:.6rem; }
.page-title { font-size:1.45rem; font-weight:700; color:#111; margin-bottom:.3rem; }
.empty-wrap { text-align:center; padding:5rem 1rem; color:#9CA3AF; }

/* 모드 선택 탭 */
.mode-box {
    background: rgba(255,255,255,0.08);
    border-radius: 10px; padding: .8rem;
    margin-bottom: .8rem;
}

/* URL 입력 카드 */
.url-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px; padding: .8rem 1rem;
    margin-bottom: .5rem;
}

.sidebar-lbl {
    font-size:.6rem; letter-spacing:.1em; color:#7B9EC4;
    font-weight:700; margin-bottom:5px; text-transform:uppercase;
}

/* 뉴스 */
.news-item {
    display:flex; align-items:flex-start; gap:.7rem;
    padding:.7rem 0; border-bottom:1px solid #F3F4F6;
}
.news-item:last-child { border-bottom:none; }
.news-date { font-size:.65rem; color:#9CA3AF; white-space:nowrap; margin-top:2px; }
.news-source { font-size:.62rem; color:#6B7280; background:#F3F4F6;
               border-radius:3px; padding:1px 5px; white-space:nowrap; }
.news-title a { font-size:.82rem; color:#111827; text-decoration:none;
                line-height:1.4; font-weight:500; }
.news-title a:hover { color:#1A3A6B; text-decoration:underline; }

/* 실적 변화 테이블 */
.perf-row { display:flex; align-items:center; gap:.5rem;
            padding:.45rem .5rem; border-radius:6px; margin-bottom:3px; }
.perf-row:hover { background:#F8FAFF; }
.perf-label { font-size:.78rem; color:#374151; font-weight:500; width:90px; flex-shrink:0; }
.perf-curr  { font-size:.82rem; font-weight:700; color:#111; width:90px; text-align:right; }
.perf-diff  { font-size:.78rem; font-weight:600; width:90px; text-align:right; }
.perf-pct   { font-size:.78rem; font-weight:600; width:60px; text-align:right; }

/* 사업 요약 */
.biz-box { background:#F8FAFF; border-radius:10px; padding:1rem 1.2rem;
           border-left:3px solid #1A3A6B; }
.biz-text { font-size:.83rem; color:#374151; line-height:1.7; }
.biz-tag { display:inline-block; background:#DBEAFE; color:#1E40AF;
           border-radius:4px; padding:2px 8px; font-size:.7rem;
           font-weight:600; margin:3px 3px 0 0; }

/* 이슈 뱃지 */
.issue-item { font-size:.8rem; color:#374151; padding:.4rem .7rem;
              background:#F9FAFB; border-radius:6px; margin-bottom:4px;
              border-left:2px solid #D1D5DB; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  DART API 설정
# ══════════════════════════════════════════════
DART = "https://opendart.fss.or.kr/api"

def api_key():
    try:    return st.secrets["DART_API_KEY"]
    except: return os.environ.get("DART_API_KEY", "")

@st.cache_data(ttl=86400, show_spinner=False)
def load_corps(key):
    try:
        r    = requests.get(f"{DART}/corpCode.xml", params={"crtfc_key": key}, timeout=30)
        z    = zipfile.ZipFile(io.BytesIO(r.content))
        root = ET.fromstring(z.read("CORPCODE.xml"))
        out  = {}
        for item in root.findall("list"):
            n = item.findtext("corp_name", "").strip()
            c = item.findtext("corp_code", "").strip()
            s = item.findtext("stock_code", "").strip()
            if n and c: out[n] = {"corp_code": c, "stock_code": s}
        return out
    except:
        return {}

# ══ DART 기업정보 / 주주 / 뉴스 ══════════════

@st.cache_data(ttl=86400, show_spinner=False)
def get_company_info(key, corp_code):
    """DART 기업개황"""
    try:
        r = requests.get(f"{DART}/company.json",
                         params={"crtfc_key": key, "corp_code": corp_code}, timeout=15)
        d = r.json()
        if d.get("status") == "000":
            return d
    except: pass
    return {}

@st.cache_data(ttl=86400, show_spinner=False)
def get_shareholders(key, corp_code):
    """5% 이상 대량보유자 (DART majorstock)"""
    try:
        r = requests.get(f"{DART}/majorstock.json",
                         params={"crtfc_key": key, "corp_code": corp_code,
                                 "reprt_code": "11011"}, timeout=15)
        d = r.json()
        if d.get("status") == "000":
            return d.get("list", [])
    except: pass
    return []

@st.cache_data(ttl=86400, show_spinner=False)
def get_executives(key, corp_code):
    """임원 현황 (사업 요약 보완용)"""
    try:
        r = requests.get(f"{DART}/exctvSttus.json",
                         params={"crtfc_key": key, "corp_code": corp_code,
                                 "reprt_code": "11011"}, timeout=15)
        d = r.json()
        if d.get("status") == "000":
            return d.get("list", [])[:3]
    except: pass
    return []

@st.cache_data(ttl=1800, show_spinner=False)
def get_news(company_name, n=5):
    """Google News RSS — 최신 뉴스"""
    query = urllib.parse.quote(company_name + " 실적")
    url   = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        r    = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        news  = []
        for item in items[:n]:
            title  = item.findtext("title", "").strip()
            link   = item.findtext("link",  "").strip()
            pub    = item.findtext("pubDate", "").strip()
            source = item.findtext("source", "").strip()
            if not title or not link: continue
            try:
                dt       = datetime.strptime(pub[:25], "%a, %d %b %Y %H:%M:%S")
                date_str = dt.strftime("%Y.%m.%d")
            except:
                date_str = pub[:10] if pub else ""
            news.append({"title": title, "link": link,
                         "date": date_str, "source": source})
        return news
    except:
        return []

def build_shareholder_chart(shareholders):
    """주주 파이차트"""
    if not shareholders:
        return None
    labels, values = [], []
    total_pct = 0.0
    for s in shareholders:
        nm  = s.get("nm", s.get("shrholdr_nm", "")).strip()
        pct_str = s.get("trmend_posesn_stock_co", s.get("bsis_posesn_stock_co", "0"))
        try:
            pct = float(str(pct_str).replace(",", "")) /                   float(str(s.get("trmend_tot_stock", s.get("bsis_tot_stock", "1"))).replace(",","")) * 100
        except:
            continue
        if nm and pct > 0:
            labels.append(nm); values.append(round(pct, 1)); total_pct += pct
    if not labels:
        return None
    # 기타 추가
    other = round(100 - total_pct, 1)
    if other > 0:
        labels.append("기타 주주"); values.append(other)
    colors = ["#1A3A6B","#3B82F6","#0D9488","#D97706","#7C3AED",
              "#059669","#DC2626","#9CA3AF"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.52,
        marker=dict(colors=colors[:len(labels)],
                    line=dict(color="white", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11, family="Noto Sans KR"),
        hovertemplate="%{label}<br>%{value:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=240,
        paper_bgcolor="white",
        font=dict(family="Noto Sans KR"),
        annotations=[dict(text="주주<br>구성", x=0.5, y=0.5,
                          font=dict(size=12, color="#374151"), showarrow=False)]
    )
    return fig

def build_perf_summary(kmap, years, name):
    """전년 대비 실적 요약 텍스트 자동 생성"""
    if len(years) < 2:
        return []
    latest = years[-1]; prev = years[-2]
    kl = kmap.get(latest, {}); kp = kmap.get(prev, {})

    def chg(cur, prv, label, unit="억원"):
        if cur is None or prv is None or prv == 0:
            return None
        diff = cur - prv
        pct  = (diff / abs(prv)) * 100
        arrow = "▲" if diff > 0 else "▼"
        color = "#059669" if diff > 0 else "#DC2626"
        sign  = "+" if diff > 0 else ""
        return {
            "label": label,
            "curr":  f"{cur:,.0f}{unit}",
            "diff":  f"{sign}{diff:,.0f}{unit}",
            "pct":   f"{sign}{pct:.1f}%",
            "arrow": arrow,
            "color": color,
            "positive": diff > 0,
        }

    items = []
    for cur_k, prv_k, label in [
        ("rev", "rev", "매출"),
        ("gp",  "gp",  "매출총이익"),
        ("op",  "op",  "영업이익"),
        ("ebi", "ebi", "EBITDA"),
        ("net", "net", "당기순이익"),
    ]:
        r = chg(kl.get(cur_k), kp.get(prv_k), label)
        if r: items.append(r)

    # 이슈 자동 판단
    issues = []
    rv, op, net = kl.get("rev"), kl.get("op"), kl.get("net")
    rv_p, op_p  = kp.get("rev"), kp.get("op")

    if rv and rv_p:
        g = (rv - rv_p) / abs(rv_p) * 100
        if g >= 10:   issues.append(f"📈 매출 {g:.1f}% 고성장 — 사업 확대 국면")
        elif g <= -10: issues.append(f"📉 매출 {abs(g):.1f}% 역성장 — 수요 둔화 또는 사업 재편 가능성")
    if op is not None and op > 0 and op_p is not None and op_p <= 0:
        issues.append("✅ 영업이익 흑자 전환 달성")
    elif op is not None and op < 0 and op_p is not None and op_p > 0:
        issues.append("⚠️ 영업이익 흑자 → 적자 전환")
    elif op is not None and op_p is not None and op_p != 0:
        g = (op - op_p) / abs(op_p) * 100
        if g >= 30:    issues.append(f"✅ 영업이익 {g:.1f}% 대폭 개선")
        elif g <= -30: issues.append(f"⚠️ 영업이익 {abs(g):.1f}% 대폭 감소")
    if net is not None and net > 0:
        if kp.get("net") is not None and kp.get("net") <= 0:
            issues.append("✅ 당기순이익 흑자 전환")
    ta, eq = kl.get("ta"), kl.get("eq")
    tl = kl.get("tl")
    if ta and eq and tl and eq != 0:
        de = tl / eq * 100
        if de > 300:   issues.append(f"⚠️ 부채비율 {de:.0f}% — 재무 레버리지 높음")
        elif de < 50:  issues.append(f"✅ 부채비율 {de:.0f}% — 안정적 재무구조")

    return {"items": items, "issues": issues, "latest": latest, "prev": prev}

def corp_search(corps, q):
    q_norm = q.replace(" ", "").lower()
    if not q_norm: return []
    exact = []
    partial = []
    for k, v in corps.items():
        k_norm = k.replace(" ", "").lower()
        if k_norm == q_norm:
            exact.append((k, v))
        elif q_norm in k_norm:
            partial.append((k, v))
    return (exact + partial)[:10]

# ── 사업보고서 재무 조회 ──────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_singl(key, corp_code, year, reprt_code, fs_div):
    try:
        r = requests.get(f"{DART}/fnlttSinglAcntAll.json", params={
            "crtfc_key": key, "corp_code": corp_code,
            "bsns_year": str(year), "reprt_code": reprt_code, "fs_div": fs_div
        }, timeout=30)
        d = r.json()
        if d.get("status") == "000":
            return d.get("list", [])
    except: pass
    return []

def fetch_business_report(key, corp_code, year, fs_div):
    """사업보고서 기반 데이터 조회 (상장사)"""
    divs = [fs_div, "OFS" if fs_div == "CFS" else "CFS"]
    for rc in ["11011", "11012", "11013", "11014"]:
        for fd in divs:
            d = fetch_singl(key, corp_code, year, rc, fd)
            if d: return d, f"{rc}/{fd}"
    return [], None

# ── 감사보고서 URL → rcpNo 추출 후 재무 조회 ──
def extract_rcp_no(url):
    """DART URL에서 rcpNo 추출"""
    url = url.strip()
    m = re.search(r"rcpNo=(\d+)", url)
    if m: return m.group(1)
    m = re.search(r"/(\d{14,})", url)
    if m: return m.group(1)
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_by_rcpno(key, rcp_no, fs_div):
    """rcpNo로 재무제표 조회 - 여러 endpoint 시도"""
    divs = [fs_div, "OFS" if fs_div == "CFS" else "CFS"]
    # 먼저 corp_code + rcpNo로 fnlttSinglAcntAll 시도
    for fd in divs:
        for ep in ["fnlttSinglAcntAll.json", "fnlttXbrlAll.json"]:
            try:
                r = requests.get(f"{DART}/{ep}", params={
                    "crtfc_key": key, "rcpNo": rcp_no, "fs_div": fd
                }, timeout=30)
                d = r.json()
                if d.get("status") == "000":
                    data = d.get("list", [])
                    if data: return data, f"{ep.replace('.json','')}/{fd}"
            except: pass
    return [], None

# ══════════════════════════════════════════════
#  파싱
# ══════════════════════════════════════════════
XBRL_MAP = {
    # PL
    "ifrs-full_Revenue":                                "revenue",
    "ifrs_Revenue":                                     "revenue",
    "dart_OperatingRevenue":                            "revenue",
    "ifrs-full_RevenueFromContractsWithCustomers":      "revenue",
    "ifrs-full_GrossProfit":                            "gross_profit",
    "dart_OperatingIncomeLoss":                         "op_income",
    "ifrs-full_ProfitLossFromOperatingActivities":      "op_income",
    "ifrs-full_OperatingIncomeLoss":                    "op_income",
    "ifrs-full_ProfitLossBeforeTax":                    "ebt",
    "ifrs-full_ProfitLoss":                             "net_income",
    "ifrs-full_ProfitLossAttributableToOwnersOfParent": "net_income",
    # BS
    "ifrs-full_Assets":                                 "total_assets",
    "ifrs-full_CurrentAssets":                          "current_assets",
    "ifrs-full_NoncurrentAssets":                       "noncurrent_assets",
    "ifrs-full_Liabilities":                            "total_liab",
    "ifrs-full_CurrentLiabilities":                     "current_liab",
    "ifrs-full_Equity":                                 "total_equity",
    "ifrs-full_CashAndCashEquivalents":                 "cash",
    # CF
    "ifrs-full_CashFlowsFromUsedInOperatingActivities": "cfo",
    "ifrs-full_CashFlowsFromUsedInInvestingActivities": "cfi",
    "ifrs-full_CashFlowsFromUsedInFinancingActivities": "cff",
    "ifrs-full_AdjustmentsForDepreciationAndAmortisationExpense": "dep",
    "dart_DepreciationAndAmortisation":                 "dep",
}

KOR_MAP = {
    "매출액": "revenue", "영업수익": "revenue", "수익(매출액)": "revenue",
    "매출총이익": "gross_profit", "매출총손익": "gross_profit",
    "영업이익": "op_income", "영업이익(손실)": "op_income",
    "영업손익": "op_income", "영업손실": "op_income",
    "법인세비용차감전순이익": "ebt", "법인세비용차감전순이익(손실)": "ebt",
    "법인세비용차감전순손실": "ebt",
    "당기순이익": "net_income", "당기순이익(손실)": "net_income", "당기순손실": "net_income",
    "자산총계": "total_assets", "부채총계": "total_liab", "자본총계": "total_equity",
    "현금및현금성자산": "cash", "유동자산": "current_assets", "비유동자산": "noncurrent_assets",
    "유동부채": "current_liab",
    "영업활동현금흐름": "cfo", "영업활동 현금흐름": "cfo",
    "투자활동현금흐름": "cfi", "투자활동 현금흐름": "cfi",
    "재무활동현금흐름": "cff", "재무활동 현금흐름": "cff",
    "감가상각비": "dep", "감가상각비 및 상각비": "dep",
}

SJ_PL_KW = ["손 익 계 산 서", "손익계산서", "포괄손익계산서", "포괄 손 익 계 산 서", "손익"]
SJ_BS_KW = ["재 무 상 태 표", "재무상태표", "대 차 대 조 표", "대차대조표"]
SJ_CF_KW = ["현 금 흐 름 표", "현금흐름표"]

def to_억(s):
    if not s or str(s).strip() in ("", "-", "－", "N/A"): return None
    try: return round(int(str(s).replace(",", "").strip()) / 1e8, 1)
    except: return None

def sj_items(raw, kws, excl=None):
    seen, out = set(), []
    for item in raw:
        sj = item.get("sj_nm", "")
        if not any(kw in sj for kw in kws): continue
        if excl and any(ex in sj for ex in excl): continue
        nm = item.get("account_nm", "").strip()
        if not nm or nm in seen: continue
        seen.add(nm)
        out.append({"account_nm": nm, "account_id": item.get("account_id", ""),
                    "curr": to_억(item.get("thstrm_amount")),
                    "prev": to_억(item.get("frmtrm_amount"))})
    return out

def parse_raw(raw):
    if not raw:
        return {"pl": [], "bs": [], "cf": [], "kv": {}}

    # sj_nm 기반 테이블 추출
    pl = (sj_items(raw, SJ_PL_KW, excl=["포괄"])
       or sj_items(raw, ["포괄손익계산서", "포괄 손 익 계 산 서"])
       or sj_items(raw, ["손익"]))
    bs = (sj_items(raw, SJ_BS_KW))
    cf = (sj_items(raw, SJ_CF_KW))

    # XBRL account_id + 한글명으로 KV 딕셔너리 구성
    kv = {}
    for item in raw:
        aid = item.get("account_id", "").strip()
        nm  = item.get("account_nm", "").strip()
        val = to_억(item.get("thstrm_amount"))
        if val is None: continue

        if aid in XBRL_MAP:
            k = XBRL_MAP[aid]
            if k not in kv: kv[k] = val
        elif nm in KOR_MAP:
            k = KOR_MAP[nm]
            if k not in kv: kv[k] = val
        else:
            for kor, k in KOR_MAP.items():
                if kor in nm and k not in kv:
                    kv[k] = val; break

    # sj_nm 분류 실패 시 → kv에서 역구성
    if not pl and any(k in kv for k in ["revenue", "op_income", "net_income"]):
        pl = _kv_to_items(raw, set(list(XBRL_MAP.values())[:12] + list(KOR_MAP.keys())[:12]))
    if not bs and "total_assets" in kv:
        bs = _kv_to_items(raw, {"total_assets", "total_liab", "total_equity",
                                 "current_assets", "noncurrent_assets", "current_liab", "cash"})
    if not cf and "cfo" in kv:
        cf = _kv_to_items(raw, {"cfo", "cfi", "cff", "dep"})

    return {"pl": pl, "bs": bs, "cf": cf, "kv": kv}

def _kv_to_items(raw, target_keys):
    seen, out = set(), []
    for item in raw:
        aid = item.get("account_id", "").strip()
        nm  = item.get("account_nm", "").strip()
        val = to_억(item.get("thstrm_amount"))
        mapped = XBRL_MAP.get(aid) or KOR_MAP.get(nm)
        if mapped and mapped in target_keys and nm not in seen:
            seen.add(nm)
            out.append({"account_nm": nm, "account_id": aid,
                        "curr": val, "prev": to_억(item.get("frmtrm_amount"))})
    return out

def get_val(kv, all_items, *keys):
    for k in keys:
        if k in kv and kv[k] is not None: return kv[k]
    fallbacks = {
        "revenue":      ["매출액","영업수익","수익(매출액)","매출"],
        "gross_profit": ["매출총이익","매출총손익"],
        "op_income":    ["영업이익","영업이익(손실)","영업손익","영업손실"],
        "ebt":          ["법인세비용차감전순이익","법인세비용차감전순이익(손실)","법인세비용차감전순손실"],
        "net_income":   ["당기순이익","당기순이익(손실)","당기순손실"],
        "total_assets": ["자산총계"],
        "total_liab":   ["부채총계"],
        "total_equity": ["자본총계"],
        "cfo":          ["영업활동현금흐름","영업활동 현금흐름"],
        "cfi":          ["투자활동현금흐름","투자활동 현금흐름"],
        "cff":          ["재무활동현금흐름","재무활동 현금흐름"],
        "dep":          ["감가상각비","감가상각비 및 상각비"],
    }
    for k in keys:
        for nm in fallbacks.get(k, []):
            for it in all_items:
                if it["account_nm"] == nm and it["curr"] is not None: return it["curr"]
            for it in all_items:
                if nm in it["account_nm"] and it["curr"] is not None: return it["curr"]
    return None

# ══════════════════════════════════════════════
#  테이블
# ══════════════════════════════════════════════
BOLD_KW = ["매출액","영업수익","수익(매출액)","매출총이익","영업이익","영업이익(손실)",
           "당기순이익","당기순이익(손실)","당기순손실","법인세비용차감전",
           "자산총계","부채총계","자본총계","영업활동","투자활동","재무활동"]

def build_table(ydata, years, key):
    latest = max(years)
    base   = ydata.get(latest, {}).get(key, [])
    if not base:
        for y in reversed(years):
            base = ydata.get(y, {}).get(key, [])
            if base: break
    acnts = [it["account_nm"] for it in base]
    maps  = {yr: {it["account_nm"]: it["curr"]
                  for it in ydata.get(yr, {}).get(key, [])} for yr in years}
    rows  = []
    for ac in acnts:
        row  = {"계정과목": ac}
        vals = []
        for yr in years:
            v = maps[yr].get(ac); row[str(yr)] = v; vals.append(v)
        for i in range(1, len(years)):
            c, p = vals[i], vals[i-1]
            row["YoY " + str(years[i])] = (
                round((c - p) / abs(p) * 100, 1)
                if c is not None and p and p != 0 else None)
        n, s, e = len(years)-1, vals[0], vals[-1]
        try:
            if s and e and s != 0 and n > 0 and (e/s) > 0:
                row["CAGR"] = round(((e/s)**(1/n)-1)*100, 1)
            else:
                row["CAGR"] = None
        except:
            row["CAGR"] = None
        rows.append(row)
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def style_table(df, years):
    def fv(v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
        return "{:,.1f}".format(v)
    def fp(v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
        a = "▲ " if v > 0 else ("▼ " if v < 0 else "")
        return a + "{:.1f}%".format(abs(v))
    yc = [str(y) for y in years]
    disp = df.copy()
    for col in disp.columns:
        if col == "계정과목": continue
        disp[col] = disp[col].apply(fv if col in yc else fp)
    disp = disp.set_index("계정과목")

    def cc(v):
        if not isinstance(v, str) or v == "—":
            return "color:#D1D5DB" if v == "—" else ""
        if "▲" in v: return "color:#059669;font-weight:500"
        if "▼" in v: return "color:#DC2626;font-weight:500"
        try:
            if float(v.replace(",", "")) < 0: return "color:#DC2626"
        except: pass
        return ""

    def cr(row):
        if any(kw in row.name for kw in BOLD_KW):
            return ["font-weight:700;background:#F0F4FF"] * len(row)
        return [""] * len(row)

    return (disp.style.apply(cr, axis=1).map(cc)
            .set_properties(**{"font-size": ".8rem", "padding": "5px 10px"})
            .set_table_styles([
                {"selector": "th", "props": [
                    ("background", "#1A3A6B"), ("color", "white"),
                    ("font-size", ".71rem"), ("font-weight", "600"),
                    ("text-align", "center"), ("padding", "8px 10px"),
                    ("white-space", "nowrap")]},
                {"selector": "th.row_heading", "props": [
                    ("text-align", "left"), ("background", "#F8FAFF"),
                    ("color", "#374151"), ("font-weight", "500"),
                    ("min-width", "160px")]},
                {"selector": "td", "props": [("text-align", "right")]},
                {"selector": "tr:hover td",
                 "props": [("background", "#EFF6FF !important")]},
            ]))

# ══════════════════════════════════════════════
#  KPI 카드 / 차트
# ══════════════════════════════════════════════
def kc(label, val, yoy=None, sub=None, color="blue", pct=False):
    vs = ("{:.1f}%".format(val) if pct else "{:,.0f}억".format(val)) if val is not None else "—"
    vc = "pos" if (val and val >= 0) else ("neg" if (val is not None and val < 0) else "")
    yh = ""
    if yoy is not None:
        a  = "▲" if yoy > 0 else ("▼" if yoy < 0 else "─")
        yc2 = "pos" if yoy > 0 else ("neg" if yoy < 0 else "")
        yh = f"<div class='kpi-yoy {yc2}'>{a} {abs(yoy):.1f}% YoY</div>"
    sh = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    return (f"<div class='kpi-card {color}'>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value {vc}'>{vs}</div>{yh}{sh}</div>")

def yoy_c(c, p):
    if c is None or p is None or p == 0: return None
    return round((c - p) / abs(p) * 100, 1)

def pct_m(v, d):
    if v is None or d is None or d == 0: return None
    return round(v / d * 100, 1)

def make_chart(kmap, years):
    vy  = [y for y in years if kmap.get(y, {}).get("rev") is not None]
    if not vy: return None
    yr  = [str(y) for y in vy]
    rev = [kmap[y].get("rev") or 0 for y in vy]
    op  = [kmap[y].get("op")  or 0 for y in vy]
    ebi = [kmap[y].get("ebi") or 0 for y in vy]
    fig = go.Figure()
    # 매출 — 네이비
    fig.add_trace(go.Bar(name="매출", x=yr, y=rev,
        marker_color="#1A3A6B", opacity=0.85, marker_line_width=0,
        text=["{:,.0f}".format(v) for v in rev],
        textposition="outside", textfont=dict(size=10, color="#1A3A6B")))
    # EBITDA — 주황색
    fig.add_trace(go.Bar(name="EBITDA", x=yr, y=ebi,
        marker_color="#F59E0B", opacity=0.85, marker_line_width=0,
        text=["{:,.0f}".format(v) for v in ebi],
        textposition="outside", textfont=dict(size=10, color="#D97706")))
    # 영업이익 — 초록(흑자) / 빨강(적자)
    fig.add_trace(go.Bar(name="영업이익", x=yr, y=op, opacity=0.85, marker_line_width=0,
        marker_color=["#DC2626" if v < 0 else "#059669" for v in op],
        text=["{:,.0f}".format(v) for v in op],
        textposition="outside", textfont=dict(size=10)))
    fig.update_layout(
        barmode="group", plot_bgcolor="white", paper_bgcolor="white",
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right",
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",", ticksuffix="억", gridcolor="#F3F4F6",
                   zeroline=True, zerolinecolor="#D1D5DB", tickfont=dict(size=10)),
        xaxis=dict(type="category", tickfont=dict(size=11)),
        font=dict(family="Noto Sans KR"))
    return fig

# ══════════════════════════════════════════════
#  사이드바
# ══════════════════════════════════════════════
def sidebar():
    key = api_key()
    with st.sidebar:
        # 헤더
        st.markdown("""
        <div style='padding:1.3rem 0 .9rem;border-bottom:1px solid rgba(255,255,255,.12);margin-bottom:1rem;'>
            <div style='font-size:.58rem;letter-spacing:.15em;color:#93B4D8;font-weight:700;margin-bottom:3px;'>SK SQUARE</div>
            <div style='font-size:.95rem;font-weight:700;color:#FFF;line-height:1.3;'>투자분석<br>재무 대시보드</div>
            <div style='font-size:.65rem;color:#7B9EC4;margin-top:3px;'>DART OpenAPI</div>
        </div>""", unsafe_allow_html=True)

        if not key:
            st.markdown("<div style='background:rgba(220,38,38,.15);border:1px solid rgba(220,38,38,.3);border-radius:8px;padding:10px;font-size:.78rem;color:#FCA5A5;line-height:1.6;'>⚠️ DART_API_KEY 미설정<br><span style='font-size:.7rem;opacity:.8;'>Streamlit Secrets에<br>DART_API_KEY 추가 필요</span></div>",
                        unsafe_allow_html=True)
            return None

        # ── 연도 설정 ──
        st.markdown("<div class='sidebar-lbl'>📅 조회 연도</div>", unsafe_allow_html=True)
        year_opts = [2025, 2024, 2023, 2022, 2021, 2020]
        sel_years = st.multiselect("", year_opts, default=[2022, 2023, 2024, 2025],
                                   key="yrs", label_visibility="collapsed")
        sel_years = sorted(sel_years)

        # ── 연결/개별 ──
        fs_label = st.selectbox("", ["연결 우선 (CFS→OFS)", "개별 우선 (OFS→CFS)"],
                                key="fs", label_visibility="collapsed")
        fs_div = "CFS" if "CFS" in fs_label else "OFS"

        st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)

        # ── 회사 검색 ──
        st.markdown("<div class='sidebar-lbl'>🔍 회사 검색</div>", unsafe_allow_html=True)
        query = st.text_input("", placeholder="회사명 입력 (예: 삼성전자)",
                              key="q", label_visibility="collapsed")
        selected = None
        if query and len(query.strip()) >= 1:
            corps   = load_corps(key)
            results = corp_search(corps, query.strip())
            if results:
                labels = [("📈 " if v["stock_code"] else "🏢 ") + n for n, v in results]
                idx    = st.selectbox("", range(len(labels)),
                                      format_func=lambda i: labels[i],
                                      key="sel", label_visibility="collapsed")
                selected = results[idx]
            else:
                st.markdown("<div style='font-size:.75rem;color:#F87171;'>검색 결과 없음</div>",
                            unsafe_allow_html=True)

        btn = st.button("📡 조회", use_container_width=True)
        if btn:
            if not selected: st.error("회사를 선택해주세요."); return key
            if not sel_years: st.error("연도를 선택해주세요."); return key
            nm, info = selected
            # 비상장사 차단
            if not info["stock_code"]:
                st.session_state.params = {"mode": "unlisted", "name": nm}
                st.session_state.cache  = {}
                st.rerun()
                return key
            st.session_state.params = {
                "mode": "business",
                "name": nm, "corp_code": info["corp_code"],
                "stock_code": info["stock_code"],
                "fs_div": fs_div, "years": sel_years,
            }
            st.session_state.cache = {}
            st.rerun()

        # 하단 안내
        st.markdown("""
        <div style='margin-top:1.5rem;padding-top:.8rem;border-top:1px solid rgba(255,255,255,.1);
        font-size:.62rem;color:#4A6FA5;line-height:1.8;'>
        📌 코스피 · 코스닥 상장사 지원<br>
        📌 DART 사업보고서 기반<br>
        📌 단위: 억원
        </div>""", unsafe_allow_html=True)

    return key

# ══════════════════════════════════════════════
#  데이터 로드
# ══════════════════════════════════════════════
def load_data(key, params):
    mode   = params["mode"]
    years  = params["years"]
    fs_div = params["fs_div"]
    ydata  = {}
    sources = {}

    prog = st.progress(0, text="데이터 로딩 중...")

    for i, yr in enumerate(years):
        prog.progress((i+1)/len(years), text=f"{yr}년 조회 중...")
        corp_code = params["corp_code"]
        raw, rc = fetch_business_report(key, corp_code, yr, fs_div)
        src = rc or "없음"
        parsed = parse_raw(raw)
        ydata[yr]   = parsed
        sources[yr] = src

    prog.empty()
    return ydata, sources

# ══════════════════════════════════════════════
#  메인 화면
# ══════════════════════════════════════════════
def render(key):
    params = st.session_state.get("params")
    if not params:
        st.markdown("""
        <div class='empty-wrap'>
            <div style='font-size:2.5rem;margin-bottom:.8rem;'>📊</div>
            <div style='font-size:1.1rem;font-weight:600;color:#374151;margin-bottom:.4rem;'>SK Square 재무 분석 대시보드</div>
            <div style='font-size:.85rem;'>좌측에서 조회 방식을 선택하고 재무제표를 불러와 주세요</div>
            <div style='margin-top:1.5rem;background:#fff;border-radius:10px;padding:1rem 1.5rem;
                display:inline-block;box-shadow:0 1px 6px rgba(0,0,0,.07);font-size:.82rem;color:#374151;'>
                📈 코스피 · 코스닥 상장사 DART 사업보고서 기반 조회
            </div>
        </div>""", unsafe_allow_html=True)
        return

    name = params["name"]
    mode = params["mode"]

    # ── 비상장사 안내 화면 ──
    if mode == "unlisted":
        st.markdown(
            "<div style='max-width:520px;margin:4rem auto;background:white;border-radius:16px;"
            "padding:2.5rem 2rem;box-shadow:0 4px 20px rgba(0,0,0,0.08);text-align:center;'>"
            "<div style='font-size:2.5rem;margin-bottom:1rem;'>🏢</div>"
            "<div style='font-size:1.15rem;font-weight:700;color:#111827;margin-bottom:.6rem;'>"
            "비상장사는 지원하지 않습니다</div>"
            "<div style='font-size:.88rem;color:#6B7280;line-height:1.7;margin-bottom:1.5rem;'>"
            + name + "은(는) 비상장 법인입니다.<br>코스피·코스닥 상장사만 지원합니다.</div>"
            "<div style='background:#F0F9FF;border:1px solid #BAE6FD;border-radius:10px;"
            "padding:1rem 1.2rem;font-size:.82rem;color:#0369A1;'>💡 상장사 예시:<br>"
            "삼성전자 · SK하이닉스 · 카카오 · NAVER</div></div>",
            unsafe_allow_html=True)
        return

    years  = params["years"]
    fs_div = params["fs_div"]

    # ── 캐시 키 ──
    ckey  = name + "_" + fs_div + "_" + "_".join(map(str, years))
    cache = st.session_state.get("cache", {})

    if ckey not in cache:
        ydata, sources = {}, {}
        prog = st.progress(0, text=f"{name} 데이터 로딩 중...")
        for i, yr in enumerate(years):
            prog.progress((i+1)/len(years), text=f"{yr}년 조회 중...")
            raw, rc = fetch_business_report(key, params["corp_code"], yr, fs_div)
            ydata[yr]   = parse_raw(raw)
            sources[yr] = rc or "없음"
        prog.empty()
        cache[ckey] = {"ydata": ydata, "sources": sources}
        st.session_state.cache = cache
    else:
        ydata   = cache[ckey]["ydata"]
        sources = cache[ckey]["sources"]

    # ── KPI 계산 ──
    kmap = {}
    for yr in years:
        kv   = ydata[yr]["kv"]
        all_ = ydata[yr]["pl"] + ydata[yr]["bs"] + ydata[yr]["cf"]
        rev  = get_val(kv, all_, "revenue")
        op   = get_val(kv, all_, "op_income")
        net  = get_val(kv, all_, "net_income")
        ebt  = get_val(kv, all_, "ebt")
        gp   = get_val(kv, all_, "gross_profit")
        ta   = get_val(kv, all_, "total_assets")
        tl   = get_val(kv, all_, "total_liab")
        eq   = get_val(kv, all_, "total_equity")
        dep  = get_val(kv, all_, "dep") or 0
        ebi  = (op + dep) if op is not None else None
        kmap[yr] = {"rev":rev,"op":op,"op_income":op,"net":net,"net_income":net,
                    "ebt":ebt,"gp":gp,"gross_profit":gp,"ebi":ebi,"dep":dep,
                    "ta":ta,"tl":tl,"total_liab":tl,"eq":eq,"total_equity":eq}

    latest = years[-1]
    prev   = years[-2] if len(years) >= 2 else None
    kl = kmap.get(latest, {}); kp = kmap.get(prev, {}) if prev else {}

    rv = kl.get("rev");  rp  = kp.get("rev")
    ov = kl.get("op");   op_ = kp.get("op")
    nv = kl.get("net");  np_ = kp.get("net")
    bv = kl.get("ebt");  bp  = kp.get("ebt")
    gv = kl.get("gp");   gp_ = kp.get("gp")
    ev = kl.get("ebi");  ep  = kp.get("ebi")
    ta = kl.get("ta");   ta_ = kp.get("ta")
    tl = kl.get("tl")
    eq = kl.get("eq");   eq_ = kp.get("eq")

    om  = pct_m(ov, rv); gm  = pct_m(gv, rv)
    nm_ = pct_m(nv, rv); em  = pct_m(ev, rv)
    de  = round(tl/eq*100,1) if (tl and eq and eq!=0) else None
    roe = pct_m(nv, eq); roa = pct_m(nv, ta)
    at_ = round(rv/ta,2) if (rv and ta and ta!=0) else None

    perf_data = build_perf_summary(kmap, years, name)
    news_list = get_news(name)

    # ── 헤더 ──
    std = "K-IFRS 연결" if fs_div == "CFS" else "K-GAAP 개별"
    src_txt = " · ".join([f"{y}: {sources.get(y,'—')}" for y in years])
    st.markdown(f"<div class='page-title'>{name}</div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='badge b-blue'>상장 📈</span>"
        "<span class='badge b-green'>사업보고서</span>"
        f"<span class='badge b-teal'>{std}</span>"
        f"<span class='badge b-gray'>{min(years)}~{max(years)}</span>",
        unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:.64rem;color:#9CA3AF;margin:4px 0 0;'>조회 소스: {src_txt}</p>",
                unsafe_allow_html=True)
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # KPI Row 1
    st.markdown("<div class='sec'>핵심 손익 지표</div>", unsafe_allow_html=True)
    r1 = "<div class='kpi-row kpi-row-6'>"
    r1 += kc(f"매출 {latest}",       rv, yoy_c(rv, rp), color="blue")
    r1 += kc(f"매출총이익 {latest}",  gv, yoy_c(gv, gp_),
             sub=f"GP margin {gm:.1f}%" if gm else None, color="blue")
    r1 += kc(f"영업이익 {latest}",    ov, yoy_c(ov, op_),
             sub=f"OPM {om:.1f}%" if om else None,
             color="green" if (ov and ov >= 0) else "red")
    r1 += kc(f"EBITDA {latest}",      ev, yoy_c(ev, ep),
             sub=f"margin {em:.1f}%" if em else None, color="teal")
    r1 += kc(f"세전이익 {latest}",    bv, yoy_c(bv, bp), color="amber")
    r1 += kc(f"당기순이익 {latest}",  nv, yoy_c(nv, np_),
             sub=f"NPM {nm_:.1f}%" if nm_ else None,
             color="green" if (nv and nv >= 0) else "red")
    r1 += "</div>"
    st.markdown(r1, unsafe_allow_html=True)

    # KPI Row 2
    st.markdown("<div class='sec'>재무건전성 지표</div>", unsafe_allow_html=True)
    de_s   = f"{de:.1f}%"  if de  is not None else "—"
    roe_s  = f"{roe:.1f}%" if roe is not None else "—"
    roa_s  = f"{roa:.1f}%" if roa is not None else "—"
    at_s   = f"{at_:.2f}x" if at_ is not None else "—"
    de_c   = "red"   if (de  and de  > 200) else "gray"
    roe_c  = "green" if (roe and roe > 0)   else ("red" if (roe and roe < 0) else "gray")
    r2 = "<div class='kpi-row kpi-row-4'>"
    r2 += kc(f"총자산 {latest}",   ta, yoy_c(ta, ta_), color="gray")
    r2 += kc(f"자본총계 {latest}", eq, yoy_c(eq, eq_), color="gray")
    r2 += (f"<div class='kpi-card {de_c}'>"
           f"<div class='kpi-label'>부채비율 {latest}</div>"
           f"<div class='kpi-value'>{de_s}</div>"
           f"<div class='kpi-sub'>부채 / 자본 × 100</div></div>")
    r2 += (f"<div class='kpi-card {roe_c}'>"
           f"<div class='kpi-label'>ROE / ROA {latest}</div>"
           f"<div class='kpi-value'>{roe_s}</div>"
           f"<div class='kpi-sub'>ROA {roa_s} · 자산회전율 {at_s}</div></div>")
    r2 += "</div>"
    st.markdown(r2, unsafe_allow_html=True)

    # 차트
    st.markdown("<div class='sec'>수익성 추이 | 단위: 억원</div>", unsafe_allow_html=True)
    fig = make_chart(kmap, years)
    if fig:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 실적 변화 + 뉴스 ──
    col_perf, col_news_panel = st.columns([1.6, 1])

    with col_perf:
        if perf_data and perf_data.get("items"):
            prev_yr   = str(perf_data["prev"])
            latest_yr = str(perf_data["latest"])
            st.markdown("<div class='sec'>" + prev_yr + " → " + latest_yr + " 실적 변화</div>",
                        unsafe_allow_html=True)
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(
                "<div style='display:grid;grid-template-columns:90px 1fr 1fr 65px;"
                "gap:.4rem;padding:.3rem .5rem;background:#F8FAFF;border-radius:6px;"
                "margin-bottom:3px;font-size:.66rem;color:#9CA3AF;'>"
                "<span>항목</span>"
                "<span style='text-align:right;'>최근(" + latest_yr + ")</span>"
                "<span style='text-align:right;'>전년비</span>"
                "<span style='text-align:right;'>증감률</span></div>",
                unsafe_allow_html=True)
            for item in perf_data["items"]:
                clr = item["color"]
                st.markdown(
                    "<div style='display:grid;grid-template-columns:90px 1fr 1fr 65px;"
                    "gap:.4rem;padding:.3rem .5rem;border-radius:6px;'>"
                    "<span style='font-size:.77rem;color:#374151;font-weight:500;'>" + item["label"] + "</span>"
                    "<span style='font-size:.79rem;font-weight:700;color:#111;text-align:right;'>" + item["curr"] + "</span>"
                    "<span style='font-size:.77rem;font-weight:600;color:" + clr + ";text-align:right;'>" + item["arrow"] + " " + item["diff"] + "</span>"
                    "<span style='font-size:.77rem;font-weight:600;color:" + clr + ";text-align:right;'>" + item["pct"] + "</span>"
                    "</div>",
                    unsafe_allow_html=True)
            issues = perf_data.get("issues", [])
            if issues:
                st.markdown("<div style='margin-top:.6rem;border-top:1px solid #F3F4F6;padding-top:.5rem;'>",
                            unsafe_allow_html=True)
                for iss in issues:
                    st.markdown("<div class='issue-item'>" + iss + "</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_news_panel:
        st.markdown("<div class='sec'>최신 뉴스</div>", unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if news_list:
            for nw in news_list:
                title = nw["title"].split(" - ")[0]
                src_tag = "<span class='news-source'>" + nw["source"] + "</span>" if nw.get("source") else ""
                st.markdown(
                    "<div class='news-item'><div style='flex:1;'>"
                    "<div class='news-title'><a href='" + nw["link"] + "' target='_blank'>" + title + "</a></div>"
                    "<div style='display:flex;gap:.4rem;margin-top:3px;align-items:center;'>"
                    "<span class='news-date'>" + nw["date"] + "</span>" + src_tag +
                    "</div></div></div>",
                    unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:.8rem;color:#9CA3AF;text-align:center;padding:2rem 1rem;'>뉴스를 불러올 수 없습니다</div>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 재무제표 3종
    for tkey, title, hd in [
        ("pl", "손익계산서 (P&L)", "sec"),
        ("bs", "재무상태표 (B/S)", "sec teal"),
        ("cf", "현금흐름표 (C/F)", "sec amber"),
    ]:
        st.markdown(f"<div class='{hd}'>{title} | 단위: 억원 · DART 원본</div>",
                    unsafe_allow_html=True)
        df = build_table(ydata, years, tkey)
        if df.empty:
            st.info(f"{tkey.upper()} 데이터 없음")
            continue
        yc   = [str(y) for y in years]
        yoc  = ["YoY " + str(y) for y in years[1:]]
        cols = ["계정과목"] + yc + yoc + ["CAGR"]
        df   = df[[c for c in cols if c in df.columns]]
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        h = min(max(len(df) * 34 + 56, 220), 620)
        st.dataframe(style_table(df, years), use_container_width=True, height=h)
        std2 = "연결" if fs_div == "CFS" else "개별"
        st.markdown(
            f"<p class='tbl-note'>DART OpenAPI {std2} {tkey.upper()} · "
            f"YoY: 전년 대비 증감률 · CAGR: {min(years)}→{max(years)}</p>",
            unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 디버그
    with st.expander("🔧 DEBUG", expanded=False):
        for yr in years:
            kv    = ydata.get(yr, {}).get("kv", {})
            pl_n  = len(ydata.get(yr, {}).get("pl", []))
            bs_n  = len(ydata.get(yr, {}).get("bs", []))
            cf_n  = len(ydata.get(yr, {}).get("cf", []))
            st.markdown(f"**{yr}**: `{sources.get(yr,'—')}` | PL:{pl_n} BS:{bs_n} CF:{cf_n} | KV: {list(kv.keys())[:10]}")

# ══════════════════════════════════════════════
#  앱 실행
# ══════════════════════════════════════════════
def main():
    for k, v in [("params", None), ("cache", {})]:
        if k not in st.session_state:
            st.session_state[k] = v
    k = sidebar()
    if k:
        render(k)

if __name__ == "__main__":
    main()
