# 🛡️ NetScope: Big Data Analytics Lab Live Demonstration Playbook
### End-to-End Practical Examination Guide & Spoken Script
**System:** NetScope (Network Traffic Intelligence & Threat Center)  
**Dataset:** Canadian Institute for Cybersecurity CICIDS2017 Benchmark (2.83M Flows, 843.7 MB)  
**Core Technologies:** Apache Spark 4.2.0, Apache Hadoop HDFS 3.5.0, Hadoop Streaming MapReduce, Streamlit, Plotly  
**Operating Environment:** macOS / Linux (Local Pseudo-Distributed Data Lake)  
**Document Version:** 1.2 (Exam Ready)  

---

## 📋 Table of Contents
1. [Overview & Quick Reference](#overview--quick-reference)
2. [Section A: Quick Start Before the Demo (Pre-Flight Setup)](#section-a-quick-start-before-the-demo-pre-flight-setup)
3. [Section B: Complete Live Demonstration Script](#section-b-complete-live-demonstration-script)
   - [5-Minute Emergency Rapid Sequence](#5-minute-emergency-rapid-sequence)
   - [Full 10–12 Minute Walkthrough (Steps 1–12)](#full-1012-minute-walkthrough-steps-112)
4. [Section C: Parameter Adjustment Cheat Sheet](#section-c-parameter-adjustment-cheat-sheet)
5. [Section D: Copy-Paste Command Reference](#section-d-copy-paste-command-reference)
6. [Section E: Expected Output & Result Validation Reference](#section-e-expected-output--result-validation-reference)
7. [Section F: Backup Plan & Troubleshooting Guide](#section-f-backup-plan--troubleshooting-guide)
8. [Section G: Comprehensive Exam Viva Q&A (24 Questions)](#section-g-comprehensive-exam-viva-qa-24-questions)
9. [Section H: Printable Demo Checklists & Screenshot Guide](#section-h-printable-demo-checklists--screenshot-guide)

---

## 🎯 Overview & Quick Reference

NetScope is an enterprise-grade Big Data cybersecurity analytics platform designed for network forensic auditing, threat categorization, and explainable anomaly detection. 

### Key System Specifications Grounded in the Codebase:
- **Hadoop Home & Config:** `/opt/homebrew/Cellar/hadoop/3.5.0/libexec` (`etc/hadoop`)
- **HDFS NameNode URI:** `hdfs://localhost:9000`
- **HDFS Web UI:** `http://localhost:9870`
- **HDFS Data Lake Directories:** `/netscope/input` (Dataset CSVs), `/netscope/output` (Parquet and MapReduce results)
- **Local Dataset Directory:** `MachineLearningCVE/` (8 CSV files, 843.66 MB total)
- **Primary Analytics Engine:** Apache Spark 4.2.0 (PySpark) initialized in `local[*]` multi-threaded mode
- **Web Dashboard URL:** `http://localhost:8501` (Streamlit 1.59+)
- **MapReduce Streaming Utility:** `scripts/mapreduce_demo.py` via `hadoop-streaming-3.5.0.jar`

---

## 🚀 Section A: Quick Start Before the Demo (Pre-Flight Setup)

Follow this exact 5-step checklist 15 minutes before the evaluator arrives to ensure all background daemons, storage endpoints, and web servers are operational.

### Step A.1: Open Terminal & Navigate to Project Root
Open macOS Terminal (or iTerm2) and navigate to the project directory:
```bash
cd /Users/ishan/bda-mp
pwd
```
*Expected Output:* `/Users/ishan/bda-mp`

### Step A.2: Verify Python & Java Runtimes
Check that Python 3.10+ and Java 17 are active:
```bash
python3 --version
java -version
```
*Expected Output:*
- `Python 3.10.x` or `Python 3.13.x`
- `openjdk version "17.0.x"` (Required by Apache Spark and Hadoop)

### Step A.3: Verify Hadoop HDFS Cluster Daemons
Run `jps` to check if NameNode, DataNode, and SecondaryNameNode are running:
```bash
jps
```
*Verification Checklist:*
- [x] `NameNode`
- [x] `DataNode`
- [x] `SecondaryNameNode`

> **If daemons are NOT running**, start them immediately:
> ```bash
> hdfs --daemon start namenode && hdfs --daemon start datanode && hdfs --daemon start secondarynamenode
> ```

Check HDFS capacity and ensure SafeMode is turned OFF:
```bash
hdfs dfsadmin -report | head -n 12
hdfs dfsadmin -safemode leave
```
*Expected Output:* `Safe mode is OFF`, `Live datanodes (1): Name: 127.0.0.1:9866`, `570+ GB remaining`.

### Step A.4: Verify Dataset on HDFS Data Lake
Verify that all 8 CSV files are present in `/netscope/input/`:
```bash
hdfs dfs -ls -h /netscope/input
```
*Expected Output:* 8 CSV files totaling 843.7 MB (`Friday-DDos`, `Wednesday-workingHours`, etc.).

### Step A.5: Launch the NetScope Streamlit Dashboard
Check if Streamlit is already running on port 8501:
```bash
curl -s http://localhost:8501/_stcore/health
```
- If output is `ok`, the dashboard is already live!
- If not running, start it in the terminal:
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in Safari or Chrome.

---

## 🎬 Section B: Complete Live Demonstration Script

### ⏱️ 5-Minute Emergency Rapid Sequence
*Use this rapid sequence if the evaluator has limited time (e.g. 5 minutes per student).*

1. **[00:00 - 00:45] Intro & Architecture:** Open browser at `http://localhost:8501`. State: *"NetScope is a Big Data network traffic intelligence system processing 2.83M flows from the CICIDS2017 benchmark using Apache Spark and Hadoop HDFS."*
2. **[00:45 - 01:30] Storage Mode Verification:** In the sidebar, point to **Storage Filesystem Mode**. Show `Hadoop HDFS (Data Lake)` selected with `🟢 HDFS Data Lake Connected` on `hdfs://localhost:9000/netscope/input/`.
3. **[01:30 - 02:45] Spark Ingestion & Analytics:** Select `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv`, choose `50,000 Flows`, and click **`⚡ Run Spark`**. Watch the progress spinner complete in ~2 seconds. Point to the **4 KPI cards** (50,000 Flows, 23,865 Malicious DDoS, 26,135 Benign) and the Donut split.
4. **[02:45 - 03:45] Anomaly Detection & Ground Truth:** Click the **`🔍 Anomaly Explorer`** tab. Point out the Confusion Matrix heatmap, explain the heuristic rules (Volumetric burst > 1MB/s, SYN flood < 50µs), and highlight that ground truth labels are strictly isolated from detection rules to avoid data leakage.
5. **[03:45 - 04:30] Live Hadoop Streaming MapReduce:** Click **`⚡ Big Data & HDFS Architecture`** tab. Click **`🚀 Execute Hadoop MapReduce on HDFS`**. Show the real Hadoop streaming job reading from HDFS and aggregating 225,745 rows into exact DDoS and Benign totals.
6. **[04:30 - 05:00] Conclusion:** Conclude by highlighting the Snappy Parquet columnar export written back to `hdfs://localhost:9000/netscope/output/cleaned_parquet`.

---

### ⏱️ Full 10–12 Minute Walkthrough (Steps 1–12)

#### Demonstration 1: Project Introduction & Problem Statement [00:00 - 01:00]
- **Screen:** Browser at `http://localhost:8501` (Dashboard Header).
- **Spoken Script:**
  > *"Good morning, Professor. Today I am presenting NetScope, an end-to-end Big Data analytics and threat intelligence platform designed to process high-velocity network flow traffic and detect cyber anomalies at scale.*
  > *Modern enterprise networks generate hundreds of gigabytes of network flows daily. Monolithic frameworks like Pandas fail because they load all data into a single process's memory, leading to out-of-memory crashes. NetScope solves this by utilizing Apache Hadoop HDFS for distributed fault-tolerant storage and Apache Spark for in-memory parallel transformations and aggregations."*
- **Big Data Concept:** Scalability bottleneck of single-node architectures vs. distributed shared-nothing architectures.

#### Demonstration 2: Dashboard Overview & SOC Executive KPIs [01:00 - 02:00]
- **Screen:** Tab `📊 Executive Overview`.
- **Action:** Point to the top status strip and the 4 metric cards.
- **Points to Highlight:**
  1. **Top Status Strip:** Shows real live statuses: `Data Pipeline: 🟢 Loaded (50,000 flows)`, `Analytics Engine: ⚡ Apache Spark 4.2.0`, `Storage System: 💾 HDFS Active (1 DN)`.
  2. **Total Valid Flows Card:** Shows total analyzed records.
  3. **Malicious Threat Flows Card:** Shows exact count and percentage of attack traffic (e.g. 23,865 flows, 47.73%).
  4. **Benign Traffic Flows Card:** Verified normal baseline enterprise traffic (e.g. 26,135 flows, 52.27%).
  5. **Distinct Threat Categories Card:** Identifies distinct attack vectors discovered in the slice.
  6. **Charts:** Donut chart showing Benign vs. Threat ratio, and horizontal bar chart illustrating attack frequency.
- **Spoken Script:**
  > *"The NetScope dashboard is modeled as a modern Security Operations Center (SOC) intelligence product. Here on the Executive Overview, you see aggregated flow distributions computed directly by Apache Spark. Every single metric and chart is derived dynamically from the loaded dataset—no numbers are hardcoded or simulated."*

#### Demonstration 3: Dataset Discovery & Schema Inspection [02:00 - 03:00]
- **Screen:** Sidebar `📁 Dataset Discovery` and Tab `🧹 Data Hygiene & Quality`.
- **Action:** Show the file list in the sidebar and click on the Data Hygiene tab.
- **Points to Highlight:**
  1. The dataset contains **8 CSV files** totaling **843.66 MB** and **2,830,743 valid flow records**.
  2. Each record has **79 flow features** extracted using `CICFlowMeter`.
  3. Explain the **Schema Cleaning Table** in the Data Hygiene tab:
     - **Whitespace Removal:** All 79 column names in the raw CSVs had leading spaces (e.g., `' Destination Port'`, `' Flow Duration'`). NetScope's `data_loader.py` strips whitespace automatically.
     - **Duplicate Column Disambiguation:** The raw dataset has two columns named `' Fwd Header Length'` (indices 34 and 55). Spark would fail with ambiguous reference errors; NetScope disambiguates the second to `Fwd Header Length_1`.
     - **Unicode Normalization:** Raw web attack labels contained corrupted replacement characters (`Web Attack \ufffd XSS`). NetScope normalizes them into clean strings.
     - **IEEE 754 Infinity / NaN Sanitization:** Microsecond flows have division by zero in `Flow Bytes/s`, producing `Infinity` and `NaN`. NetScope detects these using Spark SQL expressions and imputes them safely.
- **Spoken Script:**
  > *"In Big Data engineering, real datasets are rarely clean. In the CICIDS2017 dataset, we uncovered three critical schema quirks: duplicate column names for forward header length, corrupted unicode encoding in attack labels, and IEEE 754 floating-point infinities caused by zero-duration flows. In Tab 5, NetScope proves that 100% of these anomalies were sanitized during the Spark loading stage."*

#### Demonstration 4: Genuine Hadoop HDFS Storage Verification [03:00 - 04:00]
- **Screen:** Terminal window (run side-by-side with browser).
- **Action:** Run the HDFS verification commands in Terminal:
  ```bash
  hdfs dfsadmin -report | head -n 12
  hdfs dfs -ls -h /netscope/input
  ```
- **Points to Highlight:**
  1. NameNode is listening on `hdfs://localhost:9000`.
  2. 1 Live DataNode is active (`127.0.0.1:9866`).
  3. The directory `/netscope/input` contains the 8 CSV files.
  4. File sizes match the local source files byte-for-byte (e.g. `Friday-DDos.csv` is exactly 77,123,859 bytes on HDFS).
- **Spoken Script:**
  > *"NetScope does not merely simulate HDFS. Here in the terminal, `hdfs dfsadmin -report` confirms that our NameNode and DataNode are live and accepting RPC connections on port 9000. When we list `/netscope/input`, all 8 CSV files are present in the HDFS distributed file system, replicated across data blocks."*

#### Demonstration 5: Switching Storage Mode in Dashboard [04:00 - 04:45]
- **Screen:** Browser Sidebar.
- **Action:** Point to the **Select Storage Layer** radio control in the sidebar.
- **Controls & Behavior:**
  - Control Label: `Select Storage Layer`
  - Options: `Hadoop HDFS (Data Lake)` vs `Local POSIX Storage`
  - Toggle between them:
    * When `Hadoop HDFS` is selected: the UI queries `hdfs dfs -ls /netscope/input` and displays `🟢 HDFS Data Lake Connected` with HDFS URI `hdfs://localhost:9000/netscope/input/`.
    * When `Local POSIX Storage` is selected: the UI switches to `📁 Local POSIX Storage` reading from `MachineLearningCVE/`.
  - Point out: Changing the radio button updates the target URI and file list; clicking **`⚡ Run Spark`** triggers the actual distributed execution.
- **Spoken Script:**
  > *"Notice here in the sidebar, NetScope provides a dynamic storage switch. We can direct Apache Spark to ingest data either from the local POSIX filesystem or from our Hadoop HDFS Data Lake. The system actively probes NameNode health and only permits HDFS mode when the cluster is genuinely reachable."*

#### Demonstration 6: Apache Spark Analytics Execution [04:45 - 06:00]
- **Screen:** Browser Sidebar & Tab `⚡ Big Data & HDFS Architecture`.
- **Action:**
  1. In Sidebar, select `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv`.
  2. Set `Flow Sample Bounding` to `50,000 Flows (Standard Demo)`.
  3. Click the primary button: **`⚡ Run Spark`**.
  4. Wait ~2 seconds for the execution to finish.
  5. Switch to Tab `⚡ Big Data & HDFS Architecture`.
- **Points to Highlight:**
  1. **Spark Session:** `ACTIVE 4.2.0 (local[*])`.
  2. **Processing Duration:** e.g. `0.024 s` for in-memory aggregation pass.
  3. **Throughput:** Over `2,100,000 flows/second`.
  4. **Spark Transformation vs. Action Concept:** Loading the CSV and cleaning columns are lazy transformations (`read.csv()`, `withColumn()`, `filter()`). No execution occurs until Spark encounters an action like `.count()` or `.parquet()`, which builds an execution DAG (Directed Acyclic Graph) and executes tasks in parallel across worker partitions.
- **Spoken Script:**
  > *"When I click 'Run Spark', PySpark coordinates with the JVM. It reads the CSV from HDFS, constructs a lazy execution plan, and optimizes the DAG using the Catalyst Optimizer. When the `.count()` and aggregation actions are called, Spark executes parallel partition tasks across all available CPU cores, achieving over 2 million flows per second."*

#### Demonstration 7: Interactive Traffic Analysis [06:00 - 07:15]
- **Screen:** Tab `🌐 Traffic Analysis`.
- **Action:** Point to the Top Destination Ports bar chart and Service Port breakdown table.
- **Points to Highlight:**
  1. **Port 80 (HTTP):** Shows 26,767 flows (53.53%)—the exact volumetric target of the LOIC/HOIC DDoS attack script in this capture!
  2. **Port 53 (DNS):** Shows 11,126 flows (22.25%) legitimate lookup baseline.
  3. **Port 443 (HTTPS):** Shows 4,935 flows (9.87%).
  4. **Average Flow Duration:** e.g. `1,250,000 µs`.
  5. **Explain Dataset Design Note:** Show the cyan alert box explaining why raw IP addresses and absolute timestamps were excluded by the university researchers (to prevent supervised ML models from overfitting on specific source IP subnets).
- **Spoken Script:**
  > *"In the Traffic Analysis tab, NetScope maps raw destination port numbers to standard IANA networking protocols. Notice that Port 80 HTTP accounts for over 53% of all traffic in this slice. This directly correlates with the DDoS attack signature, where victim web servers were flooded with malicious HTTP requests."*

#### Demonstration 8: Anomaly Explorer & Ground-Truth Isolation [07:15 - 08:30]
- **Screen:** Tab `🔍 Anomaly Explorer`.
- **Action:**
  1. Point out the **2x2 Confusion Matrix Heatmap** (True Positives, False Positives, True Negatives, False Negatives).
  2. Review the KPI tiles: Accuracy, Precision, Recall, F1-Score.
  3. In the multiselect filter `Filter by Anomaly Reason:`, select `Volumetric Rate Spike (>1MB/s)` and `Rapid SYN Flood Pattern (<50µs)`.
  4. Observe the investigation table updating interactively.
  5. *(Optional)* Click **`🚀 Train Spark MLlib Model`** inside the expander to demonstrate distributed Random Forest training with an 80/20 train/test split.
- **Key Defensive Principle (Viva Critical):**
  - The heuristic rules rely **strictly on network flow characteristics** (bytes/s, packets/s, SYN flags, duration).
  - The `Label` or `Is_Malicious` column is **never referenced during detection** to prevent target leakage.
  - Ground truth is used **solely during evaluation** to assess heuristic precision and recall.
- **Spoken Script:**
  > *"A critical requirement of Big Data anomaly detection is preventing target data leakage. NetScope's heuristic rules evaluate only observable flow behaviors—such as volumetric bursts exceeding 1 MB/s or rapid microsecond SYN floods. The ground truth label is strictly quarantined and used solely to construct this Confusion Matrix. This gives security analysts transparent, explainable reason codes for every flagged alert."*

#### Demonstration 9: Live Hadoop Streaming MapReduce on HDFS [08:30 - 09:45]
- **Screen:** Tab `⚡ Big Data & HDFS Architecture`.
- **Action:**
  1. Scroll down to `🔄 Live Hadoop Streaming MapReduce on HDFS`.
  2. Click the primary button: **`🚀 Execute Hadoop MapReduce on HDFS`**.
  3. Show the job progress spinner and the resulting table:
     - `BENIGN`: 97,718
     - `DDoS`: 128,027
  4. Switch to Terminal and verify the HDFS output directory:
     ```bash
     hdfs dfs -cat /netscope/output/mr_attack_counts/part-00000
     ```
- **Points to Highlight:**
  - **Map Phase:** `scripts/mapreduce_demo.py --mapper` reads CSV stream, extracts and normalizes the label, and emits `label \t 1`.
  - **Shuffle & Sort:** Hadoop's internal engine sorts keys across DataNodes.
  - **Reduce Phase:** `scripts/mapreduce_demo.py --reducer` sums counts per key and outputs `label \t count`.
- **Spoken Script:**
  > *"To demonstrate foundational Big Data MapReduce principles, NetScope executes a real Hadoop Streaming job using `hadoop-streaming-3.5.0.jar`. The mapper streams 225,746 lines from HDFS, emits key-value pairs, the framework executes the shuffle and sort phase, and the reducer aggregates the final threat counts back onto HDFS at `/netscope/output/mr_attack_counts/part-00000`."*

#### Demonstration 10: Columnar Parquet Output on HDFS [09:45 - 10:30]
- **Screen:** Terminal window.
- **Action:** Run the command to inspect the Parquet export on HDFS:
  ```bash
  hdfs dfs -ls -h /netscope/output/cleaned_parquet
  ```
- **Points to Highlight:**
  1. Output files: `part-00000-....snappy.parquet` (6.65 MB) and `_SUCCESS` marker.
  2. Explain **Row-oriented (CSV) vs. Columnar (Parquet)**:
     - CSV stores data by row: reading 2 columns requires scanning all 79 columns from disk.
     - Parquet stores data by column with Snappy compression and dictionary encoding: queries selecting only `Destination Port` and `Label` read only those column stripes, reducing disk I/O by 80–90%.
- **Spoken Script:**
  > *"When NetScope finishes processing, it exports the sanitized dataset directly into HDFS in Apache Parquet format. Notice the 6.65 MB Snappy Parquet file and the `_SUCCESS` commit marker. Parquet's columnar layout enables predicate pushdown and column projection, making downstream analytical queries dramatically faster than raw CSV."*

#### Demonstration 11: Performance & Execution Mode Reality Check [10:30 - 11:15]
- **Screen:** Tab `⚡ Big Data & HDFS Architecture`.
- **Action:** Point to the execution metrics and explain what they measure honestly.
- **Points to Highlight:**
  1. **Timer Scope:** The timer measures the active Spark aggregation action pass on cached memory partitions.
  2. **Execution Mode:** Running on `local[*]` (multi-threaded executor using the Mac's CPU cores), not a multi-machine physical cluster.
  3. **HDFS Topology:** Pseudo-distributed single-node cluster (`dfs.replication = 1`), which validates the distributed file system protocol and APIs locally.
- **Spoken Script:**
  > *"In the interest of academic integrity, we document our performance metrics precisely. The throughput figure of 2.1 million flows per second measures in-memory distributed aggregation across parallel partitions. Our execution mode is `local[*]` on a multi-core processor, and HDFS runs in pseudo-distributed mode with replication factor 1. This demonstrates genuine HDFS RPC and block architecture on local hardware."*

#### Demonstration 12: Automated Pytest Suite & Executive Export [11:15 - 12:00]
- **Screen:** Terminal window.
- **Action:**
  1. Run the test suite:
     ```bash
     python3 -m pytest tests/ -v
     ```
  2. Point out that all **13 unit tests pass** in ~7 seconds:
     - `test_compute_overview_kpis`
     - `test_compute_attack_distribution`
     - `test_compute_port_distribution`
     - `test_rule_based_anomaly_detection`
     - `test_normalize_labels_cleaning`
     - `test_clean_numeric_features`
     - `test_quality_metrics`
     - `test_discover_csv_files`
     - `test_inspect_csv_schema`
     - `test_workspace_summary`
     - `test_check_hdfs_availability`
     - `test_list_hdfs_files`
     - `test_hdfs_deployment_commands`
  3. Switch back to browser Tab 7 and show the **`📥 Download Executive Markdown Report`** button.
- **Spoken Script:**
  > *"Finally, we ensure production software engineering standards with an automated test suite. All 13 unit tests pass, validating schema normalization, IEEE 754 infinity handling, HDFS path resolution, and anomaly metrics. NetScope also generates an automated Executive Markdown report summarizing the forensic findings. Thank you, Professor. I am ready for questions."*

---

## 🎛️ Section C: Parameter Adjustment Cheat Sheet

Use this cheat sheet to confidently adjust controls during the exam while knowing their exact scope and whether recomputation is required.

### Category A: UI Display Filters (Affects Current Display Only — Instant Response)
| Control Label | Location | Default Value | Recommended Demo Action | Expected Effect | Requires Spark Run? | How to Restore |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Filter by Anomaly Reason:** | Tab 4 (Anomaly Explorer) | None (All) | Select `Volumetric Rate Spike (>1MB/s)` | Filters investigation table to flows exceeding 1MB/s rate | **NO** (client-side Pandas filter) | Click 'x' on tag to clear filter |
| **Tab Navigation** | Main Tab Bar | Executive Overview | Click through Tabs 1 to 7 | Navigates between SOC views | **NO** | Click Tab 1 |

### Category B: Spark Processing Parameters (Requires Clicking '⚡ Run Spark')
| Control Label | Location | Default Value | Recommended Demo Action | Expected Effect | Requires Spark Run? | How to Restore |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Select Storage Layer** | Sidebar | `Hadoop HDFS` (if online) | Toggle between `Hadoop HDFS` and `Local POSIX` | Switches input URI between `hdfs://localhost:9000` and local filesystem | **YES** (Click `⚡ Run Spark`) | Re-select desired storage mode |
| **Select Target File** | Sidebar | `All Discovered / HDFS Files` | Select `Friday-...-DDos...csv` | Targets specific DDoS attack capture rather than all files | **YES** (Click `⚡ Run Spark`) | Select `All HDFS Files (Aggregated)` |
| **Flow Sample Bounding** | Sidebar | `50,000 Flows (Standard Demo)` | Select `25,000 Flows` or `100,000 Flows` | Adjusts row limit to demonstrate scalability or ultra-fast demo | **YES** (Click `⚡ Run Spark`) | Select `50,000 Flows` |

### Category C: Underlying Heuristic Thresholds (Configured in `src/anomaly_detection.py`)
| Parameter Name | Source Location | Default Value | Recommended Explanation Value | Purpose & Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `bytes_per_sec_threshold` | `src/anomaly_detection.py:27` | `1,000,000.0` (1 MB/s) | Explaining volumetric DDoS burst threshold | Flags flows with high transfer velocity typical of data exfiltration or UDP/HTTP floods |
| `packets_per_sec_threshold` | `src/anomaly_detection.py:28` | `50,000.0` pkts/s | Explaining packet velocity threshold | Flags high-frequency SYN floods or rapid port sweeping |
| `total_fwd_packets_threshold` | `src/anomaly_detection.py:29` | `500` pkts | Explaining forward flood threshold | Flags persistent packet floods |
| `min_duration_us` & `syn_flag` | `src/anomaly_detection.py:30` | `< 50 µs`, `SYN >= 1` | Explaining microsecond SYN flood rule | Detects anomalous TCP SYN packets without completed three-way handshakes |

---

## 💻 Section D: Copy-Paste Command Reference

Every command below is safe, non-destructive, and verified on the actual local setup.

### 1. Cluster Status & Diagnostics
```bash
# Check running JVM processes (NameNode, DataNode)
jps

# Check HDFS capacity and live nodes
hdfs dfsadmin -report

# Check and disable SafeMode if active
hdfs dfsadmin -safemode get
hdfs dfsadmin -safemode leave
```

### 2. HDFS File Inspection & Directory Management
```bash
# List input dataset files on HDFS with human-readable sizes
hdfs dfs -ls -h /netscope/input

# List generated Parquet files on HDFS
hdfs dfs -ls -h /netscope/output/cleaned_parquet

# View live MapReduce reduced counts from HDFS
hdfs dfs -cat /netscope/output/mr_attack_counts/part-00000
```

### 3. CLI Analytics Pipeline Execution
```bash
# Run CLI pipeline in HDFS mode on DDoS file (50,000 rows)
python3 scripts/run_pipeline.py --hdfs --file ddos --row-limit 50000

# Run CLI pipeline in Local POSIX mode on PortScan file (25,000 rows)
python3 scripts/run_pipeline.py --storage-mode local --file portscan --row-limit 25000

# Run full pipeline with Parquet export
python3 scripts/run_pipeline.py --hdfs --export-parquet
```

### 4. Hadoop Streaming MapReduce Execution
```bash
# Submit real Hadoop Streaming MapReduce job on HDFS data
hadoop jar /opt/homebrew/Cellar/hadoop/3.5.0/libexec/share/hadoop/tools/lib/hadoop-streaming-3.5.0.jar \
  -input /netscope/input/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv \
  -output /netscope/output/mr_ddos_counts \
  -mapper "python3 $(pwd)/scripts/mapreduce_demo.py --mapper" \
  -reducer "python3 $(pwd)/scripts/mapreduce_demo.py --reducer"
```

### 5. Automated Unit Tests
```bash
# Run all 13 unit tests with verbose reporting
python3 -m pytest tests/ -v
```

### 6. Graceful Service Shutdown (Post-Exam)
```bash
# Stop Streamlit process
pkill -f "streamlit run app.py"

# Stop HDFS daemons safely
hdfs --daemon stop secondarynamenode
hdfs --daemon stop datanode
hdfs --daemon stop namenode
```

---

## 📊 Section E: Expected Output & Result Validation Reference

Use this reference table to verify output values during the presentation.

| Operational Scope | Input Target | Output Metric / Artifact | Expected Reference Value | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Overall Dataset Scale** | `MachineLearningCVE/*.csv` | Total CSV Files | **8 Files** | Verified Live |
| **Overall Dataset Size** | All 8 Files | Total Uncompressed Size | **843.66 MB (884,547,459 bytes)** | Verified Live |
| **Total Valid Flows** | All 8 Files | Total Records | **2,830,743 valid flows** | Verified Live |
| **HDFS Dataset Location** | `/netscope/input` | Stored HDFS Files | **8 Files matching byte-for-byte** | Verified Live |
| **DDoS Sample (50k limit)** | `Friday-...-DDos...csv` | Malicious Flows | **23,865 flows (47.73%)** | Verified Live |
| **DDoS Sample (50k limit)** | `Friday-...-DDos...csv` | Benign Flows | **26,135 flows (52.27%)** | Verified Live |
| **DDoS Full File Counts** | `Friday-...-DDos...csv` | Total Malicious DDoS | **128,027 flows** | Verified Live |
| **DDoS Full File Counts** | `Friday-...-DDos...csv` | Total Benign Baseline | **97,718 flows** | Verified Live |
| **Top Target Port (DDoS)** | `Friday-...-DDos...csv` | Port 80 (HTTP) | **26,767 flows (53.53%)** | Verified Live |
| **HDFS Parquet Export** | `/netscope/output/cleaned_parquet` | Parquet File Size | **~6.65 MB (Snappy compressed)** | Verified Live |
| **MapReduce Reduced Counts** | `/netscope/output/mr_attack_counts` | `part-00000` | `BENIGN: 97718`, `DDoS: 128027` | Verified Live |
| **Automated Unit Tests** | `tests/` | Passed Tests | **13 Passed in ~7.6s** | Verified Live |

---

## 🛠️ Section F: Backup Plan & Troubleshooting Guide

| Symptom | Likely Root Cause | Diagnostic Command | Safe Fix Action | Emergency Fallback During Demo |
| :--- | :--- | :--- | :--- | :--- |
| **HDFS Status shows Offline in Sidebar** | NameNode or DataNode JVM stopped | `jps` | Run `hdfs --daemon start namenode && hdfs --daemon start datanode` | Switch sidebar radio to **`Local POSIX Storage`** and continue demo without pause. |
| **SafeMode Error: Cannot create directory / write output** | NameNode in SafeMode after restart | `hdfs dfsadmin -safemode get` | Run `hdfs dfsadmin -safemode leave` | Explain that NameNode enters SafeMode to verify block replicas, then disable it live. |
| **Port 8501 already occupied** | Previous Streamlit instance still running in background | `lsof -i :8501` | Run `kill -9 $(lsof -t -i:8501)` then restart `streamlit run app.py` | Run on port 8502: `streamlit run app.py --server.port 8502`. |
| **MapReduce fails: Output directory already exists** | HDFS output directory already created by prior run | `hdfs dfs -ls /netscope/output` | Run `hdfs dfs -rm -r -f /netscope/output/mr_attack_counts` | The dashboard UI button handles removal automatically; in terminal, pass `-rm -r -f`. |
| **Spark Ingestion Takes > 15s** | Large uncapped dataset selected on slow I/O | Check sidebar `Flow Sample Bounding` | Select `50,000 Flows` or `25,000 Flows` | Click **`🔄 Disk Cache`** button to instantly load pre-aggregated results from disk! |
| **ModuleNotFoundError when running pytest** | `pythonpath` not recognized | Check `pytest.ini` | Run `python3 -m pytest tests/ -v` | Always invoke pytest via `python3 -m pytest`. |

---

## 🎓 Section G: Comprehensive Exam Viva Q&A (24 Questions)

#### Q1: What is the problem statement of NetScope?
> **Answer:** Modern networks generate millions of flow records per hour, making traditional single-node analysis tools like Pandas impractical due to memory exhaustion. NetScope implements a distributed Big Data pipeline utilizing Apache Hadoop HDFS for scalable storage and Apache Spark for in-memory parallel transformations, calculating forensic traffic intelligence and explainable heuristic anomaly detection on the 2.83M flow CICIDS2017 benchmark.

#### Q2: Why did you choose network flow records instead of raw PCAP packets?
> **Answer:** Raw PCAP files contain full packet payloads, which require terabytes of storage and raise privacy/encryption concerns (e.g. HTTPS). Network flow records (generated by tools like `CICFlowMeter`) aggregate packet sequences into directional session statistics (such as duration, packet counts, inter-arrival times, and byte rates). This reduces storage by orders of magnitude while preserving essential behavioral signatures needed for threat analysis.

#### Q3: Why is this considered a Big Data project?
> **Answer:** It fulfills the core "V"s of Big Data:
> - **Volume:** 2.83 million records across 79 statistical features (~880 MB uncompressed).
> - **Velocity:** Network flows represent high-frequency streaming events that require sub-second batch aggregation (Spark throughput > 2M flows/sec).
> - **Variety:** Multiple distinct attack classes (DDoS, PortScan, Infiltration, Web Attacks) alongside benign enterprise baseline traffic.
> - **Veracity:** Raw data contains noise, missing labels, duplicate headers, and IEEE 754 infinity values requiring rigorous schema cleaning.

#### Q4: What is the size and structure of the CICIDS2017 dataset?
> **Answer:** The dataset comprises 8 CSV files totaling 843.66 MB and 2,830,743 valid data flows. Each flow contains 79 statistical features encompassing forward/backward packet counts, byte rates, inter-arrival times (IAT), flag counters (SYN, FIN, ACK), window sizes, and ground-truth attack labels.

#### Q5: What is Apache Hadoop HDFS?
> **Answer:** Hadoop Distributed File System (HDFS) is a scalable, fault-tolerant distributed filesystem designed to run on commodity hardware. It breaks large files into independent blocks (typically 128 MB) and distributes them across cluster DataNodes, managed by a centralized metadata controller called the NameNode.

#### Q6: What is the difference between HDFS and a standard POSIX filesystem (like APFS/ext4)?
> **Answer:** A standard filesystem operates on a single local disk controller and cannot scale beyond that machine. HDFS operates across a distributed network of machines, replicates blocks for hardware fault tolerance, exposes a unified namespace, and co-locates computation with data (data locality) so processing tasks execute directly where blocks reside.

#### Q7: What are the specific roles of the NameNode and DataNode?
> **Answer:** 
> - **NameNode:** The master node that maintains the filesystem directory tree, file permissions, and block mapping (which blocks reside on which DataNodes). It does not store actual data payloads.
> - **DataNode:** Worker daemons that store and retrieve the actual 128 MB data blocks on their local disks and send periodic heartbeats and block reports to the NameNode.

#### Q8: What is Apache Spark and why is it faster than classic MapReduce?
> **Answer:** Apache Spark is an open-source unified distributed analytics engine. It is up to 100x faster than classic MapReduce because it performs computations in-memory using Resilient Distributed Datasets (RDDs) and DataFrames. MapReduce writes intermediate shuffle state to physical disk between Map and Reduce phases, incurring heavy disk I/O; Spark retains intermediate state in RAM across transformation stages.

#### Q9: What is a Spark DataFrame?
> **Answer:** A Spark DataFrame is a distributed collection of data organized into named columns, conceptually equivalent to a relational database table but with distributed partitioning under the hood. It utilizes the Catalyst Optimizer to compile expressions into optimized JVM bytecode and uses the Tungsten execution engine for off-heap memory management.

#### Q10: What is the difference between Apache Spark and Hadoop MapReduce?
> **Answer:** 
> - **Hadoop MapReduce:** A rigid two-stage (Map $\to$ Shuffle/Sort $\to$ Reduce) batch processing framework that persists all intermediate state to disk.
> - **Apache Spark:** A multi-stage DAG (Directed Acyclic Graph) computation engine that supports complex arbitrary pipelines (map, filter, join, group-by) with in-memory caching, streaming, and machine learning libraries (MLlib).

#### Q11: What is Hadoop Streaming?
> **Answer:** Hadoop Streaming is a utility bundled with Hadoop that allows developers to write MapReduce jobs in any programming language (such as Python) using standard input (`sys.stdin`) and standard output (`sys.stdout`). The Hadoop framework handles reading from HDFS, feeding lines to the mapper, shuffling and sorting keys, passing sorted keys to the reducer, and writing the final output back to HDFS.

#### Q12: What do your mapper and reducer do in `scripts/mapreduce_demo.py`?
> **Answer:** 
> - **Mapper:** Reads CSV flow records from `sys.stdin`, strips header lines, extracts the label from the last column, cleans unicode artifacts, and emits `label \t 1`.
> - **Reducer:** Receives sorted key-value pairs from Hadoop's shuffle phase, sums the counts for each consecutive identical key, and emits the final aggregated count `label \t total_count`.

#### Q13: What is the relationship between HDFS and Spark in your project?
> **Answer:** HDFS serves as the **storage layer** (the Data Lake holding raw CSVs and final Parquet outputs), while Apache Spark serves as the **compute layer** (reading data from HDFS, executing parallel cleaning, and computing statistics).

#### Q14: Why do we write processed output in Parquet format?
> **Answer:** Parquet is a columnar storage format. Unlike row-based CSV:
> 1. It provides high compression ratios (e.g. Snappy compression reduces file sizes by over 70%).
> 2. It supports **column projection**: if an analyst queries only 2 columns out of 79, Spark reads only those specific column chunks from disk.
> 3. It stores statistical metadata (min/max per block), enabling **predicate pushdown** to skip irrelevant row groups entirely.

#### Q15: How does NetScope handle missing or corrupt data?
> **Answer:** 
> 1. Drops null or empty label records.
> 2. Normalizes column headers by trimming whitespace and disambiguating duplicate forward header lengths.
> 3. Cleans corrupt unicode characters in web attack labels.
> 4. Detects IEEE 754 `Infinity`, `-Infinity`, and `NaN` in rate columns (`Flow Bytes/s`, `Flow Packets/s`) caused by zero-duration flows and imputes them to `0.0`.

#### Q16: How are attack labels normalized?
> **Answer:** Raw web attack labels contain corrupted byte sequences like `Web Attack \ufffd XSS`. NetScope's regex cleaner normalizes these into standard categories (`Web Attack - XSS`, `Web Attack - Brute Force`, `Web Attack - Sql Injection`), strips whitespace, and creates a binary indicator column `Is_Malicious` (0 for BENIGN, 1 for attack).

#### Q17: How does NetScope's rule-based anomaly detection work?
> **Answer:** It applies transparent, explainable multi-factor heuristics based on observable traffic patterns:
> - **Volumetric Burst Rule:** Flags flows exceeding 1 MB/s (`Flow Bytes/s > 1,000,000`).
> - **Packet Velocity Rule:** Flags flows exceeding 50,000 packets/s.
> - **Forward Flood Rule:** Flags flows with more than 500 forward packets.
> - **Rapid SYN Flood Pattern:** Flags flows where SYN flag count is $\ge 1$ and flow duration is $< 50$ microseconds.
> Each flagged record is tagged with an explainable reason string.

#### Q18: How do you prevent target leakage in anomaly detection?
> **Answer:** Target leakage occurs if a model or rule uses the ground-truth target variable to make predictions. In NetScope, the heuristic rules inspect **only statistical flow features** (bytes, packets, duration, flags). The ground truth label `Label` is strictly isolated and used solely during post-prediction evaluation to compute the Confusion Matrix, Precision, Recall, and F1-score.

#### Q19: What does `local[*]` mean in Spark?
> **Answer:** It instructs Spark to run locally in a single JVM without a cluster manager, utilizing all available logical CPU cores on the host machine as worker execution threads (e.g., 8 threads on an 8-core Apple Silicon chip).

#### Q20: Is your Hadoop setup a physical multi-node cluster?
> **Answer:** No, it is configured in **pseudo-distributed mode** on local hardware. The NameNode, DataNode, and SecondaryNameNode run as separate JVM processes communicating over loopback sockets (`hdfs://localhost:9000`), using replication factor 1. This fully verifies the distributed HDFS protocol, block storage, and client APIs without requiring multiple physical servers.

#### Q21: What are the main limitations of this project?
> **Answer:** 
> 1. It performs **historical offline batch analytics** on completed network flows, not inline real-time packet dropping (like a Snort/Suricata firewall).
> 2. The pseudo-distributed setup uses a single DataNode, so it cannot demonstrate multi-machine hardware failover.
> 3. Heuristic anomaly thresholds require domain calibration and can yield false positives during legitimate high-throughput transfers.

#### Q22: How could NetScope be extended for enterprise production?
> **Answer:** 
> 1. Ingest live network flows via **Apache Kafka** into **Spark Structured Streaming** for continuous sliding-window analytics.
> 2. Deploy on a multi-node Kubernetes or YARN cluster on cloud object storage (AWS S3 / Azure ADLS / HDFS).
> 3. Feed anomalous flow alerts into an automated SIEM/SOAR system (such as Splunk or Elastic Security) to trigger firewall rules.

#### Q23: How do you verify that your output counts are accurate?
> **Answer:** We cross-verify output across three independent mechanisms:
> 1. Direct command-line MapReduce aggregation via `hadoop jar` on HDFS data.
> 2. PySpark distributed DataFrame `groupBy("Label").count()`.
> 3. Automated unit test assertions in `tests/test_analytics.py`. All three methods yield identical results (e.g. 128,027 DDoS flows and 97,718 Benign flows in the DDoS dataset).

#### Q24: How does NetScope demonstrate distributed storage and processing?
> **Answer:** 
> - **Distributed Storage:** Ingesting 884 MB of data into HDFS blocks across `/netscope/input` and writing Parquet back to `/netscope/output`.
> - **Distributed Processing:** Executing PySpark partition transformations across worker threads and running Hadoop Streaming MapReduce jobs with mapper, shuffle/sort, and reducer stages.

---

## 📋 Section H: Printable Demo Checklists & Screenshot Guide

### Checklist 1: Pre-Demo Preparation (T-15 Minutes)
- [ ] Terminal window 1 open at `/Users/ishan/bda-mp`.
- [ ] Python version verified (`python3 --version` $\ge$ 3.10).
- [ ] Java 17 verified (`java -version`).
- [ ] Hadoop daemons verified via `jps` (NameNode, DataNode active).
- [ ] SafeMode verified OFF (`hdfs dfsadmin -safemode leave`).
- [ ] HDFS dataset verified (`hdfs dfs -ls /netscope/input` shows 8 files).
- [ ] Streamlit running (`http://localhost:8501` responds with 200 OK).
- [ ] Browser window open at `http://localhost:8501` in fullscreen.
- [ ] Terminal window 2 prepared with copy-paste commands from Section D.

### Checklist 2: Live Demo Execution (During Presentation)
- [ ] State opening problem statement (1 minute).
- [ ] Show Executive Overview KPIs and Donut chart.
- [ ] Point out live status badges (HDFS connected, Spark 4.2 active).
- [ ] Explain Schema Cleaning & Data Hygiene in Tab 5 (duplicate column, infinity fix).
- [ ] Switch to terminal: run `hdfs dfs -ls -h /netscope/input` to prove real HDFS storage.
- [ ] Run Spark job on DDoS file (50,000 flows) and show 2-second completion.
- [ ] Show Traffic Analysis: Port 80 HTTP spike (DDoS signature).
- [ ] Explain Anomaly Explorer: show Confusion Matrix and explain ground-truth isolation.
- [ ] Click **`Execute Hadoop MapReduce on HDFS`** and show reduced output on HDFS.
- [ ] Inspect columnar Snappy Parquet export in terminal (`hdfs dfs -ls /netscope/output`).
- [ ] Run automated test suite: `python3 -m pytest tests/ -v` (13 passed).
- [ ] Conclude and invite questions.

### Checklist 3: Screenshot Checklist (For Submission Dossier)
Capture these exact 5 screens for your project report:
1. **Screenshot 1 — Executive Overview:** Capture `http://localhost:8501` showing the top status strip, 4 KPI cards (Total Flows, Malicious, Benign, Threat Classes), and the Donut/Bar charts.
2. **Screenshot 2 — HDFS Cluster Status (Tab 6):** Capture Tab 6 showing the green `ONLINE & ACTIVE` badge, NameNode URI `hdfs://localhost:9000`, 1 Live DataNode, and verified input/output endpoints.
3. **Screenshot 3 — Live MapReduce Output (Tab 6):** Capture Tab 6 after clicking `Execute Hadoop MapReduce on HDFS`, showing the resulting table (`BENIGN: 97,718`, `DDoS: 128,027`).
4. **Screenshot 4 — Anomaly Explorer Confusion Matrix (Tab 4):** Capture Tab 4 showing the 2x2 Heatmap, precision/recall tiles, and the flagged anomaly investigation table.
5. **Screenshot 5 — Terminal Verification:** Capture a split terminal showing `jps`, `hdfs dfs -ls -h /netscope/input`, and `pytest tests/ -v` (13 passed).

---
*Playbook compiled for NetScope BDA Mini Project — Academic Defense Ready.*
