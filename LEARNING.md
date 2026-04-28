# LEARNING.md : Nexus Build Journal

This file is my personal reference for why I built Nexus the way I did, what I am trying to learn at each phase, and the decisions I made along the way. It is not meant for external readers.

---

## Why This Project Exists

Nexus is intentionally over-engineered for a side project. That is the point.

Every architectural decision exists to expose me to a real production pattern — not to ship the fastest MVP. I will make mistakes in the open, read error logs, understand why a container keeps crashing, and eventually fix it. That process is the curriculum.

The system accepts documents (PDFs, emails, reports), extracts meaning using a RAG pipeline I build myself, routes them to actions based on AI decisions, and exposes the full execution trace through an observability stack I instrument myself.

No drag-and-drop. No managed AI platforms doing the heavy lifting. Everything is a service I write, containerise, deploy, and monitor.

---

## What I Am Building Toward

### AI Integration

- Building a RAG pipeline from scratch: chunking strategies, embedding models, vector similarity search
- Prompt engineering for extraction and classification tasks
- Evaluation frameworks for measuring retrieval quality
- Fine-tuning experiments on domain-specific document types (Phase 6)
- Agentic routing: letting an LLM decide which action to execute

### Observability

- Instrumenting Python services with OpenTelemetry (traces, metrics, logs)
- Understanding the difference between a metric and a trace and when each matters
- Building Grafana dashboards that reflect actual system health, not vanity numbers
- Alerting on meaningful thresholds: LLM latency p99, embedding failure rate, queue depth
- Distributed tracing across service boundaries

### Platform Engineering

- Docker: writing efficient, layered Dockerfiles; understanding build cache
- Docker Compose: local multi-service orchestration with shared networks and volumes
- Kubernetes: namespaces, deployments, services, configmaps, secrets, persistent volumes, resource limits, liveness and readiness probes
- Terraform: provisioning GKE, VPC, subnets, firewall rules, IAM, Cloud SQL
- Networking: ingress controllers, DNS, TLS termination, internal service discovery
- Linux: signals in containers, file permissions, process management, ulimits
- Security: secret management, RBAC on Kubernetes, network policies, least-privilege service accounts

---

## Phase Notes

### Phase 1 — Local Foundations

Goal: one working service, fully containerised, with a clear project structure.

What I am building:

- FastAPI ingestion endpoint that accepts a PDF and stores it
- PostgreSQL for metadata (document ID, status, timestamps)
- Docker Compose wiring everything together
- Makefile for common commands
- Pre-commit hooks and a basic CI pipeline (GitHub Actions lint + test)

What I am learning: Docker layering, Compose networking, environment variables, Makefile conventions, Python project structure.

Key questions to answer by the end of this phase:
- Why do we split the `COPY` and `RUN pip install` steps in a Dockerfile?
- What happens to a Compose service that fails its healthcheck?
- How does Docker's internal DNS resolve service names?

---

### Phase 2 — RAG Core

Goal: end-to-end document understanding in code I wrote.

What I am building:

- PDF parsing with pdfplumber
- Chunking strategy: recursive character splitting, understanding chunk size tradeoffs
- Embedding generation and storage in Qdrant
- Retrieval: cosine similarity search, top-k, reranking
- Extraction: LLM call that takes retrieved chunks and returns structured JSON
- Redis Streams queue between ingestion and workers

What I am learning: embedding intuition, chunking tradeoffs, prompt design, async workers, Redis Streams.

Key questions to answer by the end of this phase:
- What chunk size gives the best retrieval quality for my document type? How do I measure that?
- Why does the same query return different results at different top-k values?
- What does it actually mean for two embeddings to be "close"?

---

### Phase 3 — Kubernetes Migration

Goal: everything that ran in Compose now runs in Kubernetes locally (minikube or kind).

What I am building:

- One namespace per logical layer (ingestion, processing, observability)
- Deployments with resource requests and limits
- ConfigMaps for non-sensitive config, Secrets for API keys
- Persistent volumes for Qdrant and PostgreSQL
- Liveness and readiness probes on every service
- Internal service discovery (no hardcoded IPs)

What I am learning: Kubernetes primitives, YAML structure, kubectl workflows, local cluster tooling.

Key questions to answer by the end of this phase:
- What is the difference between a liveness probe and a readiness probe, and what breaks if I confuse them?
- How does kube-dns resolve `http://processing-worker.processing.svc.cluster.local`?
- Why does a pod with no resource limits become a noisy neighbour?

---

### Phase 4 — Observability

Goal: I can tell within 30 seconds whether the system is healthy, degraded, or broken.

What I am building:

- Instrument every service with OpenTelemetry: spans around LLM calls, embedding generation, queue consumption
- Push traces to Tempo, metrics to Prometheus, logs to Loki
- Grafana dashboard: document ingestion rate, embedding latency p50/p99, LLM call cost (tokens used), queue depth, error rate per service
- One alerting rule that fires on a meaningful condition

What I am learning: OpenTelemetry SDK, trace context propagation, PromQL, Grafana panel types, RED vs USE methods.

Key questions to answer by the end of this phase:
- What is the difference between a span and a metric? When does each help?
- How does trace context propagate from the ingestion API to the processing worker over Redis?
- What is a good p99 LLM latency threshold to alert on, and why?

---

### Phase 5 — Infrastructure as Code on GKE

Goal: `terraform apply` provisions a working production environment from scratch.

What I am building:

- VPC with private subnets, NAT gateway, firewall rules
- GKE Autopilot cluster
- Cloud SQL (PostgreSQL) with private IP
- Artifact Registry for Docker images
- GCS bucket for document storage
- IAM service accounts with least-privilege roles
- Workload Identity binding (no static credentials in pods)
- HTTPS ingress with managed TLS via cert-manager

What I am learning: Terraform modules, GCP IAM model, Kubernetes Workload Identity, ingress controllers, DNS management.

Cloud provider: GCP. Decision rationale: existing GKE experience from the Weather ETL project, Google Cloud Computing Foundation certification, and GCP's Workload Identity is a cleaner credential model for Kubernetes workloads than static IAM keys. Terraform modules are structured to keep storage and database layers provider-agnostic.

Key questions to answer by the end of this phase:
- What is the difference between a GCP service account and a Kubernetes service account, and how does Workload Identity bind them?
- Why do we use private IP for Cloud SQL instead of a public endpoint?
- What does `terraform state` actually store, and what breaks if I lose it?

---

### Phase 6 — Advanced AI

Goal: the AI layer becomes more capable and measurable.

What I am building:

- Evaluation framework: offline RAG evaluation with RAGAS (faithfulness, answer relevance, context recall)
- Fine-tuning experiment: prepare a training dataset from processed documents, fine-tune a small model, A/B test against the base model
- Agentic routing: an LLM agent decides which action to take based on document content and confidence score
- Structured output extraction using function calling
- Cost tracking: log token usage per request, aggregate in Grafana, set a monthly budget alert

What I am learning: RAG evaluation metrics, fine-tuning data preparation, OpenAI function calling, agent patterns.

Key questions to answer by the end of this phase:
- What does RAGAS faithfulness actually measure, and how is it different from answer relevance?
- At what point does fine-tuning outperform prompt engineering, and how do I measure the crossover?
- What is the failure mode of an agentic router, and how do I detect it in production?

---

## Architectural Decisions Log

### Why Redis Streams over Kafka

Kafka is the industry standard for event streaming but adds significant operational weight at Phase 1. Redis Streams provides the same async worker pattern (consumer groups, acknowledgment, replay) with zero additional infrastructure. The decision can be revisited in Phase 3 once I understand what I would actually gain.

### Why Qdrant over Pinecone or Weaviate

Self-hosted, runs in Kubernetes as a standard StatefulSet, and forces operational understanding of a vector store rather than treating it as a managed black box. The HTTP and gRPC APIs are clean and well-documented.

### Why three services over a monolith

Splitting ingestion, processing, and routing from day one means I encounter real distributed systems problems early: what happens when a worker crashes mid-processing? how do I replay a failed job? what does backpressure look like? Starting with a monolith would defer all of that to a refactor.

### Why GCP over AWS

Existing GKE experience, existing certification, and Workload Identity is a more elegant credential model for Kubernetes than static IAM keys. Terraform modules are written with provider-agnostic interfaces for storage and database so the architecture is portable in principle.

### Why LangChain is used minimally

LangChain abstracts over exactly the things I need to understand: chunking, embedding calls, retrieval logic. I use it as a thin convenience layer but write the core logic myself. If I cannot explain what a LangChain call does without looking at its source, I replace it.

---

## Security Progression

Phase 1: secrets in `.env`, never committed. `.env.example` documents all required variables.

Phase 2: no hardcoded credentials anywhere in application code.

Phase 3: Kubernetes Secrets (base64 encoded, mounted as env vars). Acknowledge the limitation: base64 is not encryption. Secret rotation is manual.

Phase 5: Workload Identity on GKE. No static credentials in pods. IAM service accounts per workload, least-privilege roles. Network policies restricting pod-to-pod traffic to declared routes only.

Future: Secret Manager integration, automated rotation, audit logging.

---

## Resources I Found Useful

To be filled in as I go.

## Idea — Enterprise MCP Layer (post-Nexus)

A natural extension of what Nexus builds toward. The concept is a company-wide MCP server that exposes the full business corpus as tools accessible to an LLM agent source code, technical documentation, Jira tickets, product strategy, CRM data, marketing assets, financial metrics, SLAs.
The gap in the current market is that most RAG solutions operate on technical documentation only. Crossing code with business strategy with customer data in a single coherent context is unsolved at the enterprise level.

Concrete use cases:

An engineer asks "what is the impact of this API change on our enterprise customers?" the agent consults the codebase, customer contracts, support tickets, and SLAs simultaneously.

A sales manager asks "which customers are at churn risk this quarter?" the agent crosses product usage data, support interactions, and contract renewal dates.

What makes this defensible: the MCP protocol standardises how the LLM interacts with each data source. Each business domain (engineering, sales, finance, marketing) exposes a typed MCP interface. The LLM orchestrates across all of them dynamically.

Nexus builds the exact foundations needed to tackle this: RAG pipeline, MCP patterns, Kubernetes, observability. Revisit after Phase 6.

## LLMOps Concepts

LLMOps is MLOps applied specifically to LLM-powered systems. The core insight
is that a service can be "up" with good latency and still be producing wrong,
hallucinated, or degraded answers. Standard infrastructure observability does
not catch that. LLMOps fills that gap.

### Evaluation — DeepEval / RAGAS

Measures whether the LLM is actually doing its job correctly. Key metrics for
a RAG system:

Faithfulness — is the answer grounded in the retrieved chunks or is the model
hallucinating? Answer relevance — does the response actually answer the question
asked? Context recall — did the retrieval step find the chunks that contain the
answer?

Evaluation runs continuously — on every model upgrade, prompt change, or
chunking strategy change. It is a regression test suite for AI behaviour.

Planned for Phase 6 using RAGAS.

### Analytics — Langfuse / LangSmith

Goes beyond infrastructure metrics. Tracks semantic usage: which queries are
most frequent, which consistently produce low confidence answers, where the
pipeline fails (retrieval vs generation), distribution of document types.

Requires logging inputs, outputs, and intermediate pipeline states in a
queryable way.

### Cost Governance

Every LLM call costs money. Cost governance means tracking token consumption
per request and per document type, setting budget alerts, and making intelligent
model tradeoffs. In regulated environments like Moody's this is required to
justify AI infrastructure costs.

Planned for Phase 6 — token usage logged via OpenTelemetry, aggregated in
Grafana, monthly budget alert via Prometheus.

### Model Routing — LiteLLM

Not every request needs the same model. A model router decides which model to
use based on request complexity. Simple classification goes to gpt-4o-mini,
complex extraction goes to gpt-4o, sensitive data stays on a local model.

LiteLLM provides a unified interface across OpenAI, Anthropic, and local models
with routing rules defined in config.

Planned for Phase 6 action router.