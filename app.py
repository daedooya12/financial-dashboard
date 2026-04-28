import streamlit as st
import json
import os
import glob
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="SK Square | 재무 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.main-header {
    padding: 2rem 0 1rem 0;
    border-bottom: 2px solid #E8E8E8;
    margin-bottom: 2rem;
}

.company-btn-active {
    background: #1A3A6B !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    font-weight: 500 !important;
}

.metric-card {
    background: #F8F9FA;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    border-left: 4px solid #1A3A6B;
    margin-bottom: 0.5rem;
}

.metric-label {
    font-size: 0.78rem;
    color: #6C757D;
    font-weight: 500;
    letter-spacing: 0.03em;
    margin-bottom: 0.3rem;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1A3A6B;
}

.metric-value.positive { color: #1A7F4B; }
.metric-value.negative { color: #C0392B; }

.metric-sub {
    font-size: 0.75rem;
    color: #6C757D;
    margin-top: 0.2rem;
}

.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #1A3A6B;
    border-bottom: 1px solid #E8E8E8;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}

.highlight-box {
    background: #EEF4FF;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.3rem 0;
    font-size: 0.85rem;
    color: #1A3A6B;
}

.badge-sector {
    background: #E8F0FE;
    color: #1A3A6B;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 500;
    display: inline-block;
}

.badge-unlisted {
    background: #FFF3CD;
    color: #856404;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 500;
    display: inline-block;
}

.source-note {
    font-size: 0.72rem;
    color: #ADB5BD;
    margin-top: 0.5rem;
}

div[data-testid="stButton"] button {
    width: 100%;
    border-radius: 8px;
    font-family: 'Noto Sans KR', sans-serif;
    font-weight: 400;
    transition: all 0.2s;
}

div[data-testid="stButton"] button:hover {
    background: #1A3A6B;
    color: white;
    border-color: #1A3A6B;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    font-family: 'Noto Sans KR', sans-serif;
}
</style>
""", unsafe_allow_html=True)


# ── 데이터 로드 ──────────────────────────────────────────────
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


def fmt(val, unit="억원", show_sign=True):
    if val is None:
        return "—"
    sign = ""
    if show_sign:
        sign = "+" if val >= 0 else ""
    return f"{sign}{val:,.0f} {unit}"


def color_val(val):
    if val is None or val == "흑자전환":
        return "positive"
    return "positive" if val >= 0 else "negative"


# ── 차트 ─────────────────────────────────────────────────────
def make_revenue_chart(data):
    years = data["years"]
    rev = data["income_statement"]["revenue"]
    op = data["income_statement"]["operating_income"]
    net = data["income_statement"]["net_income"]

    fig = make_subplots(specs=[[{"secondary_y": False}]])

    fig.add_trace(go.Bar(
        name="영업수익",
        x=years, y=rev,
        marker_color="#1A3A6B",
        marker_line_width=0,
        opacity=0.85,
        text=[f"{v:,}" for v in rev],
        textposition="outside",
        textfont=dict(size=11, color="#1A3A6B"),
    ))

    fig.add_trace(go.Bar(
        name="영업손익",
        x=years, y=op,
        marker_color=["#E24B4A" if v < 0 else "#1A7F4B" for v in op],
        marker_line_width=0,
        opacity=0.85,
        text=[f"{v:,}" for v in op],
        textposition="outside",
        textfont=dict(size=11),
    ))

    fig.add_trace(go.Scatter(
        name="당기순이익",
        x=years, y=net,
        mode="lines+markers+text",
        line=dict(color="#E6900A", width=2, dash="dot"),
        marker=dict(size=8, color="#E6900A"),
        text=[f"{v:,}" for v in net],
        textposition="top center",
        textfont=dict(size=10, color="#E6900A"),
    ))

    fig.update_layout(
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=12, family="Noto Sans KR"),
        ),
        yaxis=dict(
            tickformat=",",
            ticksuffix="억",
            gridcolor="#F0F0F0",
            zeroline=True,
            zerolinecolor="#CCCCCC",
            zerolinewidth=1,
        ),
        xaxis=dict(tickfont=dict(size=12), type="category"),
        font=dict(family="Noto Sans KR"),
        showlegend=True,
    )
    return fig


def make_margin_chart(data):
    years = data["years"]
    op_m = data["margins"]["operating_margin"]
    net_m = data["margins"]["net_margin"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name="영업손실률",
        x=years, y=op_m,
        mode="lines+markers+text",
        line=dict(color="#1A3A6B", width=2),
        marker=dict(size=8),
        text=[f"{v:.1f}%" for v in op_m],
        textposition="top center",
        textfont=dict(size=11),
        fill="tozeroy", fillcolor="rgba(26,58,107,0.07)",
    ))
    fig.add_trace(go.Scatter(
        name="순이익률",
        x=years, y=net_m,
        mode="lines+markers+text",
        line=dict(color="#E6900A", width=2, dash="dash"),
        marker=dict(size=8, color="#E6900A"),
        text=[f"{v:.1f}%" for v in net_m],
        textposition="bottom center",
        textfont=dict(size=11, color="#E6900A"),
    ))
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=300,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=12, family="Noto Sans KR")),
        yaxis=dict(ticksuffix="%", gridcolor="#F0F0F0", zeroline=True,
                   zerolinecolor="#CCCCCC", zerolinewidth=1),
        xaxis=dict(type="category"),
        font=dict(family="Noto Sans KR"),
    )
    return fig


def make_cost_chart(data):
    years = data["years"]
    cb = data["cost_breakdown"]
    colors = ["#1A3A6B", "#378ADD", "#85B7EB", "#B5D4F4", "#E6F1FB"]
    labels = ["용역원가", "종업원급여", "지급수수료", "감가상각비", "광고선전비"]
    keys   = ["service_cost", "employee_cost", "commission_fee", "depreciation", "advertising"]

    fig = go.Figure()
    for i, (k, label) in enumerate(zip(keys, labels)):
        fig.add_trace(go.Bar(
            name=label, x=years, y=cb[k],
            marker_color=colors[i], marker_line_width=0,
        ))
    fig.update_layout(
        barmode="stack",
        plot_bgcolor="white", paper_bgcolor="white",
        height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11, family="Noto Sans KR")),
        yaxis=dict(tickformat=",", ticksuffix="억", gridcolor="#F0F0F0"),
        xaxis=dict(type="category"),
        font=dict(family="Noto Sans KR"),
    )
    return fig


# ── 페이지 렌더링 ─────────────────────────────────────────────
def render_company(data):
    years = data["years"]
    inc = data["income_statement"]

    # 헤더
    col_title, col_badges = st.columns([3, 2])
    with col_title:
        st.markdown(f"## {data['company_name']}")
        st.markdown(f"<span class='badge-sector'>{data['sector']}</span>&nbsp;"
                    f"<span class='badge-unlisted'>{data['listing_status']}</span>&nbsp;"
                    f"<span class='badge-sector'>{data['standard']}</span>",
                    unsafe_allow_html=True)
    with col_badges:
        latest_yr = years[-1]
        dart_link = data.get("dart_links", {}).get(latest_yr, "#")
        st.markdown(f"<div style='text-align:right;margin-top:1rem;'>"
                    f"<a href='{dart_link}' target='_blank' style='font-size:0.8rem;color:#1A3A6B;'>"
                    f"📎 DART 원문 ({latest_yr})</a></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # KPI 카드
    latest = -1
    prev = -2
    rev_latest = inc["revenue"][latest]
    rev_prev = inc["revenue"][prev]
    rev_yoy = (rev_latest - rev_prev) / abs(rev_prev) * 100 if rev_prev else 0

    op_latest = inc["operating_income"][latest]
    net_latest = inc["net_income"][latest]
    cagr_rev = data["cagr"]["revenue"]

    cols = st.columns(4)
    kpis = [
        ("매출 " + years[-1], fmt(rev_latest), f"YoY {rev_yoy:+.1f}%", color_val(rev_yoy)),
        ("영업손익 " + years[-1], fmt(op_latest), f"영업이익률 {data['margins']['operating_margin'][-1]:.1f}%", color_val(op_latest)),
        ("당기순이익 " + years[-1], fmt(net_latest), f"순이익률 {data['margins']['net_margin'][-1]:.1f}%", color_val(net_latest)),
        (f"매출 CAGR ({data['cagr']['period']})", f"+{cagr_rev:.1f}%", "연평균 성장률", "positive"),
    ]
    for col, (label, val, sub, cls) in zip(cols, kpis):
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>{label}</div>
                <div class='metric-value {cls}'>{val}</div>
                <div class='metric-sub'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── 상단: 차트 탭 (Summary) ──────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📈 수익 추이", "📉 이익률 추이", "🗂 비용 구조"])

    with tab1:
        st.plotly_chart(make_revenue_chart(data), use_container_width=True)
        st.markdown("<p class='source-note'>단위: 억원 | 출처: " + data["source"] + "</p>", unsafe_allow_html=True)

    with tab2:
        st.plotly_chart(make_margin_chart(data), use_container_width=True)

    with tab3:
        st.plotly_chart(make_cost_chart(data), use_container_width=True)

    # ── 주요 시사점 ──────────────────────────────────────────
    st.markdown("<div class='section-title'>주요 시사점</div>", unsafe_allow_html=True)
    for hl in data.get("key_highlights", []):
        st.markdown(f"<div class='highlight-box'>• {hl}</div>", unsafe_allow_html=True)

    # ── 하단: 상세 테이블 (항상 표시) ───────────────────────
    st.markdown("<div class='section-title'>손익계산서 상세</div>", unsafe_allow_html=True)

    rows = {
        "영업수익": inc["revenue"],
        "영업비용": inc["operating_cost"],
        "영업손익": inc["operating_income"],
        "영업손실률(%)": data["margins"]["operating_margin"],
        "영업외손익": inc["non_operating"],
        "법인세차감전손익": inc["ebt"],
        "당기순이익(손실)": inc["net_income"],
        "순이익률(%)": data["margins"]["net_margin"],
    }
    df = pd.DataFrame(rows, index=years).T
    df.index.name = "항목"

    def style_df(v):
        if isinstance(v, (int, float)):
            return "color: #C0392B; font-weight:500" if v < 0 else "color: #1A7F4B; font-weight:500"
        return ""

    df_styled = df.style.map(style_df).format("{:,.1f}")
    st.dataframe(df_styled, use_container_width=True)

    # CAGR 테이블
    st.markdown("<div class='section-title'>CAGR 요약</div>", unsafe_allow_html=True)
    cagr = data["cagr"]
    cagr_rows = []
    labels_map = {
        "revenue": "영업수익",
        "operating_cost": "영업비용",
        "employee_cost": "종업원급여",
        "depreciation": "감가상각비",
        "advertising": "광고선전비",
    }
    for k, v in cagr.items():
        if k == "period":
            continue
        label = labels_map.get(k, k)
        cagr_rows.append({"항목": label, f"CAGR ({cagr['period']})": f"{v:+.1f}%" if isinstance(v, (int, float)) else v})
    st.dataframe(pd.DataFrame(cagr_rows).set_index("항목"), use_container_width=True)

    st.markdown(f"<p class='source-note' style='margin-top:1rem;'>출처: {data['source']} | 단위: {data['unit']} | 기준: {data['standard']}</p>",
                unsafe_allow_html=True)


# ── 메인 ─────────────────────────────────────────────────────
def main():
    companies = load_all_companies()

    # 헤더
    st.markdown("""
    <div class='main-header'>
        <h1 style='font-size:1.6rem;font-weight:700;color:#1A3A6B;margin:0;'>
            📊 SK Square · 투자분석 재무 대시보드
        </h1>
        <p style='color:#6C757D;font-size:0.85rem;margin:0.3rem 0 0 0;'>
            DART 감사보고서 기반 | Claude 분석 결과
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not companies:
        st.warning("data/ 폴더에 분석된 회사 JSON 파일이 없습니다.")
        return

    # 회사 선택 버튼
    st.markdown("**분석 완료 회사**")

    if "selected" not in st.session_state:
        st.session_state.selected = list(companies.keys())[0]

    btn_cols = st.columns(min(len(companies), 6))
    for i, (key, comp) in enumerate(companies.items()):
        with btn_cols[i % 6]:
            label = comp["company_name"]
            is_active = st.session_state.selected == key
            btn_label = f"✓ {label}" if is_active else label
            if st.button(btn_label, key=f"btn_{key}",
                         type="primary" if is_active else "secondary"):
                st.session_state.selected = key
                st.rerun()

    st.markdown("---")

    # 선택 회사 렌더링
    selected_data = companies[st.session_state.selected]
    render_company(selected_data)


if __name__ == "__main__":
    main()
