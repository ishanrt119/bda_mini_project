"""
NetScope: Data Export & Persistent Summary Module
Saves Parquet datasets, writes JSON/CSV aggregated summaries, and produces
downloadable SOC intelligence reports.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

try:
    from pyspark.sql import DataFrame
except ImportError:
    DataFrame = Any

from config import SUMMARIES_DIR, PARQUET_DIR, REPORTS_DIR


def save_aggregate_summaries(summaries: Dict[str, Any], prefix: str = "latest") -> Dict[str, str]:
    """
    Persist aggregate analytics (KPIs, attack distribution, port breakdown,
    quality metrics) to local JSON and CSV files for instant dashboard caching.
    """
    saved_files = {}
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Save complete JSON summary
    json_path = SUMMARIES_DIR / f"{prefix}_summary.json"
    serializable = {}
    for k, v in summaries.items():
        if isinstance(v, pd.DataFrame):
            serializable[k] = v.to_dict(orient="records")
            # Also save individual CSV
            csv_path = SUMMARIES_DIR / f"{prefix}_{k}.csv"
            v.to_csv(csv_path, index=False)
            saved_files[f"{k}_csv"] = str(csv_path)
        else:
            serializable[k] = v

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, default=str)
    saved_files["json_summary"] = str(json_path)

    return saved_files


def load_cached_summaries(prefix: str = "latest") -> Optional[Dict[str, Any]]:
    """
    Load pre-aggregated summary from disk if available to avoid expensive rescans.
    """
    json_path = SUMMARIES_DIR / f"{prefix}_summary.json"
    if not json_path.exists():
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert list of dicts back to pandas DataFrames where applicable
        for key in ["attack_distribution", "port_distribution", "feature_comparison", "investigation_sample"]:
            if key in data and isinstance(data[key], list):
                data[key] = pd.DataFrame(data[key])

        return data
    except Exception as e:
        print(f"[NetScope Warning] Could not load cached summary: {e}")
        return None


def export_parquet(
    df: DataFrame,
    output_location: Optional[str] = None,
    output_subfolder: str = "cleaned_flows"
) -> str:
    """
    Write processed Spark DataFrame to columnar Parquet format.
    Supports local filesystem path or HDFS URI (e.g. hdfs://localhost:9000/netscope/output/cleaned_parquet).
    """
    if output_location and output_location.startswith("hdfs://"):
        target_path = output_location
    elif output_location:
        target_path = output_location
    else:
        target_path = str(PARQUET_DIR / output_subfolder)

    df.write.mode("overwrite").parquet(target_path)
    return str(target_path)


def generate_executive_report(summaries: Dict[str, Any]) -> str:
    """
    Generate a markdown-formatted SOC executive report for security leaders.
    """
    kpis = summaries.get("kpis", {})
    quality = summaries.get("quality_metrics", {})
    spark_info = summaries.get("spark_benchmarks", {})

    report = f"""# NetScope Executive Cybersecurity & Big Data Summary Report
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Engine: Apache Spark Distributed Core | Analysis: CICIDS2017 Benchmark

## 1. Network Flow Executive Metrics
- **Total Valid Flows Analyzed:** {kpis.get('total_flows', 0):,}
- **Malicious Attack Flows:** {kpis.get('malicious_flows', 0):,} ({kpis.get('malicious_percentage', 0.0)}%)
- **Benign Normal Flows:** {kpis.get('benign_flows', 0):,} ({kpis.get('benign_percentage', 0.0)}%)
- **Distinct Threat Classes:** {kpis.get('distinct_attack_categories', 0)}

## 2. Big Data Performance & Architecture
- **Processing Time:** {spark_info.get('execution_time_seconds', 0.0)} seconds
- **Calculated Throughput:** {spark_info.get('throughput_flows_per_sec', 0.0):,} flows/sec
- **Spark Partitions:** {spark_info.get('partitions_count', 1)}

## 3. Data Hygiene & Quality Assurance
- **Raw Records Ingested:** {quality.get('raw_record_count', 0):,}
- **Cleaned Records Retained:** {quality.get('clean_record_count', 0):,}
- **Retention Percentage:** {quality.get('retention_percentage', 0.0)}%
- **Invalid Rate Elements Neutralized:** {quality.get('invalid_rate_values_count', 0):,}

---
*NetScope Security Analytics Platform*
"""
    report_path = REPORTS_DIR / "NetScope_Executive_Report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    return report
