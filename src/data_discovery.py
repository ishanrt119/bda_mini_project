"""
NetScope: Data Discovery & Schema Inspection Module
Dynamically locates dataset files, inspects headers, detects quirks (whitespace, duplicate
column names, encoding issues), and checks for optional network fields.
"""

import os
import glob
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any


def discover_csv_files(search_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for network flow CSV files in the workspace or provided directory.
    Supports nested directories and handles variations in naming.
    """
    if search_dir is None:
        # Check current working directory, MachineLearningCVE, and subfolders
        candidates = [
            Path("MachineLearningCVE"),
            Path("./MachineLearningCVE"),
            Path("../MachineLearningCVE"),
            Path("."),
        ]
        chosen_dir = None
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                csvs = list(candidate.glob("*.csv"))
                if csvs:
                    chosen_dir = candidate
                    break
        search_path = chosen_dir if chosen_dir else Path(".")
    else:
        search_path = Path(search_dir)

    discovered = []
    if not search_path.exists():
        return discovered

    csv_paths = sorted(search_path.glob("**/*.csv"))
    for p in csv_paths:
        try:
            stat = p.stat()
            size_mb = stat.st_size / (1024 * 1024)
            discovered.append({
                "path": str(p.resolve()),
                "filename": p.name,
                "relative_path": str(p),
                "size_mb": round(size_mb, 2),
                "size_bytes": stat.st_size,
            })
        except OSError:
            continue

    return discovered


def inspect_csv_schema(file_path: str) -> Dict[str, Any]:
    """
    Inspect a single CSV file:
    - Extracts raw headers and stripped headers
    - Identifies duplicate column names
    - Detects the label column
    - Checks for protocol and timestamp columns
    - Reads sample row to test encoding
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return {"error": "Empty CSV file", "columns": []}

        sample_rows = []
        for _ in range(5):
            try:
                row = next(reader)
                sample_rows.append(row)
            except StopIteration:
                break

    # Analyze header properties
    has_leading_whitespace = any(c.startswith(" ") for c in header)
    has_trailing_whitespace = any(c.endswith(" ") for c in header)
    
    stripped_headers = [c.strip() for c in header]
    
    # Detect duplicate headers
    seen_counts: Dict[str, int] = {}
    duplicates = []
    for idx, col in enumerate(stripped_headers):
        if col in seen_counts:
            seen_counts[col] += 1
            duplicates.append({"column": col, "index": idx, "occurrence": seen_counts[col]})
        else:
            seen_counts[col] = 1

    # Detect label column
    label_candidates = [
        (idx, col.strip()) for idx, col in enumerate(header) if "label" in col.lower()
    ]
    label_col = label_candidates[0][1] if label_candidates else None
    label_idx = label_candidates[0][0] if label_candidates else None

    # Detect optional fields
    has_timestamp = any("time" in c.lower() or "date" in c.lower() for c in stripped_headers)
    has_protocol = any(c.lower() in ["protocol", "proto"] for c in stripped_headers)
    has_source_ip = any("src_ip" in c.lower() or "source ip" in c.lower() for c in stripped_headers)
    has_dest_port = any("destination port" in c.lower() or "dst port" in c.lower() for c in stripped_headers)

    return {
        "file_name": path.name,
        "raw_column_count": len(header),
        "raw_headers": header,
        "clean_headers": stripped_headers,
        "has_leading_whitespace": has_leading_whitespace,
        "has_trailing_whitespace": has_trailing_whitespace,
        "duplicates": duplicates,
        "label_column": label_col,
        "label_index": label_idx,
        "has_timestamp": has_timestamp,
        "has_protocol": has_protocol,
        "has_source_ip": has_source_ip,
        "has_dest_port": has_dest_port,
        "sample_preview_count": len(sample_rows),
    }


def get_workspace_dataset_summary(search_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive discovery summary for all CSV files in the dataset folder.
    """
    files = discover_csv_files(search_dir)
    total_size_mb = sum(f["size_mb"] for f in files)
    
    file_schemas = []
    consistent_columns = True
    reference_columns = None

    for f in files:
        schema_info = inspect_csv_schema(f["path"])
        file_schemas.append({
            "filename": f["filename"],
            "path": f["path"],
            "size_mb": f["size_mb"],
            "columns_count": schema_info.get("raw_column_count", 0),
            "label_col": schema_info.get("label_column"),
            "duplicates": [d["column"] for d in schema_info.get("duplicates", [])],
        })
        if reference_columns is None:
            reference_columns = schema_info.get("clean_headers")
        elif reference_columns != schema_info.get("clean_headers"):
            consistent_columns = False

    return {
        "total_files": len(files),
        "total_size_mb": round(total_size_mb, 2),
        "files": file_schemas,
        "consistent_columns": consistent_columns,
        "has_data": len(files) > 0,
    }
