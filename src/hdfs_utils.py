"""
NetScope: Hadoop HDFS Integration & Environment Diagnostics
Provides real HDFS connection probing, command generation for Hadoop clusters,
and seamless fallback to local filesystem storage.
Never falsely reports active HDFS status.
"""

import shutil
import subprocess
import urllib.request
from typing import Dict, Any, Optional
from config import DEFAULT_HDFS_URI, DEFAULT_HDFS_DATA_DIR


def check_hdfs_availability(hdfs_uri: str = DEFAULT_HDFS_URI, timeout_seconds: float = 2.0) -> Dict[str, Any]:
    """
    Probe the real operating environment to verify if Hadoop HDFS is actively reachable.
    Checks:
    1. Local presence of 'hdfs' or 'hadoop' CLI binaries.
    2. Optional HTTP WebHDFS connectivity on port 9870 (Hadoop 3.x) or 50070 (Hadoop 2.x).
    3. HDFS filesystem test via 'hdfs dfs -test -e /'.
    """
    has_hdfs_bin = shutil.which("hdfs") is not None
    has_hadoop_bin = shutil.which("hadoop") is not None

    # Probe WebHDFS port if URI is provided
    web_accessible = False
    diagnostic_details = []

    if hdfs_uri.startswith("hdfs://"):
        host_port = hdfs_uri.replace("hdfs://", "").split("/")[0]
        host = host_port.split(":")[0] if ":" in host_port else host_port
        
        # Test common WebHDFS ports
        for test_port in [9870, 50070, 9000]:
            try:
                test_url = f"http://{host}:{test_port}/dfshealth.html"
                with urllib.request.urlopen(test_url, timeout=timeout_seconds) as response:
                    if response.status in (200, 302):
                        web_accessible = True
                        diagnostic_details.append(f"WebHDFS UI responded on port {test_port}")
                        break
            except Exception:
                continue

    # Try CLI check if binary is installed
    cli_responsive = False
    if has_hdfs_bin:
        try:
            res = subprocess.run(
                ["hdfs", "dfs", "-test", "-d", "/"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
            )
            cli_responsive = (res.returncode == 0)
            if cli_responsive:
                diagnostic_details.append("HDFS CLI connected and verified root directory.")
        except Exception as e:
            diagnostic_details.append(f"HDFS CLI probe timed out or failed: {str(e)}")

    is_active = web_accessible or cli_responsive

    if not is_active:
        if not (has_hdfs_bin or has_hadoop_bin):
            reason = "Hadoop / HDFS client binaries ('hdfs', 'hadoop') are not installed in PATH."
        else:
            reason = f"Hadoop binaries found, but HDFS daemon at {hdfs_uri} is offline or unreachable."
    else:
        reason = "HDFS NameNode is active and accepting connections."

    return {
        "is_connected": is_active,
        "mode": "HDFS (Distributed File System)" if is_active else "Local File System (Fallback)",
        "hdfs_uri": hdfs_uri,
        "has_hdfs_binary": has_hdfs_bin,
        "has_hadoop_binary": has_hadoop_bin,
        "web_ui_accessible": web_accessible,
        "cli_responsive": cli_responsive,
        "diagnostic_message": reason,
    }


def generate_hdfs_deployment_commands(
    local_dataset_dir: str = "MachineLearningCVE",
    hdfs_target_dir: str = DEFAULT_HDFS_DATA_DIR,
) -> Dict[str, str]:
    """
    Generate standard production Hadoop CLI commands for examiners and deployment.
    """
    return {
        "create_dir": f"hdfs dfs -mkdir -p {hdfs_target_dir}",
        "upload_dataset": f"hdfs dfs -put {local_dataset_dir}/*.csv {hdfs_target_dir}/",
        "verify_files": f"hdfs dfs -ls -h {hdfs_target_dir}",
        "read_spark_uri": f"spark.read.csv('{DEFAULT_HDFS_URI}{hdfs_target_dir}/*.csv')",
        "check_health": "hdfs dfsadmin -report",
    }
