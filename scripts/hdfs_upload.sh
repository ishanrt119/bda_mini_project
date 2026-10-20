#!/usr/bin/env bash
# ==============================================================================
# NetScope: Hadoop HDFS Deployment & Ingestion Script
# Uploads CICIDS2017 flow datasets to Apache Hadoop HDFS cluster
# ==============================================================================

set -euo pipefail

HDFS_BASE_DIR="/user/netscope/cicids2017"
LOCAL_DATA_DIR="MachineLearningCVE"

echo "=========================================================="
echo " NetScope: Hadoop HDFS Data Lake Deployment Utility"
echo "=========================================================="

# 1. Check if Hadoop CLI is installed
if ! command -v hdfs &> /dev/null; then
    echo "[!] Warning: 'hdfs' command not found in PATH."
    echo "[!] Ensure Hadoop 3.x or 2.x is installed and HADOOP_HOME is set."
    echo "[!] For local development without Hadoop, NetScope automatically"
    echo "    uses local filesystem Spark processing."
    exit 1
fi

echo "[*] Step 1: Checking HDFS cluster health..."
hdfs dfsadmin -report || {
    echo "[!] Failed to connect to HDFS NameNode."
    echo "[!] Please verify NameNode daemon is running (sbin/start-dfs.sh)."
    exit 1
}

echo "[*] Step 2: Creating HDFS destination directory at: ${HDFS_BASE_DIR}"
hdfs dfs -mkdir -p "${HDFS_BASE_DIR}"

echo "[*] Step 3: Uploading CICIDS2017 CSV files from ${LOCAL_DATA_DIR}..."
hdfs dfs -put -f "${LOCAL_DATA_DIR}"/*.csv "${HDFS_BASE_DIR}/"

echo "[*] Step 4: Verifying uploaded files on HDFS..."
hdfs dfs -ls -h "${HDFS_BASE_DIR}"

echo "=========================================================="
echo "[+] SUCCESS: Dataset uploaded to HDFS Data Lake."
echo "[+] You can now launch NetScope with HDFS URI:"
echo "    export HDFS_URI=hdfs://localhost:9000"
echo "    streamlit run app.py"
echo "=========================================================="
