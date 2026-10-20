"""
Unit tests for Hadoop HDFS integration, connectivity probing, and path resolution.
"""

import pytest
from src.hdfs_utils import check_hdfs_availability, list_hdfs_files, generate_hdfs_deployment_commands
from config import DEFAULT_HDFS_URI


def test_check_hdfs_availability():
    status = check_hdfs_availability()
    assert isinstance(status, dict)
    assert "is_connected" in status
    assert "state" in status
    assert "mode" in status
    assert "hdfs_uri" in status
    assert "live_datanodes" in status
    assert status["hdfs_uri"] == DEFAULT_HDFS_URI


def test_list_hdfs_files():
    # If HDFS is running, verify it lists the uploaded files
    status = check_hdfs_availability()
    if status["is_connected"]:
        files = list_hdfs_files("/netscope/input")
        assert len(files) == 8
        filenames = [f["filename"] for f in files]
        assert "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv" in filenames
        assert "Monday-WorkingHours.pcap_ISCX.csv" in filenames
        for f in files:
            assert f["hdfs_path"].startswith("hdfs://")
            assert f["size_bytes"] > 0
            assert f["size_mb"] > 0


def test_hdfs_deployment_commands():
    cmds = generate_hdfs_deployment_commands(
        local_dataset_dir="MachineLearningCVE",
        hdfs_target_dir="/netscope/input"
    )
    assert "create_dir" in cmds
    assert "upload_dataset" in cmds
    assert "verify_files" in cmds
    assert "read_spark_uri" in cmds
    assert "/netscope/input" in cmds["create_dir"]
    assert "hdfs dfs -put" in cmds["upload_dataset"]
