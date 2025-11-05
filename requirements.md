# 🧩 Truth-Based Content Validation & Enhancement System

### Plane-Aligned Specification for UCOP Architecture

---

## Overview

The **Truth-Based Content Validation & Enhancement System (TBCV)** operates across **five interdependent planes**, aligning with UCOP’s modular system architecture:

| Plane                   | Scope                           | Purpose                                                                                       |
| ----------------------- | ------------------------------- | --------------------------------------------------------------------------------------------- |
| **Agentic Plane**       | Validation & Enhancement Agents | Execute truth-based content analysis and rewriting using deterministic, idempotent workflows. |
| **Data Plane**          | Persistence & Caching           | Ensure data durability, state recovery, audit traceability, and high-speed cache reuse.       |
| **Orchestration Plane** | Workflow, Roles, and Execution  | Connect agentic logic with CLI/API, enforce roles, and manage distributed workloads.          |
| **Configuration Plane** | Schemas, Rules, and Stack       | Define operational, validation, and testing configurations for repeatable reliability.        |
| **Integration Plane**   | Dashboard & Human Oversight     | Provide visual review, approvals, audits, and feedback integration.                           |

All behavior in TBCV must remain **truth-aligned**, **schema-driven**, and **non-destructive** — preserving structure while ensuring content fidelity.

---

## 🧠 Agentic Plane

### Core Validation and Enhancement Logic

#### Validation Principles

* Validate content against **truth tables and rulesets** stored as JSON files, organized by family (e.g., Words, PDF, Cells, etc.).
* Detect product family automatically from **path or content hints**, with a **safe fallback** if ambiguous.
* Enforce **JSON Schema compliance** on truth tables at startup; abort early if schemas fail.
* Maintain **deterministic, idempotent** execution — repeated runs on unchanged input yield identical results.
* Validate **YAML front-matter** and **Markdown body** separately:
  * YAML: only validate **selected keys** configured per family.
  * Markdown: apply **two-stage validation** — heuristics first, LLM for overall evaluation of markdown content.
* Support **batch selection/filtering** by family, severity, or path for scalable runs.
* Operate **locally by default**, compatible with optional LLM backends.

#### Semantic & Structural Integrity

* Detect and flag statements that **defy truth** or omit required details.
* Preserve **byte-perfect structure** — shortcodes, anchors, code blocks, and front-matter delimiters.
* Use **fuzzy detection** (aliases, regex) for plugin and feature recognition.
* Validate **code snippets** by cross-checking API or plugin references.

#### Quality Gates

* Maintain ≥ **90 % owner identification accuracy**.
* Achieve full **sentence-level coverage**.
* Preserve **rewrite safety** and **structural fidelity** under all edits.

---

### Enhancement Logic

* Trigger enhancement **only after approval**, manually or in batch.
* Support **dry-run** and **write** modes with identical reports.
* Apply edits to **text only**, masking/unmasking structure for safety.
* Enforce **canonical phrasing** and house-style rules (e.g., no em-dash).
* **Insert dependency notes** idempotently at fixed policy locations.
* Respect **rewrite-ratio** and **blocked-topic** gates; refuse unsafe edits.
* Guarantee **idempotence** — re-running the enhancer makes no additional changes.
* Produce **unified diffs**, **timing logs**, and **error summaries**.
* Output identical structured reports for dry-run and write modes.

---

## 💾 Data Plane

### Persistence, Database, and Caching Layers

#### Persistence Model

* Persist **validation results**, **enhancement outcomes**, and **risk assessments** in a durable relational store.
* Record **approval states** with timestamps, actors, and reviewer comments.
* Keep **detailed run logs** (inputs, configs, timings, results, errors).
* Maintain a **complete audit log** of all dashboard and API actions.
* Provide **exportable reports** (JSON or Markdown) with diffs and KPIs.
* Integrate seamlessly into **CI/CD pipelines** for automated ingestion.

#### Caching Strategy

* Implement a **shared L2 cache** with **stable keying** for deterministic reuse.
* Preserve **content determinism**; prevent stale-cache side effects.
* Record and expose **cache hit/miss ratios** and latency metrics.
* Enable cache visibility via **metric hooks** and dashboards.

#### Performance Goals

| Metric           | Target                           |
| ---------------- | -------------------------------- |
| First-run speed  | 5–8 s / file                     |
| Warm-cache speed | 1–2 s / file                     |
| Cache hit rate   | ≥ 60 %                           |
| Throughput       | 400–600 files / hour (4 workers) |

---

## ⚙️ Orchestration Plane

### Execution, APIs, Roles, and Observability

#### CLI + API Parity

* All functions callable from **CLI or FastAPI** without changing working directory.
* Maintain **stable CLI flags**; extend via non-breaking options (`--family`, `--diff`, `--dry-run`).

#### FastAPI Endpoints

* **Validation API** — list validations, fetch diffs, query severity and risk flags.
* **Enhancement API** — approve/reject items, trigger enhancer runs, stream progress.
* **WebSockets** — real-time progress, pause/resume, checkpoint recovery.

#### Execution & Roles

* **Parallel processing** enabled for high throughput.
* **Roles**:

  * *Reviewer* — approve/reject.
  * *Operator* — run enhancer, pause/resume jobs.
  * *Auditor* — view-only, export history.
* Apply **rate limits** and **sandboxing** for LLM-intensive modules.

#### Metrics & Logging

* Track **throughput**, **latency**, **error rate**, **cache performance**, and **family distribution**.
* Integrate with **structured logging** and **performance counters** for observability.

---

## ⚙️ Configuration Plane

### Stack, Schemas, and Testing Framework

#### Stack Overview

| Category                  | Preferred Stack / Library                                             |
| ------------------------- | --------------------------------------------------------------------- |
| **API & Realtime**        | FastAPI, Uvicorn/Starlette, WebSockets                                |
| **Config & Validation**   | Pydantic + JSON Schema                                                |
| **Database & Jobs**       | SQL + migrations; Redis optional for cache/checkpoints                |
| **Parsing & Markup**      | YAML (front-matter), Markdown parser, regex, BeautifulSoup (optional) |
| **Search / Recall**       | Fuzzy matching; optional vector DB                                    |
| **Developer Experience**  | pytest (asyncio + coverage), rich/tqdm, structured logging            |
| **Performance Utilities** | tree-sitter (optional), aiofiles (async I/O)                          |

#### Validation Configuration

* Centralize **JSON Schema definitions** for all truth tables.
* Maintain **rule families** mapping to each product line.
* Validate both **YAML front-matter** and **Markdown** structures per schema.

#### Testing Goals

* Achieve **≥ 95 % coverage** including integration and performance tests.
* Required checks:

  * Rewrite-ratio enforcement
  * Mask/unmask safety
  * Schema validation
  * Deterministic idempotence

---

## 🌐 Integration Plane

### Dashboard and Human-in-the-Loop Review

#### Workflow

* **Inbox view** listing pending validations with metadata (file, family, owner score, severity, risk flags, summary).
* **Detail view**: side-by-side masked original vs proposed text with unified diff tab.
* **Batch actions**: multi-select → Approve/Reject → Run Enhancer.

#### Control & Monitoring

* Require **human checkpoint** before write (“changes planned”).
* Provide **run controls** (start, pause, resume) with real-time WebSocket updates.
* Display per-file **timings**, **status**, and **outcomes**.

#### History & Metrics

* Offer **filterable history** (date, family, actor, status).
* Export complete audit history for review.
* Dashboard **widgets**: throughput, cache rates, avg file time, error counts, recent incidents.

#### Access Control

* Enforce **role-based permissions**.
* Log every action in an **immutable audit trail**.
* Support **UI dry-run mode** for visual diff preview without writes.

---

### 🧭 Interactive Dashboard for Validation, Approval, and Enhancement Execution

#### Purpose

The interactive dashboard is the **operational control surface** of TBCV, allowing users to visualize validation outcomes, approve or reject proposed changes, and trigger enhancement runs on accepted items.

#### Core Functionalities

**1. Validation Review**

* Displays a live **Inbox queue** with:

  * File name, family, validation time, owner score, risk level, severity, and summary of proposed edits.
* Opens detailed view with **masked original vs proposed output** and unified diff visualization.
* Filter and sort by family, date, severity, or gating result.

**2. Approval Workflow**

* Actions: **Accept**, **Reject**, **Defer**.

  * Accept → moves to “Approved for Enhancement”.
  * Reject → archives with comment.
  * Defer → flags for later review.
* Batch approval supported with **multi-select**.
* All actions are **timestamped + audited**.

**3. Enhancement Execution**

* Trigger **Enhancer Run** from dashboard:

  * Single-file or batch.
  * Modes: `dry_run`, `write`, threshold override.
* Real-time **WebSocket progress stream** with per-file status, ETA, and errors.
* Enforces rewrite-ratio, blocked-topics, and dependency rules.
* Produces **unified diffs**, **validation scores**, and **structured logs**.

**4. Monitoring & Metrics**

* Real-time job progress board showing:

  * Cache use, throughput, latency, file timings.
* **Widgets** for:

  * Pending vs approved counts
  * Enhancer throughput
  * LLM usage and confidence
  * Cache hit rates

**5. History & Auditing**

* Full **history tab** with filters by actor, date, family, and action type.
* **Exportable reports** (JSON/Markdown/CSV).
* **Immutable audit log** ensures traceability of every operation.

**6. Roles & Permissions**

* **Reviewer** — view/approve/reject/defer.
* **Operator** — execute enhancer, pause/resume.
* **Auditor** — read-only with export rights.
* Backed by **UCOP Auth Layer** enforcing secure role mapping.

---

## 📊 Cross-Plane Performance & Determinism Summary

| Metric         | Target                           |
| -------------- | -------------------------------- |
| First run      | 5–8 s / file                     |
| Warm run       | 1–2 s / file                     |
| Throughput     | 400–600 files / hour (4 workers) |
| Cache hit rate | ≥ 60 %                           |
| Owner accuracy | ≥ 90 %                           |
| Test coverage  | ≥ 95 %                           |
| Rewrite safety | 100 % structure preservation     |

