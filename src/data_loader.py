"""
NetScope: Spark Session Management & Data Ingestion
Initializes Apache Spark safely with resource limits and provides robust
CSV / Parquet loading with schema normalization and sample bounding.
"""

import os
import sys
import time
from typing import Optional, List, Tuple, Any
from pathlib import Path

try:
    from pyspark.sql import SparkSession, DataFrame
    from pyspark.sql.functions import col
    PYSPARK_AVAILABLE = True
except ImportError:
    SparkSession = None
    DataFrame = Any
    PYSPARK_AVAILABLE = False

from config import (
    SPARK_APP_NAME,
    SPARK_MASTER,
    SPARK_DRIVER_MEMORY,
    SPARK_EXECUTOR_MEMORY,
    SPARK_SQL_SHUFFLE_PARTITIONS,
)


_spark_session: Optional[SparkSession] = None


def get_spark_session(
    app_name: str = SPARK_APP_NAME,
    master: str = SPARK_MASTER,
    driver_memory: str = SPARK_DRIVER_MEMORY,
    force_new: bool = False,
) -> Optional[SparkSession]:
    """
    Get or create an active Apache Spark session configured for local or distributed analytics.
    Returns None if PySpark is not available or initialization fails.
    """
    global _spark_session
    if not PYSPARK_AVAILABLE:
        return None

    if _spark_session is not None and not force_new:
        try:
            # Check if active
            _ = _spark_session.sparkContext.appName
            return _spark_session
        except Exception:
            _spark_session = None

    try:
        builder = (
            SparkSession.builder.appName(app_name)
            .master(master)
            .config("spark.driver.memory", driver_memory)
            .config("spark.executor.memory", SPARK_EXECUTOR_MEMORY)
            .config("spark.sql.shuffle.partitions", SPARK_SQL_SHUFFLE_PARTITIONS)
            .config("spark.ui.enabled", "false")  # Avoid port conflicts in containerized/local dev
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        )

        session = builder.getOrCreate()
        # Suppress verbose JVM log messages
        session.sparkContext.setLogLevel("WARN")
        _spark_session = session
        return _spark_session
    except Exception as e:
        print(f"[NetScope Error] Failed to initialize Spark session: {e}", file=sys.stderr)
        return None


def stop_spark_session():
    """Safely terminate the active Spark session."""
    global _spark_session
    if _spark_session is not None:
        try:
            _spark_session.stop()
        except Exception:
            pass
        _spark_session = None


def normalize_df_columns(df: DataFrame) -> DataFrame:
    """
    Normalize column names:
    - Strips whitespace
    - Resolves duplicate names such as 'Fwd Header Length'
    """
    raw_cols = df.columns
    new_cols = []
    seen = {}
    for c in raw_cols:
        base = c.strip()
        # Handle Spark 4.x appending numbers to duplicate column names
        if base.startswith("Fwd Header Length") and any(char.isdigit() for char in base):
            base = "Fwd Header Length"
        if base in seen:
            seen[base] += 1
            new_cols.append(f"{base}_{seen[base]}")
        else:
            seen[base] = 0
            new_cols.append(base)
    return df.toDF(*new_cols)


def load_network_data(
    spark: SparkSession,
    file_paths: List[str] | str,
    sample_fraction: Optional[float] = None,
    row_limit: Optional[int] = None,
) -> Tuple[DataFrame, float]:
    """
    Load network flow CSV file(s) into a PySpark DataFrame with normalized column names.
    Returns the DataFrame and the loading execution time in seconds.
    """
    if not spark:
        raise ValueError("Active SparkSession required for data loading")

    start_time = time.time()
    
    if isinstance(file_paths, str):
        paths = [file_paths]
    else:
        paths = file_paths

    if not paths:
        raise ValueError("No input file paths provided to load_network_data")

    # Read CSV with Spark
    df_raw = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .option("mode", "DROPMALFORMED")
        .csv(paths)
    )

    df_normalized = normalize_df_columns(df_raw)

    if sample_fraction is not None and 0.0 < sample_fraction < 1.0:
        df_normalized = df_normalized.sample(withReplacement=False, fraction=sample_fraction, seed=42)

    if row_limit is not None and row_limit > 0:
        df_normalized = df_normalized.limit(row_limit)

    load_duration = time.time() - start_time
    return df_normalized, load_duration
