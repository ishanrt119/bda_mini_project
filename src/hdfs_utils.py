"""
NetScope: Hadoop HDFS Integration & Environment Diagnostics
Provides real HDFS connection probing, file management, Hadoop Streaming execution,
and verified status reporting.
Never falsely reports active HDFS status.
"""

import os
import shutil
import subprocess
import urllib.request
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import DEFAULT_HDFS_URI, DEFAULT_HDFS_DATA_DIR


def check_hdfs_availability(hdfs_uri: str = DEFAULT_HDFS_URI, timeout_seconds: float = 2.5) -> Dict[str, Any]:
    """
    Probe the real operating environment to verify if Hadoop HDFS is actively reachable.
    Checks:
    1. Local presence of 'hdfs' or 'hadoop' CLI binaries.
    2. Real HDFS cluster report via 'hdfs dfsadmin -report'.
    3. NameNode web UI port 9870 / 50070.
    4. SafeMode status and live DataNode counts.
    """
    has_hdfs_bin = shutil.which("hdfs") is not None
    has_hadoop_bin = shutil.which("hadoop") is not None

    if not (has_hdfs_bin or has_hadoop_bin):
        return {
            "is_connected": False,
            "state": "uninstalled",
            "mode": "Local File System (Fallback)",
            "hdfs_uri": hdfs_uri,
            "has_hdfs_binary": False,
            "has_hadoop_binary": False,
            "web_ui_accessible": False,
            "cli_responsive": False,
            "live_datanodes": 0,
            "safemode_on": False,
            "diagnostic_message": "Hadoop client binaries ('hdfs', 'hadoop') are not found in PATH.",
        }

    # Probe WebHDFS port if URI is provided
    web_accessible = False
    diagnostic_details = []

    if hdfs_uri.startswith("hdfs://"):
        host_port = hdfs_uri.replace("hdfs://", "").split("/")[0]
        host = host_port.split(":")[0] if ":" in host_port else host_port
        
        for test_port in [9870, 50070, 9000]:
            try:
                test_url = f"http://{host}:{test_port}/dfshealth.html"
                with urllib.request.urlopen(test_url, timeout=timeout_seconds) as response:
                    if response.status in (200, 302):
                        web_accessible = True
                        diagnostic_details.append(f"WebHDFS UI active on port {test_port}")
                        break
            except Exception:
                continue

    # Query HDFS DFSAdmin report for live metrics
    cli_responsive = False
    live_datanodes = 0
    safemode_on = False
    dfs_remaining_gb = 0.0

    try:
        report_res = subprocess.run(
            ["hdfs", "dfsadmin", "-report"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
        )
        if report_res.returncode == 0:
            cli_responsive = True
            output = report_res.stdout
            if "Safe mode is ON" in output:
                safemode_on = True
            if "Live datanodes" in output:
                for line in output.split("\n"):
                    if "Live datanodes" in line and "(" in line:
                        try:
                            live_datanodes = int(line.split("(")[1].split(")")[0])
                        except ValueError:
                            pass
                    if "DFS Remaining:" in line and "GB" in line:
                        try:
                            dfs_remaining_gb = float(line.split("(")[1].split("GB")[0].strip())
                        except ValueError:
                            pass
    except Exception as e:
        diagnostic_details.append(f"dfsadmin probe failed: {str(e)}")

    is_active = cli_responsive or web_accessible

    if is_active:
        state = "connected"
        reason = f"HDFS NameNode is active with {live_datanodes} Live DataNode(s) ({dfs_remaining_gb:.1f} GB DFS Remaining)."
        if safemode_on:
            reason += " (Note: SafeMode is ON; run 'hdfs dfsadmin -safemode leave' if write operations are required)."
    else:
        state = "configured_offline"
        reason = f"Hadoop binaries are present, but HDFS daemon at {hdfs_uri} is not responding."

    return {
        "is_connected": is_active,
        "state": state,
        "mode": f"Hadoop HDFS ({hdfs_uri})" if is_active else "Local File System (Fallback)",
        "hdfs_uri": hdfs_uri,
        "has_hdfs_binary": has_hdfs_bin,
        "has_hadoop_binary": has_hadoop_bin,
        "web_ui_accessible": web_accessible,
        "cli_responsive": cli_responsive,
        "live_datanodes": live_datanodes,
        "safemode_on": safemode_on,
        "dfs_remaining_gb": dfs_remaining_gb,
        "diagnostic_message": reason,
    }


def list_hdfs_files(hdfs_dir: str = "/netscope/input") -> List[Dict[str, Any]]:
    """
    List files stored in an HDFS directory.
    Returns list of file dictionaries with filename, HDFS URI, size in MB, and bytes.
    """
    files = []
    if shutil.which("hdfs") is None:
        return files

    try:
        res = subprocess.run(
            ["hdfs", "dfs", "-ls", hdfs_dir],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        if res.returncode != 0:
            return files

        for line in res.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 8 and parts[7].endswith(".csv"):
                hdfs_full_path = parts[7]
                size_bytes = int(parts[4])
                filename = hdfs_full_path.split("/")[-1]
                files.append({
                    "filename": filename,
                    "hdfs_path": f"{DEFAULT_HDFS_URI}{hdfs_full_path}",
                    "relative_hdfs_path": hdfs_full_path,
                    "size_bytes": size_bytes,
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                })
    except Exception as e:
        print(f"[NetScope HDFS Warning] Error listing HDFS files: {e}")

    return files


def upload_local_to_hdfs(
    local_dir: str = "MachineLearningCVE",
    hdfs_target_dir: str = "/netscope/input",
) -> Dict[str, Any]:
    """
    Upload CSV files from local directory to HDFS.
    Does not delete or modify local files.
    """
    if shutil.which("hdfs") is None:
        return {"success": False, "error": "'hdfs' binary not available"}

    try:
        # Create destination directory
        subprocess.run(["hdfs", "dfs", "-mkdir", "-p", hdfs_target_dir], check=True, timeout=5.0)

        # Upload CSV files
        put_cmd = f"hdfs dfs -put -f {local_dir}/*.csv {hdfs_target_dir}/"
        res = subprocess.run(put_cmd, shell=True, capture_output=True, text=True, timeout=30.0)
        if res.returncode != 0:
            return {"success": False, "error": res.stderr}

        uploaded_files = list_hdfs_files(hdfs_target_dir)
        return {
            "success": True,
            "uploaded_count": len(uploaded_files),
            "files": uploaded_files,
            "target_dir": hdfs_target_dir,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_hadoop_streaming_mr_job(
    input_file: str = "/netscope/input/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    output_dir: str = "/netscope/output/mr_attack_counts",
) -> Dict[str, Any]:
    """
    Executes an actual Hadoop Streaming MapReduce job on HDFS.
    """
    # Find hadoop streaming jar
    jar_path = None
    search_paths = [
        "/opt/homebrew/Cellar/hadoop/3.5.0/libexec/share/hadoop/tools/lib/hadoop-streaming-3.5.0.jar",
        os.path.expanduser("~/hadoop/share/hadoop/tools/lib/hadoop-streaming*.jar"),
    ]
    for p in search_paths:
        matches = list(Path(p).parent.glob(Path(p).name))
        if matches:
            jar_path = str(matches[0])
            break

    if not jar_path:
        return {"success": False, "error": "Hadoop streaming JAR not found."}

    # Clean existing output directory if it exists
    subprocess.run(["hdfs", "dfs", "-rm", "-r", "-f", output_dir], capture_output=True)

    mapper_script = str(Path(__file__).resolve().parent.parent / "scripts" / "mapreduce_demo.py")

    cmd = [
        "hadoop", "jar", jar_path,
        "-input", input_file,
        "-output", output_dir,
        "-mapper", f"python3 {mapper_script} --mapper",
        "-reducer", f"python3 {mapper_script} --reducer",
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60.0)
        if res.returncode != 0:
            return {"success": False, "error": res.stderr, "stdout": res.stdout}

        # Read output from HDFS
        cat_res = subprocess.run(["hdfs", "dfs", "-cat", f"{output_dir}/part-00000"], capture_output=True, text=True)
        results = {}
        for line in cat_res.stdout.strip().split("\n"):
            if "\t" in line:
                k, v = line.split("\t")
                results[k] = int(v)

        return {
            "success": True,
            "output_dir": output_dir,
            "results": results,
            "job_logs": res.stderr[-500:],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_hdfs_deployment_commands(
    local_dataset_dir: str = "MachineLearningCVE",
    hdfs_target_dir: str = "/netscope/input",
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
