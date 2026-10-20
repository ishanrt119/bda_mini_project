"""
NetScope: Anomaly Detection Engine
Implements explainable rule-based anomaly detection as the default,
ground-truth evaluation (Confusion Matrix, Precision, Recall, F1),
and an optional Spark MLlib Random Forest classifier on train/test splits.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd

try:
    from pyspark.sql import DataFrame
    from pyspark.sql.functions import col, when, lit, concat_ws, array, array_remove
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.classification import RandomForestClassifier
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator
except ImportError:
    DataFrame = Any

from config import DEFAULT_ANOMALY_RULES


def apply_rule_based_anomaly_detection(
    df: DataFrame,
    bytes_per_sec_threshold: float = 1_000_000.0,  # 1 MB/s
    packets_per_sec_threshold: float = 50_000.0,
    total_fwd_packets_threshold: int = 500,
    syn_flag_threshold: int = 1,
    min_duration_us: int = 50,
) -> DataFrame:
    """
    Transparent, explainable multi-factor heuristic detection.
    Flags flows exceeding volumetric, packet rate, or protocol anomaly thresholds
    and annotates each flagged record with human-readable reason codes.
    """
    reasons = []

    # Rule 1: High Volumetric Flow Rate (Potential DDoS / Exfiltration)
    if "Flow Bytes/s" in df.columns:
        rule_volumetric = when(
            col("Flow Bytes/s") > bytes_per_sec_threshold,
            lit("Volumetric Rate Spike (>1MB/s)")
        ).otherwise(lit(""))
        reasons.append(rule_volumetric)

    # Rule 2: Ultra-High Packet Rate (Potential SYN Flood or Port Sweep)
    if "Flow Packets/s" in df.columns:
        rule_packet_rate = when(
            col("Flow Packets/s") > packets_per_sec_threshold,
            lit("High Packet Velocity (>50k pkt/s)")
        ).otherwise(lit(""))
        reasons.append(rule_packet_rate)

    # Rule 3: Abnormal Forward Packets (Volumetric Flood)
    if "Total Fwd Packets" in df.columns:
        rule_fwd_pkts = when(
            col("Total Fwd Packets") > total_fwd_packets_threshold,
            lit("Heavy Forward Packet Flood")
        ).otherwise(lit(""))
        reasons.append(rule_fwd_pkts)

    # Rule 4: SYN Flood Indicator (High SYN count with microsecond duration)
    if "SYN Flag Count" in df.columns and "Flow Duration" in df.columns:
        rule_syn_flood = when(
            (col("SYN Flag Count") >= syn_flag_threshold) & (col("Flow Duration") < min_duration_us),
            lit("Rapid SYN Flood Pattern (<50µs)")
        ).otherwise(lit(""))
        reasons.append(rule_syn_flood)

    # Combine reason codes into an array and strip empty strings
    if reasons:
        reasons_array = array_remove(array(*reasons), "")
        df_tagged = df.withColumn(
            "anomaly_reasons",
            concat_ws(" | ", reasons_array)
        )
        df_tagged = df_tagged.withColumn(
            "is_potential_anomaly",
            when(col("anomaly_reasons") != "", 1).otherwise(0)
        )
    else:
        df_tagged = df.withColumn("anomaly_reasons", lit("None"))
        df_tagged = df_tagged.withColumn("is_potential_anomaly", lit(0))

    return df_tagged


def evaluate_detection_performance(df_tagged: DataFrame) -> Dict[str, Any]:
    """
    Evaluate rule-based flags against ground-truth labels.
    Computes Confusion Matrix: TP, FP, TN, FN, Precision, Recall, Specificity, F1-Score.
    """
    # Count confusion matrix quadrants using Spark aggregations
    metrics_df = (
        df_tagged.groupBy("is_potential_anomaly", "Is_Malicious")
        .count()
        .toPandas()
    )

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for _, row in metrics_df.iterrows():
        flag = int(row["is_potential_anomaly"])
        actual = int(row["Is_Malicious"])
        count = int(row["count"])

        if flag == 1 and actual == 1:
            tp += count
        elif flag == 1 and actual == 0:
            fp += count
        elif flag == 0 and actual == 0:
            tn += count
        elif flag == 0 and actual == 1:
            fn += count

    total = tp + fp + tn + fn
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    specificity = (tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    accuracy = ((tp + tn) / total) if total > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "total_evaluated": total,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": [
            [tn, fp],
            [fn, tp],
        ],
    }


def train_optional_spark_rf_model(
    df: DataFrame,
    sample_size: int = 50000,
    test_ratio: float = 0.2,
    num_trees: int = 15,
) -> Dict[str, Any]:
    """
    Optional Machine Learning pipeline:
    Trains a Spark MLlib RandomForestClassifier on clean network flow features.
    Splits data into train and test sets to prevent target leakage.
    Evaluates model strictly on the held-out test partition.
    """
    # Select available numeric flow features (strictly excluding ground truth Label / Is_Malicious)
    candidate_features = [
        "Flow Duration",
        "Total Fwd Packets",
        "Total Backward Packets",
        "Total Length of Fwd Packets",
        "Total Length of Bwd Packets",
        "Flow Bytes/s",
        "Flow Packets/s",
        "Flow IAT Mean",
        "Destination Port",
        "FIN Flag Count",
        "SYN Flag Count",
        "RST Flag Count",
        "ACK Flag Count",
    ]
    feature_cols = [c for c in candidate_features if c in df.columns]

    if len(feature_cols) < 2 or "Is_Malicious" not in df.columns:
        return {"error": "Insufficient features or missing target for ML model"}

    # Take bounded sample for responsive model training
    df_sample = df.select(*feature_cols, "Is_Malicious").limit(sample_size)

    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")
    df_prepared = assembler.transform(df_sample)

    train_df, test_df = df_prepared.randomSplit([1.0 - test_ratio, test_ratio], seed=42)

    rf = RandomForestClassifier(
        labelCol="Is_Malicious",
        featuresCol="features",
        numTrees=num_trees,
        maxDepth=6,
        seed=42,
    )

    model = rf.fit(train_df)
    predictions = model.transform(test_df)

    evaluator_acc = MulticlassClassificationEvaluator(
        labelCol="Is_Malicious", predictionCol="prediction", metricName="accuracy"
    )
    evaluator_f1 = MulticlassClassificationEvaluator(
        labelCol="Is_Malicious", predictionCol="prediction", metricName="f1"
    )
    evaluator_prec = MulticlassClassificationEvaluator(
        labelCol="Is_Malicious", predictionCol="prediction", metricName="weightedPrecision"
    )
    evaluator_rec = MulticlassClassificationEvaluator(
        labelCol="Is_Malicious", predictionCol="prediction", metricName="weightedRecall"
    )

    test_count = test_df.count()
    train_count = train_df.count()

    acc = evaluator_acc.evaluate(predictions)
    f1 = evaluator_f1.evaluate(predictions)
    prec = evaluator_prec.evaluate(predictions)
    rec = evaluator_rec.evaluate(predictions)

    # Feature importances
    importances = model.featureImportances.toArray().tolist()
    feature_importance_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": importances
    }).sort_values(by="importance", ascending=False)

    return {
        "train_samples": train_count,
        "test_samples": test_count,
        "accuracy": round(acc, 4),
        "f1_score": round(f1, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "feature_importances": feature_importance_df.to_dict(orient="records"),
        "features_used": feature_cols,
    }
