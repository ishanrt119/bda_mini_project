#!/usr/bin/env python3
"""
NetScope: MapReduce Streaming Demonstration
Demonstrates classic Big Data MapReduce paradigm for network traffic attack classification.

Can be run:
1. In standard pipeline simulation:
   head -n 50000 MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv | python3 scripts/mapreduce_demo.py

2. In Hadoop Streaming cluster:
   hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
     -input /user/netscope/cicids2017/*.csv \
     -output /user/netscope/output_mr_labels \
     -mapper "python3 scripts/mapreduce_demo.py --mapper" \
     -reducer "python3 scripts/mapreduce_demo.py --reducer"
"""

import sys
import csv
import argparse


def mapper():
    """
    Map Phase:
    Reads CSV flow lines from sys.stdin, identifies the label column,
    normalizes the label string, and emits: <attack_label>\t1
    """
    header = None
    label_idx = -1

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]

        # Discover header line dynamically
        if header is None:
            header = [p.lower() for p in parts]
            for idx, col in enumerate(header):
                if "label" in col:
                    label_idx = idx
                    break
            # If line was header, skip emitting
            if label_idx != -1:
                continue
            else:
                # Default to last column if header not recognized
                label_idx = len(parts) - 1

        if len(parts) > label_idx:
            raw_label = parts[label_idx]
            # Normalize label
            label = raw_label.replace("\ufffd", "-").replace("\xef\xbf\xbd", "-").strip()
            if not label:
                label = "UNKNOWN"
            # Emit key-value pair
            print(f"{label}\t1")


def reducer():
    """
    Reduce Phase:
    Receives sorted <attack_label>\t<count> pairs from Shuffle & Sort phase,
    aggregates counts for each attack label, and emits final totals.
    """
    current_key = None
    current_count = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) != 2:
            continue

        key, val = parts[0], parts[1]
        try:
            val = int(val)
        except ValueError:
            continue

        if current_key == key:
            current_count += val
        else:
            if current_key is not None:
                print(f"{current_key}\t{current_count}")
            current_key = key
            current_count = val

    if current_key is not None:
        print(f"{current_key}\t{current_count}")


def run_standalone_simulation():
    """
    Simulates the entire Map -> Shuffle/Sort -> Reduce pipeline locally in memory.
    """
    print("--- [NetScope MapReduce Local Pipeline Simulation] ---")
    print("Reading from standard input...")

    from collections import defaultdict
    shuffle_buffer = defaultdict(int)
    header = None
    label_idx = -1
    total_records = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if header is None:
            header = [p.lower() for p in parts]
            for idx, col in enumerate(header):
                if "label" in col:
                    label_idx = idx
                    break
            if label_idx != -1:
                continue
            else:
                label_idx = len(parts) - 1

        if len(parts) > label_idx:
            total_records += 1
            raw_label = parts[label_idx]
            label = raw_label.replace("\ufffd", "-").replace("\xef\xbf\xbd", "-").strip()
            # Map & Shuffle
            shuffle_buffer[label] += 1

    print(f"\n[Map Phase Completed]: Processed {total_records:,} flows")
    print("[Shuffle & Sort]: Grouped by attack key")
    print("\n--- [Reduce Output: Aggregated Attack Flow Counts] ---")
    for attack, count in sorted(shuffle_buffer.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_records * 100.0) if total_records > 0 else 0.0
        print(f"{attack:35s}: {count:10,d} ({pct:6.2f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hadoop MapReduce Demo for Traffic Analysis")
    parser.add_argument("--mapper", action="store_true", help="Run mapper mode")
    parser.add_argument("--reducer", action="store_true", help="Run reducer mode")
    args = parser.parse_args()

    if args.mapper:
        mapper()
    elif args.reducer:
        reducer()
    else:
        run_standalone_simulation()
