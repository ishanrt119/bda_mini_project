"""
NetScope: Configuration & Constants
Centralized settings for Spark, storage paths, SOC dark theme,
anomaly thresholds, and network port mappings.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "MachineLearningCVE"
OUTPUTS_DIR = BASE_DIR / "outputs"
SUMMARIES_DIR = OUTPUTS_DIR / "summaries"
PARQUET_DIR = OUTPUTS_DIR / "parquet"
REPORTS_DIR = OUTPUTS_DIR / "reports"

# Ensure output directories exist
for path in [OUTPUTS_DIR, SUMMARIES_DIR, PARQUET_DIR, REPORTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Spark Settings
SPARK_APP_NAME = "NetScope-NetworkAnalytics"
SPARK_MASTER = os.environ.get("SPARK_MASTER", "local[*]")
SPARK_DRIVER_MEMORY = os.environ.get("SPARK_DRIVER_MEMORY", "4g")
SPARK_EXECUTOR_MEMORY = os.environ.get("SPARK_EXECUTOR_MEMORY", "4g")
SPARK_SQL_SHUFFLE_PARTITIONS = "8"

# HDFS Defaults
DEFAULT_HDFS_URI = os.environ.get("HDFS_URI", "hdfs://localhost:9000")
DEFAULT_HDFS_DATA_DIR = "/user/netscope/cicids2017"

# Well-Known Destination Ports Mapping
WELL_KNOWN_PORTS = {
    20: "FTP-Data",
    21: "FTP-Control",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    119: "NNTP",
    123: "NTP",
    135: "RPC/NetBIOS",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    993: "IMAPS",
    995: "POP3S",
    1433: "MS-SQL",
    1521: "Oracle",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    8080: "HTTP-Proxy/Alt",
    8443: "HTTPS-Alt",
}

# Label Normalization Dictionary
LABEL_CLEANING_MAP = {
    "Web Attack  Brute Force": "Web Attack - Brute Force",
    "Web Attack  XSS": "Web Attack - XSS",
    "Web Attack  Sql Injection": "Web Attack - Sql Injection",
    "Web Attack \ufffd Brute Force": "Web Attack - Brute Force",
    "Web Attack \ufffd XSS": "Web Attack - XSS",
    "Web Attack \ufffd Sql Injection": "Web Attack - Sql Injection",
}

# Anomaly Detection Defaults (Configurable in Dashboard)
DEFAULT_ANOMALY_RULES = {
    # Flow bytes/s threshold (e.g. volumetric DDoS bursts)
    "flow_bytes_per_s_quantile": 0.99,
    # Flow packets/s threshold
    "flow_packets_per_s_quantile": 0.99,
    # Total packets threshold
    "total_fwd_packets_threshold": 1000,
    # Zero or ultra-short duration with high packet count (e.g. port scan or syn flood)
    "min_duration_syn_flood_us": 10,
    "syn_flag_count_threshold": 1,
    # Rare or high-risk destination port scanning
    "sensitive_ports": [21, 22, 23, 135, 139, 445, 1433, 3389],
}

# SOC Dark Theme Aesthetics
SOC_THEME = {
    "bg_main": "#0b0f19",
    "bg_card": "#131b2e",
    "bg_card_hover": "#1c263f",
    "bg_card_border": "#1e293b",
    "text_primary": "#e2e8f0",
    "text_muted": "#94a3b8",
    "accent_cyan": "#00f2fe",
    "accent_teal": "#00c9a7",
    "accent_blue": "#38bdf8",
    "warning_amber": "#f59e0b",
    "alert_red": "#ef4444",
    "success_green": "#10b981",
    "benign_color": "#10b981",
    "malicious_color": "#ef4444",
}
