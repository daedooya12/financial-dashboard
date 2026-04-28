import streamlit as st
import json
import os
import glob
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #F4F6FA;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2447 0%, #1A3A6B 60%, #1e4d8c 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E8EEF8 !important; }
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color: #FFFFFF !important; }

[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: 100%;
    background: rgba(255,255,255,0.07) !important;
    color: #C8D8F0 !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    padding: 0.55rem 1rem !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
    text-align: left !important;
    transition: all 0.2s !important;
    margin-bottom: 4px !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: rgba(255,255,255,0.18) !important;
    color: #FFFFFF !important;
    border-color: rgba(255,255,255,0.35) !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
    background: rgba(82,160,255,0.25) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(82,160,255,0.6) !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"] {
    background: rgba(255,255,255,0.07) !important;
    color: #C8D8F0 !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}

.main .block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 100%; }

.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 1.5rem; }
.kpi-card {
    background: white; border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border-top: 4px solid #1A3A6B;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.kpi-card.green  { border-top-color: #1A7F4B; }
.kpi-card.red    { border-top-color: #C0392B; }
.kpi-card.amber  { border-top-color: #D97706; }
.kpi-card.blue   { border-top-color: #1A3A6B; }
.kpi-label { font-size: 0.72rem; color: #6B7280; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value { font-size: 1.55rem; font-weight: 700; color: #111827; line-height: 1.1; }
.kpi-value.pos { color: #1A7F4B; }
.kpi-value.neg { color: #C0392B; }
.kpi-sub { font-size: 0.75rem; color: #9CA3AF; margin-top: 5px; }

.section-hd {
    font-size: 0.8rem; font-weight: 600; color: #374151;
    text-transform: uppercase; letter-spacing: 0.06em;
    border-left: 3px solid #1A3A6B;
    padding-left: 10px; margin: 1.6rem 0 0.8rem 0;
}

.hl-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 8px; margin-bottom: 1rem; }
.hl-item {
    background: white; border-radius: 8px;
    padding: 0.7rem 1rem;
    font-size: 0.82rem; color: #374151;
    border-left: 3px solid #3B82F6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.badge { display: inline-block; border-radius: 4px; padding: 2px 9px; font-size: 0.72rem; font-weight: 500; margin-right: 5px; }
.badge-blue   { background:#DBEAFE; color:#1E40AF; }
.badge-yellow { background:#FEF3C7; color:#92400E; }
.badge-gray   { background:#F3F4F6; color:#374151; }

.src-note { font-size: 0.7rem; color: #9CA3AF; margin-top: 0.5rem; }
.chart-card { background: white; border-radius: 12px; padding: 1.2rem 1.2rem 0.5rem 1.2rem; box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin-bottom: 1rem; }
.tbl-wrap { background: white; border-radius: 12px; padding: 1.2rem; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_all_companies():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    files = glob.glob(os.path.join(data_dir, "*.json"))
    companies = {}
    for f in sorted(files):
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        key = os.path.basename(f).replace(".json", "")
        companies[key] = d
    return companies


def fmt_num(v):
    if v is None: return "—"
    return f"{v:,.0f}"

def fmt_pct(v, decimals=1):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.{decimals}f}%"

def cagr_str(arr, n):
    try:
        start, end = arr[0], arr[-1]
        if start == 0 or start is None or end is None: return "—"
        v = ((end / start) ** (1 / n) - 1) * 100
        sign = "+" if v >= 0 else ""
        return f"{sign}{v:.1f}%"
    except:
        return "—"

def compute_ebitda(inc, cb):
    return [inc["operating_income"][i] + cb["depreciation"][i] for i in range(len(inc["operating_income"]))]

def yoy(arr):
    result = [None]
    for i in range(1, len(arr)):
        prev = arr[i-1]
        if prev and prev != 0:
            result.append((arr[i] - prev) / abs(prev) * 100)
        else:
            result.append(None)
    return result


COLORS = {
    "navy": "#1A3A6B", "blue": "#3B82F6", "teal": "#0D9488",
    "red": "#EF4444", "amber": "#F59E0B", "green": "#16A34A",
    "light_blue": "#93C5FD",
}


def make_revenue_chart(data):
    years = data["years"]
    inc = data["income_statement"]
    rev = inc["revenue"]
    op  = inc["operating_income"]
    net = inc["net_income"]
    ebi = compute_ebitda(inc, data["cost_breakdown"])

    fig = go.Figure()
    fig.add_trace(go.Bar(name="영업수익", x=years, y=rev,
        marker_color=COLORS["navy"], marker_line_width=0, opacity=0.9,
        text=[f"{v:,}" for v in rev], textposition="outside",
        textfont=dict(size=10, color=COLORS["navy"])))
    fig.add_trace(go.Bar(name="EBITDA", x=years, y=ebi,
        marker_color=COLORS["teal"], marker_line_width=0, opacity=0.85,
        text=[f"{v:,}" for v in ebi], textposition="outside",
        textfont=dict(size=10, color=COLORS["teal"])))
    fig.add_trace(go.Bar(name="영업손익", x=years, y=op,
        marker_color=[COLORS["red"] if v < 0 else COLORS["green"] for v in op],
        marker_line_width=0, opacity=0.85,
        text=[f"{v:,}" for v in op], textposition="outside",
        textfont=dict(size=10)))
    fig.add_trace(go.Scatter(name="당기순이익", x=years, y=net,
        mode="lines+markers",
        line=dict(color=COLORS["amber"], width=2.5, dash="dot"),
        marker=dict(size=9, color=COLORS["amber"], line=dict(color="white", width=2))))
    fig.update_layout(
        barmode="group", plot_bgcolor="white", paper_bgcolor="white",
        height=360, margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    font=dict(size=11, family="Noto Sans KR"), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",", ticksuffix="억", gridcolor="#F3F4F6",
                   zeroline=True, zerolinecolor="#D1D5DB", zerolinewidth=1, tickfont=dict(size=11)),
        xaxis=dict(type="category", tickfont=dict(size=12)),
        font=dict(family="Noto Sans KR"))
    return fig


def make_margin_chart(data):
    years = data["years"]
    inc = data["income_statement"]
    op_m  = data["margins"]["operating_margin"]
    net_m = data["margins"]["net_margin"]
    ebi   = compute_ebitda(inc, data["cost_breakdown"])
    rev   = inc["revenue"]
    ebi_m = [round(e / r * 100, 1) if r else 0 for e, r in zip(ebi, rev)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(name="EBITDA margin", x=years, y=ebi_m,
        mode="lines+markers+text", line=dict(color=COLORS["teal"], width=2.5),
        marker=dict(size=8, color=COLORS["teal"], line=dict(color="white", width=2)),
        text=[f"{v:.1f}%" for v in ebi_m], textposition="top center",
        textfont=dict(size=10, color=COLORS["teal"]),
        fill="tozeroy", fillcolor="rgba(13,148,136,0.07)"))
    fig.add_trace(go.Scatter(name="영업이익률", x=years, y=op_m,
        mode="lines+markers+text", line=dict(color=COLORS["navy"], width=2.5),
        marker=dict(size=8, color=COLORS["navy"], line=dict(color="white", width=2)),
        text=[f"{v:.1f}%" for v in op_m], textposition="bottom center",
        textfont=dict(size=10, color=COLORS["navy"])))
    fig.add_trace(go.Scatter(name="순이익률", x=years, y=net_m,
        mode="lines+markers+text", line=dict(color=COLORS["amber"], width=2, dash="dash"),
        marker=dict(size=8, color=COLORS["amber"], line=dict(color="white", width=2)),
        text=[f"{v:.1f}%" for v in net_m], textposition="top center",
        textfont=dict(size=10, color=COLORS["amber"])))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        height=320, margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    font=dict(size=11, family="Noto Sans KR"), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(ticksuffix="%", gridcolor="#F3F4F6",
                   zeroline=True, zerolinecolor="#D1D5DB", zerolinewidth=1, tickfont=dict(size=11)),
        xaxis=dict(type="category", tickfont=dict(size=12)),
        font=dict(family="Noto Sans KR"))
    return fig


def make_cost_chart(data):
    years = data["years"]
    cb = data["cost_breakdown"]
    palette = [COLORS["navy"], COLORS["blue"], COLORS["teal"], COLORS["light_blue"], COLORS["amber"]]
    labels  = ["용역원가", "종업원급여", "지급수수료", "감가상각비", "광고선전비"]
    keys    = ["service_cost", "employee_cost", "commission_fee", "depreciation", "advertising"]

    fig = go.Figure()
    for i, (k, label) in enumerate(zip(keys, labels)):
        fig.add_trace(go.Bar(name=label, x=years, y=cb[k],
            marker_color=palette[i], marker_line_width=0))
    fig.update_layout(
        barmode="stack", plot_bgcolor="white", paper_bgcolor="white",
        height=320, margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    font=dict(size=11, family="Noto Sans KR"), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",", ticksuffix="억", gridcolor="#F3F4F6", tickfont=dict(size=11)),
        xaxis=dict(type="category", tickfont=dict(size=12)),
        font=dict(family="Noto Sans KR"))
    return fig


def make_pl_table(data):
    years = data["years"]
    inc = data["income_statement"]
    cb  = data["cost_breakdown"]
    mar = data["margins"]
    n   = len(years) - 1

    ebi   = compute_ebitda(inc, cb)
    rev   = inc["revenue"]
    ebi_m = [round(e / r * 100, 1) if r else 0 for e, r in zip(ebi, rev)]

    # (label, values, is_pct, bold, sub_item)
    rows_def = [
        ("영업수익",           inc["revenue"],              False, True,  False),
        ("  용역원가",         cb["service_cost"],          False, False, True),
        ("  종업원급여",       cb["employee_cost"],         False, False, True),
        ("  지급수수료",       cb["commission_fee"],        False, False, True),
        ("  감가상각비",       cb["depreciation"],          False, False, True),
        ("  광고선전비",       cb["advertising"],           False, False, True),
        ("영업비용 합계",      inc["operating_cost"],       False, False, False),
        ("영업손익",           inc["operating_income"],     False, True,  False),
        ("  영업이익률 (%)",   mar["operating_margin"],     True,  False, True),
        ("EBITDA",             ebi,                         False, True,  False),
        ("  EBITDA margin (%)",ebi_m,                       True,  False, True),
        ("영업외손익",         inc["non_operating"],        False, False, False),
        ("법인세차감전손익",   inc["ebt"],                  False, True,  False),
        ("당기순이익(손실)",   inc["net_income"],           False, True,  False),
        ("  순이익률 (%)",     mar["net_margin"],           True,  False, True),
    ]

    yoy_years = years[1:]
    col_yoy   = [f"YoY {y}" for y in yoy_years]
    cagr_col  = f"CAGR ({years[0]}→{years[-1]})"

    records = []
    bold_flags = []
    sub_flags  = []

    for label, vals, is_pct, bold, is_sub in rows_def:
        row = {"항목": label}
        # 연도별 수치
        for i, y in enumerate(years):
            v = vals[i]
            row[y] = fmt_pct(v) if is_pct else fmt_num(v)
        # YoY
        if is_pct:
            for cy in col_yoy:
                row[cy] = "—"
            row[cagr_col] = "—"
        else:
            yoy_vals = yoy(vals)
            for i, cy in enumerate(col_yoy):
                row[cy] = fmt_pct(yoy_vals[i+1])
            row[cagr_col] = cagr_str(vals, n)
        records.append(row)
        bold_flags.append(bold)
        sub_flags.append(is_sub)

    df = pd.DataFrame(records).set_index("항목")

    def style_cell(v):
        if not isinstance(v, str): return ""
        if v == "—": return "color: #D1D5DB"
        stripped = v.strip()
        if stripped.startswith("-") or (stripped.startswith("(") and ")" in stripped):
            return "color: #C0392B; font-weight: 500"
        if stripped.startswith("+"):
            return "color: #1A7F4B; font-weight: 500"
        return ""

    def style_row(row):
        idx = list(df.index).index(row.name)
        if bold_flags[idx]:
            return ["font-weight:600; background:#F0F4FF; color:#111827"] * len(row)
        if sub_flags[idx]:
            return ["color:#6B7280; font-size:0.85em"] * len(row)
        return [""] * len(row)

    styled = df.style.apply(style_row, axis=1).map(style_cell)
    return styled


def render_sidebar(companies):
    with st.sidebar:
        st.markdown("""
        <div style='padding:1.5rem 0 1.2rem 0;border-bottom:1px solid rgba(255,255,255,0.12);margin-bottom:1.2rem;'>
            <div style='font-size:0.68rem;letter-spacing:0.12em;color:#93B4D8;font-weight:600;margin-bottom:6px;'>SK SQUARE</div>
            <div style='font-size:1.05rem;font-weight:700;color:#FFFFFF;line-height:1.3;'>투자분석<br>재무 대시보드</div>
            <div style='font-size:0.7rem;color:#7B9EC4;margin-top:6px;'>DART 기반 · Claude 분석</div>
        </div>
        <div style='font-size:0.68rem;letter-spacing:0.1em;color:#7B9EC4;font-weight:600;margin-bottom:8px;'>포트폴리오 회사</div>
        """, unsafe_allow_html=True)

        if "selected" not in st.session_state:
            st.session_state.selected = list(companies.keys())[0]

        for key, comp in companies.items():
            is_active = st.session_state.selected == key
            label = ("▶  " if is_active else "    ") + comp["company_name"]
            if st.button(label, key=f"btn_{key}", type="primary" if is_active else "secondary"):
                st.session_state.selected = key
                st.rerun()

        st.markdown("""
        <div style='margin-top:2rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.08);'>
            <div style='font-size:0.68rem;color:#4A6FA5;line-height:1.6;'>
                새 회사 추가:<br>data/ 폴더에 JSON 파일<br>업로드 후 재배포
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_company(data):
    years = data["years"]
    inc   = data["income_statement"]
    cb    = data["cost_breakdown"]
    mar   = data["margins"]
    ebi   = compute_ebitda(inc, cb)
    rev   = inc["revenue"]

    rev_latest  = rev[-1]
    rev_prev    = rev[-2]
    rev_yoy     = (rev_latest - rev_prev) / abs(rev_prev) * 100 if rev_prev else 0
    op_latest   = inc["operating_income"][-1]
    net_latest  = inc["net_income"][-1]
    ebi_latest  = ebi[-1]
    ebi_margin  = round(ebi_latest / rev_latest * 100, 1) if rev_latest else 0
    latest_yr   = years[-1]
    dart_link   = data.get("dart_links", {}).get(latest_yr, "#")

    # 헤더
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f"## {data['company_name']}")
        st.markdown(
            f"<span class='badge badge-blue'>{data['sector']}</span>"
            f"<span class='badge badge-yellow'>{data['listing_status']}</span>"
            f"<span class='badge badge-gray'>{data['standard']}</span>",
            unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"<div style='text-align:right;margin-top:1.2rem;'>"
            f"<a href='{dart_link}' target='_blank' style='font-size:0.78rem;color:#3B82F6;text-decoration:none;'>"
            f"📎 DART 원문 ({latest_yr})</a></div>",
            unsafe_allow_html=True)

    # KPI
    def kpi_color(v): return "green" if v >= 0 else "red"
    kpis = [
        ("매출 " + latest_yr,       fmt_num(rev_latest) + "억",  f"YoY {rev_yoy:+.1f}%",                             "blue"  if rev_yoy >= 0 else "red"),
        ("영업손익 " + latest_yr,   fmt_num(op_latest)  + "억",  f"영업이익률 {mar['operating_margin'][-1]:.1f}%",   kpi_color(op_latest)),
        ("EBITDA " + latest_yr,     fmt_num(ebi_latest) + "억",  f"EBITDA margin {ebi_margin:.1f}%",                 kpi_color(ebi_latest)),
        ("당기순이익 " + latest_yr, fmt_num(net_latest) + "억",  f"순이익률 {mar['net_margin'][-1]:.1f}%",           kpi_color(net_latest)),
    ]
    kpi_html = "<div class='kpi-grid'>"
    for label, val, sub, color in kpis:
        neg = val.startswith("-") or (val.startswith("(") and ")" in val)
        val_cls = "neg" if neg else "pos"
        kpi_html += f"""<div class='kpi-card {color}'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value {val_cls}'>{val}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>"""
    kpi_html += "</div>"
    st.markdown(kpi_html, unsafe_allow_html=True)

    # 차트
    st.markdown("<div class='section-hd'>Performance Summary</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📊 수익 & 손익 추이", "📉 이익률 추이", "🗂 비용 구조"])
    with tab1:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(make_revenue_chart(data), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with tab2:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(make_margin_chart(data), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with tab3:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(make_cost_chart(data), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 하이라이트
    st.markdown("<div class='section-hd'>Key Highlights</div>", unsafe_allow_html=True)
    hl_items = data.get("key_highlights", [])
    hl_html = "<div class='hl-grid'>"
    for hl in hl_items:
        hl_html += f"<div class='hl-item'>• {hl}</div>"
    hl_html += "</div>"
    st.markdown(hl_html, unsafe_allow_html=True)

    # 통합 손익 테이블
    st.markdown("<div class='section-hd'>손익계산서 상세 | 단위: 억원</div>", unsafe_allow_html=True)
    st.markdown("<div class='tbl-wrap'>", unsafe_allow_html=True)
    styled = make_pl_table(data)
    st.dataframe(styled, use_container_width=True, height=545)
    st.markdown(
        f"<p class='src-note'>출처: {data['source']} | 단위: {data['unit']} | 기준: {data['standard']} "
        f"| EBITDA = 영업손익 + 감가상각비 및 상각비 | 음수: 빨강, 양수 증감: 초록</p>",
        unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    companies = load_all_companies()
    if not companies:
        st.warning("data/ 폴더에 분석된 회사 JSON 파일이 없습니다.")
        return
    render_sidebar(companies)
    render_company(companies[st.session_state.get("selected", list(companies.keys())[0])])


if __name__ == "__main__":
    main()
