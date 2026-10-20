#!/usr/bin/env python3
"""
NetScope: Word Document Playbook Generator
Generates docs/NetScope_Live_Demo_Playbook.docx with professional styling,
styled tables, callout containers, monospaced code blocks, and comprehensive exam walkthroughs.
"""

import os
import sys
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
DOCX_OUTPUT = DOCS_DIR / "NetScope_Live_Demo_Playbook.docx"

# Color Palette Constants
HEX_NAVY = "0A192F"
HEX_STEEL = "0284C7"
HEX_LIGHT_BG = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_AMBER_BG = "FEF3C7"
HEX_AMBER_BORDER = "D97706"
HEX_GREEN_BG = "ECFDF5"
HEX_GREEN_BORDER = "059669"
HEX_CODE_BG = "F1F5F9"

COLOR_NAVY = RGBColor(10, 25, 47)
COLOR_STEEL = RGBColor(2, 132, 199)
COLOR_DARK = RGBColor(30, 41, 59)
COLOR_MUTED = RGBColor(100, 116, 139)
COLOR_AMBER = RGBColor(217, 119, 6)
COLOR_GREEN = RGBColor(5, 150, 105)


def set_cell_bg(cell, hex_code):
    """Sets background fill color of a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_code}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal padding for a table cell (in twips: 20 twips = 1 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_header_footer(doc):
    """Adds persistent headers and footers to all sections."""
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

        # Header
        header = section.header
        p_hdr = header.paragraphs[0]
        p_hdr.text = "NetScope: Big Data Analytics Lab Live Demonstration Playbook"
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_hdr.style.font.name = "Arial"
        p_hdr.style.font.size = Pt(8)
        p_hdr.style.font.color.rgb = COLOR_MUTED

        # Footer
        footer = section.footer
        p_ftr = footer.paragraphs[0]
        p_ftr.text = "Practical Examination Guide | Apache Spark & Hadoop HDFS Integration"
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ftr.style.font.name = "Arial"
        p_ftr.style.font.size = Pt(8)
        p_ftr.style.font.color.rgb = COLOR_MUTED


def add_title_block(doc, title, subtitle, author_meta):
    """Creates a stylized cover title block."""
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_icon = p_title.add_run("🛡️ ")
    run_icon.font.size = Pt(28)
    run_title = p_title.add_run(title)
    run_title.font.name = "Arial"
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_NAVY
    p_title.paragraph_format.space_after = Pt(4)

    p_sub = doc.add_paragraph()
    run_sub = p_sub.add_run(subtitle)
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = COLOR_STEEL
    p_sub.paragraph_format.space_after = Pt(12)

    # Metadata card table
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.8)
    cell = table.cell(0, 0)
    set_cell_bg(cell, HEX_LIGHT_BG)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)

    p_meta = cell.paragraphs[0]
    p_meta.paragraph_format.space_after = Pt(0)
    for label, val in author_meta.items():
        r1 = p_meta.add_run(f"{label}: ")
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_NAVY
        r2 = p_meta.add_run(f"{val}   |   ")
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(8)


def add_h1(doc, text):
    """Styled Heading 1."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = COLOR_NAVY
    return p


def add_h2(doc, text):
    """Styled Heading 2."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = COLOR_STEEL
    return p


def add_h3(doc, text):
    """Styled Heading 3."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = COLOR_DARK
    return p


def add_body(doc, text, bold_prefix=None):
    """Styled Body Paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.bold = True
        r_pre.font.size = Pt(9.5)
        r_pre.font.color.rgb = COLOR_DARK
    r_body = p.add_run(text)
    r_body.font.name = "Arial"
    r_body.font.size = Pt(9.5)
    r_body.font.color.rgb = COLOR_DARK
    return p


def add_bullet(doc, text, bold_prefix=None):
    """Styled Bullet Item."""
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.bold = True
        r_pre.font.size = Pt(9.5)
        r_pre.font.color.rgb = COLOR_NAVY
    r_body = p.add_run(text)
    r_body.font.name = "Arial"
    r_body.font.size = Pt(9.5)
    r_body.font.color.rgb = COLOR_DARK
    return p


def add_code_block(doc, code_str):
    """Monospaced Code Block in a shaded box."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.8)
    cell = table.cell(0, 0)
    set_cell_bg(cell, HEX_CODE_BG)
    set_cell_margins(cell, top=100, bottom=100, left=160, right=160)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(code_str.strip())
    run.font.name = "Courier New"
    run.font.size = Pt(8.5)
    run.font.color.rgb = COLOR_NAVY
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_speech_box(doc, text, speaker="Spoken Script (What to say)"):
    """Stylized callout box for what to say to the examiner."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.8)
    cell = table.cell(0, 0)
    set_cell_bg(cell, "F0FDF4")  # Light emerald green tint
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r_title = p.add_run(f"🗣️  {speaker}:\n")
    r_title.font.bold = True
    r_title.font.size = Pt(9.5)
    r_title.font.color.rgb = COLOR_GREEN

    r_text = p.add_run(f'"{text}"')
    r_text.font.italic = True
    r_text.font.size = Pt(9.5)
    r_text.font.color.rgb = COLOR_DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_concept_box(doc, concept_title, text):
    """Stylized callout box for Big Data architectural concept."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.8)
    cell = table.cell(0, 0)
    set_cell_bg(cell, "F8FAFC")
    set_cell_margins(cell, top=100, bottom=100, left=180, right=180)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r_title = p.add_run(f"💡 Big Data Concept — {concept_title}:\n")
    r_title.font.bold = True
    r_title.font.size = Pt(9.5)
    r_title.font.color.rgb = COLOR_STEEL

    r_text = p.add_run(text)
    r_text.font.size = Pt(9.0)
    r_text.font.color.rgb = COLOR_DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_table_styled(doc, headers, rows, col_widths=None):
    """Creates a beautifully styled professional data table."""
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header Row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_bg(hdr_cells[i], HEX_NAVY)
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(255, 255, 255)

    # Body Rows
    for row_idx, row_data in enumerate(rows):
        cells = table.rows[row_idx + 1].cells
        bg_color = HEX_LIGHT_BG if (row_idx % 2 == 1) else "FFFFFF"
        for col_idx, cell_value in enumerate(row_data):
            cells[col_idx].text = str(cell_value)
            set_cell_bg(cells[col_idx], bg_color)
            set_cell_margins(cells[col_idx], top=80, bottom=80, left=120, right=120)
            p = cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            for r in p.runs:
                r.font.size = Pt(8.5)
                r.font.color.rgb = COLOR_DARK

    # Column Widths
    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return table


def generate_playbook():
    print("[*] Generating NetScope Live Demo Playbook (.docx)...")
    doc = docx.Document()
    add_header_footer(doc)

    # 1. Cover & Title Block
    author_metadata = {
        "Course": "Big Data Analytics Lab (CS / IT)",
        "Examination": "Practical Lab Exam & Viva",
        "Stack": "PySpark 4.2 | Hadoop HDFS 3.5 | Streamlit",
        "Target Dataset": "CICIDS2017 (2.83M Flows, 843.7 MB)",
        "Document Version": "1.2 (Exam Verified)",
    }
    add_title_block(
        doc,
        "NetScope: Live Demo Playbook",
        "Comprehensive Practical Examination Walkthrough, Spoken Scripts & Viva Guide",
        author_metadata
    )

    # Executive Overview
    add_h1(doc, "1. Executive System Summary")
    add_body(
        doc,
        "NetScope is an enterprise-grade Big Data network forensic and anomaly analytics system built on Apache Spark and Apache Hadoop HDFS. It processes over 2.83 million real flow captures from the Canadian Institute for Cybersecurity (CICIDS2017) benchmark. This document serves as the student's exact live examination guide, providing step-by-step UI actions, copy-paste terminal commands, natural student-friendly dialogue scripts, defensive viva answers, and emergency contingency plans."
    )

    # 2. Section A: Quick Start Before Demo
    add_h1(doc, "Section A: Quick Start Before the Demo (Pre-Flight Setup)")
    add_body(
        doc,
        "Execute these exact 5 checks 15 minutes prior to the evaluator's arrival to guarantee that all background daemons, storage endpoints, and web applications are healthy."
    )

    add_h2(doc, "A.1 Terminal Navigation & Directory Verification")
    add_body(doc, "Open Terminal and confirm you are located at the project workspace root:")
    add_code_block(doc, "cd /Users/ishan/bda-mp\npwd")

    add_h2(doc, "A.2 Runtime Environment Diagnostics")
    add_body(doc, "Verify that Python 3.10+ and Java 17 OpenJDK are configured:")
    add_code_block(doc, "python3 --version\njava -version")
    add_bullet(doc, "Python must be 3.10 or higher (PySpark 4.2.0 compatibility).", "Requirement: ")
    add_bullet(doc, "Java OpenJDK 17 must be active (Required by both Hadoop HDFS and Apache Spark JVM workers).", "Requirement: ")

    add_h2(doc, "A.3 Hadoop HDFS Cluster Daemons Check")
    add_body(doc, "Run the Java process status command to verify the pseudo-distributed HDFS daemons:")
    add_code_block(doc, "jps")
    add_body(doc, "Confirm that all three daemons are present in the output: NameNode, DataNode, and SecondaryNameNode. If any daemon is missing, execute:")
    add_code_block(doc, "hdfs --daemon start namenode && hdfs --daemon start datanode && hdfs --daemon start secondarynamenode")

    add_h2(doc, "A.4 HDFS Health & SafeMode Verification")
    add_body(doc, "Check cluster storage capacity and ensure SafeMode is turned OFF so writes are allowed:")
    add_code_block(doc, "hdfs dfsadmin -report | head -n 12\nhdfs dfsadmin -safemode leave")

    add_h2(doc, "A.5 Web Application Status & Launch")
    add_body(doc, "Check if Streamlit is already running on port 8501:")
    add_code_block(doc, "curl -s http://localhost:8501/_stcore/health")
    add_body(doc, "If it returns 'ok', the dashboard is live. If not running, launch it with:")
    add_code_block(doc, "streamlit run app.py")
    add_body(doc, "Open http://localhost:8501 in Safari or Chrome in full-screen mode.")

    # 3. Section B: Demonstration Script
    add_h1(doc, "Section B: Complete Live Demonstration Script")
    add_body(
        doc,
        "Choose between the 5-Minute Emergency Rapid Sequence (for time-constrained evaluations) or the Full 10–12 Minute Walkthrough."
    )

    add_h2(doc, "5-Minute Emergency Rapid Demo Sequence")
    add_bullet(doc, "State problem statement: processing 2.83M CICIDS2017 network flows using Apache Spark & Hadoop HDFS.", "[00:00 - 00:45] Intro: ")
    add_bullet(doc, "Show sidebar: point out 'Hadoop HDFS (Data Lake)' radio option and the green 'HDFS Data Lake Connected' badge on port 9000.", "[00:45 - 01:30] Storage Mode: ")
    add_bullet(doc, "Select Friday-DDos file (50,000 flows), click '⚡ Run Spark', show 2-second completion, and explain the 4 KPI cards & Donut chart.", "[01:30 - 02:45] Spark Ingestion: ")
    add_bullet(doc, "Click Tab 4 'Anomaly Explorer', show 2x2 Confusion Matrix heatmap, explain explainable heuristics without data leakage.", "[02:45 - 03:45] Anomaly Detection: ")
    add_bullet(doc, "Click Tab 6 'Big Data & HDFS Architecture', click '🚀 Execute Hadoop MapReduce on HDFS', show real reduced output on HDFS.", "[03:45 - 04:30] MapReduce Demo: ")
    add_bullet(doc, "Show 6.65 MB Snappy Parquet file on HDFS (/netscope/output/cleaned_parquet) and conclude.", "[04:30 - 05:00] Conclusion: ")

    add_h2(doc, "Full 10–12 Minute Walkthrough (Steps 1 to 12)")

    # Demo 1
    add_h3(doc, "Demonstration 1: Project Introduction & Problem Statement [00:00 - 01:00]")
    add_body(doc, "Open browser at http://localhost:8501 with the dashboard header visible.")
    add_speech_box(
        doc,
        "Good morning, Professor. Today I am demonstrating NetScope, a Big Data network traffic intelligence and threat detection platform built on Apache Spark and Hadoop HDFS.\n\nModern enterprise backbones generate hundreds of millions of network flow records every day. Traditional single-node tools like Pandas fail at scale because they load entire datasets into single-process virtual memory, causing memory exhaustion. NetScope solves this by utilizing Apache Hadoop HDFS for distributed fault-tolerant storage and Apache Spark for in-memory parallel transformations and aggregations across 2.83 million benchmark flow records.",
        "What to Say (Natural Script)"
    )
    add_concept_box(
        doc,
        "Distributed Computing Bottlenecks",
        "Single-node shared-memory architectures cannot scale horizontally. Shared-nothing architectures like HDFS and Spark distribute data partitions across independent nodes and worker threads."
    )

    # Demo 2
    add_h3(doc, "Demonstration 2: Dashboard Overview & SOC Executive KPIs [01:00 - 02:00]")
    add_body(doc, "Navigate to Tab 1: '📊 Executive Overview'. Point out the top status strip and the four metric cards.")
    add_bullet(doc, "Displays active Spark 4.2.0, HDFS cluster mode, and current dataset load count.", "Top Status Strip: ")
    add_bullet(doc, "50,000 valid flows processed.", "Total Valid Flows Card: ")
    add_bullet(doc, "23,865 malicious flows (47.73% of sample).", "Malicious Threat Flows Card: ")
    add_bullet(doc, "26,135 legitimate baseline flows (52.27%).", "Benign Traffic Flows Card: ")
    add_bullet(doc, "1 distinct attack category (DDoS in this file).", "Distinct Threat Categories Card: ")
    add_bullet(doc, "Interactive donut split of Benign vs Malicious, and attack frequency bar chart.", "Charts: ")
    add_speech_box(
        doc,
        "The NetScope interface is modeled after a modern Security Operations Center (SOC) intelligence dashboard. Notice that every single card, percentage, and chart is derived dynamically by Apache Spark from the active dataset. In this 50,000-flow DDoS slice, Spark accurately isolated 23,865 malicious flows against 26,135 benign flows without any hardcoded mock data.",
        "What to Say"
    )

    # Demo 3
    add_h3(doc, "Demonstration 3: Dataset Discovery & Schema Inspection [02:00 - 03:00]")
    add_body(doc, "Navigate to Tab 5: '🧹 Data Hygiene & Quality'. Point out the schema transformations table.")
    add_body(doc, "Explain the real dataset findings discovered in MachineLearningCVE/ (8 CSVs, 843.66 MB total, 79 features):")
    add_bullet(doc, "All 79 column names contained leading whitespace (e.g. ' Destination Port'). Automated trimming was applied.", "Header Whitespace: ")
    add_bullet(doc, "Indices 34 and 55 both contained 'Fwd Header Length'. NetScope disambiguates the second to 'Fwd Header Length_1' to prevent Spark AnalysisException errors.", "Duplicate Header Disambiguation: ")
    add_bullet(doc, "Raw labels had replacement characters ('Web Attack \\ufffd XSS'). Cleaned into 'Web Attack - XSS'.", "Corrupt Unicode Normalization: ")
    add_bullet(doc, "Division by zero in microsecond flows produced IEEE 754 Infinity and NaN in rate columns. Neutralized to 0.0.", "Infinity & NaN Imputation: ")
    add_speech_box(
        doc,
        "In production Big Data engineering, raw datasets are rarely clean. During pre-implementation inspection of CICIDS2017, we identified three critical anomalies: duplicate forward header length columns, corrupted unicode characters in web attacks, and floating-point infinities caused by zero-duration flows. In Tab 5, NetScope demonstrates our data hygiene pipeline that sanitized all 79 columns with 100% data retention.",
        "What to Say"
    )

    # Demo 4
    add_h3(doc, "Demonstration 4: Genuine HDFS Storage Inspection & File Integrity [03:00 - 04:00]")
    add_body(doc, "Open Terminal side-by-side with browser. Execute:")
    add_code_block(doc, "hdfs dfsadmin -report | head -n 12\nhdfs dfs -ls -h /netscope/input")
    add_body(doc, "Point out the live NameNode listening on hdfs://localhost:9000, 1 active DataNode on port 9866, and the 8 uploaded CSV files in /netscope/input. Emphasize that every file matches local source byte-for-byte.")
    add_speech_box(
        doc,
        "NetScope does not merely simulate HDFS through helper scripts. Here in the terminal, our NameNode and DataNode are live and accepting RPC connections on port 9000. When we list /netscope/input, all 8 benchmark CSV files reside on the HDFS distributed file system, totaling 884 megabytes with 100% verified byte integrity.",
        "What to Say"
    )

    # Demo 5
    add_h3(doc, "Demonstration 5: Switching Storage Mode in Dashboard [04:00 - 04:45]")
    add_body(doc, "In the Streamlit Sidebar, point to the 'Select Storage Layer' radio control.")
    add_body(doc, "Toggle between 'Hadoop HDFS (Data Lake)' and 'Local POSIX Storage':")
    add_bullet(doc, "Queries HDFS via 'hdfs dfs -ls' and displays '🟢 HDFS Data Lake Connected' with URI hdfs://localhost:9000/netscope/input/.", "Hadoop HDFS Mode: ")
    add_bullet(doc, "Reverts to local POSIX filesystem reading from MachineLearningCVE/.", "Local POSIX Mode: ")
    add_speech_box(
        doc,
        "In the sidebar, NetScope provides a dynamic storage selector. We can instruct Spark to ingest either from local POSIX disks or directly from our Hadoop HDFS Data Lake. The dashboard actively probes NameNode health and only enables HDFS mode when the cluster is genuinely reachable, maintaining a reliable local fallback for offline development.",
        "What to Say"
    )

    # Demo 6
    add_h3(doc, "Demonstration 6: Apache Spark Analytics Execution [04:45 - 06:00]")
    add_body(doc, "In Sidebar, select 'Friday-...-DDos...csv', set sample to '50,000 Flows', and click '⚡ Run Spark'.")
    add_body(doc, "Switch to Tab 6: '⚡ Big Data & HDFS Architecture'. Point to the live execution benchmark.")
    add_speech_box(
        doc,
        "When I click 'Run Spark', PySpark coordinates with the JVM. It reads the CSV from HDFS, constructs a lazy execution plan, and optimizes the DAG using the Catalyst Optimizer. When actions like .count() are triggered, Spark executes parallel partition tasks across all available CPU cores, completing in under 0.03 seconds and achieving over 2 million flows per second.",
        "What to Say"
    )
    add_concept_box(
        doc,
        "Lazy Evaluation: Transformations vs Actions",
        "Spark transformations (like .filter(), .withColumn(), .groupBy()) are lazy and do not execute immediately; they merely build a lineage graph. Computation is only executed when an action (like .count(), .collect(), or .write.parquet()) is invoked."
    )

    # Demo 7
    add_h3(doc, "Demonstration 7: Interactive Traffic Analysis & Port Mapping [06:00 - 07:15]")
    add_body(doc, "Navigate to Tab 2: '🌐 Traffic Analysis'. Point to the Destination Ports chart and table.")
    add_bullet(doc, "Shows 26,767 flows (53.53%)—the exact volumetric target of the HTTP flood script!", "Port 80 (HTTP): ")
    add_bullet(doc, "Shows 11,126 flows (22.25%) legitimate baseline lookup.", "Port 53 (DNS): ")
    add_bullet(doc, "Shows 4,935 flows (9.87%).", "Port 443 (HTTPS): ")
    add_speech_box(
        doc,
        "In Tab 2, NetScope maps raw destination port numbers to standard network service definitions. Notice that Port 80 HTTP accounts for over 53% of all traffic in this slice. This directly correlates with the DDoS attack signature, where victim web servers were bombarded with malicious HTTP requests.",
        "What to Say"
    )

    # Demo 8
    add_h3(doc, "Demonstration 8: Anomaly Explorer & Ground-Truth Isolation [07:15 - 08:30]")
    add_body(doc, "Navigate to Tab 4: '🔍 Anomaly Explorer'. Point out the 2x2 Confusion Matrix Heatmap.")
    add_body(doc, "Explain the heuristic rules (Volumetric rate > 1MB/s, Packet rate > 50k pkts/s, SYN flood < 50µs).")
    add_speech_box(
        doc,
        "A critical principle in Big Data anomaly detection is preventing target data leakage. NetScope's heuristic rules evaluate only observable flow behaviors—such as volumetric bursts exceeding 1 MB/s or rapid microsecond SYN floods. The ground truth label is strictly quarantined and used solely to construct this Confusion Matrix. This gives security analysts transparent, explainable reason codes for every flagged alert.",
        "What to Say"
    )

    # Demo 9
    add_h3(doc, "Demonstration 9: Live Hadoop Streaming MapReduce on HDFS [08:30 - 09:45]")
    add_body(doc, "Navigate to Tab 6: '⚡ Big Data & HDFS Architecture'. Scroll to the MapReduce section and click:")
    add_body(doc, "'🚀 Execute Hadoop MapReduce on HDFS'")
    add_body(doc, "Show the resulting table: BENIGN: 97,718 | DDoS: 128,027.")
    add_body(doc, "Switch to Terminal and show the output file on HDFS:")
    add_code_block(doc, "hdfs dfs -cat /netscope/output/mr_attack_counts/part-00000")
    add_speech_box(
        doc,
        "To demonstrate foundational Big Data MapReduce principles, NetScope executes an actual Hadoop Streaming job using hadoop-streaming-3.5.0.jar. The mapper streams 225,746 lines from HDFS, emits key-value pairs, the framework executes the shuffle and sort phase, and the reducer aggregates the final threat counts back onto HDFS at /netscope/output/mr_attack_counts/part-00000.",
        "What to Say"
    )
    add_concept_box(
        doc,
        "MapReduce Paradigm",
        "Map extracts and normalizes the attack key; Shuffle & Sort groups identical keys across partitions; Reduce sums the values per key. This demonstrates the core architectural paradigm of Hadoop."
    )

    # Demo 10
    add_h3(doc, "Demonstration 10: Columnar Parquet Output on HDFS [09:45 - 10:30]")
    add_body(doc, "In Terminal, list the Parquet export on HDFS:")
    add_code_block(doc, "hdfs dfs -ls -h /netscope/output/cleaned_parquet")
    add_body(doc, "Point out the 6.65 MB Snappy Parquet file and the _SUCCESS commit marker.")
    add_speech_box(
        doc,
        "When NetScope finishes processing, it exports the sanitized dataset directly into HDFS in Apache Parquet format. Notice the 6.65 MB Snappy Parquet file and the _SUCCESS commit marker. Parquet's columnar layout enables predicate pushdown and column projection, making downstream analytical queries dramatically faster than raw CSV.",
        "What to Say"
    )

    # Demo 11
    add_h3(doc, "Demonstration 11: Performance & Execution Mode Reality Check [10:30 - 11:15]")
    add_body(doc, "In Tab 6, review the throughput and execution parameters.")
    add_speech_box(
        doc,
        "In the interest of academic integrity, we document our performance metrics precisely. The throughput figure of 2.1 million flows per second measures in-memory distributed aggregation across parallel partitions. Our execution mode is local[*] on a multi-core processor, and HDFS runs in pseudo-distributed mode with replication factor 1. This demonstrates genuine HDFS RPC and block architecture on local hardware.",
        "What to Say"
    )

    # Demo 12
    add_h3(doc, "Demonstration 12: Automated Pytest Suite & Executive Export [11:15 - 12:00]")
    add_body(doc, "In Terminal, run the automated test suite:")
    add_code_block(doc, "python3 -m pytest tests/ -v")
    add_body(doc, "Point out that all 13 unit tests pass in ~7 seconds.")
    add_speech_box(
        doc,
        "Finally, we ensure production software engineering standards with an automated test suite. All 13 unit tests pass, validating schema normalization, IEEE 754 infinity handling, HDFS path resolution, and anomaly metrics. NetScope also generates an automated Executive Markdown report summarizing the forensic findings. Thank you, Professor. I am ready for questions.",
        "What to Say"
    )

    # 4. Section C: Parameter Adjustment Cheat Sheet
    add_h1(doc, "Section C: Parameter Adjustment Cheat Sheet")
    add_body(doc, "Use this cheat sheet during the live demo to safely adjust parameters and explain their behavior:")

    headers_c = ["Feature / Control", "Parameter Name", "Default Value", "Recommended Demo Value", "Expected Effect", "Requires Run?", "Restore Method"]
    rows_c = [
        ["Storage Mode", "Select Storage Layer", "Hadoop HDFS (if live)", "Toggle HDFS vs Local", "Switches target URI & dataset discovery", "YES (⚡ Run Spark)", "Re-select HDFS"],
        ["Target File", "Select Target File", "All Discovered / HDFS", "Friday-...-DDos...csv", "Targets DDoS attack capture slice", "YES (⚡ Run Spark)", "Select All Files"],
        ["Sample Size", "Flow Sample Bounding", "50,000 Flows", "25,000 or 100,000", "Adjusts row bounding for speed/scale", "YES (⚡ Run Spark)", "Select 50,000 Flows"],
        ["Reason Filter", "Filter by Anomaly Reason", "None (All)", "Volumetric Spike (>1MB/s)", "Filters investigation table to burst flows", "NO (Client filter)", "Clear multiselect tag"],
        ["Tab Navigation", "Navigation Tabs", "Executive Overview", "Click through Tabs 1-7", "Switches SOC analytics perspective", "NO", "Click Tab 1"],
    ]
    add_table_styled(doc, headers_c, rows_c, [1.1, 1.2, 0.9, 1.1, 1.3, 0.6, 0.7])

    # 5. Section D: Copy-Paste Command Reference
    add_h1(doc, "Section D: Copy-Paste Command Reference")
    add_body(doc, "Compact reference of verified terminal commands:")

    headers_d = ["Operation", "Exact Terminal Command", "Purpose & Safety"]
    rows_d = [
        ["Check JVM Processes", "jps", "Verify NameNode and DataNode are active. (Safe)"],
        ["HDFS Health Report", "hdfs dfsadmin -report", "Check storage capacity and live DataNodes. (Safe)"],
        ["Disable SafeMode", "hdfs dfsadmin -safemode leave", "Disable read-only SafeMode after startup. (Safe)"],
        ["List HDFS Dataset", "hdfs dfs -ls -h /netscope/input", "List 8 CSV files in HDFS Data Lake. (Safe)"],
        ["List HDFS Output", "hdfs dfs -ls -h /netscope/output/cleaned_parquet", "Verify generated Parquet output on HDFS. (Safe)"],
        ["View MapReduce Output", "hdfs dfs -cat /netscope/output/mr_attack_counts/part-00000", "View reduced label counts from HDFS. (Safe)"],
        ["Run CLI Pipeline", "python3 scripts/run_pipeline.py --hdfs --file ddos --row-limit 50000", "Run full ingestion, cleaning & analytics via CLI. (Safe)"],
        ["Submit MapReduce Job", "hadoop jar /opt/homebrew/Cellar/hadoop/3.5.0/libexec/share/hadoop/tools/lib/hadoop-streaming-3.5.0.jar -input /netscope/input/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv -output /netscope/output/mr_ddos_counts -mapper \"python3 $(pwd)/scripts/mapreduce_demo.py --mapper\" -reducer \"python3 $(pwd)/scripts/mapreduce_demo.py --reducer\"", "Execute Hadoop streaming job on HDFS data. (Safe)"],
        ["Run Unit Tests", "python3 -m pytest tests/ -v", "Execute all 13 automated unit tests. (Safe)"],
    ]
    add_table_styled(doc, headers_d, rows_d, [1.4, 3.4, 2.0])

    # 6. Section E: Expected Output Reference
    add_h1(doc, "Section E: Expected Output & Result Validation Reference")
    add_body(doc, "Verified reference values for cross-checking live demo results:")

    headers_e = ["Scope / Input", "Target Output Metric", "Verified Reference Value", "Verification Status"]
    rows_e = [
        ["Overall Dataset", "Total Discovered Files", "8 CSV Files", "Verified Live"],
        ["Overall Dataset", "Total Uncompressed Size", "843.66 MB (884,547,459 bytes)", "Verified Live"],
        ["Overall Dataset", "Total Flow Records", "2,830,743 valid flows", "Verified Live"],
        ["HDFS Input Directory", "/netscope/input", "8 Files matching byte-for-byte", "Verified Live"],
        ["DDoS Sample (50k limit)", "Malicious Threat Flows", "23,865 flows (47.73%)", "Verified Live"],
        ["DDoS Sample (50k limit)", "Benign Normal Flows", "26,135 flows (52.27%)", "Verified Live"],
        ["DDoS Full File Counts", "Malicious DDoS Flows", "128,027 flows", "Verified Live"],
        ["DDoS Full File Counts", "Benign Baseline Flows", "97,718 flows", "Verified Live"],
        ["Top Target Port (DDoS)", "Port 80 (HTTP)", "26,767 flows (53.53%)", "Verified Live"],
        ["HDFS Parquet Export", "/netscope/output/cleaned_parquet", "6.65 MB Snappy Parquet", "Verified Live"],
        ["MapReduce Reduced Output", "/netscope/output/mr_attack_counts", "BENIGN 97718 | DDoS 128027", "Verified Live"],
        ["Automated Pytest Suite", "tests/ (13 tests)", "13 Passed in ~7.6s", "Verified Live"],
    ]
    add_table_styled(doc, headers_e, rows_e, [1.6, 2.0, 2.0, 1.2])

    # 7. Section F: Backup Plan & Troubleshooting
    add_h1(doc, "Section F: Backup Plan & Troubleshooting Guide")
    add_body(doc, "Troubleshooting matrix for handling any unexpected live demo issues:")

    headers_f = ["Symptom", "Root Cause", "Diagnostic Command", "Safe Fix Action", "Emergency Fallback"]
    rows_f = [
        ["HDFS Status shows Offline in Sidebar", "NameNode/DataNode stopped", "jps", "hdfs --daemon start namenode && hdfs --daemon start datanode", "Switch sidebar radio to 'Local POSIX Storage' and proceed seamlessly."],
        ["SafeMode Error on HDFS write", "NameNode in SafeMode", "hdfs dfsadmin -safemode get", "hdfs dfsadmin -safemode leave", "Explain SafeMode block check and disable it live."],
        ["Port 8501 already in use", "Prior Streamlit process running", "lsof -i :8501", "kill -9 $(lsof -t -i:8501) then streamlit run app.py", "Run on port 8502: streamlit run app.py --server.port 8502."],
        ["MapReduce fails: Output dir exists", "Output directory already on HDFS", "hdfs dfs -ls /netscope/output", "hdfs dfs -rm -r -f /netscope/output/mr_attack_counts", "The dashboard button deletes it automatically before submitting."],
        ["Spark ingestion takes > 15 seconds", "Large uncapped dataset selected", "Check Sample Bounding", "Select '50,000 Flows' or '25,000 Flows'", "Click '🔄 Disk Cache' button to load pre-aggregated results instantly."],
        ["pytest fails with ModuleNotFoundError", "Python path issue", "Check pytest.ini", "Always run python3 -m pytest tests/ -v", "Run pytest with python3 -m prefix."],
    ]
    add_table_styled(doc, headers_f, rows_f, [1.2, 1.2, 1.4, 1.6, 1.4])

    # 8. Section G: Viva Q&A (All 24 Questions)
    add_h1(doc, "Section G: Comprehensive Exam Viva Q&A (24 Questions)")
    add_body(doc, "Review these concise, technically sound answers before entering the viva examination room:")

    viva_qa = [
        ("Q1: What is the problem statement of NetScope?",
         "Modern networks generate millions of flow records per hour, making traditional single-node analysis tools like Pandas impractical due to memory exhaustion. NetScope implements a distributed Big Data pipeline utilizing Apache Hadoop HDFS for scalable storage and Apache Spark for in-memory parallel transformations, calculating forensic traffic intelligence and explainable heuristic anomaly detection on the 2.83M flow CICIDS2017 benchmark."),

        ("Q2: Why did you choose network flow records instead of raw PCAP packets?",
         "Raw PCAP files contain full packet payloads, which require terabytes of storage and raise privacy/encryption concerns (e.g. HTTPS). Network flow records (generated by tools like CICFlowMeter) aggregate packet sequences into directional session statistics (such as duration, packet counts, inter-arrival times, and byte rates). This reduces storage by orders of magnitude while preserving essential behavioral signatures needed for threat analysis."),

        ("Q3: Why is this considered a Big Data project?",
         "It fulfills the core 'V's of Big Data: Volume (2.83M records across 79 features, ~880 MB uncompressed); Velocity (high-frequency flows requiring sub-second batch aggregation with Spark throughput > 2M flows/sec); Variety (multiple distinct attack classes alongside benign baseline); Veracity (raw data contains noise, missing labels, duplicate headers, and IEEE 754 infinity values requiring rigorous schema cleaning)."),

        ("Q4: What is the size and structure of the CICIDS2017 dataset?",
         "The dataset comprises 8 CSV files totaling 843.66 MB and 2,830,743 valid data flows. Each flow contains 79 statistical features encompassing forward/backward packet counts, byte rates, inter-arrival times (IAT), flag counters (SYN, FIN, ACK), window sizes, and ground-truth attack labels."),

        ("Q5: What is Apache Hadoop HDFS?",
         "Hadoop Distributed File System (HDFS) is a scalable, fault-tolerant distributed filesystem designed to run on commodity hardware. It breaks large files into independent blocks (typically 128 MB) and distributes them across cluster DataNodes, managed by a centralized metadata controller called the NameNode."),

        ("Q6: What is the difference between HDFS and a standard POSIX filesystem?",
         "A standard filesystem operates on a single local disk controller and cannot scale beyond that machine. HDFS operates across a distributed network of machines, replicates blocks for hardware fault tolerance, exposes a unified namespace, and co-locates computation with data (data locality) so processing tasks execute directly where blocks reside."),

        ("Q7: What are the specific roles of the NameNode and DataNode?",
         "NameNode: The master node that maintains the filesystem directory tree, file permissions, and block mapping (which blocks reside on which DataNodes). It does not store actual data payloads.\nDataNode: Worker daemons that store and retrieve the actual 128 MB data blocks on their local disks and send periodic heartbeats and block reports to the NameNode."),

        ("Q8: What is Apache Spark and why is it faster than classic MapReduce?",
         "Apache Spark is an open-source unified distributed analytics engine. It is up to 100x faster than classic MapReduce because it performs computations in-memory using Resilient Distributed Datasets (RDDs) and DataFrames. MapReduce writes intermediate shuffle state to physical disk between Map and Reduce phases, incurring heavy disk I/O; Spark retains intermediate state in RAM across transformation stages."),

        ("Q9: What is a Spark DataFrame?",
         "A Spark DataFrame is a distributed collection of data organized into named columns, conceptually equivalent to a relational database table but with distributed partitioning under the hood. It utilizes the Catalyst Optimizer to compile expressions into optimized JVM bytecode and uses the Tungsten execution engine for off-heap memory management."),

        ("Q10: What is the difference between Apache Spark and Hadoop MapReduce?",
         "Hadoop MapReduce is a rigid two-stage (Map -> Shuffle/Sort -> Reduce) batch processing framework that persists all intermediate state to disk. Apache Spark is a multi-stage DAG (Directed Acyclic Graph) computation engine that supports complex arbitrary pipelines (map, filter, join, group-by) with in-memory caching, streaming, and machine learning libraries (MLlib)."),

        ("Q11: What is Hadoop Streaming?",
         "Hadoop Streaming is a utility bundled with Hadoop that allows developers to write MapReduce jobs in any programming language (such as Python) using standard input (sys.stdin) and standard output (sys.stdout). The Hadoop framework handles reading from HDFS, feeding lines to the mapper, shuffling and sorting keys, passing sorted keys to the reducer, and writing the final output back to HDFS."),

        ("Q12: What do your mapper and reducer do in scripts/mapreduce_demo.py?",
         "Mapper: Reads CSV flow records from sys.stdin, strips header lines, extracts the label from the last column, cleans unicode artifacts, and emits 'label \\t 1'.\nReducer: Receives sorted key-value pairs from Hadoop's shuffle phase, sums the counts for each consecutive identical key, and emits the final aggregated count 'label \\t total_count'."),

        ("Q13: What is the relationship between HDFS and Spark in your project?",
         "HDFS serves as the storage layer (the Data Lake holding raw CSVs and final Parquet outputs), while Apache Spark serves as the compute layer (reading data from HDFS, executing parallel cleaning, and computing statistics)."),

        ("Q14: Why do we write processed output in Parquet format?",
         "Parquet is a columnar storage format. Unlike row-based CSV: (1) It provides high compression ratios (e.g. Snappy compression reduces file sizes by over 70%). (2) It supports column projection: if an analyst queries only 2 columns out of 79, Spark reads only those specific column chunks from disk. (3) It stores statistical metadata (min/max per block), enabling predicate pushdown to skip irrelevant row groups entirely."),

        ("Q15: How does NetScope handle missing or corrupt data?",
         "1. Drops null or empty label records.\n2. Normalizes column headers by trimming whitespace and disambiguating duplicate forward header lengths.\n3. Cleans corrupt unicode characters in web attack labels.\n4. Detects IEEE 754 Infinity, -Infinity, and NaN in rate columns (Flow Bytes/s, Flow Packets/s) caused by zero-duration flows and imputes them to 0.0."),

        ("Q16: How are attack labels normalized?",
         "Raw web attack labels contain corrupted byte sequences like 'Web Attack \\ufffd XSS'. NetScope's regex cleaner normalizes these into standard categories (Web Attack - XSS, Web Attack - Brute Force, Web Attack - Sql Injection), strips whitespace, and creates a binary indicator column Is_Malicious (0 for BENIGN, 1 for attack)."),

        ("Q17: How does NetScope's rule-based anomaly detection work?",
         "It applies transparent, explainable multi-factor heuristics based on observable traffic patterns: Volumetric Burst Rule (Flow Bytes/s > 1,000,000); Packet Velocity Rule (Flow Packets/s > 50,000); Forward Flood Rule (Total Fwd Packets > 500); Rapid SYN Flood Pattern (SYN Flag Count >= 1 and Flow Duration < 50 µs). Each flagged record is tagged with an explainable reason string."),

        ("Q18: How do you prevent target leakage in anomaly detection?",
         "Target leakage occurs if a model or rule uses the ground-truth target variable to make predictions. In NetScope, the heuristic rules inspect only statistical flow features (bytes, packets, duration, flags). The ground truth label Label is strictly isolated and used solely during post-prediction evaluation to compute the Confusion Matrix, Precision, Recall, and F1-score."),

        ("Q19: What does local[*] mean in Spark?",
         "It instructs Spark to run locally in a single JVM without a cluster manager, utilizing all available logical CPU cores on the host machine as worker execution threads (e.g., 8 threads on an 8-core Apple Silicon chip)."),

        ("Q20: Is your Hadoop setup a physical multi-node cluster?",
         "No, it is configured in pseudo-distributed mode on local hardware. The NameNode, DataNode, and SecondaryNameNode run as separate JVM processes communicating over loopback sockets (hdfs://localhost:9000), using replication factor 1. This fully verifies the distributed HDFS protocol, block storage, and client APIs without requiring multiple physical servers."),

        ("Q21: What are the main limitations of this project?",
         "1. It performs historical offline batch analytics on completed network flows, not inline real-time packet dropping (like a Snort/Suricata firewall).\n2. The pseudo-distributed setup uses a single DataNode, so it cannot demonstrate multi-machine hardware failover.\n3. Heuristic anomaly thresholds require domain calibration and can yield false positives during legitimate high-throughput transfers."),

        ("Q22: How could NetScope be extended for enterprise production?",
         "1. Ingest live network flows via Apache Kafka into Spark Structured Streaming for continuous sliding-window analytics.\n2. Deploy on a multi-node Kubernetes or YARN cluster on cloud object storage (AWS S3 / Azure ADLS / HDFS).\n3. Feed anomalous flow alerts into an automated SIEM/SOAR system (such as Splunk or Elastic Security) to trigger firewall rules."),

        ("Q23: How do you verify that your output counts are accurate?",
         "We cross-verify output across three independent mechanisms: (1) Direct command-line MapReduce aggregation via hadoop jar on HDFS data. (2) PySpark distributed DataFrame groupBy('Label').count(). (3) Automated unit test assertions in tests/test_analytics.py. All three methods yield identical results (e.g. 128,027 DDoS flows and 97,718 Benign flows in the DDoS dataset)."),

        ("Q24: How does NetScope demonstrate distributed storage and processing?",
         "Distributed Storage: Ingesting 884 MB of data into HDFS blocks across /netscope/input and writing Parquet back to /netscope/output.\nDistributed Processing: Executing PySpark partition transformations across worker threads and running Hadoop Streaming MapReduce jobs with mapper, shuffle/sort, and reducer stages."),
    ]

    for q, a in viva_qa:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(8)
        p_q.paragraph_format.space_after = Pt(2)
        p_q.paragraph_format.keep_with_next = True
        r_q = p_q.add_run(q)
        r_q.font.bold = True
        r_q.font.size = Pt(10)
        r_q.font.color.rgb = COLOR_NAVY

        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_after = Pt(4)
        p_a.paragraph_format.line_spacing = 1.15
        r_a = p_a.add_run(a)
        r_a.font.size = Pt(9.5)
        r_a.font.color.rgb = COLOR_DARK

    # 9. Section H: Printable Checklists & Screenshots Guide
    add_h1(doc, "Section H: Printable Demo Checklists & Screenshot Guide")

    add_h2(doc, "H.1 Pre-Demo Preparation Checklist (T-15 Minutes)")
    add_bullet(doc, "Terminal open at /Users/ishan/bda-mp.", "[ ] ")
    add_bullet(doc, "Python version verified (>= 3.10) and Java OpenJDK 17 verified.", "[ ] ")
    add_bullet(doc, "Hadoop JVM processes verified via jps (NameNode, DataNode active).", "[ ] ")
    add_bullet(doc, "SafeMode verified OFF (hdfs dfsadmin -safemode leave).", "[ ] ")
    add_bullet(doc, "HDFS input dataset verified (hdfs dfs -ls /netscope/input shows 8 CSVs).", "[ ] ")
    add_bullet(doc, "Streamlit dashboard running at http://localhost:8501.", "[ ] ")
    add_bullet(doc, "Browser window open in full-screen mode showing Executive Overview.", "[ ] ")

    add_h2(doc, "H.2 Live Demo Execution Checklist (During Presentation)")
    add_bullet(doc, "State opening problem statement (1 minute).", "[ ] ")
    add_bullet(doc, "Show Executive Overview KPIs and Donut chart.", "[ ] ")
    add_bullet(doc, "Show sidebar storage toggle and HDFS Online green badge.", "[ ] ")
    add_bullet(doc, "Run terminal command: hdfs dfs -ls -h /netscope/input.", "[ ] ")
    add_bullet(doc, "Click '⚡ Run Spark' and show sub-second execution on DDoS file.", "[ ] ")
    add_bullet(doc, "Show Traffic Analysis Tab: Port 80 HTTP spike (DDoS signature).", "[ ] ")
    add_bullet(doc, "Show Anomaly Explorer Tab: 2x2 Confusion Matrix and ground-truth isolation.", "[ ] ")
    add_bullet(doc, "Click '🚀 Execute Hadoop MapReduce on HDFS' and display aggregated counts.", "[ ] ")
    add_bullet(doc, "Show Snappy Parquet file on HDFS (/netscope/output/cleaned_parquet).", "[ ] ")
    add_bullet(doc, "Run automated test suite: python3 -m pytest tests/ -v (13 passed).", "[ ] ")

    add_h2(doc, "H.3 Screenshot Capture Guide for Lab Project Submission Dossier")
    add_body(doc, "Capture these 5 screenshots directly from your screen for inclusion in your final submission report:")
    add_bullet(doc, "Capture http://localhost:8501 showing top status strip, 4 KPI cards, and Donut/Bar charts.", "Screenshot 1 — Executive Overview: ")
    add_bullet(doc, "Capture Tab 6 showing ONLINE & ACTIVE badge, NameNode URI hdfs://localhost:9000, and 1 Live DataNode.", "Screenshot 2 — HDFS Cluster Status: ")
    add_bullet(doc, "Capture Tab 6 after clicking 'Execute Hadoop MapReduce on HDFS' showing the reduced output table.", "Screenshot 3 — Live MapReduce Output: ")
    add_bullet(doc, "Capture Tab 4 showing 2x2 Heatmap, precision/recall tiles, and flagged anomaly table.", "Screenshot 4 — Anomaly Explorer Confusion Matrix: ")
    add_bullet(doc, "Capture terminal running 'jps', 'hdfs dfs -ls /netscope/input', and 'pytest tests/ -v'.", "Screenshot 5 — Terminal Verification: ")

    # Save document
    doc.save(str(DOCX_OUTPUT))
    print(f"[+] Successfully generated Word playbook at: {DOCX_OUTPUT}")


if __name__ == "__main__":
    generate_playbook()
