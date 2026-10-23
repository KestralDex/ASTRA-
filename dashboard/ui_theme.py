from __future__ import annotations

import html
from pathlib import Path

import streamlit as st


def apply_astra_dashboard_theme() -> None:
    """
    ASTRA reference-inspired visual system.

    The styling intentionally stays flat, compact and enterprise-like:
    dark navy navigation, light canvas, thin borders, small radii, restrained
    shadows, compact typography and high information density.
    """

    st.markdown(
        """
        <style>
        :root {
            --astra-navy-950: #031733;
            --astra-navy-900: #061d43;
            --astra-navy-850: #082650;
            --astra-blue: #1268dc;
            --astra-blue-dark: #0b56bd;
            --astra-cyan: #159bb2;
            --astra-green: #129064;
            --astra-green-bg: #e8f7f1;
            --astra-amber: #e17a13;
            --astra-amber-bg: #fff3e1;
            --astra-red: #dc3e47;
            --astra-red-bg: #fff0f1;
            --astra-ink: #10223e;
            --astra-text: #263b58;
            --astra-muted: #6c7d94;
            --astra-line: #dce4ee;
            --astra-line-soft: #e9eef4;
            --astra-canvas: #f7f9fc;
            --astra-card: #ffffff;
        }

        /* ---------- Streamlit chrome ---------- */
        #MainMenu,
        footer,
        [data-testid="stToolbar"] {
            visibility: hidden !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
            min-height: 0 !important;
        }

        .stApp {
            background: var(--astra-canvas);
        }

        .block-container {
            max-width: 1600px;
            padding-top: 1.10rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 1.12rem !important;
            padding-right: 1.12rem !important;
        }

        html, body, [class*="css"] {
            font-family:
                Inter, "Segoe UI", ui-sans-serif, system-ui, -apple-system,
                BlinkMacSystemFont, sans-serif;
        }

        h1, h2, h3, p {
            color: var(--astra-ink);
        }

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {
            width: 226px !important;
            min-width: 226px !important;
            max-width: 226px !important;
            background:
                linear-gradient(180deg, #06224d 0%, #041b3d 58%, #031733 100%) !important;
            border-right: 1px solid rgba(255,255,255,.05) !important;
        }

        section[data-testid="stSidebar"] > div {
            width: 226px !important;
            background: transparent !important;
        }

        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"],
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
        section[data-testid="stSidebar"] [data-testid="stElementContainer"] {
            background: transparent !important;
        }

        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-left: .72rem !important;
            padding-right: .72rem !important;
        }

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: #dbe8f8;
        }

        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            display: flex;
            align-items: center;
            min-height: 2.68rem;
            margin: .16rem 0;
            padding: .52rem .68rem;
            border-radius: 7px;
            border: 1px solid transparent;
            background: transparent !important;
            color: #dce8f7 !important;
            font-size: .83rem;
            font-weight: 590;
            text-decoration: none !important;
        }

        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
            background: rgba(255,255,255,.075) !important;
            color: #ffffff !important;
        }

        section[data-testid="stSidebar"]
        a[data-testid="stPageLink-NavLink"][aria-current="page"] {
            background: #1268dc !important;
            border-color: #1f78e6 !important;
            color: #ffffff !important;
        }

        .astra-brand {
            padding: .72rem .38rem .95rem .38rem;
            margin-bottom: .42rem;
            border-bottom: 1px solid rgba(255,255,255,.10);
        }

        .astra-brand-line {
            display: flex;
            align-items: center;
            gap: .64rem;
        }

        .astra-brand-symbol {
            position: relative;
            width: 33px;
            height: 33px;
        }

        .astra-brand-symbol:before,
        .astra-brand-symbol:after {
            content: "";
            position: absolute;
            left: 14px;
            top: 1px;
            width: 6px;
            height: 31px;
            border-radius: 3px;
            transform-origin: center;
        }

        .astra-brand-symbol:before {
            background: #29b8da;
            transform: rotate(44deg);
        }

        .astra-brand-symbol:after {
            background: #3d88f4;
            transform: rotate(-44deg);
        }

        .astra-brand-name {
            color: #ffffff !important;
            font-size: 1.54rem;
            line-height: 1;
            font-weight: 790;
            letter-spacing: .02em;
        }

        .astra-brand-sub {
            margin-top: .20rem;
            color: #9ab2d1 !important;
            font-size: .62rem;
            line-height: 1.2;
        }

        .astra-side-label {
            margin: .85rem .42rem .38rem .42rem;
            color: #6f8daf !important;
            font-size: .60rem;
            font-weight: 760;
            letter-spacing: .13em;
            text-transform: uppercase;
        }

        .astra-side-globe {
            position: relative;
            height: 112px;
            margin: 1.35rem .30rem .62rem .30rem;
            border-radius: 8px;
            overflow: hidden;
            background:
                radial-gradient(circle at 50% 60%, rgba(29,126,231,.28), transparent 36%),
                radial-gradient(circle at 43% 56%, rgba(38,191,223,.16), transparent 54%);
        }

        .astra-side-globe:before,
        .astra-side-globe:after {
            content: "";
            position: absolute;
            left: 50%;
            top: 56%;
            transform: translate(-50%,-50%);
            border: 1px solid rgba(65,166,255,.28);
            border-radius: 50%;
        }

        .astra-side-globe:before {
            width: 118px;
            height: 68px;
        }

        .astra-side-globe:after {
            width: 82px;
            height: 82px;
        }

        .astra-side-motto {
            color: #e9f2ff !important;
            font-size: .72rem;
            font-weight: 680;
            line-height: 1.42;
            margin: .0rem .45rem 1rem .45rem;
        }

        .astra-side-foot {
            border-top: 1px solid rgba(255,255,255,.09);
            padding: .82rem .45rem .2rem .45rem;
            color: #8099ba !important;
            font-size: .62rem;
            line-height: 1.55;
        }

        /* ---------- Header ---------- */
        .astra-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1.15rem;
            margin-bottom: .92rem;
        }

        .astra-title {
            color: #10294f;
            font-size: 2.02rem;
            line-height: 1.0;
            font-weight: 790;
            letter-spacing: .015em;
        }

        .astra-subtitle {
            margin-top: .26rem;
            color: #6c7d94;
            font-size: .92rem;
        }

        .astra-header-actions {
            display: flex;
            justify-content: flex-end;
            flex-wrap: wrap;
            gap: .44rem;
        }

        .astra-top-control {
            display: inline-flex;
            align-items: center;
            gap: .38rem;
            height: 2.18rem;
            padding: 0 .72rem;
            border: 1px solid #dce4ee;
            border-radius: 7px;
            background: #ffffff;
            color: #324965;
            box-shadow: 0 1px 4px rgba(15,35,65,.025);
            font-size: .69rem;
            font-weight: 620;
            white-space: nowrap;
        }

        .astra-live-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #16a36f;
            box-shadow: 0 0 0 3px rgba(22,163,111,.10);
        }

        .astra-flow-line {
            color: #7a8aa0;
            font-size: .65rem;
            margin-top: -.54rem;
            margin-bottom: .82rem;
        }

        /* ---------- General card system ---------- */
        .astra-card {
            height: 100%;
            background: #ffffff;
            border: 1px solid var(--astra-line);
            border-radius: 8px;
            box-shadow: 0 1px 5px rgba(17,37,68,.025);
        }

        .astra-card-pad {
            padding: .84rem .90rem;
        }

        .astra-card-title {
            display: flex;
            align-items: center;
            gap: .44rem;
            color: #23405f;
            font-size: .69rem;
            font-weight: 760;
            letter-spacing: .01em;
            text-transform: uppercase;
        }

        .astra-card-title-normal {
            color: #233a58;
            font-size: .75rem;
            font-weight: 710;
        }

        .astra-rule {
            height: 1px;
            background: var(--astra-line-soft);
            margin: .68rem 0;
        }

        .astra-mini-icon {
            display: inline-grid;
            place-items: center;
            width: 27px;
            height: 27px;
            border-radius: 50%;
            font-size: .66rem;
            font-weight: 800;
            flex: 0 0 auto;
        }

        .mi-blue  { background:#e8f1ff; color:#1768d2; }
        .mi-green { background:#e6f5ef; color:#0c8b62; }
        .mi-red   { background:#ffebed; color:#d53743; }
        .mi-amber { background:#fff0db; color:#d66e0b; }
        .mi-cyan  { background:#e4f4f7; color:#138ca3; }

        /* ---------- KPI row ---------- */
        .astra-kpi {
            min-height: 121px;
            padding: .86rem .90rem .73rem .90rem;
        }

        .astra-kpi-head {
            display: flex;
            align-items: center;
            gap: .54rem;
        }

        .astra-kpi-name {
            color: #243e5c;
            font-size: .70rem;
            font-weight: 690;
            line-height: 1.2;
        }

        .astra-kpi-main {
            display: flex;
            align-items: baseline;
            gap: .32rem;
            margin-top: .64rem;
        }

        .astra-kpi-value {
            color: #0f2c50;
            font-size: 1.55rem;
            line-height: 1;
            font-weight: 770;
            letter-spacing: -.025em;
        }

        .astra-kpi-unit {
            color: #8a99aa;
            font-size: .67rem;
            font-weight: 600;
        }

        .astra-kpi-accent-blue  { color:#1268dc; }
        .astra-kpi-accent-green { color:#129064; }
        .astra-kpi-accent-red   { color:#d73a45; }
        .astra-kpi-accent-amber { color:#dd720c; }

        .astra-kpi-caption {
            margin-top: .35rem;
            color: #798ba1;
            font-size: .62rem;
            line-height: 1.35;
        }

        /* ---------- Alert / explanation / next-step row ---------- */
        .astra-signal-card {
            min-height: 187px;
        }

        .astra-signal-red {
            background: linear-gradient(180deg,#fffafa 0%,#ffffff 100%);
            border-color: #f0cfd2;
        }

        .astra-signal-blue {
            background: linear-gradient(180deg,#f8fbff 0%,#ffffff 100%);
            border-color: #ccdff6;
        }

        .astra-signal-green {
            background: #ffffff;
            border-color: #d6e9e1;
        }

        .astra-signal-heading {
            margin-top: .68rem;
            color: #17324f;
            font-size: .94rem;
            line-height: 1.25;
            font-weight: 720;
        }

        .astra-signal-copy {
            margin-top: .50rem;
            color: #536981;
            font-size: .71rem;
            line-height: 1.58;
        }

        .astra-risk-number {
            margin-top: .62rem;
            font-size: 1.72rem;
            line-height: 1;
            font-weight: 800;
            color: #d43b45;
        }

        .astra-risk-number-neutral {
            color: #1d62bf;
        }

        .astra-tag {
            display: inline-flex;
            align-items: center;
            min-height: 1.42rem;
            padding: 0 .46rem;
            border-radius: 5px;
            margin-top: .45rem;
            font-size: .60rem;
            font-weight: 720;
        }

        .tag-red   { background:#fee8ea; color:#c72e39; }
        .tag-blue  { background:#e9f2ff; color:#135ebf; }
        .tag-green { background:#e8f7f1; color:#0c835e; }
        .tag-muted { background:#eef2f7; color:#65778e; }

        .astra-next-row {
            display: flex;
            align-items: center;
            gap: .48rem;
            min-height: 42px;
            padding: .42rem 0;
            border-bottom: 1px solid #edf1f5;
        }

        .astra-next-row:last-child {
            border-bottom: 0;
        }

        .astra-next-index {
            display: grid;
            place-items: center;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #1268dc;
            color: white;
            font-size: .62rem;
            font-weight: 760;
            flex: 0 0 auto;
        }

        .astra-next-title {
            color: #263f5c;
            font-size: .68rem;
            font-weight: 700;
        }

        .astra-next-sub {
            color: #8695a7;
            font-size: .58rem;
            margin-top: .05rem;
        }

        /* ---------- Lower grid ---------- */
        .astra-lower-card {
            min-height: 267px;
        }

        .astra-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: .58rem;
            font-size: .62rem;
        }

        .astra-table th {
            color: #77899e;
            font-size: .56rem;
            font-weight: 720;
            text-align: left;
            padding: .38rem .34rem;
            border-bottom: 1px solid #e7edf3;
            background: #f9fbfd;
        }

        .astra-table td {
            color: #405873;
            padding: .38rem .34rem;
            border-bottom: 1px solid #edf1f5;
        }

        .astra-heat-low  { background:#e9f7f1; color:#087c57 !important; font-weight:700; }
        .astra-heat-med  { background:#fff3df; color:#c86a0c !important; font-weight:700; }
        .astra-heat-high { background:#ffeaec; color:#c7323d !important; font-weight:700; }

        .astra-metric-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: .5rem;
            padding: .42rem 0;
            border-bottom: 1px solid #edf1f5;
        }

        .astra-metric-row:last-child {
            border-bottom: 0;
        }

        .astra-metric-name {
            color:#61748b;
            font-size:.63rem;
        }

        .astra-metric-val {
            color:#173552;
            font-size:.69rem;
            font-weight:740;
        }

        .astra-bar-track {
            height: 7px;
            border-radius: 5px;
            background:#edf2f7;
            overflow:hidden;
            margin-top:.26rem;
        }

        .astra-bar-fill-blue {
            height:100%;
            background:#1268dc;
        }

        .astra-bar-fill-green {
            height:100%;
            background:#19a170;
        }

        .astra-bar-fill-cyan {
            height:100%;
            background:#229db1;
        }

        .astra-status-item {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:.6rem;
            padding:.42rem 0;
            border-bottom:1px solid #edf1f5;
        }

        .astra-status-item:last-child {
            border-bottom:0;
        }

        .astra-status-name {
            color:#4b6079;
            font-size:.64rem;
        }

        .astra-status-badge {
            padding:.15rem .38rem;
            border-radius:4px;
            font-size:.55rem;
            font-weight:750;
        }

        /* ---------- Bottom evidence ---------- */
        .astra-source-grid {
            display:grid;
            grid-template-columns:repeat(3,1fr);
            gap:.08rem 1rem;
            margin-top:.60rem;
        }

        .astra-source {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:.55rem;
            min-height:34px;
            border-bottom:1px solid #eef2f6;
        }

        .astra-source-name {
            color:#405873;
            font-size:.62rem;
            font-weight:620;
        }

        .astra-source-state {
            color:#129064;
            font-size:.57rem;
            font-weight:730;
        }

        .astra-source-planned {
            color:#8595a8;
        }

        /* ---------- Inputs / buttons ---------- */
        [data-testid="stForm"] {
            border: 1px solid #dce4ee !important;
            border-radius: 8px !important;
            background: #ffffff !important;
            padding: .84rem !important;
        }

        div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {
            border-radius: 6px !important;
            border-color: #dce4ee !important;
        }

        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            min-height: 2.36rem;
            border-radius: 6px;
            font-size: .72rem;
            font-weight: 680;
            box-shadow: none;
        }

        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background:#1268dc;
            border-color:#1268dc;
        }

        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            background:#0c5cc6;
            border-color:#0c5cc6;
        }

        [data-testid="stExpander"] {
            border: 1px solid #dce4ee !important;
            border-radius: 8px !important;
            background:#ffffff !important;
        }

        [data-testid="stMetric"] {
            background:#ffffff;
            border:1px solid #e0e7ef;
            border-radius:7px;
            padding:.58rem .66rem;
        }

        [data-testid="stMetricLabel"] p {
            color:#6d8096 !important;
            font-size:.61rem !important;
        }

        [data-testid="stMetricValue"] {
            color:#173451 !important;
            font-size:1.12rem !important;
            font-weight:760 !important;
        }

        [data-testid="stDataFrame"] {
            border:1px solid #dce4ee;
            border-radius:7px;
            overflow:hidden;
        }

        /* Avoid the "large white sidebar card" regression. */
        section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
        section[data-testid="stSidebar"] [data-testid="stForm"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:nth-of-type(1) {
            min-height: 2rem;
            font-size: 0.68rem;
            opacity: 0.78;
            margin-bottom: 0.55rem;
        }

        @media (max-width: 1100px) {
            section[data-testid="stSidebar"] {
                width: 210px !important;
                min-width: 210px !important;
                max-width: 210px !important;
            }

            section[data-testid="stSidebar"] > div {
                width: 210px !important;
            }

            .astra-source-grid {
                grid-template-columns:1fr 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_astra_theme(page_label: str | None = None) -> None:
    """Backward-compatible theme function used by the other ASTRA pages."""
    apply_astra_dashboard_theme()

    if page_label:
        safe = html.escape(str(page_label))
        st.markdown(
            f"""
            <div style="
                color:#6d7e93;
                font-size:.63rem;
                font-weight:760;
                letter-spacing:.10em;
                text-transform:uppercase;
                margin:0 0 .48rem 0;
            ">{safe}</div>
            """,
            unsafe_allow_html=True,
        )


def render_astra_sidebar(active_page: str = "dashboard") -> None:
    """
    Render the same ASTRA navigation on every Streamlit page.

    Streamlit multipage pages execute independently, so a custom sidebar placed
    only in dashboard/app.py disappears after navigation. Keeping it here makes
    navigation persistent across Dashboard, Data Explorer, Scenario Lab and
    Governance.
    """
    del active_page  # Streamlit handles the current-page state.

    project_root = Path(__file__).resolve().parents[1]
    data_explorer = project_root / "dashboard" / "pages" / "1_Data_Explorer.py"
    scenario_lab = project_root / "dashboard" / "pages" / "2_Scenario_Lab.py"
    governance = project_root / "dashboard" / "pages" / "3_Governance.py"

    with st.sidebar:
        st.markdown(
            """
            <div class="astra-brand">
                <div class="astra-brand-line">
                    <div class="astra-brand-symbol"></div>
                    <div>
                        <div class="astra-brand-name">ASTRA</div>
                        <div class="astra-brand-sub">Supply Chain Intelligence</div>
                    </div>
                </div>
            </div>
            <div class="astra-side-label">Workspace</div>
            """,
            unsafe_allow_html=True,
        )

        if governance.is_file():
            st.page_link(
                "pages/3_Governance.py",
                label="🛡  Governance",
                use_container_width=True,
            )

        st.page_link(
            "app.py",
            label="Dashboard",
            use_container_width=True,
        )

        if data_explorer.is_file():
            st.page_link(
                "pages/1_Data_Explorer.py",
                label="Data Explorer",
                use_container_width=True,
            )

        if scenario_lab.is_file():
            st.page_link(
                "pages/2_Scenario_Lab.py",
                label="Scenario Lab",
                use_container_width=True,
            )

      

        st.markdown(
            """
            <div class="astra-side-globe"></div>
            <div class="astra-side-motto">
                Building<br>
                Resilient<br>
                Supply Chains.
            </div>
            <div class="astra-side-foot">
                ASTRA decision-support prototype<br>
                v0.1 · M3 milestone<br>
                No autonomous execution
            </div>
            """,
            unsafe_allow_html=True,
        )
