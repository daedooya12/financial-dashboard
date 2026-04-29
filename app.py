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
html,body,[class*="css"],.stApp{font-family:'Noto Sans KR',sans-serif;background:#F0F2F8;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F2447 0%,#1A3A6B 60%,#1e4d8c 100%);border-right:none;}
[data-testid="stSidebar"] *{color:#E8EEF8 !important;}
[data-testid="stSidebar"] input[type="text"]{background:#fff !important;color:#1A3A6B !important;border:none !important;border-radius:8px !important;font-size:.88rem !important;}
[data-testid="stSidebar"] input[type="text"]::placeholder{color:#9CA3AF !important;}
[data-testid="stSidebar"] div[data-baseweb="select"]>div:first-child{background:#fff !important;border-radius:8px !important;border:none !important;}
[data-testid="stSidebar"] div[data-baseweb="select"] span,[data-testid="stSidebar"] div[data-baseweb="select"] div{color:#1A3A6B !important;}
[data-testid="stSidebar"] div[data-testid="stButton"] button{width:100% !important;background:#3B82F6 !important;color:#fff !important;border:none !important;border-radius:8px !important;font-size:.85rem !important;font-weight:600 !important;padding:.55rem 1rem !important;}
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover{background:#2563EB !important;}
.main .block-container{padding:1.5rem 2rem 3rem 2rem;max-width:100%;}
.kpi-row{display:grid;gap:12px;margin-bottom:1rem;}
.kpi-row-6{grid-template-columns:repeat(6,1fr);}
.kpi-row-4{grid-template-columns:repeat(4,1fr);}
.kpi-card{background:white;border-radius:12px;padding:1.1rem 1.2rem;border-top:3px solid #1A3A6B;box-shadow:0 2px 8px rgba(0,0,0,.06);}
.kpi-card.blue{border-top-color:#1A3A6B;}.kpi-card.green{border-top-color:#059669;}.kpi-card.red{border-top-color:#DC2626;}
.kpi-card.teal{border-top-color:#0D9488;}.kpi-card.amber{border-top-color:#D97706;}.kpi-card.gray{border-top-color:#6B7280;}
.kpi-label{font-size:.67rem;color:#9CA3AF;font-weight:600;letter-spacing:.05em;text-transform:uppercase;margin-bottom:5px;}
.kpi-value{font-size:1.3rem;font-weight:700;color:#111827;line-height:1;margin-bottom:3px;}
.kpi-value.pos{color:#059669;}.kpi-value.neg{color:#DC2626;}
.kpi-yoy{font-size:.73rem;font-weight:500;}.kpi-yoy.pos{color:#059669;}.kpi-yoy.neg{color:#DC2626;}
.kpi-sub{font-size:.68rem;color:#9CA3AF;margin-top:2px;}
.section-hd{font-size:.74rem;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.07em;border-left:3px solid #1A3A6B;padding-left:10px;margin:1.8rem 0 .8rem 0;}
.section-hd.teal{border-left-color:#0D9488;}.section-hd.amber{border-left-color:#D97706;}
.badge{display:inline-block;border-radius:4px;padding:3px 10px;font-size:.72rem;font-weight:600;margin-right:4px;}
.badge-blue{background:#DBEAFE;color:#1E40AF;}.badge-teal{background:#CCFBF1;color:#0F766E;}
.badge-gray{background:#F3F4F6;color:#374151;}.badge-green{background:#DCFCE7;color:#166534;}
.chart-wrap{background:white;border-radius:14px;padding:1.4rem;box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:1rem;}
.tbl-wrap{background:white;border-radius:14px;padding:1.4rem;box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:1rem;}
.tbl-note{font-size:.69rem;color:#9CA3AF;margin-top:.7rem;}
.page-title{font-size:1.5rem;font-weight:700;color:#111827;margin-bottom:.3rem;}
.empty-state{text-align:center;padding:5rem 2rem;color:#9CA3AF;}
.sidebar-lbl{font-size:.62rem;letter-spacing:.1em;color:#7B9EC4;font-weight:700;margin-bottom:5px;text-transform:uppercase;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  XBRL account_id → 표준 key 매핑
#  IFRS / K-IFRS / K-GAAP 혼합 대응
# ══════════════════════════════════════════════
XBRL_PL = {
    # 매출
    "ifrs-full_Revenue":                                    "revenue",
    "ifrs_Revenue":                                         "revenue",
    "dart_OperatingRevenue":                                "revenue",
    "ifrs-full_RevenueFromContractsWithCustomers":          "revenue",
    # 매출원가
    "ifrs-full_CostOfSales":                                "cogs",
    # 매출총이익
    "ifrs-full_GrossProfit":                                "gross_profit",
    # 판관비
    "ifrs-full_SellingGeneralAndAdministrativeExpense":     "sga",
    # 영업이익
    "dart_OperatingIncomeLoss":                             "operating_income",
    "ifrs-full_ProfitLossFromOperatingActivities":          "operating_income",
    "ifrs-full_OperatingIncomeLoss":                        "operating_income",
    # 금융수익/비용
    "ifrs-full_FinanceIncome":                              "finance_income",
    "ifrs-full_FinanceCosts":                               "finance_costs",
    # 세전이익
    "ifrs-full_ProfitLossBeforeTax":                        "ebt",
    # 법인세
    "ifrs-full_IncomeTaxExpenseContinuingOperations":       "tax",
    # 당기순이익
    "ifrs-full_ProfitLoss":                                 "net_income",
    "ifrs-full_ProfitLossAttributableToOwnersOfParent":     "net_income_parent",
}

XBRL_BS = {
    # 자산
    "ifrs-full_Assets":                                     "total_assets",
    "ifrs-full_CurrentAssets":                              "current_assets",
    "ifrs-full_NoncurrentAssets":                           "noncurrent_assets",
    "ifrs-full_CashAndCashEquivalents":                     "cash",
    # 부채
    "ifrs-full_Liabilities":                                "total_liabilities",
    "ifrs-full_CurrentLiabilities":                         "current_liabilities",
    "ifrs-full_NoncurrentLiabilities":                      "noncurrent_liabilities",
    # 자본
    "ifrs-full_Equity":                                     "total_equity",
    "ifrs-full_EquityAttributableToOwnersOfParent":         "equity_parent",
    "ifrs-full_IssuedCapital":                              "capital",
    "ifrs-full_RetainedEarnings":                           "retained_earnings",
}

XBRL_CF = {
    "ifrs-full_CashFlowsFromUsedInOperatingActivities":     "cfo",
    "ifrs-full_CashFlowsFromUsedInInvestingActivities":     "cfi",
    "ifrs-full_CashFlowsFromUsedInFinancingActivities":     "cff",
    "ifrs-full_IncreaseDecreaseInCashAndCashEquivalents":   "net_cash_change",
    # 감가상각 (영업CF 조정 항목)
    "ifrs-full_AdjustmentsForDepreciationAndAmortisationExpense": "dep_amort",
    "ifrs-full_DepreciationAndAmortisationExpense":          "dep_amort",
    "dart_DepreciationAndAmortisation":                      "dep_amort",
}

# 한글 계정명 → key (fallback)
KOR_PL = {
    "매출액":           "revenue", "영업수익":         "revenue",
    "수익(매출액)":     "revenue", "매출":             "revenue",
    "매출원가":         "cogs",
    "매출총이익":       "gross_profit", "매출총손익":   "gross_profit",
    "판매비와관리비":   "sga",    "판관비":            "sga",
    "영업이익":         "operating_income", "영업이익(손실)": "operating_income",
    "영업손익":         "operating_income", "영업손실": "operating_income",
    "법인세비용차감전순이익":        "ebt",
    "법인세비용차감전순이익(손실)":  "ebt",
    "법인세비용차감전순손실":        "ebt",
    "당기순이익":       "net_income", "당기순이익(손실)": "net_income",
    "당기순손실":       "net_income",
}
KOR_BS = {
    "자산총계": "total_assets", "부채총계": "total_liabilities",
    "자본총계": "total_equity", "현금및현금성자산": "cash",
    "유동자산": "current_assets", "비유동자산": "noncurrent_assets",
    "유동부채": "current_liabilities", "비유동부채": "noncurrent_liabilities",
}
KOR_CF = {
    "영업활동 현금흐름": "cfo", "영업활동현금흐름": "cfo",
    "투자활동 현금흐름": "cfi", "투자활동현금흐름": "cfi",
    "재무활동 현금흐름": "cff", "재무활동현금흐름": "cff",
    "감가상각비": "dep_amort", "감가상각비 및 상각비": "dep_amort",
}

# ══════════════════════════════════════════════
#  DART API
# ══════════════════════════════════════════════
DART = "https://opendart.fss.or.kr/api"

def api_key():
    try:    return st.secrets["DART_API_KEY"]
    except: return os.environ.get("DART_API_KEY","")

@st.cache_data(ttl=86400, show_spinner=False)
def load_corps(key):
    try:
        r = requests.get(f"{DART}/corpCode.xml", params={"crtfc_key":key}, timeout=30)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        root = ET.fromstring(z.read("CORPCODE.xml"))
        out={}
        for item in root.findall("list"):
            n=item.findtext("corp_name","").strip()
            c=item.findtext("corp_code","").strip()
            s=item.findtext("stock_code","").strip()
            if n and c: out[n]={"corp_code":c,"stock_code":s}
        return out
    except: return {}

def corp_search(corps, q):
    q=q.strip()
    if not q: return []
    exact  =[(k,v) for k,v in corps.items() if k==q]
    partial=[(k,v) for k,v in corps.items() if q in k and k!=q]
    return (exact+partial)[:10]

@st.cache_data(ttl=3600, show_spinner=False)
def get_report_list(key, corp_code, year):
    """해당 연도 보고서 목록 (사업보고서 + 감사보고서)"""
    found={}
    for pt in ["A","B"]:
        try:
            r=requests.get(f"{DART}/list.json", params={
                "crtfc_key":key,"corp_code":corp_code,
                "bgn_de":f"{year}0101","end_de":f"{year+1}0630",
                "pblntf_ty":pt,"page_count":"20"
            }, timeout=15)
            d=r.json()
            if d.get("status")=="000":
                for it in d.get("list",[]):
                    nm=it.get("report_nm",""); rcp=it.get("rcept_no","")
                    if not rcp: continue
                    if "사업보고서" in nm and "사업" not in found:   found["사업보고서"]=rcp
                    if "연결감사보고서" in nm and "연결감사" not in found: found["연결감사보고서"]=rcp
                    if "감사보고서" in nm and "감사" not in found:   found["감사보고서"]=rcp
        except: pass
    return found

@st.cache_data(ttl=3600, show_spinner=False)
def call_singl(key, corp_code, year, reprt_code, fs_div):
    try:
        r=requests.get(f"{DART}/fnlttSinglAcntAll.json", params={
            "crtfc_key":key,"corp_code":corp_code,
            "bsns_year":str(year),"reprt_code":reprt_code,"fs_div":fs_div
        }, timeout=30)
        d=r.json()
        if d.get("status")=="000": return d.get("list",[])
    except: pass
    return []

@st.cache_data(ttl=3600, show_spinner=False)
def call_xbrl_rcp(key, rcp_no, fs_div):
    """rcpNo 기반 XBRL 전체 재무제표"""
    for ep in ["fnlttXbrlAll.json","fnlttSinglAcntAll.json"]:
        try:
            r=requests.get(f"{DART}/{ep}", params={
                "crtfc_key":key,"rcpNo":rcp_no,"fs_div":fs_div
            }, timeout=30)
            d=r.json()
            if d.get("status")=="000":
                data=d.get("list",[])
                if data: return data, ep
        except: pass
    return [], None

@st.cache_data(ttl=3600, show_spinner=False)
def call_xbrl_corp(key, corp_code, year, fs_div):
    """corp_code + year 기반 XBRL (사업보고서 없어도 동작)"""
    try:
        r=requests.get(f"{DART}/fnlttXbrlAll.json", params={
            "crtfc_key":key,"corp_code":corp_code,
            "bsns_year":str(year),"reprt_code":"11011","fs_div":fs_div
        }, timeout=30)
        d=r.json()
        if d.get("status")=="000":
            data=d.get("list",[])
            if data: return data
    except: pass
    return []

def fetch_smart(key, corp_code, year, fs_div):
    """
    우선순위:
    1. fnlttSinglAcntAll (사업보고서 기반, 상장사)
    2. fnlttXbrlAll by corp_code+year
    3. 감사보고서 rcpNo → fnlttXbrlAll / fnlttSinglAcntAll
    연결/개별 모두 시도
    """
    divs=[fs_div, "OFS" if fs_div=="CFS" else "CFS"]

    # 1) 사업보고서
    for rc in ["11011","11012","11013","11014"]:
        for fd in divs:
            d=call_singl(key, corp_code, year, rc, fd)
            if d: return d, f"사업보고서({rc}/{fd})"

    # 2) XBRL by corp+year
    for fd in divs:
        d=call_xbrl_corp(key, corp_code, year, fd)
        if d: return d, f"XBRL-corp({fd})"

    # 3) 감사보고서 rcpNo
    rpts=get_report_list(key, corp_code, year)
    rcp=rpts.get("연결감사보고서") or rpts.get("감사보고서")
    if rcp:
        for fd in divs:
            d, ep=call_xbrl_rcp(key, rcp, fd)
            if d: return d, f"감사보고서-XBRL({rcp[:6]}…/{fd})"

    return [], "없음"

# ══════════════════════════════════════════════
#  파싱: account_id 우선, 한글명 fallback
# ══════════════════════════════════════════════
def to_억(s):
    if not s or str(s).strip() in ("","-","－","N/A"): return None
    try: return round(int(str(s).replace(",","").strip())/1e8,1)
    except: return None

def parse_raw(raw):
    """
    raw 항목 리스트에서 PL/BS/CF를 두 가지 방식으로 추출:
    1) account_id XBRL 태그 매핑
    2) sj_nm + account_nm 키워드 매핑 (fallback)
    반환: {"pl": [...], "bs": [...], "cf": [...], "kv": {key:value}}
    """
    if not raw:
        return {"pl":[],"bs":[],"cf":[],"kv":{}}

    # ── sj_nm으로 구분 (원본 표 구조 보존용) ──
    def by_sj(*kws, excl=None):
        seen,out=[],[]
        for item in raw:
            sj=item.get("sj_nm","")
            nm=item.get("account_nm","").strip()
            if not any(kw in sj for kw in kws): continue
            if excl and any(ex in sj for ex in excl): continue
            if nm in seen: continue
            seen.append(nm)
            out.append({"account_nm":nm,"account_id":item.get("account_id",""),
                        "curr":to_억(item.get("thstrm_amount")),
                        "prev":to_억(item.get("frmtrm_amount"))})
        return out

    pl_items = (by_sj("손 익 계 산 서","손익계산서", excl=["포괄"])
             or by_sj("포괄손익계산서","포괄 손 익 계 산 서")
             or by_sj("손익"))
    bs_items = (by_sj("재 무 상 태 표","재무상태표")
             or by_sj("대 차 대 조 표","대차대조표"))
    cf_items = (by_sj("현 금 흐 름 표","현금흐름표"))

    # ── account_id XBRL 매핑으로 key:value 추출 ──
    kv={}
    all_maps = {**XBRL_PL, **XBRL_BS, **XBRL_CF}
    kor_maps  = {**KOR_PL,  **KOR_BS,  **KOR_CF}

    for item in raw:
        acc_id = item.get("account_id","").strip()
        acc_nm = item.get("account_nm","").strip()
        val    = to_억(item.get("thstrm_amount"))
        if val is None: continue

        # XBRL 태그 매핑
        if acc_id in all_maps:
            k=all_maps[acc_id]
            if k not in kv: kv[k]=val
            continue

        # 한글 계정명 정확 매핑
        if acc_nm in kor_maps:
            k=kor_maps[acc_nm]
            if k not in kv: kv[k]=val
            continue

        # 부분 매핑 (포함 여부)
        for kor, k in kor_maps.items():
            if kor in acc_nm and k not in kv:
                kv[k]=val; break

    # sj_nm 기반 항목이 없으면 → account_id로 재구성
    if not pl_items:
        pl_items=_rebuild_from_xbrl(raw, XBRL_PL, KOR_PL)
    if not bs_items:
        bs_items=_rebuild_from_xbrl(raw, XBRL_BS, KOR_BS)
    if not cf_items:
        cf_items=_rebuild_from_xbrl(raw, XBRL_CF, KOR_CF)

    return {"pl":pl_items,"bs":bs_items,"cf":cf_items,"kv":kv}

def _rebuild_from_xbrl(raw, xbrl_map, kor_map):
    """account_id나 한글명으로 항목 재구성 (sj_nm 없을 때)"""
    seen,out={},[]
    for item in raw:
        acc_id=item.get("account_id","").strip()
        acc_nm=item.get("account_nm","").strip()
        val=to_억(item.get("thstrm_amount"))

        label=None
        if acc_id in xbrl_map: label=acc_nm or acc_id
        elif acc_nm in kor_map: label=acc_nm
        else:
            for kor in kor_map:
                if kor in acc_nm: label=acc_nm; break

        if label and label not in seen:
            seen[label]=True
            out.append({"account_nm":acc_nm,"account_id":acc_id,
                        "curr":val,"prev":to_억(item.get("frmtrm_amount"))})
    return out

def get_kv_val(kv, pl, *keys):
    """kv dict 우선, 없으면 pl/bs/cf 항목에서 찾기"""
    for k in keys:
        if k in kv and kv[k] is not None: return kv[k]
    # 한글 account_nm에서 직접 찾기
    kor_keys_map={
        "revenue":          ["매출액","영업수익","수익(매출액)","매출"],
        "gross_profit":     ["매출총이익","매출총손익"],
        "operating_income": ["영업이익","영업이익(손실)","영업손익","영업손실"],
        "ebt":              ["법인세비용차감전순이익","법인세비용차감전순이익(손실)","법인세비용차감전순손실"],
        "net_income":       ["당기순이익","당기순이익(손실)","당기순손실"],
        "total_assets":     ["자산총계"],
        "total_liabilities":["부채총계"],
        "total_equity":     ["자본총계"],
        "cfo":              ["영업활동 현금흐름","영업활동현금흐름","영업활동으로 인한 현금흐름"],
        "cfi":              ["투자활동 현금흐름","투자활동현금흐름","투자활동으로 인한 현금흐름"],
        "cff":              ["재무활동 현금흐름","재무활동현금흐름","재무활동으로 인한 현금흐름"],
        "dep_amort":        ["감가상각비","감가상각비 및 상각비","유형자산감가상각비"],
    }
    for k in keys:
        nms=kor_keys_map.get(k,[])
        for nm in nms:
            for it in pl:
                if it["account_nm"]==nm and it["curr"] is not None: return it["curr"]
            for it in pl:
                if nm in it["account_nm"] and it["curr"] is not None: return it["curr"]
    return None

# ══════════════════════════════════════════════
#  테이블 / 스타일
# ══════════════════════════════════════════════
BOLD_KW=["매출액","영업수익","수익(매출액)","매출총이익","영업이익","영업이익(손실)",
         "당기순이익","당기순이익(손실)","당기순손실","법인세비용차감전",
         "자산총계","부채총계","자본총계","영업활동","투자활동","재무활동"]

def build_table(ydata, years, key):
    latest=max(years)
    base=ydata.get(latest,{}).get(key,[])
    if not base:
        for y in reversed(years):
            base=ydata.get(y,{}).get(key,[])
            if base: break
    acnts=[it["account_nm"] for it in base]
    maps={yr:{it["account_nm"]:it["curr"] for it in ydata.get(yr,{}).get(key,[])} for yr in years}
    rows=[]
    for ac in acnts:
        row={"계정과목":ac}
        vals=[]
        for yr in years:
            v=maps[yr].get(ac); row[str(yr)]=v; vals.append(v)
        for i in range(1,len(years)):
            c,p=vals[i],vals[i-1]
            row["YoY "+str(years[i])]=round((c-p)/abs(p)*100,1) if (c is not None and p and p!=0) else None
        n=len(years)-1; s,e=vals[0],vals[-1]
        row["CAGR"]=round(((e/s)**(1/n)-1)*100,1) if (s and e and s!=0 and n>0) else None
        rows.append(row)
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def style_df(df, years):
    def fv(v):
        if v is None or (isinstance(v,float) and np.isnan(v)): return "—"
        return "{:,.1f}".format(v)
    def fp(v):
        if v is None or (isinstance(v,float) and np.isnan(v)): return "—"
        arr="▲ " if v>0 else ("▼ " if v<0 else "")
        return arr+"{:.1f}%".format(abs(v))
    yc=[str(y) for y in years]
    disp=df.copy()
    for col in disp.columns:
        if col=="계정과목": continue
        disp[col]=disp[col].apply(fv if col in yc else fp)
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
        .set_properties(**{"font-size":".81rem","padding":"5px 10px"})
        .set_table_styles([
            {"selector":"th","props":[("background","#1A3A6B"),("color","white"),
             ("font-size",".72rem"),("font-weight","600"),("text-align","center"),
             ("padding","8px 10px"),("white-space","nowrap")]},
            {"selector":"th.row_heading","props":[("text-align","left"),("background","#F8FAFF"),
             ("color","#374151"),("font-weight","500"),("min-width","180px")]},
            {"selector":"td","props":[("text-align","right")]},
            {"selector":"tr:hover td","props":[("background","#EFF6FF !important")]},
        ]))

# ══════════════════════════════════════════════
#  KPI 카드 / 차트
# ══════════════════════════════════════════════
def kpi_card(label, val, yoy=None, sub=None, color="blue", is_pct=False):
    if is_pct:
        vs=("{:.1f}%".format(val)) if val is not None else "—"
        vc="pos" if (val and val>0) else ("neg" if (val and val<0) else "")
    else:
        vs=("{:,.0f}억".format(val)) if val is not None else "—"
        vc="neg" if (val is not None and val<0) else "pos"
    yh=""
    if yoy is not None:
        arr="▲" if yoy>0 else ("▼" if yoy<0 else "─")
        yc="pos" if yoy>0 else ("neg" if yoy<0 else "")
        yh=f"<div class='kpi-yoy {yc}'>{arr} {abs(yoy):.1f}% YoY</div>"
    sh=(f"<div class='kpi-sub'>{sub}</div>") if sub else ""
    return (f"<div class='kpi-card {color}'>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value {vc}'>{vs}</div>{yh}{sh}</div>")

def yoy_c(c,p):
    if c is None or p is None or p==0: return None
    return round((c-p)/abs(p)*100,1)
def pct(v,d):
    if v is None or d is None or d==0: return None
    return round(v/d*100,1)

def make_chart(kmap, years):
    vy=[y for y in years if kmap.get(y,{}).get("rev") is not None]
    if not vy: return None
    yr=[str(y) for y in vy]
    rev=[kmap[y].get("rev") or 0 for y in vy]
    op =[kmap[y].get("op")  or 0 for y in vy]
    net=[kmap[y].get("net") or 0 for y in vy]
    ebi=[kmap[y].get("ebi") or 0 for y in vy]
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
    fig.update_layout(barmode="group",plot_bgcolor="white",paper_bgcolor="white",
        height=320,margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h",y=1.02,x=1,xanchor="right",
                    font=dict(size=11),bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",",ticksuffix="억",gridcolor="#F3F4F6",
                   zeroline=True,zerolinecolor="#D1D5DB",tickfont=dict(size=11)),
        xaxis=dict(type="category",tickfont=dict(size=12)),
        font=dict(family="Noto Sans KR"))
    return fig

# ══════════════════════════════════════════════
#  사이드바
# ══════════════════════════════════════════════
def sidebar():
    key=api_key()
    with st.sidebar:
        st.markdown("""
        <div style='padding:1.4rem 0 1rem 0;border-bottom:1px solid rgba(255,255,255,0.12);margin-bottom:1.1rem;'>
        <div style='font-size:.6rem;letter-spacing:.14em;color:#93B4D8;font-weight:700;margin-bottom:4px;'>SK SQUARE</div>
        <div style='font-size:.98rem;font-weight:700;color:#FFF;line-height:1.35;'>투자분석 재무 대시보드</div>
        <div style='font-size:.67rem;color:#7B9EC4;margin-top:4px;'>DART OpenAPI 기반</div></div>
        """, unsafe_allow_html=True)

        if not key:
            st.markdown("<div style='background:rgba(220,38,38,.15);border:1px solid rgba(220,38,38,.3);border-radius:8px;padding:10px;font-size:.78rem;color:#FCA5A5;'>⚠️ DART_API_KEY 미설정</div>",unsafe_allow_html=True)
            return None

        st.markdown("<div class='sidebar-lbl'>🔍 Company Search</div>",unsafe_allow_html=True)
        query=st.text_input("",placeholder="회사명 입력",key="q",label_visibility="collapsed")

        selected=None
        if query and len(query.strip())>=1:
            corps=load_corps(key)
            results=corp_search(corps,query.strip())
            if results:
                labels=[("(📈) " if v["stock_code"] else "(🏢) ")+n for n,v in results]
                idx=st.selectbox("",range(len(labels)),format_func=lambda i:labels[i],
                                 key="sel",label_visibility="collapsed")
                selected=results[idx]
            else:
                st.markdown("<div style='font-size:.78rem;color:#F87171;'>검색 결과 없음</div>",unsafe_allow_html=True)

        st.markdown("<div class='sidebar-lbl' style='margin-top:.9rem;'>⚙️ Settings</div>",unsafe_allow_html=True)
        fs_label=st.selectbox("",["연결 우선 (CFS→OFS)","개별 우선 (OFS→CFS)"],
                              key="fs",label_visibility="collapsed")
        fs_div="CFS" if "CFS" in fs_label else "OFS"

        year_opts=[2025,2024,2023,2022,2021,2020]
        sel_years=st.multiselect("",year_opts,default=[2022,2023,2024,2025],
                                 key="yrs",label_visibility="collapsed")

        st.markdown("<div style='height:.4rem'></div>",unsafe_allow_html=True)
        btn=st.button("📡  재무제표 조회",use_container_width=True)

        if btn:
            if not selected: st.error("회사를 선택해주세요."); return key
            if not sel_years: st.error("연도를 선택해주세요."); return key
            nm,info=selected
            st.session_state.params={"name":nm,"corp_code":info["corp_code"],
                                     "stock_code":info["stock_code"],
                                     "fs_div":fs_div,"years":sorted(sel_years)}
            st.session_state.cache={}
            st.rerun()

        st.markdown("""
        <div style='margin-top:1.5rem;padding-top:.8rem;border-top:1px solid rgba(255,255,255,.1);
        font-size:.63rem;color:#4A6FA5;line-height:1.9;'>
        📌 사업보고서 → XBRL → 감사보고서 순 자동 탐색<br>
        📌 account_id(XBRL) + 한글명 이중 파싱<br>
        📌 연결↔개별 자동 전환<br>
        📌 단위: 억원
        </div>""",unsafe_allow_html=True)
    return key

# ══════════════════════════════════════════════
#  메인
# ══════════════════════════════════════════════
def main_view(key):
    params=st.session_state.get("params")
    if not params:
        st.markdown("""<div class='empty-state'>
        <div style='font-size:3rem;margin-bottom:1rem;'>📊</div>
        <div style='font-size:1.1rem;font-weight:600;color:#374151;margin-bottom:.5rem;'>SK Square 재무 분석 대시보드</div>
        <div style='font-size:.85rem;'>좌측에서 회사명을 검색하고 조회 버튼을 눌러주세요</div>
        </div>""",unsafe_allow_html=True)
        return

    name=params["name"]; corp_code=params["corp_code"]
    fs_div=params["fs_div"]; years=params["years"]

    ckey=f"{corp_code}_{fs_div}_{'_'.join(map(str,years))}"
    cache=st.session_state.get("cache",{})

    if ckey not in cache:
        ydata={}; sources={}
        prog=st.progress(0,text=f"{name} 데이터 로딩 중...")
        for i,yr in enumerate(years):
            prog.progress((i+1)/len(years),text=f"{yr}년 조회 중...")
            raw,src=fetch_smart(key,corp_code,yr,fs_div)
            parsed=parse_raw(raw)
            ydata[yr]=parsed; sources[yr]=src
        prog.empty()
        cache[ckey]={"ydata":ydata,"sources":sources}
        st.session_state.cache=cache
    else:
        ydata=cache[ckey]["ydata"]; sources=cache[ckey]["sources"]

    # ── KPI 수집 ──
    kmap={}
    for yr in years:
        kv =ydata[yr]["kv"]
        pl =ydata[yr]["pl"]
        bs =ydata[yr]["bs"]
        cf =ydata[yr]["cf"]
        all_items=pl+bs+cf
        rev=get_kv_val(kv,all_items,"revenue")
        op =get_kv_val(kv,all_items,"operating_income")
        net=get_kv_val(kv,all_items,"net_income")
        ebt=get_kv_val(kv,all_items,"ebt")
        gp =get_kv_val(kv,all_items,"gross_profit")
        ta =get_kv_val(kv,all_items,"total_assets")
        tl =get_kv_val(kv,all_items,"total_liabilities")
        eq =get_kv_val(kv,all_items,"total_equity")
        dep=get_kv_val(kv,all_items,"dep_amort") or 0
        ebi=(op+dep) if op is not None else None
        kmap[yr]={"rev":rev,"op":op,"net":net,"ebt":ebt,"gp":gp,
                  "ebi":ebi,"dep":dep,"ta":ta,"tl":tl,"eq":eq}

    latest=years[-1]; prev=years[-2] if len(years)>=2 else None
    kl=kmap.get(latest,{}); kp=kmap.get(prev,{}) if prev else {}
    rv,rp=kl.get("rev"),kp.get("rev"); ov,op_=kl.get("op"),kp.get("op")
    nv,np_=kl.get("net"),kp.get("net"); bv,bp=kl.get("ebt"),kp.get("ebt")
    gv,gp_=kl.get("gp"),kp.get("gp"); ev,ep=kl.get("ebi"),kp.get("ebi")
    ta,ta_p=kl.get("ta"),kp.get("ta"); tl=kl.get("tl")
    eq,eq_p=kl.get("eq"),kp.get("eq"); dep=kl.get("dep",0) or 0

    om=pct(ov,rv); gm=pct(gv,rv); nm=pct(nv,rv); em=pct(ev,rv)
    de=round(tl/eq*100,1) if (tl and eq and eq!=0) else None
    roe=pct(nv,eq); roa=pct(nv,ta)
    at_=round(rv/ta,2) if (rv and ta and ta!=0) else None

    # ── 헤더 ──
    listing="상장 📈" if params.get("stock_code") else "비상장 🏢"
    std="K-IFRS 연결" if fs_div=="CFS" else "K-GAAP 개별"
    src_info=" | ".join([f"{y}: {sources.get(y,'—')}" for y in years])

    st.markdown(f"<div class='page-title'>{name}</div>",unsafe_allow_html=True)
    st.markdown(f"<span class='badge badge-blue'>{listing}</span>"
                f"<span class='badge badge-teal'>{std}</span>"
                f"<span class='badge badge-gray'>사업/감사보고서</span>"
                f"<span class='badge badge-gray'>{min(years)}~{max(years)}</span>",
                unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:.67rem;color:#9CA3AF;margin:5px 0 0 0;'>조회 소스: {src_info}</p>",
                unsafe_allow_html=True)
    st.markdown("<div style='height:.8rem'></div>",unsafe_allow_html=True)

    # ── KPI Row1: 손익 ──
    st.markdown("<div class='section-hd'>핵심 손익 지표</div>",unsafe_allow_html=True)
    r1="<div class='kpi-row kpi-row-6'>"
    r1+=kpi_card(f"매출 {latest}",      rv, yoy_c(rv,rp), color="blue")
    r1+=kpi_card(f"매출총이익 {latest}", gv, yoy_c(gv,gp_),
                 sub=f"GP margin {gm:.1f}%" if gm else None, color="blue")
    r1+=kpi_card(f"영업이익 {latest}",   ov, yoy_c(ov,op_),
                 sub=f"OPM {om:.1f}%" if om else None,
                 color="green" if (ov and ov>=0) else "red")
    r1+=kpi_card(f"EBITDA {latest}",     ev, yoy_c(ev,ep),
                 sub=f"margin {em:.1f}%" if em else None, color="teal")
    r1+=kpi_card(f"세전이익 {latest}",   bv, yoy_c(bv,bp), color="amber")
    r1+=kpi_card(f"당기순이익 {latest}", nv, yoy_c(nv,np_),
                 sub=f"NPM {nm:.1f}%" if nm else None,
                 color="green" if (nv and nv>=0) else "red")
    r1+="</div>"
    st.markdown(r1,unsafe_allow_html=True)

    # ── KPI Row2: 재무건전성 ──
    st.markdown("<div class='section-hd'>재무건전성 지표</div>",unsafe_allow_html=True)
    de_s=f"{de:.1f}%" if de is not None else "—"
    roe_s=f"{roe:.1f}%" if roe is not None else "—"
    roa_s=f"{roa:.1f}%" if roa is not None else "—"
    at_s=f"{at_:.2f}x" if at_ is not None else "—"
    r2="<div class='kpi-row kpi-row-4'>"
    r2+=kpi_card(f"총자산 {latest}", ta, yoy_c(ta,ta_p), color="gray")
    r2+=kpi_card(f"자본총계 {latest}",eq,yoy_c(eq,eq_p), color="gray")
    r2+=(f"<div class='kpi-card {'red' if (de and de>200) else 'gray'}'>"
         f"<div class='kpi-label'>부채비율 {latest}</div>"
         f"<div class='kpi-value'>{de_s}</div>"
         f"<div class='kpi-sub'>부채 / 자본 × 100</div></div>")
    r2+=(f"<div class='kpi-card {'green' if (roe and roe>0) else 'red' if (roe and roe<0) else 'gray'}'>"
         f"<div class='kpi-label'>ROE / ROA {latest}</div>"
         f"<div class='kpi-value'>{roe_s}</div>"
         f"<div class='kpi-sub'>ROA {roa_s} | 자산회전율 {at_s}</div></div>")
    r2+="</div>"
    st.markdown(r2,unsafe_allow_html=True)

    # ── 차트 ──
    st.markdown("<div class='section-hd'>수익성 추이 | 단위: 억원</div>",unsafe_allow_html=True)
    fig=make_chart(kmap,years)
    if fig:
        st.markdown("<div class='chart-wrap'>",unsafe_allow_html=True)
        st.plotly_chart(fig,use_container_width=True)
        st.markdown("</div>",unsafe_allow_html=True)

    # ── 재무제표 3종 ──
    for tkey,title,hd in [
        ("pl","손익계산서 (P&L)","section-hd"),
        ("bs","재무상태표 (B/S)","section-hd teal"),
        ("cf","현금흐름표 (C/F)","section-hd amber"),
    ]:
        st.markdown(f"<div class='{hd}'>{title} | 단위: 억원 · DART 원본 계정</div>",unsafe_allow_html=True)
        df=build_table(ydata,years,tkey)
        if df.empty:
            st.info(f"{tkey.upper()} 데이터를 불러오지 못했습니다.")
            continue
        yc=[str(y) for y in years]
        yoc=["YoY "+str(y) for y in years[1:]]
        cols=["계정과목"]+yc+yoc+["CAGR"]
        df=df[[c for c in cols if c in df.columns]]
        st.markdown("<div class='tbl-wrap'>",unsafe_allow_html=True)
        h=min(max(len(df)*35+60,250),650)
        st.dataframe(style_df(df,years),use_container_width=True,height=h)
        std2="연결" if fs_div=="CFS" else "개별"
        st.markdown(f"<p class='tbl-note'>출처: DART OpenAPI {std2} {tkey.upper()} | "
                    f"YoY: 전년 대비 증감률 | CAGR: {min(years)}→{max(years)} | "
                    f"EBITDA = 영업이익 + 감가상각비</p>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    # ── 디버그 ──
    with st.expander("🔧 DEBUG",expanded=False):
        st.markdown(f"**corp_code:** `{corp_code}` | **fs_div:** `{fs_div}`")
        for yr in years:
            raw_cnt=len(ydata.get(yr,{}).get("pl",[]))+len(ydata.get(yr,{}).get("bs",[]))+len(ydata.get(yr,{}).get("cf",[]))
            kv=ydata.get(yr,{}).get("kv",{})
            st.markdown(f"**{yr}**: `{sources.get(yr,'—')}` | 파싱항목 {raw_cnt}건 | KV키: {list(kv.keys())[:8]}")

def main():
    for k,v in [("params",None),("cache",{})]:
        if k not in st.session_state: st.session_state[k]=v
    k=sidebar()
    if k: main_view(k)

if __name__=="__main__":
    main()
