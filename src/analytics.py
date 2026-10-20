"""
NetScope: Big Data Network Analytics Engine
Executes distributed aggregations in Apache Spark for traffic intelligence,
attack categorization, service port analysis, packet statistics, and throughput benchmarking.
"""

import time
from typing import Dict, Any, Optional
import pandas as pd

try:
    from pyspark.sql import DataFrame
    from pyspark.sql.functions import col, count, sum as spark_sum, avg, round as spark_round, min as spark_min, max as spark_max
except ImportError:
    DataFrame = Any

from config import WELL_KNOWN_PORTS


def compute_overview_kpis(df: DataFrame) -> Dict[str, Any]:
    """
    Compute core Executive SOC KPIs using a single distributed aggregation:
    - Total valid flows
    - Malicious flows count and percentage
    - Benign flows count and percentage
    - Distinct attack categories observed
    """
    # Group by Is_Malicious for fast KPI computation
    summary = df.groupBy("Is_Malicious").count().toPandas()
    
    benign_count = 0
    malicious_count = 0
    for _, row in summary.iterrows():
        if row["Is_Malicious"] == 0:
            benign_count = int(row["count"])
        else:
            malicious_count = int(row["count"])

    total_flows = benign_count + malicious_count
    malicious_pct = (malicious_count / total_flows * 100.0) if total_flows > 0 else 0.0
    benign_pct = (benign_count / total_flows * 100.0) if total_flows > 0 else 0.0

    # Distinct attack categories
    attack_cat_df = df.filter(col("Is_Malicious") == 1).select("Label").distinct().toPandas()
    distinct_attacks = len(attack_cat_df)

    return {
        "total_flows": total_flows,
        "benign_flows": benign_count,
        "benign_percentage": round(benign_pct, 2),
        "malicious_flows": malicious_count,
        "malicious_percentage": round(malicious_pct, 2),
        "distinct_attack_categories": distinct_attacks,
    }


def compute_attack_distribution(df: DataFrame) -> pd.DataFrame:
    """
    Compute flow counts and percentage shares for all observed attack categories.
    """
    total = df.count()
    pdf = (
        df.groupBy("Label")
        .agg(count("*").alias("count"))
        .orderBy(col("count").desc())
        .toPandas()
    )
    if total > 0:
        pdf["percentage"] = (pdf["count"] / total * 100.0).round(3)
        pdf["is_attack"] = pdf["Label"] != "BENIGN"
    else:
        pdf["percentage"] = 0.0
        pdf["is_attack"] = False
    return pdf


def compute_port_distribution(df: DataFrame, top_n: int = 15) -> pd.DataFrame:
    """
    Compute top destination ports and map to well-known network services.
    """
    port_col = None
    for c in ["Destination Port", "destination_port", "dst_port"]:
        if c in df.columns:
            port_col = c
            break

    if not port_col:
        return pd.DataFrame(columns=["port", "service", "count", "percentage"])

    total = df.count()
    pdf = (
        df.groupBy(port_col)
        .agg(count("*").alias("count"))
        .orderBy(col("count").desc())
        .limit(top_n)
        .toPandas()
    )

    pdf.rename(columns={port_col: "port"}, inplace=True)
    pdf["service"] = pdf["port"].apply(lambda p: WELL_KNOWN_PORTS.get(int(p), f"Ephemeral/Other ({p})") if pd.notnull(p) else "Unknown")
    pdf["percentage"] = ((pdf["count"] / total) * 100.0).round(2) if total > 0 else 0.0
    return pdf


def compute_traffic_volume_stats(df: DataFrame) -> Dict[str, Any]:
    """
    Aggregate packet counts, byte volumes, and flow durations across the dataset.
    """
    agg_exprs = []
    
    if "Flow Duration" in df.columns:
        agg_exprs.extend([
            spark_round(avg("Flow Duration"), 2).alias("avg_duration_us"),
            spark_max("Flow Duration").alias("max_duration_us"),
        ])
    if "Total Fwd Packets" in df.columns:
        agg_exprs.append(spark_sum("Total Fwd Packets").alias("total_fwd_packets"))
        agg_exprs.append(spark_round(avg("Total Fwd Packets"), 2).alias("avg_fwd_packets"))
    if "Total Backward Packets" in df.columns:
        agg_exprs.append(spark_sum("Total Backward Packets").alias("total_bwd_packets"))
    if "Total Length of Fwd Packets" in df.columns:
        agg_exprs.append(spark_sum("Total Length of Fwd Packets").alias("total_fwd_bytes"))
    if "Total Length of Bwd Packets" in df.columns:
        agg_exprs.append(spark_sum("Total Length of Bwd Packets").alias("total_bwd_bytes"))
    if "Flow Bytes/s" in df.columns:
        agg_exprs.append(spark_round(avg("Flow Bytes/s"), 2).alias("avg_flow_bytes_per_s"))

    if not agg_exprs:
        return {}

    result_df = df.agg(*agg_exprs).toPandas()
    return result_df.to_dict(orient="records")[0] if not result_df.empty else {}


def compute_attack_feature_comparison(df: DataFrame) -> pd.DataFrame:
    """
    Compare numeric flow metrics across attack categories:
    Flow Duration, Fwd Packets, Fwd Bytes, and Bytes/sec.
    """
    available_cols = df.columns
    agg_list = [count("*").alias("flow_count")]

    if "Flow Duration" in available_cols:
        agg_list.append(spark_round(avg("Flow Duration"), 1).alias("avg_duration_us"))
    if "Total Fwd Packets" in available_cols:
        agg_list.append(spark_round(avg("Total Fwd Packets"), 1).alias("avg_fwd_packets"))
    if "Total Length of Fwd Packets" in available_cols:
        agg_list.append(spark_round(avg("Total Length of Fwd Packets"), 1).alias("avg_fwd_bytes"))
    if "Flow Bytes/s" in available_cols:
        agg_list.append(spark_round(avg("Flow Bytes/s"), 1).alias("avg_bytes_per_s"))

    comparison_df = (
        df.groupBy("Label")
        .agg(*agg_list)
        .orderBy(col("flow_count").desc())
        .toPandas()
    )
    return comparison_df


def benchmark_spark_execution(df: DataFrame, operation_name: str = "Full Dataset Aggregation") -> Dict[str, Any]:
    """
    Measures processing duration and calculated throughput (flows/second) for Spark execution.
    """
    start_time = time.time()
    # Trigger an action that traverses all rows
    row_count = df.count()
    duration = time.time() - start_time

    throughput = (row_count / duration) if duration > 0 else 0.0

    return {
        "operation": operation_name,
        "rows_processed": row_count,
        "execution_time_seconds": round(duration, 3),
        "throughput_flows_per_sec": round(throughput, 1),
        "partitions_count": df.rdd.getNumPartitions() if hasattr(df, "rdd") else 1,
    }
