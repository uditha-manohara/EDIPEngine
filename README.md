# Edge Deterministic Ingestion Protocol (EDIP)

[![PyPI version](https://img.shields.io/pypi/v/edip)](https://pypi.org/project/edip/)
[![Python versions](https://img.shields.io/pypi/pyversions/edip)](https://pypi.org/project/edip/)
[![License: Proprietary](https://img.shields.io/badge/license-Proprietary-red)](https://neziora.com)
[![Platform: Windows x64](https://img.shields.io/badge/platform-Windows%20x64-blue)](https://pypi.org/project/edip/)

**Official Links:** [PyPI](https://pypi.org/project/edip/) · [Neziora](https://neziora.com) · [Documentation](https://neziora.com) · [Author: Uditha Manohara Prasad](https://udithamanohara.dev) · [LinkedIn](https://www.linkedin.com/in/uditha-manohara/)

> **Autonomous, air-gapped document ingestion middleware that disciplines probabilistic Small Language Models (SLMs) using relational database constraint reflection and tri-folder isolation.**

**Keywords:** Air-Gapped AI · Edge AI · Local SLM Inference · Deterministic Data Ingestion · Closed-Loop Constraint Reflection · SQLite Schema Introspection · Document Intelligence · AI Engineering · Data Integrity · Dead-Letter Queue (DLQ) · Proprietary Software · Offline AI Middleware

---

## Executive Summary

Enterprise document extraction pipelines face reliability challenges when deploying generative AI at the edge. Small Language Models (SLMs), particularly locally deployed models with 1B–3B parameters, may hallucinate identifiers, produce incorrectly typed values, or introduce relational inconsistencies. Conventional pipelines may fail during database insertion or accept invalid extracted data if appropriate validation is absent.

The **Edge Deterministic Ingestion Protocol (EDIP)** uses relational database integrity constraints—including Primary Keys, Foreign Keys, CHECK constraints, and NOT NULL rules—as part of a closed-loop error-reflection process.

Operating with locally hosted models through Ollama, EDIP is designed to support offline document ingestion without requiring cloud-based inference APIs during runtime. Database constraints provide structural validation at the transaction boundary, while the ingestion engine uses constraint feedback to guide extraction retries.

EDIP is intended to improve the reliability of local document-processing workflows while preserving control over sensitive documents and their extracted data.

---

## Architectural Highlights

```text
┌────────────────────────────┐
│    ./Inbound_Invoices      │
│  Monitored Entry Directory │
│      Watchdog Service      │
└─────────────┬──────────────┘
              │
              ▼
       ┌───────────────┐
       │  EDIP Engine  │
       │     Loop      │
       └───────┬───────┘
               │
               ├─ Dynamic Schema Introspection
               │  (SQLite PRAGMA inspection)
               │
               ├─ Structured Extraction
               │  (Local SLM via Ollama)
               │
               ├─ Transactional Validation
               │  (SQLite constraints)
               │
               └─ Error-Reflection Loop
                  (Runtime constraint feedback)
               │
        ┌──────┴─────────────────────────┐
        │                                │
        ▼                                ▼
┌──────────────────────┐    ┌──────────────────────────┐
│ SUCCESS / DEDUPLICATE│    │ CONSTRAINT FAILURE /     │
│                      │    │ RETRIES EXHAUSTED        │
└──────────┬───────────┘    └────────────┬─────────────┘
           │                             │
           ▼                             ▼
┌──────────────────────┐    ┌──────────────────────────┐
│ ./Processed_Archive  │    │ ./Quarantine_Documents   │
│                      │    │ Human Review Queue       │
└──────────────────────┘    └────────────┬─────────────┘
                                         │
                                         ▼
                              ┌────────────────────────┐
                              │ Dead-Letter Queue      │
                              │ audit_status:          │
                              │ PENDING_HUMAN_AUDIT    │
                              └────────────────────────┘
```

### Key Capabilities

- **Local-First Operation**: Supports local inference using quantized models such as `llama3.2:1b` and `qwen2.5:1.5b` through Ollama. Offline operation depends on the model and runtime being available locally.
- **Dynamic Schema Introspection**: Inspects SQLite tables, column types, relational dependencies, and foreign-key references using native SQLite metadata commands.
- **Tri-Folder Document Routing**:
  - `Inbound_Invoices`: Monitored entry directory.
  - `Processed_Archive`: Archives successfully processed or deduplicated documents.
  - `Quarantine_Documents`: Isolates invalid or unresolvable documents for manual review.
- **Dead-Letter Queue (DLQ) Auditing**: Stores relevant payloads, raw text, processing attempts, and failure reasons for administrative review.
- **SQLite WAL Support**: Uses SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL`) to support concurrent readers while maintaining SQLite's transactional write behavior.
- **Constraint-Guided Extraction**: Uses database constraint feedback to guide subsequent extraction attempts.

---

## Installation

Install the package from PyPI:

```bash
pip install edip
```

### Prerequisites

- Python 3.9 or newer
- SQLite
- Ollama installed and running
- A supported local language model
- PDF extraction dependency supported by the installed EDIP version

Pull a supported model:

```bash
ollama pull llama3.2:1b
```

Start Ollama before running EDIP.

---

## Quickstart & Usage

### 1. Initialize the Engine

```python
from edip import EDIPEngine, AmbientWatcher

# Configure the engine targeting your database
engine = EDIPEngine(
    db_path="enterprise_erp.db",
    target_tables=["Invoices"],
    model="llama3.2:1b",
    api_url="http://localhost:11434/api/generate",
    max_retries=3,
    archive_dir="./Processed_Archive",
    quarantine_dir="./Quarantine_Documents"
)
```

### 2. Process Inbound Documents Headlessly

```python
# Ingest a single document directly
success, result = engine.ingest_document(
    "path/to/invoice.pdf"
)

if success:
    print(f"Ingested successfully: {result['payload']}")
    print(f"Archived to: {result['archived_path']}")
else:
    print(f"Quarantined for audit: {result['quarantined_path']}")
    print(f"DLQ Reference ID: #{result['quarantine_id']}")
```

### 3. Continuous Directory Monitoring

```python
def audit_callback(file_path, success, info):
    status = "SUCCESS" if success else "QUARANTINED"

    print(
        f"[{status}] File: {file_path} | Details: {info}"
    )


# Launch continuous directory monitoring
watcher = AmbientWatcher(
    engine=engine,
    watch_dir="./Inbound_Invoices",
    callback=audit_callback
)

watcher.start(blocking=True)
```

---

## Adversarial Stress-Test Scenarios

The following scenarios are included in EDIP's adversarial test suite. The final outcomes should be confirmed by running the tests against the target database, model, and runtime configuration.

| Scenario | Adversarial Challenge | Intended EDIP Behavior | Expected Final State |
|---|---|---|---|
| **Legacy ID Migration** | Invoice contains deprecated vendor code (`9999`) while referencing legacy supplier ID (`101`). | Constraint feedback guides extraction toward a registered supplier ID. | Archived if corrected to `supplier_id: 101` |
| **Messy Layout / Unstructured Data** | Amount is written in descriptive prose rather than tabular columns. | Extracts and validates the amount against the target column's type and constraints. | Archived if valid (`total_amount: 5250.5`) |
| **Prompt Injection Attempt** | Document contains malicious instructions such as `"DROP TABLE INVOICES"`. | Extracted values are subject to validation and parameterized SQL execution. | Quarantined if processing fails validation |
| **Duplicate Submission** | Previously processed invoice is submitted again. | UNIQUE constraint prevents insertion of a duplicate invoice number. | Archived or handled as a duplicate, according to engine behavior |
| **Unregistered Vendor** | Invoice references a supplier absent from the master table. | Foreign-key constraint rejects the invalid relationship. | Quarantined if retries are exhausted |

> **Security note:** Database constraints and parameterized SQL provide important safeguards, but they do not independently guarantee complete prompt-injection prevention. EDIP's security properties should be evaluated through testing.

---

## Intellectual Property & Authorship

The architectural design and implementation of the Edge Deterministic Ingestion Protocol (EDIP) are developed by **Uditha Manohara Prasad** and associated with **Neziora**.

### Lead Architect

**Uditha Manohara Prasad**  
*Software Engineer & AI Systems Researcher*

- **LinkedIn**: [linkedin.com/in/uditha-manohara](https://www.linkedin.com/in/uditha-manohara/)
- **X / Twitter**: [@uditha_manohara](https://x.com/uditha_manohara)
- **Instagram**: [@uditha.manohara](https://www.instagram.com/uditha.manohara/)
- **Facebook**: [facebook.com/udithamprasad](https://www.facebook.com/udithamprasad/)
- **TikTok**: [@udithamprasad](https://www.tiktok.com/@udithamprasad)
- **WhatsApp**: +94 76 182 3815

### Organization

**Neziora**  
*Technology Venture*

- **Website**: [neziora.com](https://neziora.com)
- **LinkedIn**: [linkedin.com/company/neziora](https://www.linkedin.com/company/neziora)
- **X / Twitter**: [@Neziora](https://x.com/Neziora)
- **Instagram**: [@nezioraofficial](https://www.instagram.com/nezioraofficial/)
- **Facebook**: [facebook.com/neziora](https://www.facebook.com/neziora/)
- **TikTok**: [@neziora](https://www.tiktok.com/@neziora)
- **WhatsApp**: +94 72 654 5635

---

## Citation

If you reference the EDIP methodology or architecture in technical reports, academic publications, or repositories, please cite:

```bibtex
@software{prasad2026edip,
  author       = {Uditha Manohara Prasad},
  title        = {Edge Deterministic Ingestion Protocol (EDIP): Closed-Loop Relational Constraint Reflection for Edge AI},
  year         = {2026},
  publisher    = {Neziora},
  url          = {https://pypi.org/project/edip/}
}
```

---

## License

Copyright © 2026 Neziora & Uditha Manohara Prasad. All rights reserved.

Source code distribution, binary compilation, and commercial deployment are subject to proprietary licensing terms.
