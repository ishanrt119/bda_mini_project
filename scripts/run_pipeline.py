#!/usr/bin/env python3
"""
NetScope: Big Data Pipeline Execution CLI
Runs full ingestion, data cleaning, distributed Spark analytics,
explainable anomaly detection, and summary export directly from the terminal.
Supports both Local POSIX Storage and Apache Hadoop HDFS Data Lake.
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.data_discovery import discover_csv_files, get_workspace_dataset_summary
from src.data_loader import get_spark_session, load_network_data, stop_spark_session
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
)
from src.export_utils import (
    save_aggregate_summaries,
    export_parquet,
    generate_executive_report,
)
from src.hdfs_utils import (
    check_hdfs_availability,
    list_hdfs_files,
    upload_local_to_hdfs,
)
from config import DEFAULT_HDFS_URI


def main():
    parser = argparse.ArgumentParser(description="NetScope Big Data Network Analytics Pipeline")
    parser.add_argument("--storage-mode", type=str, choices=["local", "hdfs"], default="local", help="Storage filesystem mode (local or hdfs)")
    parser.add_argument("--hdfs", action="store_true", help="Shorthand to use Hadoop HDFS storage mode")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory containing CSV files (for local mode)")
    parser.add_argument("--sample-fraction", type=float, default=None, help="Sampling fraction (e.g. 0.1 for 10%)")
    parser.add_argument("--row-limit", type=int, default=None, help="Row limit for quick execution")
    parser.add_argument("--export-parquet", action="store_true", help="Export cleaned dataset to Parquet format")
    parser.add_argument("--file", type=str, default=None, help="Specific CSV filename to process")
    args = parser.parse_args()

    use_hdfs = args.hdfs or (args.storage_mode == "hdfs")

    print("==================================================================")
    print("  NetScope: Big Data Network Analytics & Anomaly Detection Pipeline")
    print("  Engine: Apache Spark 4.x / PySpark | Storage: Local / Hadoop HDFS")
    print("==================================================================")

    # 1. Environment & HDFS Diagnostics
    print("\n[*] Probing Storage & Hadoop Environment...")
    hdfs_info = check_hdfs_availability()
    print(f"    Mode: {hdfs_info['mode']}")
    print(f"    Status: {hdfs_info['diagnostic_message']}")

    if use_hdfs:
        if not hdfs_info["is_connected"]:
            print("\n[!] Error: HDFS storage mode requested, but Hadoop HDFS is not reachable.")
            print("    Please start Hadoop daemons ('start-dfs.sh' or 'hdfs --daemon start namenode')")
            print("    or run in local mode without --hdfs flag.")
            sys.exit(1)
        print("    [+] Genuine Hadoop HDFS cluster verified active.")

    # 2. Target Dataset Selection
    if use_hdfs:
        print("\n[*] Querying Hadoop HDFS Data Lake (/netscope/input)...")
        hdfs_files = list_hdfs_files("/netscope/input")
        if not hdfs_files:
            print("    [!] /netscope/input is empty on HDFS. Uploading local dataset...")
            upload_res = upload_local_to_hdfs("MachineLearningCVE", "/netscope/input")
            if not upload_res["success"]:
                print(f"    [!] Failed to upload to HDFS: {upload_res['error']}")
                sys.exit(1)
            hdfs_files = upload_res["files"]

        print(f"    Found {len(hdfs_files)} file(s) on HDFS ({sum(f['size_mb'] for f in hdfs_files):.2f} MB):")
        for f in hdfs_files:
            print(f"    - {f['filename']} ({f['size_mb']} MB)")

        if args.file:
            selected_paths = [f["hdfs_path"] for f in hdfs_files if args.file.lower() in f["filename"].lower()]
            if not selected_paths:
                print(f"[!] Specified file '{args.file}' not found in HDFS /netscope/input.")
                sys.exit(1)
        else:
            selected_paths = [f["hdfs_path"] for f in hdfs_files]
        input_desc = f"HDFS ({len(selected_paths)} files in /netscope/input)"
    else:
        print("\n[*] Discovering Dataset Files on Local Storage...")
        discovered = discover_csv_files(args.data_dir)
        if not discovered:
            print("[!] Error: No CSV files discovered in workspace.")
            sys.exit(1)

        print(f"    Discovered {len(discovered)} CSV file(s) ({sum(f['size_mb'] for f in discovered):.2f} MB total):")
        for f in discovered:
            print(f"    - {f['filename']} ({f['size_mb']} MB)")

        if args.file:
            selected_paths = [f["path"] for f in discovered if args.file.lower() in f["filename"].lower()]
            if not selected_paths:
                print(f"[!] Specified file '{args.file}' not found among discovered files.")
                sys.exit(1)
        else:
            selected_paths = [f["path"] for f in discovered]
        input_desc = f"Local POSIX ({len(selected_paths)} files in MachineLearningCVE/)"

    # 3. Start PySpark Session
    print("\n[*] Initializing Apache Spark Session...")
    t0 = time.time()
    spark = get_spark_session()
    if not spark:
        print("[!] Error: Failed to initialize Apache Spark session.")
        sys.exit(1)
    print(f"    Spark Session initialized in {time.time() - t0:.2f}s (Master: {spark.sparkContext.master})")

    try:
        # 4. Ingest Data
        print(f"\n[*] Ingesting data from: {selected_paths[0] if len(selected_paths)==1 else selected_paths[0] + ' ...'}...")
        df_raw, load_time = load_network_data(
            spark,
            selected_paths,
            sample_fraction=args.sample_fraction,
            row_limit=args.row_limit,
        )
        print(f"    Ingestion complete in {load_time:.2f}s. Columns: {len(df_raw.columns)}")

        # 5. Clean Data & Validate Quality
        print("\n[*] Executing Data Cleaning & Schema Normalization Pipeline...")
        t_clean = time.time()
        df_clean, quality_metrics = clean_network_dataframe(df_raw)
        df_clean.cache()
        clean_time = time.time() - t_clean
        print(f"    Cleaning finished in {clean_time:.2f}s")
        print(f"    - Raw Records:      {quality_metrics['raw_record_count']:,}")
        print(f"    - Clean Records:    {quality_metrics['clean_record_count']:,}")
        print(f"    - Invalid Rates:    {quality_metrics['invalid_rate_values_count']:,}")
        print(f"    - Retention Rate:   {quality_metrics['retention_percentage']:.2f}%")

        # 6. Spark Analytics & Aggregations
        print("\n[*] Computing Distributed Network Analytics...")
        kpis = compute_overview_kpis(df_clean)
        print(f"    - Total Flows:      {kpis['total_flows']:,}")
        print(f"    - Malicious Flows:  {kpis['malicious_flows']:,} ({kpis['malicious_percentage']}%)")
        print(f"    - Benign Flows:     {kpis['benign_flows']:,} ({kpis['benign_percentage']}%)")
        print(f"    - Attack Classes:   {kpis['distinct_attack_categories']}")

        attack_dist = compute_attack_distribution(df_clean)
        print("\n    Top Observed Attack Classes:")
        for _, row in attack_dist.head(6).iterrows():
            print(f"      {row['Label']:30s}: {row['count']:8,d} ({row['percentage']:5.2f}%)")

        port_dist = compute_port_distribution(df_clean, top_n=8)
        print("\n    Top Destination Service Ports:")
        for _, row in port_dist.iterrows():
            print(f"      Port {str(row['port']):6s} ({row['service']:20s}): {row['count']:8,d} ({row['percentage']:5.2f}%)")

        traffic_stats = compute_traffic_volume_stats(df_clean)
        feature_comp = compute_attack_feature_comparison(df_clean)
        benchmarks = benchmark_spark_execution(df_clean, "Full Aggregation Pass")
        print(f"\n    Throughput Benchmark: {benchmarks['throughput_flows_per_sec']:,} flows/sec ({benchmarks['execution_time_seconds']}s)")

        # 7. Anomaly Detection
        print("\n[*] Running Rule-Based Explainable Anomaly Detection Engine...")
        df_tagged = apply_rule_based_anomaly_detection(df_clean)
        df_tagged.cache()
        eval_metrics = evaluate_detection_performance(df_tagged)
        print(f"    - Accuracy:         {eval_metrics['accuracy'] * 100:.2f}%")
        print(f"    - Precision:        {eval_metrics['precision'] * 100:.2f}%")
        print(f"    - Recall:           {eval_metrics['recall'] * 100:.2f}%")
        print(f"    - F1 Score:         {eval_metrics['f1_score']:.4f}")
        print(f"    - True Positives:   {eval_metrics['true_positives']:,}")
        print(f"    - False Positives:  {eval_metrics['false_positives']:,}")

        # Sample for investigation
        investigation_df = (
            df_tagged.filter(df_tagged["is_potential_anomaly"] == 1)
            .select("Destination Port", "Flow Duration", "Flow Bytes/s", "Flow Packets/s", "Label", "anomaly_reasons")
            .limit(100)
            .toPandas()
        )

        # 8. Export & Cache Summaries
        print("\n[*] Persisting Aggregated Summaries to Disk...")
        summary_payload = {
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
            "storage_mode": "HDFS" if use_hdfs else "Local",
            "source_target": input_desc,
        }
        saved = save_aggregate_summaries(summary_payload, prefix="latest")
        for k, p in saved.items():
            print(f"    Saved {k}: {p}")

        # Optional Parquet export
        out_parquet_path = None
        if args.export_parquet or use_hdfs:
            if use_hdfs:
                out_parquet_path = f"{DEFAULT_HDFS_URI}/netscope/output/cleaned_parquet"
                print(f"\n[*] Writing Cleaned Dataset to HDFS Parquet ({out_parquet_path})...")
            else:
                out_parquet_path = str(Path(BASE_DIR) / "outputs" / "parquet" / "cleaned_flows")
                print(f"\n[*] Writing Cleaned Dataset to Local Parquet ({out_parquet_path})...")

            pq_path = export_parquet(df_clean, output_location=out_parquet_path)
            print(f"    Parquet saved to: {pq_path}")

        # Generate Executive Report
        generate_executive_report(summary_payload)
        print("    Executive Markdown report generated in outputs/reports/")

        # Final Verification & Audit Summary Table
        print("\n==================================================================")
        print("  NETSCOPE EXECUTION & BIG DATA AUDIT SUMMARY")
        print("==================================================================")
        print(f"  Storage Filesystem:  {'Hadoop HDFS (hdfs://localhost:9000)' if use_hdfs else 'Local POSIX File Lake'}")
        print(f"  Input Location:      {selected_paths[0] if len(selected_paths)==1 else selected_paths[0] + ' ...'}")
        print(f"  Output Parquet:      {out_parquet_path if out_parquet_path else 'outputs/summaries/'}")
        print(f"  Total Valid Flows:   {kpis['total_flows']:,}")
        print(f"  Malicious Threat:    {kpis['malicious_flows']:,} ({kpis['malicious_percentage']}%)")
        print(f"  Execution Time:      {benchmarks['execution_time_seconds']}s")
        print(f"  Throughput:          {benchmarks['throughput_flows_per_sec']:,} flows/sec")
        print(f"  Execution Status:    SUCCESS (Verified Live)")
        print("==================================================================")

    finally:
        stop_spark_session()


if __name__ == "__main__":
    main()
