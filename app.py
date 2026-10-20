"""
NetScope: Big Data Network Traffic Analytics & Anomaly Detection
Streamlit Cyber Security Operations Center (SOC) Analytics Platform.
Supports dual storage backends: Local POSIX Data Lake and Apache Hadoop HDFS.
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd
import streamlit as st

# Ensure project root is in path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import SOC_THEME, DEFAULT_ANOMALY_RULES, DEFAULT_HDFS_URI
from src.dashboard_ui import (
    inject_soc_theme,
    render_metric_card,
    build_traffic_split_chart,
    build_attack_breakdown_chart,
    build_port_service_chart,
    build_confusion_matrix_chart,
)
from src.data_discovery import discover_csv_files, get_workspace_dataset_summary
from src.data_loader import get_spark_session, load_network_data
from src.data_cleaning import clean_network_dataframe
from src.analytics import (
    compute_overview_kpis,
    compute_attack_distribution,
    compute_port_distribution,
    compute_traffic_volume_stats,
    compute_attack_feature_comparison,
    benchmark_spark_execution,
)
from src.anomaly_detection import (
    apply_rule_based_anomaly_detection,
    evaluate_detection_performance,
    train_optional_spark_rf_model,
)
from src.hdfs_utils import (
    check_hdfs_availability,
    list_hdfs_files,
    upload_local_to_hdfs,
    run_hadoop_streaming_mr_job,
    generate_hdfs_deployment_commands,
)
from src.export_utils import (
    save_aggregate_summaries,
    load_cached_summaries,
    export_parquet,
    generate_executive_report,
)

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NetScope | Big Data Network Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_soc_theme()

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "summaries" not in st.session_state:
    cached = load_cached_summaries(prefix="latest")
    st.session_state["summaries"] = cached

if "spark_df_clean" not in st.session_state:
    st.session_state["spark_df_clean"] = None

# Refresh HDFS status
st.session_state["hdfs_info"] = check_hdfs_availability()
hdfs_info = st.session_state["hdfs_info"]

# -----------------------------------------------------------------------------
# Sidebar: Brand, Storage Selection & Pipeline Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 10px 0 16px 0;">
            <div style="font-size: 22px; font-weight: 800; letter-spacing: -0.03em; color: #ffffff;">
                🛡️ NetScope <span style="font-size: 11px; background: rgba(0, 242, 254, 0.15); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.3); padding: 2px 6px; border-radius: 4px; font-weight: 700; margin-left: 6px;">SPARK-HDFS</span>
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                Big Data Network Traffic & Threat Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 💾 Storage Filesystem Mode")
    storage_choice = st.radio(
        "Select Storage Layer",
        options=["Hadoop HDFS (Data Lake)", "Local POSIX Storage"],
        index=0 if hdfs_info["is_connected"] else 1,
        help="Select whether Spark reads from Hadoop HDFS or Local Storage."
    )
    is_hdfs_mode = (storage_choice == "Hadoop HDFS (Data Lake)")

    # Handle HDFS Mode Selection
    if is_hdfs_mode:
        if not hdfs_info["is_connected"]:
            st.error(f"⚠️ HDFS Cluster Offline: {hdfs_info['diagnostic_message']}")
            st.caption("Falling back to local storage controls until Hadoop NameNode is started.")
            target_files_list = []
            selected_file_option = None
        else:
            hdfs_files = list_hdfs_files("/netscope/input")
            total_hdfs_mb = sum(f["size_mb"] for f in hdfs_files)

            st.markdown(
                f"""
                <div class="netscope-card" style="padding: 10px 14px; border-left: 3px solid #10b981; background: rgba(16, 185, 129, 0.05);">
                    <div style="font-size: 11px; color: #10b981; font-weight: 700; text-transform: uppercase;">🟢 HDFS Data Lake Connected</div>
                    <div style="font-size: 12px; color: #f8fafc; font-family: monospace; margin-top: 2px;">{hdfs_info['hdfs_uri']}/netscope/input/</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 11px; color: #94a3b8;">
                        <span>{len(hdfs_files)} CSV Files</span>
                        <span>{total_hdfs_mb:.1f} MB</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not hdfs_files:
                st.warning("HDFS directory `/netscope/input` is empty.")
                if st.button("📤 Upload Local CSVs to HDFS", use_container_width=True):
                    with st.spinner("Uploading dataset to HDFS..."):
                        up_res = upload_local_to_hdfs("MachineLearningCVE", "/netscope/input")
                        if up_res["success"]:
                            st.success(f"Uploaded {up_res['uploaded_count']} files to HDFS!")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {up_res['error']}")

            file_options = ["All HDFS Files (Aggregated)"] + [f["filename"] for f in hdfs_files]
            selected_file_option = st.selectbox("Select Target File", options=file_options, index=0)
    else:
        # Local Storage Mode
        discovered_files = discover_csv_files()
        total_size = sum(f["size_mb"] for f in discovered_files)

        st.markdown(
            f"""
            <div class="netscope-card" style="padding: 10px 14px; border-left: 3px solid #38bdf8;">
                <div style="font-size: 11px; color: #38bdf8; font-weight: 700; text-transform: uppercase;">📁 Local POSIX Storage</div>
                <div style="font-size: 12px; color: #f8fafc; font-family: monospace; margin-top: 2px;">MachineLearningCVE/</div>
                <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 11px; color: #94a3b8;">
                    <span>{len(discovered_files)} CSV Files</span>
                    <span>{total_size:.1f} MB</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        file_options = ["All Discovered CSV Files (Aggregated)"] + [f["filename"] for f in discovered_files]
        selected_file_option = st.selectbox("Select Target File", options=file_options, index=0)

    # Row Sampling Option
    sample_options = {
        "25,000 Flows (Instant Preview)": 25000,
        "50,000 Flows (Standard Demo)": 50000,
        "100,000 Flows (Deep Analysis)": 100000,
        "250,000 Flows (Large Scale)": 250000,
        "Full File / Uncapped": None,
    }
    selected_sample_label = st.selectbox("Flow Sample Bounding", list(sample_options.keys()), index=1)
    target_row_limit = sample_options[selected_sample_label]

    # Processing Buttons
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        run_analysis = st.button("⚡ Run Spark", type="primary", use_container_width=True)
    with col_btn2:
        reload_cache = st.button("🔄 Disk Cache", use_container_width=True)

    if reload_cache:
        cached = load_cached_summaries(prefix="latest")
        if cached:
            st.session_state["summaries"] = cached
            st.success("Loaded disk cache!")
        else:
            st.warning("No disk cache found. Please run Spark analytics first.")

    st.divider()

    # System Status Panel
    st.markdown("### 🖥️ Engine Status")
    hdfs_badge = "badge-online" if hdfs_info["is_connected"] else "badge-warning"
    hdfs_text = f"HDFS ONLINE ({hdfs_info['live_datanodes']} DN)" if hdfs_info["is_connected"] else "LOCAL FALLBACK"

    st.markdown(
        f"""
        <div class="netscope-card" style="padding: 12px 14px; font-size: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #94a3b8;">Spark Engine:</span>
                <span class="status-badge badge-online">ACTIVE 4.2.0</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #94a3b8;">HDFS Cluster:</span>
                <span class="status-badge {hdfs_badge}">{hdfs_text}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #94a3b8;">Spark Master:</span>
                <span style="color: #e2e8f0; font-family: monospace;">local[*]</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("NetScope v1.1.0 | Real Hadoop HDFS & Spark Integration")


# -----------------------------------------------------------------------------
# Trigger Spark Analytics Computation
# -----------------------------------------------------------------------------
if run_analysis:
    with st.spinner("Initializing Apache Spark Engine and ingesting flow dataset..."):
        spark = get_spark_session()
        if not spark:
            st.error("Failed to initialize Apache Spark session. Please check Java installation.")
        else:
            try:
                # Determine paths based on selected storage mode
                if is_hdfs_mode:
                    if not hdfs_info["is_connected"]:
                        st.error("Cannot run HDFS pipeline: NameNode is offline.")
                        st.stop()
                    hdfs_files = list_hdfs_files("/netscope/input")
                    if selected_file_option == "All HDFS Files (Aggregated)":
                        target_paths = [f["hdfs_path"] for f in hdfs_files]
                    else:
                        target_paths = [f["hdfs_path"] for f in hdfs_files if f["filename"] == selected_file_option]
                    mode_tag = "Hadoop HDFS"
                    out_parquet_path = f"{DEFAULT_HDFS_URI}/netscope/output/cleaned_parquet"
                else:
                    discovered_files = discover_csv_files()
                    if selected_file_option == "All Discovered CSV Files (Aggregated)":
                        target_paths = [f["path"] for f in discovered_files]
                    else:
                        target_paths = [f["path"] for f in discovered_files if f["filename"] == selected_file_option]
                    mode_tag = "Local POSIX"
                    out_parquet_path = str(Path(BASE_DIR) / "outputs" / "parquet" / "cleaned_flows")

                # Ingestion
                df_raw, load_time = load_network_data(spark, target_paths, row_limit=target_row_limit)

                # Cleaning
                df_clean, quality_metrics = clean_network_dataframe(df_raw)
                df_clean.cache()

                # Analytics
                kpis = compute_overview_kpis(df_clean)
                attack_dist = compute_attack_distribution(df_clean)
                port_dist = compute_port_distribution(df_clean, top_n=15)
                traffic_stats = compute_traffic_volume_stats(df_clean)
                feature_comp = compute_attack_feature_comparison(df_clean)
                benchmarks = benchmark_spark_execution(df_clean, f"{mode_tag} Aggregation Pass")

                # Anomaly Tagging
                df_tagged = apply_rule_based_anomaly_detection(df_clean)
                df_tagged.cache()
                eval_metrics = evaluate_detection_performance(df_tagged)

                # Sample for investigation
                investigation_df = (
                    df_tagged.filter(df_tagged["is_potential_anomaly"] == 1)
                    .select("Destination Port", "Flow Duration", "Flow Bytes/s", "Flow Packets/s", "Label", "anomaly_reasons")
                    .limit(200)
                    .toPandas()
                )

                # Write Parquet to target storage (HDFS or local)
                pq_saved = export_parquet(df_clean, output_location=out_parquet_path)

                # Store in session state & disk cache
                summary_data = {
                    "kpis": kpis,
                    "quality_metrics": quality_metrics,
                    "attack_distribution": attack_dist,
                    "port_distribution": port_dist,
                    "traffic_stats": traffic_stats,
                    "feature_comparison": feature_comp,
                    "anomaly_eval": eval_metrics,
                    "spark_benchmarks": benchmarks,
                    "investigation_sample": investigation_df,
                    "last_processed_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "storage_mode": mode_tag,
                    "source_target": target_paths[0] if len(target_paths) == 1 else f"{len(target_paths)} files ({target_paths[0]}...)",
                    "output_parquet": pq_saved,
                }
                save_aggregate_summaries(summary_data, prefix="latest")
                generate_executive_report(summary_data)

                st.session_state["summaries"] = summary_data
                st.session_state["spark_df_clean"] = df_clean
                st.success(f"Processing complete on {mode_tag}! Analyzed {kpis['total_flows']:,} flows in {benchmarks['execution_time_seconds']}s")
            except Exception as e:
                st.error(f"Spark Processing Error: {str(e)}")


# -----------------------------------------------------------------------------
# Top Status Bar & Main Header
# -----------------------------------------------------------------------------
summaries = st.session_state.get("summaries")
last_ts = summaries.get("last_processed_timestamp", "Not Executed Yet") if summaries else "Not Executed Yet"
source_lbl = summaries.get("source_target", "Default Sample") if summaries else "Default Sample"
storage_lbl = summaries.get("storage_mode", "Local File Lake") if summaries else "Local File Lake"

# Top Status Strip
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    status_label = f"🟢 Loaded ({summaries['kpis']['total_flows']:,} flows)" if summaries else "🟡 Ready to Ingest"
    st.markdown(f"**Data Pipeline:** {status_label}")
with col_s2:
    st.markdown("**Analytics Engine:** ⚡ Apache Spark 4.2.0")
with col_s3:
    mode_text = f"HDFS Active ({hdfs_info['live_datanodes']} DN)" if hdfs_info["is_connected"] else "Local POSIX (Active)"
    st.markdown(f"**Storage System:** 💾 {mode_text}")
with col_s4:
    st.markdown(f"**Last Analysis:** 🕒 {last_ts}")

st.markdown(
    """
    <div style="margin-top: 10px; margin-bottom: 20px;">
        <h1 style="font-size: 28px; font-weight: 800; color: #ffffff; margin-bottom: 4px;">
            Network Traffic Intelligence & Threat Center
        </h1>
        <div style="font-size: 14px; color: #94a3b8;">
            High-performance distributed flow analytics and rule-based anomaly detection on the CICIDS2017 benchmark dataset.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Main Navigation Tabs
# -----------------------------------------------------------------------------
tabs = st.tabs([
    "📊 Executive Overview",
    "🌐 Traffic Analysis",
    "🎯 Threat Intelligence",
    "🔍 Anomaly Explorer",
    "🧹 Data Hygiene & Quality",
    "⚡ Big Data & HDFS Architecture",
    "📚 Methodology & Viva Guide",
])

if not summaries:
    st.info("👋 Welcome to NetScope! Click **'⚡ Run Spark'** in the sidebar to execute real Apache Spark analytics on the CICIDS2017 dataset, or click **'🔄 Disk Cache'** to load cached analytics.")

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------
with tabs[0]:
    if summaries:
        kpis = summaries["kpis"]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Total Valid Flows", f"{kpis['total_flows']:,}", f"Storage: {storage_lbl}", "#38bdf8")
        with col2:
            render_metric_card("Malicious Threat Flows", f"{kpis['malicious_flows']:,}", f"{kpis['malicious_percentage']}% of traffic", "#ef4444")
        with col3:
            render_metric_card("Benign Traffic Flows", f"{kpis['benign_flows']:,}", f"{kpis['benign_percentage']}% verified normal", "#10b981")
        with col4:
            render_metric_card("Distinct Threat Categories", f"{kpis['distinct_attack_categories']}", "Identified Attack Classes", "#f59e0b")

        st.markdown("<br>", unsafe_allow_html=True)
        col_chart1, col_chart2 = st.columns([1, 1.3])
        with col_chart1:
            st.markdown("#### Traffic Composition: Benign vs Threat")
            fig_donut = build_traffic_split_chart(kpis)
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_chart2:
            st.markdown("#### Attack Distribution Breakdown")
            attack_df = summaries["attack_distribution"]
            fig_bar = build_attack_breakdown_chart(attack_df)
            st.plotly_chart(fig_bar, use_container_width=True)

        # Quick Highlights & Threat Alerts
        st.markdown("#### 🚨 Security Operations Alert Summary")
        if kpis["malicious_flows"] > 0:
            top_attack = attack_df[attack_df["Label"] != "BENIGN"].iloc[0] if not attack_df[attack_df["Label"] != "BENIGN"].empty else None
            top_attack_name = top_attack["Label"] if top_attack is not None else "None"
            top_attack_count = top_attack["count"] if top_attack is not None else 0
            st.markdown(
                f"""
                <div class="netscope-card" style="border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.05);">
                    <div style="font-weight: 700; color: #ef4444; font-size: 15px;">CRITICAL THREAT CLUSTER DETECTED</div>
                    <div style="font-size: 13px; color: #e2e8f0; margin-top: 4px;">
                        Dominant attack pattern: <b>{top_attack_name}</b> accounting for <b>{top_attack_count:,}</b> flagged flows.
                        High-rate packet surges indicate aggressive volumetric disruption or reconnaissance targeting infrastructure services.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="netscope-card" style="border-left: 4px solid #10b981; background: rgba(16, 185, 129, 0.05);">
                    <div style="font-weight: 700; color: #10b981; font-size: 15px;">BENIGN BASELINE OBSERVED</div>
                    <div style="font-size: 13px; color: #e2e8f0; margin-top: 4px;">
                        The selected dataset slice consists exclusively of legitimate baseline enterprise network activity (e.g., Monday working hours capture).
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.write("Awaiting Spark execution. Click '⚡ Run Spark' in the sidebar.")

# -----------------------------------------------------------------------------
# TAB 2: TRAFFIC ANALYSIS
# -----------------------------------------------------------------------------
with tabs[1]:
    if summaries:
        st.markdown("### Destination Service & Flow Volume Intelligence")
        col_t1, col_t2 = st.columns([1.2, 1])
        with col_t1:
            port_df = summaries["port_distribution"]
            fig_port = build_port_service_chart(port_df)
            st.plotly_chart(fig_port, use_container_width=True)

        with col_t2:
            st.markdown("#### 📡 Service Port Mapping Breakdown")
            st.dataframe(
                port_df[["port", "service", "count", "percentage"]].rename(
                    columns={
                        "port": "Port",
                        "service": "Service Description",
                        "count": "Flows",
                        "percentage": "Share (%)",
                    }
                ),
                use_container_width=True,
                height=300,
                hide_index=True,
            )

        # Volumetric & Packet Statistics
        st.markdown("#### 📦 Flow Duration and Volume Statistics")
        stats = summaries["traffic_stats"]
        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        with col_v1:
            st.metric("Avg Flow Duration", f"{stats.get('avg_duration_us', 0):,.1f} µs")
        with col_v2:
            st.metric("Avg Fwd Packets", f"{stats.get('avg_fwd_packets', 0):,.1f} pkts/flow")
        with col_v3:
            st.metric("Total Fwd Data", f"{stats.get('total_fwd_bytes', 0) / (1024*1024):,.2f} MB")
        with col_v4:
            st.metric("Avg Flow Rate", f"{stats.get('avg_flow_bytes_per_s', 0):,.1f} B/s")

        # Informative Notice Regarding Timestamps & Protocol Strings
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="netscope-card" style="border-left: 3px solid #00f2fe; background: rgba(0, 242, 254, 0.04);">
                <div style="font-weight: 600; color: #00f2fe; font-size: 13px;">ℹ️ DATASET SCHEMA ARCHITECTURE NOTE</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                    In the pre-processed CICIDS2017 <code>MachineLearningCVE</code> feature extraction subset, raw IP addresses and absolute timestamps were intentionally omitted by the University of New Brunswick (UNB) researchers to prevent supervised models from memorizing specific host IPs. Time-based dynamics are captured through high-resolution relative timing features: <code>Flow Duration</code>, <code>Flow Inter-Arrival Times (IAT)</code>, and <code>Active/Idle</code> cycle windows.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.write("Awaiting Spark execution.")

# -----------------------------------------------------------------------------
# TAB 3: THREAT INTELLIGENCE
# -----------------------------------------------------------------------------
with tabs[2]:
    if summaries:
        st.markdown("### Threat Classification & Attack Feature Profiling")
        attack_df = summaries["attack_distribution"]

        col_a1, col_a2 = st.columns([1, 1.2])
        with col_a1:
            st.markdown("#### Observed Threat Classes")
            st.dataframe(
                attack_df[["Label", "count", "percentage", "is_attack"]].rename(
                    columns={
                        "Label": "Threat Category",
                        "count": "Flow Count",
                        "percentage": "Proportion (%)",
                        "is_attack": "Is Attack",
                    }
                ),
                use_container_width=True,
                height=350,
                hide_index=True,
            )

        with col_a2:
            st.markdown("#### Feature Comparison Across Threat Classes")
            feature_comp = summaries["feature_comparison"]
            st.dataframe(
                feature_comp.rename(
                    columns={
                        "Label": "Threat Category",
                        "flow_count": "Total Flows",
                        "avg_duration_us": "Avg Duration (µs)",
                        "avg_fwd_packets": "Avg Fwd Pkts",
                        "avg_fwd_bytes": "Avg Fwd Bytes",
                        "avg_bytes_per_s": "Avg Rate (B/s)",
                    }
                ),
                use_container_width=True,
                height=350,
                hide_index=True,
            )

        # Download Attack Distribution
        csv_data = attack_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Attack Distribution (CSV)",
            data=csv_data,
            file_name="netscope_attack_distribution.csv",
            mime="text/csv",
        )
    else:
        st.write("Awaiting Spark execution.")

# -----------------------------------------------------------------------------
# TAB 4: ANOMALY EXPLORER
# -----------------------------------------------------------------------------
with tabs[3]:
    if summaries:
        st.markdown("### Explainable Rule-Based Anomaly Detection & Model Evaluation")
        st.markdown(
            """
            <div style="font-size: 13px; color: #94a3b8; margin-bottom: 16px;">
                NetScope uses an explainable heuristic anomaly engine. Flows exceeding volumetric rate, packet velocity, or SYN-flood thresholds are flagged with human-readable reason codes, then evaluated against ground-truth dataset labels.
            </div>
            """,
            unsafe_allow_html=True,
        )

        eval_metrics = summaries["anomaly_eval"]
        col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns(5)
        with col_e1:
            render_metric_card("Accuracy", f"{eval_metrics['accuracy'] * 100:.1f}%", "Overall Agreement", "#38bdf8")
        with col_e2:
            render_metric_card("Precision", f"{eval_metrics['precision'] * 100:.1f}%", "TP / (TP + FP)", "#00c9a7")
        with col_e3:
            render_metric_card("Recall", f"{eval_metrics['recall'] * 100:.1f}%", "TP / (TP + FN)", "#f59e0b")
        with col_e4:
            render_metric_card("F1-Score", f"{eval_metrics['f1_score']:.4f}", "Harmonic Mean", "#a855f7")
        with col_e5:
            render_metric_card("True Positives", f"{eval_metrics['true_positives']:,}", "Confirmed Attacks", "#10b981")

        st.markdown("<br>", unsafe_allow_html=True)
        col_cm, col_rules = st.columns([1, 1.2])
        with col_cm:
            st.markdown("#### Confusion Matrix (Ground Truth vs Heuristic)")
            fig_cm = build_confusion_matrix_chart(eval_metrics["confusion_matrix"])
            st.plotly_chart(fig_cm, use_container_width=True)

        with col_rules:
            st.markdown("#### Heuristic Rule Thresholds & Rationale")
            st.markdown(
                """
                <div class="netscope-card" style="font-size: 13px;">
                    <ul style="padding-left: 18px; margin: 0; line-height: 1.8;">
                        <li><b>Volumetric Burst Rule:</b> Flow Rate &gt; 1,000,000 Bytes/sec (Volumetric DDoS / Exfiltration).</li>
                        <li><b>High Packet Velocity:</b> Flow Rate &gt; 50,000 Packets/sec (SYN floods or port sweep).</li>
                        <li><b>Forward Flood Rule:</b> Total Forward Packets &gt; 500 per flow.</li>
                        <li><b>Rapid SYN Pattern:</b> SYN Flag Count &ge; 1 with Flow Duration &lt; 50 µs.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Flagged Flow Investigation Table
        st.markdown("#### 🔎 Anomaly Investigation Workbench (Flagged Records)")
        inv_df = summaries.get("investigation_sample", pd.DataFrame())
        if not inv_df.empty:
            all_reasons = set()
            for r in inv_df["anomaly_reasons"].dropna():
                for part in r.split(" | "):
                    if part.strip():
                        all_reasons.add(part.strip())

            selected_reasons = st.multiselect("Filter by Anomaly Reason:", options=sorted(list(all_reasons)))
            filtered_inv = inv_df
            if selected_reasons:
                filtered_inv = inv_df[inv_df["anomaly_reasons"].apply(lambda x: any(sr in str(x) for sr in selected_reasons))]

            st.dataframe(
                filtered_inv.rename(
                    columns={
                        "Destination Port": "Dst Port",
                        "Flow Duration": "Duration (µs)",
                        "Flow Bytes/s": "Bytes/s",
                        "Flow Packets/s": "Pkts/s",
                        "Label": "Ground Truth Label",
                        "anomaly_reasons": "Triggered Heuristics",
                    }
                ),
                use_container_width=True,
                height=280,
                hide_index=True,
            )

            # Download Investigation Results
            csv_inv = filtered_inv.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Investigation Table (CSV)",
                data=csv_inv,
                file_name="netscope_flagged_anomalies.csv",
                mime="text/csv",
            )
        else:
            st.info("No flows exceeded the anomaly thresholds in the current dataset slice.")

        # Optional Machine Learning Model Section
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🤖 Optional Machine Learning Pipeline (Spark MLlib Random Forest)"):
            st.markdown(
                """
                Train a distributed **Spark MLlib Random Forest Classifier** on network flow features with strict train/test splitting (80/20) and no target leakage.
                """
            )
            col_ml1, col_ml2 = st.columns([1, 2])
            with col_ml1:
                run_ml = st.button("🚀 Train Spark MLlib Model", type="secondary")
            
            if run_ml:
                with st.spinner("Training Spark MLlib Random Forest on clean feature partitions..."):
                    clean_df = st.session_state.get("spark_df_clean")
                    if clean_df is None:
                        spark = get_spark_session()
                        if spark:
                            clean_df, _ = load_network_data(spark, [f["path"] for f in discover_csv_files()], row_limit=50000)
                            clean_df, _ = clean_network_dataframe(clean_df)

                    if clean_df is not None:
                        ml_res = train_optional_spark_rf_model(clean_df, sample_size=40000, test_ratio=0.2)
                        if "error" in ml_res:
                            st.error(ml_res["error"])
                        else:
                            st.success(f"Model trained! Evaluated on {ml_res['test_samples']:,} held-out test flows.")
                            m1, m2, m3, m4 = st.columns(4)
                            with m1:
                                st.metric("Test Accuracy", f"{ml_res['accuracy']*100:.2f}%")
                            with m2:
                                st.metric("Test Precision", f"{ml_res['precision']*100:.2f}%")
                            with m3:
                                st.metric("Test Recall", f"{ml_res['recall']*100:.2f}%")
                            with m4:
                                st.metric("Test F1-Score", f"{ml_res['f1_score']:.4f}")

                            st.markdown("##### Feature Importance Ranking")
                            st.dataframe(pd.DataFrame(ml_res["feature_importances"]).head(8), hide_index=True)
                    else:
                        st.error("No active Spark DataFrame available for training.")
    else:
        st.write("Awaiting Spark execution.")

# -----------------------------------------------------------------------------
# TAB 5: DATA HYGIENE & QUALITY
# -----------------------------------------------------------------------------
with tabs[4]:
    if summaries:
        st.markdown("### Data Quality Assurance & Schema Hygiene Audit")
        qm = summaries["quality_metrics"]

        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        with col_q1:
            render_metric_card("Raw Ingested Records", f"{qm['raw_record_count']:,}", "Pre-cleaning volume", "#38bdf8")
        with col_q2:
            render_metric_card("Clean Retained Records", f"{qm['clean_record_count']:,}", f"{qm['retention_percentage']}% data retention", "#10b981")
        with col_q3:
            render_metric_card("Invalid / Infinite Rates", f"{qm['invalid_rate_values_count']:,}", "IEEE 754 Inf / NaN Neutralized", "#f59e0b")
        with col_q4:
            render_metric_card("Cleaned Schema Columns", f"{qm['total_columns']}", "Spaces & Duplicates Resolved", "#a855f7")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Applied Cleansing Transformations")
        st.markdown(
            """
            <div class="netscope-card" style="font-size: 13px;">
                <table style="width: 100%; border-collapse: collapse; color: #e2e8f0;">
                    <tr style="border-bottom: 1px solid #1e293b; color: #94a3b8; text-align: left;">
                        <th style="padding: 8px;">Pipeline Stage</th>
                        <th style="padding: 8px;">Issue Detected</th>
                        <th style="padding: 8px;">Resolution Mechanism</th>
                        <th style="padding: 8px;">Status</th>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 8px;"><b>Schema Normalization</b></td>
                        <td style="padding: 8px;">Whitespace in headers (e.g. <code>' Destination Port'</code>)</td>
                        <td style="padding: 8px;">Automated string trimming on all 79 columns</td>
                        <td style="padding: 8px; color: #10b981;">RESOLVED</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 8px;"><b>Duplicate Columns</b></td>
                        <td style="padding: 8px;">Column 34 & 55 both named <code>'Fwd Header Length'</code></td>
                        <td style="padding: 8px;">Disambiguated to <code>'Fwd Header Length'</code> and <code>'Fwd Header Length_1'</code></td>
                        <td style="padding: 8px; color: #10b981;">RESOLVED</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 8px;"><b>Label Encoding</b></td>
                        <td style="padding: 8px;">Unicode replacement char <code>\ufffd</code> in web attacks</td>
                        <td style="padding: 8px;">Normalized to <code>'Web Attack - Brute Force / XSS'</code></td>
                        <td style="padding: 8px; color: #10b981;">RESOLVED</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 8px;"><b>Rate Columns Sanity</b></td>
                        <td style="padding: 8px;">IEEE 754 <code>Infinity</code> and <code>NaN</code> in Flow Bytes/s</td>
                        <td style="padding: 8px;">Imputed to 0.0 or cast to clean double precision</td>
                        <td style="padding: 8px; color: #10b981;">RESOLVED</td>
                    </tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.write("Awaiting Spark execution.")

# -----------------------------------------------------------------------------
# TAB 6: BIG DATA & HDFS ARCHITECTURE
# -----------------------------------------------------------------------------
with tabs[5]:
    st.markdown("### Distributed Big Data Processing & Hadoop HDFS Integration")

    if summaries:
        benchmarks = summaries.get("spark_benchmarks", {})
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            render_metric_card("Processing Duration", f"{benchmarks.get('execution_time_seconds', 0)} s", f"Engine: {summaries.get('storage_mode', 'Local')}", "#38bdf8")
        with col_b2:
            render_metric_card("Spark Throughput", f"{benchmarks.get('throughput_flows_per_sec', 0):,} flows/s", "Distributed Processing Rate", "#00c9a7")
        with col_b3:
            render_metric_card("Spark RDD Partitions", f"{benchmarks.get('partitions_count', 1)}", "Parallel Execution Slices", "#a855f7")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🌐 Genuine Hadoop HDFS Data Lake Architecture")
    
    col_h1, col_h2 = st.columns([1.2, 1])
    with col_h1:
        st.markdown(
            f"""
            <div class="netscope-card" style="font-size: 13px;">
                <div style="font-weight: 700; color: #ffffff; margin-bottom: 10px;">Hadoop HDFS Cluster Status</div>
                <div style="margin-bottom: 8px;"><b>Operating State:</b> <span class="status-badge {'badge-online' if hdfs_info['is_connected'] else 'badge-offline'}">{'ONLINE & ACTIVE' if hdfs_info['is_connected'] else 'OFFLINE'}</span></div>
                <div style="margin-bottom: 8px;"><b>NameNode URI:</b> <code>{hdfs_info['hdfs_uri']}</code></div>
                <div style="margin-bottom: 8px;"><b>Live DataNodes:</b> <b>{hdfs_info['live_datanodes']} node(s)</b> active</div>
                <div style="margin-bottom: 8px;"><b>DFS Remaining:</b> <b>{hdfs_info.get('dfs_remaining_gb', 0.0):.1f} GB</b></div>
                <div style="margin-bottom: 8px;"><b>SafeMode:</b> {'ON' if hdfs_info.get('safemode_on') else 'OFF'}</div>
                <div style="margin-bottom: 8px;"><b>HDFS CLI Binary:</b> {'Found (/opt/homebrew/bin/hdfs)' if hdfs_info['has_hdfs_binary'] else 'Missing'}</div>
                <div><b>Diagnostics:</b> <span style="color: {'#10b981' if hdfs_info['is_connected'] else '#f59e0b'};">{hdfs_info['diagnostic_message']}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_h2:
        st.markdown("#### Verified Storage Locations")
        last_in = summaries.get("source_target", "Not executed yet") if summaries else "Not executed yet"
        last_out = summaries.get("output_parquet", "outputs/parquet/cleaned_flows") if summaries else "outputs/parquet/cleaned_flows"
        st.markdown(
            f"""
            <div class="netscope-card" style="font-size: 12px;">
                <div style="font-weight: 700; color: #ffffff; margin-bottom: 8px;">Data Pipeline Endpoints</div>
                <div style="margin-bottom: 6px;"><b>Input Location:</b><br><code style="font-size: 11px; word-break: break-all;">{last_in}</code></div>
                <div style="margin-bottom: 6px;"><b>Output Location (Parquet):</b><br><code style="font-size: 11px; word-break: break-all;">{last_out}</code></div>
                <div><b>Last Verified Result:</b><br><span style="color: #10b981;">{summaries['kpis']['total_flows']:,} flows successfully processed</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Real Live Hadoop Streaming MapReduce Section
    st.markdown("#### 🔄 Live Hadoop Streaming MapReduce on HDFS")
    st.markdown(
        """
        <div style="font-size: 13px; color: #94a3b8; margin-bottom: 12px;">
            Execute a genuine <b>Hadoop Streaming MapReduce job</b> using <code>hadoop-streaming-3.5.0.jar</code> against the dataset on HDFS (<code>/netscope/input</code>).
            The Map phase extracts and normalizes flow labels; the Shuffle/Sort groups them on DataNodes; the Reduce phase calculates total attack occurrences and writes results back to HDFS (<code>/netscope/output/mr_attack_counts</code>).
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_mr1, col_mr2 = st.columns([1, 2])
    with col_mr1:
        run_mr = st.button("🚀 Execute Hadoop MapReduce on HDFS", type="primary", use_container_width=True)

    if run_mr:
        with st.spinner("Submitting and executing MapReduce streaming job on Hadoop cluster..."):
            mr_job = run_hadoop_streaming_mr_job(
                input_file="/netscope/input/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
                output_dir="/netscope/output/mr_attack_counts"
            )
            if mr_job["success"]:
                st.success("Hadoop Streaming MapReduce job completed successfully on HDFS!")
                res_df = pd.DataFrame([{"Attack Class": k, "MapReduce Aggregated Count": v} for k, v in mr_job["results"].items()])
                st.dataframe(res_df, use_container_width=True, hide_index=True)
                st.caption(f"Output stored on HDFS at: {mr_job['output_dir']}/part-00000")
            else:
                st.error(f"Hadoop MapReduce Error: {mr_job.get('error')}")

# -----------------------------------------------------------------------------
# TAB 7: METHODOLOGY & VIVA GUIDE
# -----------------------------------------------------------------------------
with tabs[6]:
    st.markdown("### Methodology, Analytical Principles & Exam Viva Guide")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("#### 🔬 Dataset & Feature Engineering Background")
        st.markdown(
            """
            - **Benchmark Dataset:** CICIDS2017 published by the Canadian Institute for Cybersecurity (ISCX / University of New Brunswick).
            - **Flow Generation Engine:** Created using `CICFlowMeter`, which analyzes bidirectional packet sequences (pcap) and extracts over 80 statistical features per network flow.
            - **Capture Environment:** A realistic topology encompassing diverse victim machines (Windows, Ubuntu, web servers) and simulated attacker agents executing multi-vector intrusions over 5 business days.
            - **Attacks Captured:** DDoS, DoS (Slowloris, Slowhttptest, Hulk, GoldenEye), PortScan, Botnets, Infiltration, FTP-Patator, SSH-Patator, and Web Attacks (Brute Force, XSS, SQL Injection).
            """
        )

    with col_m2:
        st.markdown("#### ⚖️ Offline Flow Analytics vs Real-Time IDS")
        st.markdown(
            """
            - **Offline Historical Flow Analytics (NetScope):**
              - Analyzes completed bidirectional flow sessions.
              - Well suited for forensic investigation, audit, capacity planning, and threat hunting across hundreds of millions of records using Apache Spark and Hadoop.
            - **Real-Time Intrusion Detection (Suricata / Snort):**
              - Operates inline on live packet streams at Layer 3/4/7.
              - Inspects payload byte signatures and enforces immediate TCP resets or packet dropping at sub-millisecond latencies.
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🎓 College Practical Exam / Viva Defense Cheat Sheet")
    with st.expander("Q1: Why use Apache Spark instead of standard Pandas for this project?"):
        st.write(
            "CICIDS2017 contains over 2.8 million flow records totaling nearly 1 GB uncompressed. While Pandas loads the entire dataset into a single thread's virtual memory—causing out-of-memory (OOM) crashes on large datasets—PySpark partitions the data into distributed Resilient Distributed Datasets (RDDs) and DataFrames, executing parallel map, filter, and aggregation transformations across multiple CPU cores without memory exhaustion."
        )

    with st.expander("Q2: How does NetScope handle missing or invalid values during data cleaning?"):
        st.write(
            "In CICIDS2017, flow metrics such as 'Flow Bytes/s' frequently contain IEEE 754 positive/negative infinity or NaN caused by zero-duration flows (division by zero). NetScope detects these using PySpark SQL conditional expressions (`isnan`, `col == float('inf')`), replaces them with 0.0 or drops corrupted rows, normalizes unicode encoding artifacts in web attack labels, and disambiguates duplicate column names ('Fwd Header Length')."
        )

    with st.expander("Q3: How does the rule-based anomaly detection avoid data leakage?"):
        st.write(
            "The heuristic anomaly rules rely exclusively on observable network flow properties (volumetric rate, packet velocity, forward packet count, SYN flag timing) without ever referencing the target 'Label' or 'Is_Malicious' column. The ground-truth label is used strictly during post-detection evaluation to compute precision, recall, and the confusion matrix."
        )

    with st.expander("Q4: How does Hadoop HDFS fit into this Big Data pipeline?"):
        st.write(
            "In production Big Data deployments, network flow pcap files and CSVs are ingested into Hadoop HDFS, which replicates blocks (default 128 MB) across DataNodes for fault tolerance. Apache Spark runs computation locally on the nodes storing the data (data locality). NetScope provides real HDFS connectivity checking, file management, and native HDFS read/write in Parquet format."
        )

    # Executive Report Download
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📄 Executive Cybersecurity Report Export")
    if summaries:
        report_md = generate_executive_report(summaries)
        st.download_button(
            label="📥 Download Executive Markdown Report",
            data=report_md.encode("utf-8"),
            file_name="NetScope_Executive_Report.md",
            mime="text/markdown",
        )
    else:
        st.info("Execute Spark analytics to generate the executive report.")
