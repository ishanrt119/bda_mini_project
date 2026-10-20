"""
Unit tests for NetScope analytics aggregations and KPIs.
"""

import pytest
from pyspark.sql import SparkSession
from src.analytics import (
    compute_overview_kpis,
    compute_attack_distribution,
    compute_port_distribution,
    compute_traffic_volume_stats,
)


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder.master("local[1]")
        .appName("test_analytics")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def test_compute_overview_kpis(spark):
    data = [
        ("BENIGN", 0),
        ("BENIGN", 0),
        ("DDoS", 1),
        ("PortScan", 1),
        ("BENIGN", 0),
    ]
    df = spark.createDataFrame(data, ["Label", "Is_Malicious"])
    kpis = compute_overview_kpis(df)

    assert kpis["total_flows"] == 5
    assert kpis["benign_flows"] == 3
    assert kpis["malicious_flows"] == 2
    assert kpis["benign_percentage"] == 60.0
    assert kpis["malicious_percentage"] == 40.0
    assert kpis["distinct_attack_categories"] == 2


def test_compute_attack_distribution(spark):
    data = [
        ("BENIGN", 0),
        ("BENIGN", 0),
        ("DDoS", 1),
        ("DDoS", 1),
        ("PortScan", 1),
    ]
    df = spark.createDataFrame(data, ["Label", "Is_Malicious"])
    pdf = compute_attack_distribution(df)

    assert len(pdf) == 3
    # Top should be BENIGN or DDoS with count 2
    top_label = pdf.iloc[0]["Label"]
    assert top_label in ["BENIGN", "DDoS"]
    assert pdf.iloc[0]["count"] == 2


def test_compute_port_distribution(spark):
    data = [
        (80, "BENIGN"),
        (80, "BENIGN"),
        (443, "BENIGN"),
        (22, "SSH-Patator"),
        (9999, "DDoS"),
    ]
    df = spark.createDataFrame(data, ["Destination Port", "Label"])
    ports_df = compute_port_distribution(df, top_n=5)

    assert len(ports_df) == 4
    # Port 80 should be top and have service HTTP
    p80 = ports_df[ports_df["port"] == 80].iloc[0]
    assert p80["count"] == 2
    assert p80["service"] == "HTTP"
