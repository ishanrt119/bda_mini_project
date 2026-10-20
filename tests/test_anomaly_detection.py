"""
Unit tests for rule-based anomaly detection and performance evaluation.
"""

import pytest
from pyspark.sql import SparkSession
from src.anomaly_detection import apply_rule_based_anomaly_detection, evaluate_detection_performance


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder.master("local[1]")
        .appName("test_anomaly")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def test_rule_based_anomaly_detection(spark):
    data = [
        # Normal flow
        (80, 500.0, 10.0, 5, 0, 1000, 0),
        # Volumetric spike (>1MB/s)
        (80, 2_000_000.0, 10.0, 5, 0, 1000, 1),
        # High packet velocity (>50k pkt/s)
        (443, 100.0, 60_000.0, 5, 0, 1000, 1),
        # Heavy fwd packets (>500)
        (22, 100.0, 10.0, 800, 0, 1000, 1),
        # Rapid SYN flood
        (80, 100.0, 10.0, 5, 2, 20, 1),
    ]
    columns = [
        "Destination Port",
        "Flow Bytes/s",
        "Flow Packets/s",
        "Total Fwd Packets",
        "SYN Flag Count",
        "Flow Duration",
        "Is_Malicious",
    ]
    df = spark.createDataFrame(data, columns)

    df_tagged = apply_rule_based_anomaly_detection(
        df,
        bytes_per_sec_threshold=1_000_000.0,
        packets_per_sec_threshold=50_000.0,
        total_fwd_packets_threshold=500,
        syn_flag_threshold=1,
        min_duration_us=50,
    )

    results = df_tagged.collect()
    assert results[0]["is_potential_anomaly"] == 0
    assert results[0]["anomaly_reasons"] == ""

    # All others should be tagged with reasons
    for row in results[1:]:
        assert row["is_potential_anomaly"] == 1
        assert len(row["anomaly_reasons"]) > 0

    # Test evaluation metrics
    metrics = evaluate_detection_performance(df_tagged)
    assert metrics["true_positives"] == 4
    assert metrics["false_positives"] == 0
    assert metrics["true_negatives"] == 1
    assert metrics["false_negatives"] == 0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0
