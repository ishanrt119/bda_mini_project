"""
Unit tests for NetScope data cleaning and schema normalization module.
Uses small synthetic Spark DataFrames to test isolated transformation logic.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from src.data_cleaning import normalize_labels, clean_numeric_features, calculate_data_quality_metrics


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder.master("local[1]")
        .appName("test_data_cleaning")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def test_normalize_labels_cleaning(spark):
    data = [
        (80, "  BENIGN  "),
        (443, "Web Attack \ufffd XSS"),
        (22, "Web Attack \xef\xbf\xbd Brute Force"),
        (21, "DoS Hulk"),
        (8080, "BENIGN"),
    ]
    df = spark.createDataFrame(data, ["Destination Port", "Label"])
    df_clean = normalize_labels(df)

    rows = {r["Label"]: r["Is_Malicious"] for r in df_clean.collect()}

    assert "BENIGN" in rows
    assert rows["BENIGN"] == 0
    assert "Web Attack - XSS" in rows
    assert rows["Web Attack - XSS"] == 1
    assert "Web Attack - Brute Force" in rows
    assert rows["Web Attack - Brute Force"] == 1
    assert "DoS Hulk" in rows
    assert rows["DoS Hulk"] == 1


def test_clean_numeric_features(spark):
    data = [
        (100.0, float("inf"), -5.0, "BENIGN"),
        (200.0, float("nan"), 10.0, "DDoS"),
        (float("-inf"), 50.0, 20.0, "BENIGN"),
    ]
    df = spark.createDataFrame(
        data,
        ["Flow Bytes/s", "Flow Packets/s", "Flow Duration", "Label"]
    )
    df_clean = clean_numeric_features(df)
    results = df_clean.collect()

    for r in results:
        # No infinity or NaN or negative should remain in Flow Bytes/s or Flow Packets/s or Flow Duration
        assert r["Flow Bytes/s"] >= 0.0
        assert r["Flow Packets/s"] >= 0.0
        assert r["Flow Duration"] >= 0.0


def test_quality_metrics(spark):
    raw_data = [
        (80, 100.0, "BENIGN"),
        (443, float("inf"), "DDoS"),
        (22, 50.0, None),  # Missing label
    ]
    df_raw = spark.createDataFrame(raw_data, ["Destination Port", "Flow Bytes/s", "Label"])
    df_labeled = normalize_labels(df_raw)
    df_sanitized = clean_numeric_features(df_labeled)

    metrics = calculate_data_quality_metrics(df_raw, df_sanitized)

    assert metrics["raw_record_count"] == 3
    assert metrics["clean_record_count"] == 2
    assert metrics["dropped_record_count"] == 1
    assert metrics["invalid_rate_values_count"] == 1
    assert metrics["retention_percentage"] > 60.0
