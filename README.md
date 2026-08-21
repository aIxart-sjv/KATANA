# KATANA

> **Kernel Anomaly Tracking, Analysis & Neural Assistant**

KATANA is an AI-powered Linux security monitoring and behavioral anomaly detection system. It observes host activity, learns normal behavior, detects deviations using machine learning, analyzes suspicious behavior, and presents the results through a live web dashboard.

---

# Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running KATANA](#running-katana)
- [Baseline Training](#baseline-training)
- [How KATANA Works](#how-katana-works)
- [Machine Learning and Detection](#machine-learning-and-detection)
- [Threat Analysis](#threat-analysis)
- [Dashboard and API](#dashboard-and-api)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

---

# Overview

Traditional security systems often depend heavily on known signatures and predefined rules. KATANA also uses a behavioral approach.

Instead of asking only:

> Does this process match a known malicious signature?

KATANA asks:

> Is this behavior unusual compared with what is normal for this host?

The complete concept is:

```text
OBSERVE
   |
   v
LEARN
   |
   v
MONITOR
   |
   v
DETECT
   |
   v
ANALYZE
   |
   v
EXPLAIN
   |
   v
INVESTIGATE
```

KATANA monitors supported Linux host activity, converts observations into behavioral features, learns a baseline, scores new behavior, compares that score against a threshold, and sends confirmed anomalies to a threat-analysis pipeline.

---

# Architecture

```text
+-------------------------+
|        FRONTEND         |
|                         |
| Next.js / React         |
| Live Security Dashboard |
+------------+------------+
             |
             | HTTP / JSON
             v
+------------+------------+
|         BACKEND         |
|                         |
| FastAPI                  |
| Event Pipeline           |
| Feature Processing       |
| ML Anomaly Detection     |
| Threat Engine            |
| Runtime State            |
+------------+------------+
             |
             v
+------------+------------+
|       LINUX HOST        |
|                         |
| Processes               |
| Filesystem              |
| Network                 |
| Kernel-level events     |
+-------------------------+
```

High-level pipeline:

```text
Linux Host Activity
        |
        v
Event Collectors
        |
        v
Event Bus
        |
        v
Feature Extraction
        |
        v
Baseline Learning / ML Model
        |
        v
Anomaly Score
        |
   +----+-----+
   |          |
Normal     Anomalous
   |          |
   v          v
Dashboard  Threat Engine
               |
               v
           Evidence
               |
               v
     Investigation Commands
               |
               v
        Incident Dashboard
```

---

# Core Features

KATANA currently provides:

- Linux host behavioral monitoring.
- Process activity monitoring.
- Resource usage features.
- Filesystem activity features.
- Network-related activity features.
- Support for kernel-related event features where available.
- Normal behavioral baseline learning.
- Machine-learning anomaly detection.
- Threshold-based anomaly decisions.
- Threat severity classification.
- Incident tracking.
- Human-readable evidence.
- Investigation recommendations and commands.
- Live FastAPI backend.
- Live Next.js dashboard.
- Frontend dashboard polling.
- Normal workload generation for baseline training.

---

# Requirements

KATANA is designed primarily for Linux.

Recommended environment:

- Linux
- Python 3.11 or newer
- Node.js
- npm
- Git
- curl
- A modern web browser
- Internet access for dependency installation

The project was developed in an Arch Linux environment. Other distributions may work, but package commands may differ.

---

# Before Cloning the Repository

Install the required tools.

## Arch Linux

```bash
sudo pacman -S git python nodejs npm curl
```

Verify:

```bash
git --version
python --version
node --version
npm --version
curl --version
```

Python virtual environments are also required. Verify:

```bash
python -m venv --help
```

---

# Installation

## Clone the Repository

Choose a location:

```bash
cd ~/Documents/Projects
```

Clone:

```bash
git clone https://github.com/aIxart-sjv/KATANA.git
```

Enter the repository:

```bash
cd KATANA
```

Expected top-level layout:

```text
KATANA/
├── backend/
├── frontend/
├── training/
└── README.md
```

---

# Backend Setup

Enter the backend:

```bash
cd ~/Documents/Projects/KATANA/backend
```

Create a virtual environment:

## Install uv

KATANA uses **uv** to manage the Python environment and install Python dependencies.

### Universal Installation Method

The recommended method works on most Linux distributions:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
uv venv --python 3.14
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The virtual environment should remain activated while running the backend.

---

# Frontend Setup

Open another terminal:

```bash
cd ~/Documents/Projects/KATANA/frontend
```

Install dependencies:

```bash
npm install
```

Create `.env.local`:

```bash
nano .env.local
```

Add:

```env
NEXT_PUBLIC_KATANA_API_URL=http://127.0.0.1:8000
```

This tells the frontend where the backend API is running.

---

# Running KATANA

Use separate terminals.

Recommended:

```text
Terminal 1 -> Backend
Terminal 2 -> Frontend
Terminal 3 -> Normal workload generator
```

## Terminal 1 — Backend

```bash
cd ~/Documents/Projects/KATANA/backend
source .venv/bin/activate
sudo .venv/bin/uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

The dashboard API is:

```text
http://127.0.0.1:8000/api/dashboard
```

Test it:

```bash
curl http://127.0.0.1:8000/api/dashboard
```

A successful response returns JSON containing:

```text
system
ml
events
incidents
analysis
```

## Terminal 2 — Frontend

```bash
cd ~/Documents/Projects/KATANA/frontend
npm run dev
```

Open the URL shown by Next.js, typically:

```text
http://localhost:3000
```

## Terminal 3 — Training Workload

KATANA includes:

```text
training/normal_workload.sh
```

Run:

```bash
cd ~/Documents/Projects/KATANA/training
chmod +x normal_workload.sh
./normal_workload.sh
```

---

# Baseline Training

When KATANA starts, the ML system initially enters:

```text
LEARNING
```

During this phase it collects normal behavioral samples.

Example:

```text
Baseline Samples: 3 / 60
Status: LEARNING
```

When the required baseline is complete:

```text
Baseline Samples: 60 / 60
Status: MONITORING
```

KATANA then evaluates new behavior against the learned baseline.

## Why Normal Workload Matters

Training on a completely idle machine is a bad baseline. If the model learns that almost no activity is normal, ordinary usage can later appear suspicious.

The workload generator produces normal user-like activity such as:

- Opening terminal processes.
- Running normal commands.
- Opening applications.
- Creating ordinary process activity.
- Performing ordinary filesystem activity.
- Closing applications and processes.

The workload should not be an artificial explosion where everything starts simultaneously. A realistic sequence is better:

```text
 Run command
      |
      v
     Wait
      |
      v
Open application
      |
      v
     Wait
      |
      v
Run another command
      |
      v
     Wait
      |
      v
 Close process
```

Some overlap is normal, but the goal is realistic host behavior.

---

# How KATANA Works

## 1. Host Activity

The Linux machine continuously generates activity:

- Processes start and terminate.
- Files are accessed or modified.
- Applications consume CPU and memory.
- Network connections occur.
- Services may restart.
- Kernel-related events may occur.

## 2. Event Collection

Collectors observe supported activity and create KATANA events:

```text
System Activity
      |
      v
Collector
      |
      v
KATANA Event
```

## 3. Event Bus

Events move through an internal event pipeline:

```text
Collector
   |
   v
Event Bus
   |
   +--> Dashboard State
   |
   +--> Feature Processing
   |
   +--> Other Subscribers
```

This keeps components modular.

## 4. Feature Extraction

Raw events are converted into measurable behavioral features.

Examples include:

```text
process_creation_rate
process_termination_rate
unique_process_count

average_cpu
maximum_cpu

average_memory
maximum_memory

external_connections
failed_logins
privilege_escalations

filesystem_modifications
service_restarts

kernel_exec_count
kernel_connect_count
kernel_open_count
kernel_unlink_count
kernel_setuid_count
kernel_ptrace_count
```

The ML system evaluates a feature vector rather than raw events directly.

---

# Machine Learning and Detection

The basic process is:

```text
Learn normal behavior
        |
        v
Evaluate new behavior
        |
        v
Calculate anomaly score
        |
        v
Compare with threshold
```

KATANA uses anomaly scoring semantics where the decision is based on the relationship between the score and threshold:

```text
score <= threshold
```

means:

```text
ANOMALY
```

while:

```text
score > threshold
```

means:

```text
NORMAL
```

Example normal result:

```text
Score:      -0.457
Threshold:  -0.502

-0.457 > -0.502
Result: Normal
```

Example anomalous result:

```text
Score:      -0.583
Threshold:  -0.502

-0.583 <= -0.502
Result: Anomaly
```

The actual numerical values depend on the trained model and threshold calibration.

---

# Threat Analysis

When an anomaly is detected, KATANA sends it to the threat engine.

The threat engine evaluates context such as:

- Anomaly score.
- Behavioral features.
- Process activity.
- Filesystem activity.
- Triggered signals.

The resulting incident can contain:

```text
Severity
Confidence
Evidence
Triggered Features
Recommended Actions
Investigation Commands
```

Example:

```text
ANOMALY DETECTED

Severity: High
Confidence: 0.58

Evidence:
High process creation rate

Recommendation:
Inspect recently spawned processes.
```

KATANA therefore does not only return a raw ML score. It also attempts to explain why the behavior deserves investigation.

---

# Dashboard and API

The frontend communicates with:

```text
GET /api/dashboard
```

The full local request is:

```text
http://127.0.0.1:8000/api/dashboard
```

The response contains data similar to:

```json
{
  "system": {
    "pipeline_running": true,
    "started_at": "..."
  },
  "ml": {
    "status": "monitoring",
    "baseline_samples": 60,
    "baseline_required": 60,
    "latest_anomaly_score": -0.457,
    "threshold": -0.501
  },
  "events": {
    "total": 9334014,
    "last_event_at": "..."
  },
  "incidents": {
    "total": 12,
    "current_severity": "High",
    "current_confidence": 0.58,
    "recent": []
  },
  "analysis": {
    "latest_ai_analysis": null,
    "latest_recommendations": []
  }
}
```

## Frontend Polling

The dashboard refreshes data every:

```text
2000 ms
```

or:

```text
2 seconds
```

Conceptually:

```text
Frontend
   |
   | every 2 seconds
   v
/api/dashboard
   |
   v
Latest Runtime State
```

The frontend can also maintain a short local history of values it receives during repeated polling. This means a live graph can be created from already received values without adding a separate backend history endpoint, provided the graph only needs data from the current frontend session.

---

# Dashboard Runtime States

## Pipeline Running

```text
pipeline_running = true
```

means the monitoring pipeline is active.

## Learning

```text
status = learning
```

means KATANA is still collecting the behavioral baseline.

## Monitoring

```text
status = monitoring
```

means the baseline has completed and new observations are being evaluated.

## Incidents

When a confirmed anomaly is processed:

```text
incidents.total
```

increases.

The dashboard can show:

- Severity.
- Confidence.
- Recent incidents.
- Evidence.
- Recommendations.
- Investigation commands.

---

# Project Structure

```text
KATANA/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── explainability/
│   │   ├── ml/
│   │   ├── pipeline/
│   │   ├── state/
│   │   ├── threat_engine/
│   │   └── ...
│   ├── data/
│   ├── tests/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── public/
│   ├── .env.local
│   └── package.json
│
├── training/
│   └── normal_workload.sh
│
└── README.md
```

## Important Backend Areas

### `app/api`

Backend API routes, including the dashboard route.

### `app/state`

Stores dashboard-facing runtime information:

- Pipeline state.
- Start time.
- ML state.
- Baseline progress.
- Latest anomaly score.
- Threshold.
- Event totals.
- Incident totals.
- Current severity.
- Current confidence.
- Recent incidents.
- Analysis.
- Investigation recommendations.

This component stores state; it does not itself perform anomaly detection.

### `app/ml`

Machine-learning functionality including baseline learning, scoring, thresholds, validation, and feature-related processing.

### `app/pipeline`

Main orchestration logic:

```text
Receive Features
      |
      v
Learning?
  /       \
Yes        No
 |          |
 v          v
Collect    Score
Baseline     |
             v
      Compare Threshold
         /         \
      Normal      Anomaly
```

### `app/threat_engine`

Interprets anomalies and produces severity, confidence, evidence, and recommendations.

### `app/explainability`

Provides human-readable context where analysis is available.

## Important Frontend Areas

### `lib/katana-api.ts`

Contains the API client and dashboard response types.

### `hooks/use-katana-dashboard.ts`

Fetches dashboard data repeatedly and handles:

1. Requesting the dashboard.
2. Storing the latest response.
3. Reporting connection errors.
4. Refreshing every configured interval.

### `components/dashboard`

Contains the security dashboard interface.

The interface presents the main overview while also organizing detailed information into dedicated sections rather than putting the entire application into one massive screen.

---

# Testing the Backend API

Basic test:

```bash
curl http://127.0.0.1:8000/api/dashboard
```

CORS test:

```bash
curl -i   -H "Origin: http://localhost:3000"   http://127.0.0.1:8000/api/dashboard
```

A successful CORS response should include an allowed origin similar to:

```text
access-control-allow-origin: http://localhost:3000
```

---

# Troubleshooting

## Dashboard Shows No Values

Check whether the backend is running:

```bash
curl http://127.0.0.1:8000/api/dashboard
```

If JSON is returned, verify:

```bash
cat frontend/.env.local
```

Expected:

```env
NEXT_PUBLIC_KATANA_API_URL=http://127.0.0.1:8000
```

Restart the frontend after changing environment variables.

## Dashboard Is Still Learning

If:

```text
baseline_samples < baseline_required
```

then KATANA is still learning.

Example:

```text
3 / 60
```

Run normal activity and allow more samples to be collected.

## `normal_workload.sh` Permission Denied

```bash
chmod +x normal_workload.sh
./normal_workload.sh
```

## Python Module Errors

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

## Frontend Dependency Problems

From the frontend:

```bash
rm -rf node_modules
npm install
npm run dev
```

---

# Stopping KATANA

Stop the backend or frontend process with:

```text
Ctrl + C
```

Leave the Python virtual environment with:

```bash
deactivate
```

---

# Security Notes

KATANA is an AI-assisted behavioral monitoring system. It is not a complete replacement for enterprise security infrastructure.

Important limitations:

- Baseline quality depends on the training environment.
- Activity absent during training may initially appear unusual.
- An anomaly does not automatically prove malicious intent.
- False positives are possible.
- Missed anomalies are also possible.
- Investigation commands should be reviewed before execution.

The correct workflow is:

```text
Anomaly
   |
   v
Investigate
   |
   v
Collect Evidence
   |
   v
Determine Whether Behavior Is Malicious
```

Not:

```text
Anomaly = Automatically Confirmed Attack
```

---

# Current Project Status

KATANA currently provides an end-to-end pipeline:

```text
Linux Activity
      |
      v
Collectors
      |
      v
Events
      |
      v
Features
      |
      v
ML Baseline / Monitoring
      |
      v
Anomaly Detection
      |
      v
Threat Analysis
      |
      v
Incident State
      |
      v
FastAPI
      |
      v
Next.js Dashboard
```

The implemented workflow includes:

- Backend and frontend communication.
- Live dashboard updates.
- Runtime state tracking.
- Event counting.
- Baseline learning.
- Monitoring mode.
- Anomaly scoring.
- Threshold comparison.
- Threat classification.
- Incident tracking.
- Evidence generation.
- Investigation recommendations.
- Normal workload generation for baseline training.

---

# Quick Start

## Install tools

```bash
sudo pacman -S git python nodejs npm curl
```

## Clone

```bash
git clone <YOUR_KATANA_REPOSITORY_URL>
cd KATANA
```

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Frontend

Open another terminal:

```bash
cd frontend
npm install
```

Create `.env.local`:

```env
NEXT_PUBLIC_KATANA_API_URL=http://127.0.0.1:8000
```

Run:

```bash
npm run dev
```

## Training Workload

Open another terminal:

```bash
cd training
chmod +x normal_workload.sh
./normal_workload.sh
```

Open:

```text
http://localhost:3000
```

---

# Final Concept

KATANA is not just a dashboard, and it is not just an ML model.

It is an integrated behavioral security pipeline that continuously observes the Linux host, learns normal activity, detects deviations, analyzes suspicious behavior, and gives the user evidence and investigation guidance.

**KATANA — Kernel Anomaly Tracking, Analysis & Neural Assistant**
