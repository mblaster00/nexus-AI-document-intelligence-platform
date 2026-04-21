# Nexus

**AI-powered document intelligence platform built production-grade on Kubernetes and GCP.**

Nexus ingests documents (PDFs, reports, emails), runs them through a from-scratch RAG pipeline to extract structured meaning, and routes the output to downstream actions all observable end-to-end through distributed tracing, metrics, and logs.

[![CI](https://github.com/mblaster00/nexus-AI-document-intelligence-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mblaster00/nexus-AI-document-intelligence-platform/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

A document enters the ingestion API. It is queued, picked up by an async worker, parsed, chunked, and embedded into a vector store. An LLM extracts structured data from the most relevant chunks. A router decides the downstream action — Slack notification, Cloud Storage, webhook, or escalation based on content and confidence. Every step emits traces, metrics, and logs to a full observability stack.

```
Ingestion API → Redis Streams → Processing Worker
                                      ↓
                               RAG Pipeline (chunk → embed → retrieve)
                                      ↓
                         Qdrant ←→ LLM Router (gpt-4o-mini)
                                      ↓
                               Action Router
                                      ↓
                     Slack · GCS · Webhook · Escalation
                                      ↓
              OTel Collector → Prometheus → Grafana · Loki · Tempo
```

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| API | FastAPI (Python 3.12) | Async-native, typed, fast to iterate |
| Queue | Redis Streams | Async workers with consumer groups, no extra broker |
| Vector store | Qdrant (self-hosted) | Full operational control, clean API, runs in Kubernetes |
| Embeddings | `text-embedding-3-small` | Cost-efficient, strong retrieval quality |
| LLM | `gpt-4o-mini` | Structured extraction via function calling |
| Database | PostgreSQL (Cloud SQL) | Document metadata, job state, audit trail |
| Object storage | GCS | Raw document archive |
| Orchestration | Kubernetes / GKE Autopilot | Production workload management |
| Infrastructure | Terraform | Reproducible GCP provisioning |
| Observability | OTel + Prometheus + Grafana + Loki + Tempo | Full three-pillar stack |

---

## Architecture decisions

**Three services over a monolith.** Ingestion, processing, and routing are separate deployments. This surfaces real distributed systems problems early like job replay, backpressure, partial failure rather than deferring them to a refactor.

**Redis Streams over Kafka.** Same consumer group semantics, acknowledgment, and replay capability with zero additional infrastructure at this scale.

**Self-hosted Qdrant over managed vector services.** Forces operational understanding of the vector store: StatefulSet, persistent volumes, resource limits, backup strategy.

**GCP Workload Identity over static credentials.** No IAM keys in pods. Each Kubernetes service account is bound to a GCP service account with least-privilege roles. Credentials rotate automatically.

**Provider-agnostic storage and database modules.** Terraform modules for GCS and Cloud SQL expose provider-agnostic interfaces, making the architecture portable to AWS or Azure without rewriting application code.

---

## Observability

Three signals, three questions. Metrics tell you something is wrong. Traces tell you where. Logs tell you what happened.

Every service is instrumented with the OpenTelemetry Python SDK. Spans wrap LLM calls, embedding generation, queue consumption, and downstream action execution. Trace context propagates across service boundaries using W3C Trace Context headers.

The Grafana dashboard tracks:

- Document ingestion rate and end-to-end processing duration
- Embedding latency p50 / p99
- LLM call latency p50 / p99 and token consumption rate
- Queue depth (backpressure indicator)
- Error rate per service

---

## Running locally

**Prerequisites:** Docker Desktop, Python 3.12, `make`, OpenAI API key.

```bash
git clone https://github.com/yourname/nexus.git
cd nexus

cp .env.example .env
# Add your OPENAI_API_KEY to .env

make up               # Start all application services
make observability-up # Start Prometheus, Grafana, Loki, Tempo
make seed             # Ingest sample documents
```

Grafana is available at `http://localhost:3000` (admin / admin).
The ingestion API is available at `http://localhost:8000/docs`.

**Common targets**

```
make up                 Start application services
make down               Stop everything
make observability-up   Start the observability stack
make logs svc=worker    Tail a specific service
make test               Run unit and integration tests
make lint               ruff + mypy
make seed               Ingest sample documents
make k8s-apply          Apply Kubernetes manifests
```

---

## Deploying to GKE

Infrastructure is fully managed by Terraform. A single `terraform apply` provisions the VPC, GKE Autopilot cluster, Cloud SQL instance, GCS bucket, Artifact Registry, and IAM bindings.

```bash
cd infrastructure/terraform/environments/prod
terraform init
terraform plan
terraform apply
```

Workload Identity is configured per service. No static credentials are required in the cluster.

---

## Repository structure

```
nexus/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── LEARNING.md
├── Makefile
├── docker-compose.yml
├── data/
│   └── samples/          ← your test PDFs go here
└── services/
    └── ingestion-api/    ← the only service we are building right now
```

---

## Status

| Phase | Description | Status |
|---|---|---|
| 1 | Local foundations — Docker, Compose, FastAPI, PostgreSQL | Complete |
| 2 | RAG core — chunking, embeddings, Qdrant, Redis Streams | In progress |
| 3 | Kubernetes migration — namespaces, probes, persistent volumes | Planned |
| 4 | Observability — OTel instrumentation, Grafana dashboards | Planned |
| 5 | GKE deployment — Terraform, Workload Identity, TLS ingress | Planned |
| 6 | Advanced AI — RAGAS evaluation, fine-tuning, agentic routing | Planned |

---

## License

MIT