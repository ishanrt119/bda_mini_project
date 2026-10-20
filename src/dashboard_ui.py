"""
NetScope: SOC Dashboard UI Theme & Visualizations
Provides custom dark styling, metric card rendering, and Plotly charts.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List

from config import SOC_THEME


def inject_soc_theme():
    """
    Injects custom CSS for a modern, high-contrast SOC dark analytics theme.
    Deep navy, slate cards, subtle borders, crisp typography, and status badges.
    """
    css = f"""
    <style>
    /* Global Base */
    .stApp {{
        background-color: {SOC_THEME["bg_main"]};
        color: {SOC_THEME["text_primary"]};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    
    /* Top Header & Navigation */
    header[data-testid="stHeader"] {{
        background-color: {SOC_THEME["bg_main"]};
    }}
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: #080c14;
        border-right: 1px solid {SOC_THEME["bg_card_border"]};
    }}
    
    /* NetScope Card Component */
    .netscope-card {{
        background: {SOC_THEME["bg_card"]};
        border: 1px solid {SOC_THEME["bg_card_border"]};
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 16px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .netscope-card:hover {{
        border-color: #334155;
    }}
    
    /* Status Badge */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .badge-online {{
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }}
    .badge-offline {{
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    .badge-warning {{
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }}
    
    /* Metric Cards */
    .metric-value {{
        font-size: 28px;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
        margin-top: 4px;
        letter-spacing: -0.02em;
    }}
    .metric-label {{
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: {SOC_THEME["text_muted"]};
        letter-spacing: 0.06em;
    }}
    .metric-subtext {{
        font-size: 12px;
        color: {SOC_THEME["accent_cyan"]};
        margin-top: 4px;
    }}
    
    /* Tab Navigation */
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        color: {SOC_THEME["text_muted"]} !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        border-bottom: 2px solid transparent !important;
        padding: 8px 16px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {SOC_THEME["accent_cyan"]} !important;
        border-bottom: 2px solid {SOC_THEME["accent_cyan"]} !important;
    }}
    
    /* Clean DataFrame Styling */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {SOC_THEME["bg_card_border"]};
        border-radius: 8px;
        overflow: hidden;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def get_plotly_layout_defaults() -> Dict[str, Any]:
    """Base layout template for SOC dark Plotly charts."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=SOC_THEME["text_primary"], family="-apple-system, sans-serif", size=12),
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis=dict(
            gridcolor=SOC_THEME["bg_card_border"],
            zerolinecolor=SOC_THEME["bg_card_border"],
            tickfont=dict(color=SOC_THEME["text_muted"]),
        ),
        yaxis=dict(
            gridcolor=SOC_THEME["bg_card_border"],
            zerolinecolor=SOC_THEME["bg_card_border"],
            tickfont=dict(color=SOC_THEME["text_muted"]),
        ),
        legend=dict(
            font=dict(color=SOC_THEME["text_primary"]),
            bgcolor="rgba(0,0,0,0)",
        ),
    )


def render_metric_card(title: str, value: str, subtext: str = "", border_color: str = "#1e293b"):
    """Render a KPI metric tile."""
    st.markdown(
        f"""
        <div class="netscope-card" style="border-left: 3px solid {border_color};">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtext" style="color: {border_color};">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_traffic_split_chart(kpis: Dict[str, Any]) -> go.Figure:
    """Donut chart showing Benign vs Malicious flow distribution."""
    labels = ["Benign Flows", "Malicious Flows"]
    values = [kpis.get("benign_flows", 0), kpis.get("malicious_flows", 0)]
    colors = [SOC_THEME["benign_color"], SOC_THEME["malicious_color"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=colors, line=dict(color=SOC_THEME["bg_card"], width=2)),
                textinfo="percent+label",
                textposition="outside",
                hoverinfo="label+value+percent",
            )
        ]
    )
    layout = get_plotly_layout_defaults()
    layout.update(
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{kpis.get('total_flows', 0):,}</b><br><span style='font-size:11px;color:#94a3b8'>TOTAL FLOWS</span>",
                x=0.5,
                y=0.5,
                font_size=16,
                font_color="#ffffff",
                showarrow=False,
            )
        ],
    )
    fig.update_layout(**layout)
    return fig


def build_attack_breakdown_chart(attack_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart showing attack classes and counts."""
    # Exclude BENIGN to highlight attack composition
    attacks_only = attack_df[attack_df["Label"] != "BENIGN"].copy()
    if attacks_only.empty:
        # If no attacks in current sample, show top labels including benign
        attacks_only = attack_df.head(10).copy()

    attacks_only = attacks_only.sort_values(by="count", ascending=True)

    fig = go.Figure(
        go.Bar(
            x=attacks_only["count"],
            y=attacks_only["Label"],
            orientation="h",
            marker=dict(
                color=SOC_THEME["alert_red"],
                line=dict(color="rgba(255,255,255,0.1)", width=1),
            ),
            text=attacks_only["count"].apply(lambda x: f"{x:,}"),
            textposition="auto",
        )
    )
    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text="Identified Attack Categories", font=dict(size=14, color="#ffffff")),
        xaxis_title="Flow Count",
        yaxis_title="",
        height=320,
    )
    fig.update_layout(**layout)
    return fig


def build_port_service_chart(port_df: pd.DataFrame) -> go.Figure:
    """Vertical bar chart showing top target destination ports."""
    if port_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Port Data Available", **get_plotly_layout_defaults())
        return fig

    display_df = port_df.head(10).copy()
    display_df["display_name"] = display_df.apply(lambda r: f"Port {r['port']} ({r['service']})", axis=1)

    fig = go.Figure(
        go.Bar(
            x=display_df["display_name"],
            y=display_df["count"],
            marker=dict(
                color=SOC_THEME["accent_cyan"],
                line=dict(color="rgba(255,255,255,0.1)", width=1),
            ),
            text=display_df["count"].apply(lambda x: f"{x:,}"),
            textposition="auto",
        )
    )
    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text="Top Target Destination Ports & Services", font=dict(size=14, color="#ffffff")),
        xaxis=dict(tickangle=-35),
        yaxis_title="Flow Volume",
        height=320,
    )
    fig.update_layout(**layout)
    return fig


def build_confusion_matrix_chart(cm_data: List[List[int]]) -> go.Figure:
    """Interactive 2x2 Confusion Matrix Heatmap."""
    tn, fp = cm_data[0][0], cm_data[0][1]
    fn, tp = cm_data[1][0], cm_data[1][1]

    z = [[tn, fp], [fn, tp]]
    x_labels = ["Predicted Normal", "Predicted Anomaly"]
    y_labels = ["Actual Benign", "Actual Malicious"]
    text_annotations = [
        [f"True Negative (TN)<br><b>{tn:,}</b>", f"False Positive (FP)<br><b>{fp:,}</b>"],
        [f"False Negative (FN)<br><b>{fn:,}</b>", f"True Positive (TP)<br><b>{tp:,}</b>"],
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x_labels,
            y=y_labels,
            colorscale=[[0, "#131b2e"], [0.5, "#1e3a8a"], [1.0, "#00c9a7"]],
            text=text_annotations,
            texttemplate="%{text}",
            textfont={"size": 13, "color": "#ffffff"},
            showscale=False,
        )
    )
    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text="Detection Evaluation Matrix (Ground Truth vs Heuristic)", font=dict(size=14, color="#ffffff")),
        height=280,
    )
    fig.update_layout(**layout)
    return fig
