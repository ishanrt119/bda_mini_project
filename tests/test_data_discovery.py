"""
Unit tests for data discovery and schema inspection.
"""

from src.data_discovery import discover_csv_files, inspect_csv_schema, get_workspace_dataset_summary


def test_discover_csv_files():
    files = discover_csv_files()
    assert len(files) >= 1
    for f in files:
        assert f["filename"].endswith(".csv")
        assert f["size_mb"] > 0
        assert "path" in f


def test_inspect_csv_schema():
    files = discover_csv_files()
    assert len(files) >= 1
    first_file = files[0]["path"]

    schema = inspect_csv_schema(first_file)
    assert schema["raw_column_count"] == 79
    assert schema["label_column"] is not None
    assert "label" in schema["label_column"].lower()
    # Check that duplicates were detected (the duplicate 'Fwd Header Length')
    dup_names = [d["column"] for d in schema["duplicates"]]
    assert "Fwd Header Length" in dup_names
    # Check optional fields detection
    assert schema["has_dest_port"] is True


def test_workspace_summary():
    summary = get_workspace_dataset_summary()
    assert summary["has_data"] is True
    assert summary["total_files"] >= 1
    assert summary["total_size_mb"] > 0
