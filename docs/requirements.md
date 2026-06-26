# GridLens Product Requirements Document

**Product name:** GridLens  
**Product type:** Multi-tenant utility intelligence, program evaluation, and AI decision-support platform  
**Document version:** 2.0  
**Audience:** Public repository readers, software engineers, product reviewers, and technical stakeholders  
**Primary learning goals:** Python, microservices, AWS, AI/LLM + RAG, React, secure data platforms  
**Project posture:** Real-world-like, production-minded, larger than a toy MVP  

---

## 1. Problem Statement

Utilities, municipalities, energy program operators, and infrastructure teams often make high-impact decisions using fragmented, messy, and poorly documented operational data. Meter readings may arrive late or contain gaps. Program participation files may not match account records. Weather data may require normalization. Business rules may change by program, tenant, geography, or reporting period. Supporting documents such as evaluation methodologies, data dictionaries, contracts, and client requirements may live outside the data platform entirely.

This creates several recurring problems:

1. **Slow data onboarding**  
   Analysts spend too much time cleaning files, reconciling column names, identifying missing records, and explaining why datasets do not match.

2. **Weak auditability**  
   Stakeholders may see a dashboard result but cannot easily trace it back to the source file, transformation version, model run, or assumption that produced it.

3. **Limited tenant isolation**  
   A platform serving multiple organizations must guarantee that users, dashboards, documents, model runs, object storage, vector retrieval, logs, and exports are scoped to the correct tenant.

4. **Difficult program evaluation**  
   Program managers need defensible answers to questions such as “Did this energy-efficiency program work?”, “Which customers saved the most?”, “Which data issues affect the conclusion?”, and “What assumptions should be disclosed?”

5. **Disconnected analytics and documentation**  
   Evaluation results may exist in a database while methodology documents, scope notes, and data dictionaries exist elsewhere. This makes natural-language exploration hard to trust.

6. **LLM risk in client-facing workflows**  
   AI assistants can help users explore data and documents, but they must be grounded, tenant-scoped, auditable, cost-aware, and able to refuse unsupported answers.

7. **Operational complexity**  
   Real systems need CI/CD, retries, idempotency, observability, secure secrets handling, least-privilege cloud access, performance controls, and documentation that survives beyond one developer.

**GridLens solves this by providing a realistic multi-tenant platform where organizations can ingest utility and program data, validate it, run evaluation pipelines, visualize outcomes, and use a grounded AI assistant to explain results with traceable evidence.**

---

## 2. Product Vision

GridLens is a cloud-native intelligence platform for utility, infrastructure, and energy-program analytics.

The platform enables organizations to:

1. Upload and manage messy operational datasets.
2. Validate, normalize, and version data through repeatable pipelines.
3. Evaluate energy and infrastructure programs using transparent analytical models.
4. Monitor data quality, anomalies, pipeline status, and model outputs.
5. Ask natural-language questions over approved datasets, documents, and generated reports.
6. Produce audit-ready summaries that explain results, assumptions, risks, and limitations.
7. Operate in a multi-tenant environment with secure tenant isolation and role-based access.

The product should feel like a credible internal or client-facing data platform, not a simple demo. It should expose the builder to practical engineering decisions across backend services, data modeling, cloud infrastructure, frontend dashboards, RAG systems, and production-readiness.

---

## 3. Product Objectives

### 3.1 Business Objectives

- Reduce the time required to onboard and validate utility/program datasets.
- Make program evaluation outputs more explainable and auditable.
- Provide stakeholders with dashboards that connect metrics to source data and model runs.
- Enable tenant-safe natural-language exploration of documents, data dictionaries, and evaluation outputs.
- Demonstrate a secure, scalable, cloud-native architecture appropriate for client-facing data products.

### 3.2 Technical Objectives

- Build Python services using clear API contracts and service boundaries.
- Implement multi-tenant data modeling from the beginning.
- Use asynchronous processing for ingestion, transformation, evaluation, and document indexing.
- Store raw, cleaned, curated, and generated artifacts with lineage.
- Deploy a working environment to AWS using infrastructure-as-code.
- Implement CI/CD with tests, security checks, and deployment gates.
- Build a React frontend with dashboards, workflows, and a chat interface.
- Implement a RAG system with tenant-scoped retrieval, source citations, refusals, and evaluation tests.

### 3.3 Learning Objectives

By building GridLens, the developer should gain hands-on experience with:

- Python API development.
- Data validation and transformation pipelines.
- SQL design and query performance.
- Microservice-oriented architecture.
- AWS services and IAM.
- Infrastructure-as-code.
- GitHub Actions CI/CD.
- React and TypeScript frontend engineering.
- LLM/RAG orchestration.
- Security, privacy, auditability, and tenant isolation.
- Product requirements, architecture documents, and technical tradeoff writing.

---

## 4. Product Summary

GridLens is a multi-tenant analytics platform with four major product areas:

### 4.1 Data Operations Hub

A workspace where tenant users upload files, monitor ingestion jobs, review validation errors, inspect schema drift, and manage curated datasets.

### 4.2 Program Evaluation Engine

A pipeline that estimates program impact using meter readings, participation data, building attributes, weather features, and transparent baseline models.

### 4.3 Intelligence Dashboard

A React dashboard that shows program savings, data quality, anomalies, model runs, tenant usage, cost indicators, and audit events.

### 4.4 Evidence-Grounded AI Assistant

A tenant-scoped RAG assistant that answers questions using uploaded documents, data dictionaries, evaluation outputs, data-quality reports, and generated summaries.

---

## 5. Target Users and Personas

### 5.1 Program Manager

A non-technical stakeholder responsible for understanding whether a program worked and communicating outcomes to funders, regulators, internal leadership, or clients.

**Primary needs:**

- View program performance.
- Understand savings, participation, and anomalies.
- Export summaries.
- Ask plain-English questions.
- Understand assumptions and limitations.

**Representative questions:**

- “How much energy did this program save?”
- “Which participant segments performed best?”
- “What should I mention in the monthly report?”
- “Are there any data-quality issues that weaken this conclusion?”

### 5.2 Analyst / Data Scientist

A technical user responsible for validating inputs, running models, reviewing outputs, and explaining methodology.

**Primary needs:**

- Upload and validate datasets.
- Inspect data-quality reports.
- Review transformed tables.
- Configure evaluation runs.
- Compare evaluation versions.
- Export data for external analysis.

**Representative questions:**

- “Which rows failed validation?”
- “What transformation version produced this result?”
- “How did the baseline model handle weather?”
- “Which accounts are driving negative savings?”

### 5.3 Tenant Administrator

A user responsible for managing users, roles, documents, tenant settings, and audit review for one organization.

**Primary needs:**

- Invite and manage tenant users.
- Assign roles.
- Configure tenant policies.
- Upload approved methodology documents.
- Review audit events.
- Monitor tenant usage.

### 5.4 Platform Administrator

A system-level operator responsible for supporting all tenants, monitoring services, managing platform configuration, and reviewing operational health.

**Primary needs:**

- View all tenants.
- Monitor API health and job queues.
- Review error rates.
- Manage platform-level feature flags.
- Investigate failed jobs.
- Monitor LLM usage and cost.

### 5.5 Auditor / Reviewer

A read-only user who needs evidence, lineage, logs, and exports.

**Primary needs:**

- Review evaluation history.
- Review audit logs.
- Trace dashboard metrics to source files and model runs.
- Export evidence packages.
- Verify that data and documents were accessed appropriately.

---

## 6. Core Use Cases

### UC-001: Onboard a New Tenant

A platform admin creates a tenant, configures default roles, invites a tenant admin, and enables the required product modules.

**Expected outcome:** The tenant can securely access its own workspace without seeing other tenants.

### UC-002: Upload Messy Meter Data

An analyst uploads a CSV containing meter readings with missing values, duplicate records, unexpected columns, and inconsistent date formats.

**Expected outcome:** The system validates the file, stores the raw version, produces a data-quality report, quarantines invalid rows, and loads valid records into curated tables.

### UC-003: Run an Energy Program Evaluation

An analyst selects a program, date range, model configuration, and input datasets. The system runs a baseline model and estimates savings.

**Expected outcome:** The system produces a versioned evaluation run with account-level, segment-level, and aggregate savings.

### UC-004: Review Executive Dashboard

A program manager opens the dashboard to review total savings, monthly trends, participation, anomalies, and data-quality warnings.

**Expected outcome:** The manager understands whether the program appears successful and what caveats apply.

### UC-005: Ask an AI Assistant About the Results

A user asks, “Why did reported savings decrease in March?”

**Expected outcome:** The assistant retrieves relevant evaluation outputs, anomaly reports, and methodology notes, then responds with citations and uncertainty where appropriate.

### UC-006: Generate an Evidence Package

An auditor exports a report containing source datasets, validation summary, model version, assumptions, results, and audit trail references.

**Expected outcome:** The exported package supports defensible decision-making and later review.

### UC-007: Prevent Cross-Tenant Data Leakage

A user from Tenant A attempts to access a dataset, document, vector chunk, chat session, or report belonging to Tenant B.

**Expected outcome:** The request is denied, logged, and covered by automated tests.

---

## 7. Product Scope

### 7.1 In Scope

GridLens shall include the following product capabilities:

- Tenant onboarding and tenant configuration.
- User authentication and role-based authorization.
- Tenant-scoped data ingestion.
- File upload for CSV and Parquet datasets.
- Schema validation and data-quality reporting.
- Raw, validated, curated, and generated data layers.
- Dataset catalog and metadata management.
- Transformation jobs with lineage.
- Program evaluation pipeline.
- Baseline modeling and savings estimation.
- Data anomaly detection.
- Tenant-safe dashboards.
- Document upload and indexing.
- RAG assistant with citations.
- Guardrails for unsupported or risky AI responses.
- Audit logging.
- Usage and cost tracking.
- CI/CD workflow.
- AWS deployment path.
- Infrastructure-as-code.
- Documentation and architecture decision records.

### 7.2 Out of Scope for Initial Public Version

The initial version shall not include:

- Real customer PII.
- Real regulated data.
- Production billing and invoicing.
- Enterprise SSO beyond basic OIDC/Cognito-style patterns.
- Full HIPAA/GDPR/SOC 2 compliance certification.
- Real-time production meter feeds.
- Fine-tuned LLMs.
- Native mobile applications.
- Production lakehouse scale.
- Fully automated regulatory filing.

### 7.3 Advanced Scope

Future versions may include:

- Difference-in-differences evaluation.
- Bayesian shrinkage or hierarchical modeling.
- Time-series forecasting.
- Demand response event analysis.
- Building-level load-shape clustering.
- Geospatial analysis.
- Natural-language-to-SQL with strict governance.
- Bedrock Knowledge Bases integration.
- Multi-region deployment.
- Data contracts and schema registry.
- Streaming ingestion simulator.
- Tenant-level cost allocation.
- Human-in-the-loop review workflows for AI responses.

---

## 8. Guiding Product Principles

### 8.1 Defensible Over Flashy

Every dashboard result should be traceable to source data, transformations, assumptions, and model runs. The product should prefer explainable outputs over impressive but opaque features.

### 8.2 Tenant Isolation by Design

Tenant isolation must be enforced across APIs, databases, object storage, document retrieval, vector search, logs, jobs, and exports.

### 8.3 AI Must Be Grounded

The assistant must answer from retrieved evidence when possible and refuse or qualify answers when evidence is insufficient.

### 8.4 Messy Data Is Normal

The ingestion experience should assume files will contain missing values, inconsistent formats, duplicate rows, schema changes, and incomplete relationships.

### 8.5 Asynchronous by Default for Heavy Work

Uploads, transformations, evaluations, document indexing, and exports should run as jobs rather than blocking user requests.

### 8.6 Security Is a Product Feature

Authentication, authorization, encryption, audit logs, token redaction, and least-privilege cloud permissions are required product capabilities, not implementation details.

### 8.7 Written Decisions Matter

The repository should include design docs, API contracts, ADRs, tradeoff notes, and runbooks that explain how the system works and why decisions were made.

---

## 9. High-Level System Architecture

GridLens shall be designed as a service-oriented platform. The first implementation may use a modular monolith or a small set of services, but service boundaries must be clear enough to split later.

### 9.1 Logical Services

#### 9.1.1 API Gateway / Backend-for-Frontend

Responsible for routing frontend requests, enforcing request-level authentication, attaching tenant context, and coordinating calls to internal services.

#### 9.1.2 Identity and Tenant Service

Responsible for tenants, users, roles, invitations, tenant settings, and feature flags.

#### 9.1.3 Dataset Catalog Service

Responsible for dataset metadata, schema definitions, source-file registration, data lineage, and dataset status.

#### 9.1.4 Ingestion Service

Responsible for uploads, file inspection, schema validation, quarantine handling, and ingestion job orchestration.

#### 9.1.5 Transformation Service

Responsible for converting raw inputs into normalized, tenant-scoped, queryable tables.

#### 9.1.6 Evaluation Service

Responsible for model configuration, baseline calculation, savings estimation, anomaly generation, evaluation comparison, and model-run metadata.

#### 9.1.7 Reporting Service

Responsible for report generation, evidence packages, downloadable exports, and scheduled summaries.

#### 9.1.8 RAG Service

Responsible for document ingestion, chunking, embeddings, retrieval, prompt orchestration, response generation, citations, and RAG evaluation.

#### 9.1.9 Audit Service

Responsible for recording and retrieving security, data, job, and business audit events.

#### 9.1.10 Usage and Cost Service

Responsible for tenant-level usage tracking, including file storage, rows processed, jobs executed, API calls, LLM tokens, and estimated AI cost.

#### 9.1.11 Frontend Web App

A React application that provides user workflows, dashboards, chat, administration, and monitoring.

---

## 10. Recommended Technology Stack

### 10.1 Backend

| Concern | Recommended Technology |
|---|---|
| API framework | FastAPI |
| Validation | Pydantic |
| Database access | SQLAlchemy or SQLModel |
| Migrations | Alembic |
| Data processing | Pandas or Polars |
| Testing | Pytest |
| Async workers | Celery, Dramatiq, RQ, or custom worker |
| API documentation | OpenAPI generated from FastAPI |
| Logging | Structured JSON logs |
| Configuration | Environment variables and typed settings |

### 10.2 Frontend

| Concern | Recommended Technology |
|---|---|
| UI framework | React |
| Language | TypeScript |
| Build tool | Vite |
| Routing | React Router |
| Server state | TanStack Query |
| Forms | React Hook Form |
| Tables | TanStack Table |
| Charts | Recharts, Nivo, or ECharts |
| Styling | Tailwind CSS or a component library |
| Testing | Vitest and React Testing Library |

### 10.3 Data and AI

| Concern | Recommended Technology |
|---|---|
| Relational database | PostgreSQL |
| Local vector search | pgvector |
| Document parsing | Python loaders for PDF, Markdown, CSV, TXT |
| Embeddings | Provider-based embedding API or local embedding model |
| LLM orchestration | Lightweight custom orchestration or LangChain/LlamaIndex if desired |
| RAG evaluation | Custom test harness with expected-answer dataset |
| Analytics | SQL, Pandas/Polars, scikit-learn for simple models |

### 10.4 AWS

| Layer | AWS Service | Purpose |
|---|---|---|
| Static frontend | S3 + CloudFront or Amplify | Host React app. |
| API entry | API Gateway or ALB | Route frontend/API traffic. |
| Compute | ECS Fargate and/or Lambda | Run Python services and workers. |
| Object storage | S3 | Store raw files, documents, exports, and generated artifacts. |
| Relational DB | RDS/Aurora PostgreSQL | Store tenants, jobs, records, metrics, and audit logs. |
| Vector storage | Aurora PostgreSQL pgvector, OpenSearch, or managed vector option | Store and query embeddings. |
| Queueing | SQS | Dispatch background jobs. |
| Workflow orchestration | Step Functions | Coordinate ingestion and evaluation pipelines. |
| Authentication | Cognito or OIDC-compatible provider | Authenticate users. |
| Secrets | Secrets Manager / SSM Parameter Store | Store credentials and API keys. |
| Observability | CloudWatch | Logs, metrics, dashboards, and alarms. |
| IaC | AWS CDK or Terraform | Reproducible infrastructure. |
| CI/CD | GitHub Actions | Test, build, and deploy. |

### 10.5 Local Development

| Cloud Concern | Local Equivalent |
|---|---|
| S3 | MinIO or LocalStack |
| RDS PostgreSQL | Dockerized PostgreSQL |
| SQS | LocalStack or Redis-backed queue |
| Cognito | Dev JWT auth or local auth service |
| ECS/Lambda | Docker Compose services |
| CloudWatch | Structured console logs |
| Secrets Manager | Local `.env` files for development only |

---

## 11. Data Domain

### 11.1 Core Entities

GridLens shall model the following entities.

#### Tenant

An organization using the platform.

Example fields:

- `tenant_id`
- `name`
- `slug`
- `region`
- `status`
- `created_at`
- `updated_at`

#### User

A person with access to one or more tenant workspaces.

Example fields:

- `user_id`
- `tenant_id`
- `email`
- `display_name`
- `role`
- `status`
- `created_at`
- `last_login_at`

#### Dataset

Metadata for an uploaded or generated dataset.

Example fields:

- `dataset_id`
- `tenant_id`
- `dataset_type`
- `source_name`
- `storage_uri`
- `schema_version`
- `status`
- `row_count`
- `created_by`
- `created_at`

#### Ingestion Job

A background job that processes a file.

Example fields:

- `job_id`
- `tenant_id`
- `dataset_id`
- `status`
- `started_at`
- `completed_at`
- `valid_row_count`
- `invalid_row_count`
- `error_summary`
- `retry_count`

#### Account

A synthetic customer or service account.

Example fields:

- `account_id`

