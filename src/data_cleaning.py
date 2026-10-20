"""
NetScope: Data Cleaning & Quality Assurance Module
Performs schema-aware data cleansing, label normalization, infinite/NaN handling,
and computes comprehensive data quality metrics before and after cleaning.
"""

from typing import Tuple, Dict, Any
try:
    from pyspark.sql import DataFrame
    from pyspark.sql.functions import col, when, trim, regexp_replace, isnan, count, lit
except ImportError:
    DataFrame = Any


def normalize_labels(df: DataFrame, label_column_name: str = "Label") -> DataFrame:
    """
    Standardize flow labels:
    - Strips whitespace
    - Normalizes corrupted characters (UTF-8 replacement characters in web attacks)
    - Adds binary indicator `Is_Malicious` (0 for BENIGN, 1 for attacks)
    - Adds `Attack_Category` column matching standardized label
    """
    # Find exact matching label column name
    actual_col = None
    for c in df.columns:
        if c.strip().lower() == label_column_name.lower():
            actual_col = c
            break

    if not actual_col:
        raise ValueError(f"Label column '{label_column_name}' not found in DataFrame columns: {df.columns}")

    # Rename to canonical 'Label' if needed
    if actual_col != "Label":
        df = df.withColumnRenamed(actual_col, "Label")

    # Filter null or blank labels
    df_clean = df.filter(col("Label").isNotNull() & (trim(col("Label")) != ""))

    # Trim whitespace
    df_clean = df_clean.withColumn("Label", trim(col("Label")))

    # Replace unicode replacement characters (e.g. 'Web Attack \ufffd XSS' -> 'Web Attack - XSS')
    df_clean = df_clean.withColumn(
        "Label",
        regexp_replace(col("Label"), r"[\ufffd\xef\xbf\xbd]+", " - ")
    )
    # Collapse possible double dashes or spaces
    df_clean = df_clean.withColumn(
        "Label",
        regexp_replace(col("Label"), r"\s*-\s*", " - ")
    )
    df_clean = df_clean.withColumn(
        "Label",
        regexp_replace(col("Label"), r"\s+", " ")
    )

    # Standardize specific known categories
    df_clean = df_clean.withColumn(
        "Label",
        when(col("Label").like("%Web Attack%Brute Force%"), "Web Attack - Brute Force")
        .when(col("Label").like("%Web Attack%XSS%"), "Web Attack - XSS")
        .when(col("Label").like("%Web Attack%Sql Injection%"), "Web Attack - Sql Injection")
        .otherwise(col("Label"))
    )

    # Add binary classification column (0: BENIGN, 1: Malicious)
    df_clean = df_clean.withColumn(
        "Is_Malicious",
        when(col("Label") == "BENIGN", 0).otherwise(1)
    )

    return df_clean


def clean_numeric_features(df: DataFrame) -> DataFrame:
    """
    Sanitize network flow numeric features:
    - Replaces IEEE 754 Infinity, -Infinity, NaN, and corrupt negative values in rate columns
    - Ensures non-negative packet counts and durations
    """
    numeric_cols = [
        "Flow Bytes/s",
        "Flow Packets/s",
        "Flow Duration",
        "Total Fwd Packets",
        "Total Backward Packets",
        "Total Length of Fwd Packets",
        "Total Length of Bwd Packets",
    ]

    for c in numeric_cols:
        if c in df.columns:
            # Check for float inf, nan, or negative
            df = df.withColumn(
                c,
                when(
                    col(c).isNull()
                    | isnan(col(c))
                    | (col(c) == float("inf"))
                    | (col(c) == float("-inf"))
                    | (col(c) < 0),
                    0.0,
                ).otherwise(col(c).cast("double")),
            )

    return df


def calculate_data_quality_metrics(df_raw: DataFrame, df_clean: DataFrame) -> Dict[str, Any]:
    """
    Compute structured data quality and hygiene metrics:
    - Initial row count
    - Cleaned row count
    - Invalid numeric values detected
    - Null labels filtered
    - Retention rate
    """
    raw_count = df_raw.count()
    clean_count = df_clean.count()
    dropped_count = raw_count - clean_count

    # Check for invalid values in key rate columns in the raw dataset
    rate_col = "Flow Bytes/s" if "Flow Bytes/s" in df_raw.columns else None
    invalid_rates = 0
    if rate_col:
        invalid_rates = df_raw.filter(
            col(rate_col).isNull()
            | isnan(col(rate_col))
            | (col(rate_col) == float("inf"))
            | (col(rate_col) == float("-inf"))
            | (col(rate_col) < 0)
        ).count()

    retention_pct = (clean_count / raw_count * 100.0) if raw_count > 0 else 0.0

    return {
        "raw_record_count": raw_count,
        "clean_record_count": clean_count,
        "dropped_record_count": dropped_count,
        "invalid_rate_values_count": invalid_rates,
        "retention_percentage": round(retention_pct, 4),
        "total_columns": len(df_clean.columns),
    }


def clean_network_dataframe(df_raw: DataFrame) -> Tuple[DataFrame, Dict[str, Any]]:
    """
    End-to-end cleaning workflow:
    1. Label normalization and binary flag generation
    2. Numeric sanitization (Infinity, NaN, negative rates)
    3. Quality metrics computation
    """
    df_labeled = normalize_labels(df_raw)
    df_sanitized = clean_numeric_features(df_labeled)
    quality_metrics = calculate_data_quality_metrics(df_raw, df_sanitized)

    return df_sanitized, quality_metrics
