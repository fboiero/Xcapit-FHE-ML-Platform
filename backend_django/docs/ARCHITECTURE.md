# Xcapit FHE-ML Platform - Architecture & Design Document

**Version:** 2.0.0
**Last Updated:** January 2026
**Framework:** Django 5.2 LTS (supported until April 2028)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Component Description](#3-component-description)
4. [Data Flow](#4-data-flow)
5. [API Reference](#5-api-reference)
6. [Complete Usage Example](#6-complete-usage-example)
7. [Security Architecture](#7-security-architecture)
8. [Database Schema](#8-database-schema)

---

## 1. System Overview

### What is Xcapit FHE-ML?

Xcapit FHE-ML is a **privacy-preserving machine learning platform** that enables multiple organizations to collaboratively train ML models on their combined data **without ever exposing the raw data** to each other or to the platform.

### Key Capabilities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         XCAPIT FHE-ML PLATFORM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │  Encrypted   │   │ Collaborative│   │  On-Chain    │   │  Regulatory  │ │
│  │   ML/AI      │   │   Training   │   │  Governance  │   │  Compliance  │ │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘ │
│                                                                              │
│  • Train on encrypted    • Multi-party      • Voting system   • GDPR       │
│    data (FHE)             consortiums       • Audit trail     • HIPAA      │
│  • No data exposure      • Contribution     • Blockchain TX   • SOC2       │
│  • 128/192/256-bit        proofs           • Rewards          • PCI-DSS    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Django 5.2 LTS + Django REST Framework |
| **Database** | PostgreSQL (production) |
| **Cache** | Redis |
| **FHE Engine** | TenSEAL (CKKS scheme) |
| **Blockchain** | Arbitrum (Ethereum L2) |
| **Authentication** | JWT (access + refresh tokens) |
| **API Docs** | OpenAPI 3.1 (drf-spectacular) |

---

## 2. Architecture Diagram

### High-Level System Architecture

```
                                    ┌─────────────────────────────────────┐
                                    │           INTERNET                   │
                                    └──────────────┬──────────────────────┘
                                                   │
                              ┌────────────────────┼────────────────────┐
                              │                    │                    │
                              ▼                    ▼                    ▼
                    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
                    │   Frontend      │  │   Mobile App    │  │   Third-Party   │
                    │   (React/Vite)  │  │   (Future)      │  │   Integration   │
                    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
                             │                    │                    │
                             └────────────────────┼────────────────────┘
                                                  │
                                                  ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                      API GATEWAY                         │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
                    │  │ Rate Limit  │  │ JWT Auth    │  │ CORS        │      │
                    │  │ (100/1000   │  │ (Bearer)    │  │ Headers     │      │
                    │  │  req/hour)  │  │             │  │             │      │
                    │  └─────────────┘  └─────────────┘  └─────────────┘      │
                    └─────────────────────────┬───────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DJANGO BACKEND                                      │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                           APPLICATION LAYER                               │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │    Core     │ │ Consortiums │ │ Governance  │ │   Models    │        │  │
│  │  │  (Users,    │ │ (Members,   │ │ (Proposals, │ │ (Training,  │        │  │
│  │  │  Companies, │ │  Contrib.)  │ │  Votes)     │ │  Predict)   │        │  │
│  │  │  API Keys)  │ │             │ │             │ │             │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │ Compliance  │ │ Marketplace │ │  Federated  │ │ Data Quality│        │  │
│  │  │ (GDPR,HIPAA)│ │ (Pre-train) │ │ (Inference) │ │ (Scoring)   │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                        │  │
│  │  │  Ensemble   │ │Explainabil. │ │ Competitive │                        │  │
│  │  │ (Multi-mdl) │ │ (SHAP,etc)  │ │  Insights   │                        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘                        │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                           SERVICE LAYER                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │  │
│  │  │ BaseService     │  │ AuditService    │  │ QualityService  │          │  │
│  │  │ ServiceContext  │  │ ConsortiumSvc   │  │ MemberService   │          │  │
│  │  │ ServiceResult   │  │                 │  │                 │          │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘          │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└────────────────┬─────────────────────────────────┬───────────────────────────────┘
                 │                                 │
                 ▼                                 ▼
    ┌────────────────────────┐       ┌────────────────────────┐
    │      PostgreSQL        │       │         Redis          │
    │  ┌──────────────────┐  │       │  ┌──────────────────┐  │
    │  │ • Users          │  │       │  │ • Session Cache  │  │
    │  │ • Companies      │  │       │  │ • Rate Limiting  │  │
    │  │ • Consortiums    │  │       │  │ • Token Blacklist│  │
    │  │ • Models         │  │       │  └──────────────────┘  │
    │  │ • Audit Logs     │  │       └────────────────────────┘
    │  │ • 39 Tables      │  │
    │  └──────────────────┘  │
    └────────────────────────┘

                 │
                 ▼
    ┌────────────────────────────────────────────────────────┐
    │                   ARBITRUM BLOCKCHAIN                   │
    │  ┌─────────────────┐ ┌─────────────────┐ ┌───────────┐ │
    │  │ Consortium      │ │ ModelRegistry   │ │ Verifier  │ │
    │  │ Governance.sol  │ │ .sol            │ │ .sol      │ │
    │  └─────────────────┘ └─────────────────┘ └───────────┘ │
    └────────────────────────────────────────────────────────┘
```

### Multi-Tenant Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MULTI-TENANT ISOLATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐     │
│  │   Company A     │      │   Company B     │      │   Company C     │     │
│  │  ┌───────────┐  │      │  ┌───────────┐  │      │  ┌───────────┐  │     │
│  │  │ Users     │  │      │  │ Users     │  │      │  │ Users     │  │     │
│  │  │ API Keys  │  │      │  │ API Keys  │  │      │  │ API Keys  │  │     │
│  │  │ Audit Logs│  │      │  │ Audit Logs│  │      │  │ Audit Logs│  │     │
│  │  └───────────┘  │      │  └───────────┘  │      │  └───────────┘  │     │
│  └────────┬────────┘      └────────┬────────┘      └────────┬────────┘     │
│           │                        │                        │              │
│           └────────────────────────┼────────────────────────┘              │
│                                    │                                        │
│                                    ▼                                        │
│                      ┌─────────────────────────┐                           │
│                      │      CONSORTIUM         │                           │
│                      │  "Healthcare Alliance"  │                           │
│                      │                         │                           │
│                      │  • Company A (Owner)    │                           │
│                      │  • Company B (Admin)    │                           │
│                      │  • Company C (Member)   │                           │
│                      │                         │                           │
│                      │  Shared:                │                           │
│                      │  • Encrypted Model      │                           │
│                      │  • Governance Rules     │                           │
│                      │  • Training Results     │                           │
│                      │                         │                           │
│                      │  NOT Shared:            │                           │
│                      │  • Raw Data             │                           │
│                      │  • Internal Records     │                           │
│                      └─────────────────────────┘                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Description

### 3.1 Core Module (`apps.core`)

**Purpose:** User identity, company management, and access control.

```
┌─────────────────────────────────────────────────────────────┐
│                        CORE MODULE                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User                          Company                       │
│  ├── email (primary auth)      ├── name                     │
│  ├── password (hashed)         ├── industry                 │
│  ├── company (FK)              ├── is_verified              │
│  └── role                      └── users[]                  │
│                                                              │
│  APIKey                        AuditLog                      │
│  ├── key_hash (SHA-256)        ├── user/company             │
│  ├── permissions (JSON)        ├── action                   │
│  ├── rate_limit               ├── resource_type/id         │
│  └── expires_at               └── ip_address               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Consortiums Module (`apps.consortiums`)

**Purpose:** Multi-party collaboration management.

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSORTIUMS MODULE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Consortium                    ConsortiumMember              │
│  ├── name                      ├── consortium (FK)          │
│  ├── owner (Company)           ├── company (FK)             │
│  ├── status                    ├── role                     │
│  │   • draft                   │   • owner                  │
│  │   • active                  │   • admin                  │
│  │   • training                │   • contributor            │
│  │   • completed               │   • observer               │
│  │   • archived                └── status                   │
│  ├── model_type                                              │
│  │   • linear_regression       ContributionProof            │
│  │   • logistic_regression     ├── consortium (FK)          │
│  │   • decision_tree           ├── company (FK)             │
│  │   • kmeans                  ├── record_count             │
│  └── ml_config (JSON)          ├── data_hash (SHA-256)      │
│                                 ├── verified                 │
│                                 └── blockchain_tx            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Governance Module (`apps.governance`)

**Purpose:** On-chain voting and audit trail.

```
┌─────────────────────────────────────────────────────────────┐
│                    GOVERNANCE MODULE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Proposal                      Vote                          │
│  ├── consortium (FK)           ├── proposal (FK)            │
│  ├── proposer                  ├── voter                    │
│  ├── proposal_type             ├── support (bool)           │
│  │   • add_member              └── weight                   │
│  │   • remove_member                                        │
│  │   • change_model            AuditEvent (Hash Chain)      │
│  │   • start_training          ├── consortium (FK)          │
│  │   • distribute_rewards      ├── event_type               │
│  │   • dissolve                ├── previous_hash            │
│  ├── status                    ├── event_hash               │
│  │   • active                  └── blockchain_tx            │
│  │   • passed                                                │
│  │   • rejected                                              │
│  │   • executed                                              │
│  └── voting_threshold                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Models Module (`apps.models`)

**Purpose:** ML model lifecycle management.

```
┌─────────────────────────────────────────────────────────────┐
│                      MODELS MODULE                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  MLModel                       TrainingRun                   │
│  ├── owner (Company)           ├── model (FK)               │
│  ├── consortium (FK)           ├── status                   │
│  ├── model_type                │   • queued                 │
│  ├── status                    │   • running                │
│  │   • created                 │   • completed              │
│  │   • training                │   • failed                 │
│  │   • trained                 ├── epochs_completed         │
│  │   • failed                  ├── current_loss             │
│  │   • archived                └── metrics (JSON)           │
│  ├── params (JSON)                                          │
│  └── feature_names             ModelCheckpoint              │
│                                 ├── model (FK)               │
│  PredictionLog                 ├── epoch                    │
│  ├── model (FK)                ├── weights_encrypted        │
│  ├── requester                 └── blockchain_tx            │
│  ├── n_samples                                              │
│  ├── encrypted (bool)                                       │
│  └── latency_ms                                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Data Flow

### 4.1 User Registration & Authentication Flow

```
┌─────────┐                    ┌─────────────┐                    ┌──────────┐
│  User   │                    │   Backend   │                    │ Database │
└────┬────┘                    └──────┬──────┘                    └────┬─────┘
     │                                │                                 │
     │  POST /auth/register/          │                                 │
     │  {email, password, company}    │                                 │
     │ ──────────────────────────────>│                                 │
     │                                │                                 │
     │                                │  Validate password (12+ chars)  │
     │                                │  Hash password (PBKDF2)         │
     │                                │                                 │
     │                                │  INSERT Company                 │
     │                                │ ────────────────────────────────>│
     │                                │                                 │
     │                                │  INSERT User                    │
     │                                │ ────────────────────────────────>│
     │                                │                                 │
     │  201 Created                   │                                 │
     │  {user, company}               │                                 │
     │ <──────────────────────────────│                                 │
     │                                │                                 │
     │  POST /auth/token/             │                                 │
     │  {email, password}             │                                 │
     │ ──────────────────────────────>│                                 │
     │                                │                                 │
     │                                │  Verify credentials             │
     │                                │ ────────────────────────────────>│
     │                                │                                 │
     │                                │  Generate JWT tokens            │
     │                                │                                 │
     │  200 OK                        │                                 │
     │  {access_token, refresh_token} │                                 │
     │ <──────────────────────────────│                                 │
     │                                │                                 │
```

### 4.2 Consortium Creation & Member Flow

```
┌───────────┐  ┌───────────┐  ┌───────────┐        ┌─────────────┐
│ Company A │  │ Company B │  │ Company C │        │   Backend   │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘        └──────┬──────┘
      │              │              │                      │
      │  POST /consortiums/         │                      │
      │  {name, model_type}         │                      │
      │ ───────────────────────────────────────────────────>│
      │                             │                      │
      │  201 Created                │                      │
      │  {consortium_id, status: draft}                    │
      │ <───────────────────────────────────────────────────│
      │                             │                      │
      │  POST /consortiums/invitations/                    │
      │  {invitee: Company B, role: admin}                 │
      │ ───────────────────────────────────────────────────>│
      │                             │                      │
      │  POST /consortiums/invitations/                    │
      │  {invitee: Company C, role: contributor}           │
      │ ───────────────────────────────────────────────────>│
      │                             │                      │
      │              │  [Email notification]               │
      │              │ <────────────────────────────────────│
      │              │              │                      │
      │              │  PUT /invitations/{id}/accept/      │
      │              │ ────────────────────────────────────>│
      │              │              │                      │
      │              │              │  PUT /invitations/{id}/accept/
      │              │              │ ─────────────────────>│
      │              │              │                      │
      │  PUT /consortiums/{id}/activate/                   │
      │ ───────────────────────────────────────────────────>│
      │                             │                      │
      │  200 OK                     │                      │
      │  {status: active}           │                      │
      │ <───────────────────────────────────────────────────│
      │              │              │                      │
```

### 4.3 Data Contribution Flow (Privacy-Preserving)

```
┌───────────┐                           ┌─────────────┐       ┌──────────────┐
│  Company  │                           │   Backend   │       │  Blockchain  │
└─────┬─────┘                           └──────┬──────┘       └──────┬───────┘
      │                                        │                     │
      │  [Local: Compute data hash]            │                     │
      │  data_hash = SHA256(encrypted_data)    │                     │
      │                                        │                     │
      │  POST /consortiums/{id}/contributions/ │                     │
      │  {                                     │                     │
      │    record_count: 50000,                │                     │
      │    feature_count: 25,                  │                     │
      │    data_hash: "abc123...",             │                     │
      │    checksum: "def456..."               │                     │
      │  }                                     │                     │
      │  [NOTE: NO raw data sent!]             │                     │
      │ ───────────────────────────────────────>│                     │
      │                                        │                     │
      │                                        │  Validate checksum  │
      │                                        │  Store metadata     │
      │                                        │                     │
      │  201 Created                           │                     │
      │  {contribution_id, verified: false}    │                     │
      │ <───────────────────────────────────────│                     │
      │                                        │                     │
      │                                        │  [Verification]     │
      │                                        │                     │
      │                                        │  Record on chain    │
      │                                        │ ────────────────────>│
      │                                        │                     │
      │                                        │  {tx_hash}          │
      │                                        │ <────────────────────│
      │                                        │                     │
      │  [Webhook: Contribution verified]      │                     │
      │  {verified: true, blockchain_tx}       │                     │
      │ <───────────────────────────────────────│                     │
      │                                        │                     │
```

### 4.4 Governance Voting Flow

```
┌───────────┐  ┌───────────┐  ┌───────────┐        ┌─────────────┐
│ Company A │  │ Company B │  │ Company C │        │   Backend   │
│  (Owner)  │  │  (Admin)  │  │ (Member)  │        └──────┬──────┘
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘               │
      │              │              │                      │
      │  POST /governance/proposals/                       │
      │  {                                                 │
      │    type: "start_training",                         │
      │    title: "Begin Q1 Training",                     │
      │    data: {epochs: 100}                             │
      │  }                                                 │
      │ ───────────────────────────────────────────────────>│
      │                                                    │
      │  201 Created                                       │
      │  {proposal_id, status: active, expires_at}         │
      │ <───────────────────────────────────────────────────│
      │                                                    │
      │  POST /governance/votes/                           │
      │  {proposal_id, support: true}                      │
      │ ───────────────────────────────────────────────────>│
      │              │                                     │
      │              │  POST /governance/votes/            │
      │              │  {proposal_id, support: true}       │
      │              │ ────────────────────────────────────>│
      │              │              │                      │
      │              │              │  POST /governance/votes/
      │              │              │  {proposal_id, support: true}
      │              │              │ ─────────────────────>│
      │                                                    │
      │                    [Voting threshold reached]      │
      │                                                    │
      │  POST /proposals/{id}/execute/                     │
      │ ───────────────────────────────────────────────────>│
      │                                                    │
      │  200 OK                                            │
      │  {status: executed, action: "training_started"}    │
      │ <───────────────────────────────────────────────────│
      │              │              │                      │
```

---

## 5. API Reference

### 5.1 Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v2/auth/register/` | Register new user |
| `POST` | `/api/v2/auth/token/` | Obtain JWT tokens |
| `POST` | `/api/v2/auth/token/refresh/` | Refresh access token |
| `POST` | `/api/v2/auth/logout/` | Blacklist refresh token |
| `GET` | `/api/v2/auth/me/` | Get current user |

### 5.2 Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/api/v2/companies/` | List/Create companies |
| `GET/PATCH` | `/api/v2/companies/me/` | Get/Update own company |
| `GET/POST` | `/api/v2/users/` | List/Create users |
| `GET/PATCH` | `/api/v2/users/me/` | Get/Update profile |
| `GET/POST` | `/api/v2/api-keys/` | Manage API keys |
| `POST` | `/api/v2/api-keys/{id}/revoke/` | Revoke API key |
| `GET` | `/api/v2/audit-logs/` | View audit logs |
| `GET` | `/api/v2/health/` | Health check |

### 5.3 Consortium Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/api/v2/consortiums/` | List/Create consortiums |
| `GET/PATCH/DELETE` | `/api/v2/consortiums/{id}/` | Manage consortium |
| `GET/POST` | `/api/v2/consortiums/{id}/members/` | Manage members |
| `POST` | `/api/v2/consortiums/{id}/members/{mid}/approve/` | Approve member |
| `GET/POST` | `/api/v2/consortiums/{id}/contributions/` | Data contributions |
| `POST` | `/api/v2/consortiums/{id}/contributions/{cid}/verify/` | Verify contribution |
| `GET/POST` | `/api/v2/consortiums/invitations/` | Manage invitations |
| `POST` | `/api/v2/consortiums/invitations/{id}/accept/` | Accept invitation |

### 5.4 Governance Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/api/v2/governance/proposals/` | List/Create proposals |
| `POST` | `/api/v2/governance/proposals/{id}/execute/` | Execute passed proposal |
| `GET/POST` | `/api/v2/governance/votes/` | List/Cast votes |
| `GET` | `/api/v2/governance/audit-events/` | View audit trail |
| `GET/POST` | `/api/v2/governance/rewards/` | Reward distributions |

### 5.5 Models Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/api/v2/models/` | List/Create models |
| `GET/PATCH` | `/api/v2/models/{id}/` | Manage model |
| `POST` | `/api/v2/models/{id}/train/` | Start training |
| `GET` | `/api/v2/models/{id}/training-runs/` | Training history |
| `POST` | `/api/v2/models/{id}/predict/` | Make prediction |
| `GET` | `/api/v2/models/{id}/predictions/` | Prediction logs |

### 5.6 Data Quality Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/api/v2/data-quality/assessments/` | Quality assessments |
| `GET` | `/api/v2/data-quality/alerts/` | Quality alerts |
| `GET` | `/api/v2/data-quality/dashboard/` | Quality dashboard |

### 5.7 Compliance Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v2/compliance/frameworks/` | Available frameworks |
| `GET/POST` | `/api/v2/compliance/checks/` | Compliance checks |
| `GET` | `/api/v2/compliance/reports/` | Compliance reports |
| `GET/POST` | `/api/v2/compliance/attestations/` | Attestations |

---

## 6. Complete Usage Example

This section provides a complete step-by-step example of using the platform.

### Prerequisites

```bash
# Start the backend server
cd backend_django
source .venv/bin/activate
python manage.py runserver

# Server running at http://localhost:8000
```

### Step 1: Register Users and Companies

**Register Company A (Healthcare Provider)**

```bash
# Request
curl -X POST http://localhost:8000/api/v2/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@hospital-a.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Alice",
    "last_name": "Admin",
    "company_name": "Hospital A"
  }'

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "email": "admin@hospital-a.com",
  "first_name": "Alice",
  "last_name": "Admin",
  "company": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "name": "Hospital A",
    "industry": null,
    "is_verified": false
  }
}
```

**Register Company B (Research Lab)**

```bash
curl -X POST http://localhost:8000/api/v2/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@research-lab.com",
    "password": "SecurePass456!",
    "password_confirm": "SecurePass456!",
    "first_name": "Bob",
    "last_name": "Researcher",
    "company_name": "Research Lab B"
  }'
```

**Register Company C (Insurance)**

```bash
curl -X POST http://localhost:8000/api/v2/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "carol@insurance-c.com",
    "password": "SecurePass789!",
    "password_confirm": "SecurePass789!",
    "first_name": "Carol",
    "last_name": "Analyst",
    "company_name": "Insurance C"
  }'
```

### Step 2: Authenticate and Get Tokens

```bash
# Login as Company A
curl -X POST http://localhost:8000/api/v2/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@hospital-a.com",
    "password": "SecurePass123!"
  }'

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cC..."
}

# Save the access token
export TOKEN_A="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Step 3: Create a Consortium

```bash
# Company A creates a consortium
curl -X POST http://localhost:8000/api/v2/consortiums/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{
    "name": "Healthcare Fraud Detection Alliance",
    "description": "Collaborative fraud detection using encrypted patient data",
    "model_type": "logistic_regression",
    "industry": "healthcare",
    "min_members": 3,
    "voting_threshold": 0.66,
    "voting_duration_days": 7,
    "ml_config": {
      "learning_rate": 0.01,
      "max_epochs": 100,
      "batch_size": 32
    }
  }'

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "name": "Healthcare Fraud Detection Alliance",
  "status": "draft",
  "owner": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "name": "Hospital A"
  },
  "model_type": "logistic_regression",
  "member_count": 1,
  "created_at": "2026-01-23T10:00:00Z"
}

export CONSORTIUM_ID="550e8400-e29b-41d4-a716-446655440100"
```

**Visual State:**

```
┌─────────────────────────────────────────────────────────────┐
│              CONSORTIUM: Healthcare Fraud Alliance          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Status: DRAFT                                               │
│  Model Type: Logistic Regression                             │
│  Min Members: 3                                              │
│  Voting Threshold: 66%                                       │
│                                                              │
│  Members:                                                    │
│  ┌───────────────────┐                                       │
│  │ Hospital A        │ ← Owner                               │
│  │ Status: Active    │                                       │
│  └───────────────────┘                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 4: Invite Members

```bash
# Invite Company B as Admin
curl -X POST http://localhost:8000/api/v2/consortiums/invitations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{
    "consortium": "'$CONSORTIUM_ID'",
    "invitee_email": "bob@research-lab.com",
    "role": "admin",
    "message": "Join our healthcare fraud detection consortium!"
  }'

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "consortium": "550e8400-e29b-41d4-a716-446655440100",
  "invitee_company": {
    "id": "550e8400-e29b-41d4-a716-446655440011",
    "name": "Research Lab B"
  },
  "role": "admin",
  "status": "pending",
  "expires_at": "2026-01-30T10:00:00Z"
}

# Invite Company C as Contributor
curl -X POST http://localhost:8000/api/v2/consortiums/invitations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{
    "consortium": "'$CONSORTIUM_ID'",
    "invitee_email": "carol@insurance-c.com",
    "role": "contributor",
    "message": "Join our healthcare fraud detection consortium!"
  }'
```

### Step 5: Accept Invitations

```bash
# Login as Company B
export TOKEN_B="..."  # (obtain token for bob@research-lab.com)

# Accept invitation
curl -X POST http://localhost:8000/api/v2/consortiums/invitations/550e8400-e29b-41d4-a716-446655440200/accept/ \
  -H "Authorization: Bearer $TOKEN_B"

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "status": "accepted",
  "member": {
    "id": "550e8400-e29b-41d4-a716-446655440300",
    "company": "Research Lab B",
    "role": "admin",
    "status": "active"
  }
}

# Company C also accepts (similar process)
```

**Visual State After Invitations Accepted:**

```
┌─────────────────────────────────────────────────────────────┐
│              CONSORTIUM: Healthcare Fraud Alliance          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Status: DRAFT → ACTIVE                                      │
│                                                              │
│  Members (3):                                                │
│  ┌───────────────────┐  ┌───────────────────┐               │
│  │ Hospital A        │  │ Research Lab B    │               │
│  │ Role: Owner       │  │ Role: Admin       │               │
│  │ Status: Active    │  │ Status: Active    │               │
│  └───────────────────┘  └───────────────────┘               │
│                                                              │
│  ┌───────────────────┐                                       │
│  │ Insurance C       │                                       │
│  │ Role: Contributor │                                       │
│  │ Status: Active    │                                       │
│  └───────────────────┘                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 6: Submit Data Contributions

**Important:** Raw data is NEVER sent to the platform. Only metadata and hashes.

```bash
# Company A contributes data
# First, locally compute the hash of your encrypted data
# data_hash = SHA256(your_encrypted_data_file)

curl -X POST http://localhost:8000/api/v2/consortiums/$CONSORTIUM_ID/contributions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{
    "record_count": 50000,
    "feature_count": 25,
    "data_hash": "a3f2b8c9d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
    "checksum": "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5",
    "description": "Patient claims data Q4 2025"
  }'

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440400",
  "company": "Hospital A",
  "record_count": 50000,
  "feature_count": 25,
  "data_hash": "a3f2b8c9...",
  "verified": false,
  "created_at": "2026-01-23T11:00:00Z"
}

# Company B and C also contribute (similar process)
```

**Visual State After Contributions:**

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA CONTRIBUTIONS                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Company         Records    Features    Verified    Hash    │
│  ─────────────────────────────────────────────────────────  │
│  Hospital A      50,000     25          ✓           a3f2... │
│  Research Lab B  75,000     25          ✓           b4c5... │
│  Insurance C     100,000    25          ✓           c5d6... │
│  ─────────────────────────────────────────────────────────  │
│  TOTAL          225,000     25                              │
│                                                              │
│  [!] No raw data stored - only hashes and metadata          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 7: Create and Vote on Training Proposal

```bash
# Company A creates a proposal to start training
curl -X POST http://localhost:8000/api/v2/governance/proposals/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{
    "consortium": "'$CONSORTIUM_ID'",
    "proposal_type": "start_training",
    "title": "Start Q1 2026 Model Training",
    "description": "Begin training on combined encrypted dataset",
    "data": {
      "epochs": 100,
      "learning_rate": 0.01,
      "early_stopping": true
    }
  }'

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440500",
  "proposal_type": "start_training",
  "title": "Start Q1 2026 Model Training",
  "status": "active",
  "yes_votes": 0,
  "no_votes": 0,
  "expires_at": "2026-01-30T11:00:00Z"
}

export PROPOSAL_ID="550e8400-e29b-41d4-a716-446655440500"
```

**Cast Votes:**

```bash
# Company A votes YES
curl -X POST http://localhost:8000/api/v2/governance/votes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{
    "proposal": "'$PROPOSAL_ID'",
    "support": true
  }'

# Company B votes YES
curl -X POST http://localhost:8000/api/v2/governance/votes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_B" \
  -d '{
    "proposal": "'$PROPOSAL_ID'",
    "support": true
  }'

# Company C votes YES
curl -X POST http://localhost:8000/api/v2/governance/votes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_C" \
  -d '{
    "proposal": "'$PROPOSAL_ID'",
    "support": true
  }'
```

**Visual State After Voting:**

```
┌─────────────────────────────────────────────────────────────┐
│                 PROPOSAL: Start Q1 2026 Training            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Status: ACTIVE → PASSED (100% > 66% threshold)             │
│                                                              │
│  Votes:                                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │  ████████████████████████████████████████  100%    │    │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  YES     │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Hospital A    : YES (weight: 22.2%)                        │
│  Research Lab B: YES (weight: 33.3%)                        │
│  Insurance C   : YES (weight: 44.4%)                        │
│                                                              │
│  [✓] Threshold met - Ready to execute                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 8: Execute Proposal and Start Training

```bash
# Execute the passed proposal
curl -X POST http://localhost:8000/api/v2/governance/proposals/$PROPOSAL_ID/execute/ \
  -H "Authorization: Bearer $TOKEN_A"

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440500",
  "status": "executed",
  "executed_at": "2026-01-23T12:00:00Z",
  "result": {
    "action": "training_started",
    "training_run_id": "550e8400-e29b-41d4-a716-446655440600"
  }
}
```

### Step 9: Monitor Training Progress

```bash
# Check training status
curl -X GET http://localhost:8000/api/v2/models/$MODEL_ID/training-runs/ \
  -H "Authorization: Bearer $TOKEN_A"

# Response
{
  "count": 1,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440600",
      "status": "running",
      "epochs_completed": 45,
      "epochs_total": 100,
      "current_loss": 0.234,
      "metrics": {
        "accuracy": 0.89,
        "f1_score": 0.87,
        "auc_roc": 0.92
      },
      "started_at": "2026-01-23T12:00:00Z"
    }
  ]
}
```

**Visual Training Progress:**

```
┌─────────────────────────────────────────────────────────────┐
│                    TRAINING PROGRESS                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Model: Fraud Detection (Logistic Regression)               │
│  Status: RUNNING                                             │
│                                                              │
│  Progress:                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ████████████████████░░░░░░░░░░░░░░░░░░░░░  45%     │    │
│  └─────────────────────────────────────────────────────┘    │
│  Epoch 45 / 100                                              │
│                                                              │
│  Metrics:                                                    │
│  ┌─────────────┬────────────┬────────────┐                  │
│  │  Accuracy   │  F1 Score  │  AUC-ROC   │                  │
│  │    89.0%    │    87.0%   │   92.0%    │                  │
│  └─────────────┴────────────┴────────────┘                  │
│                                                              │
│  Loss: 0.234 (decreasing ↓)                                 │
│                                                              │
│  [!] Training on encrypted data - no raw data exposed       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 10: Make Predictions (Encrypted Inference)

```bash
# After training completes, make an encrypted prediction
curl -X POST http://localhost:8000/api/v2/federated/requests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{
    "endpoint": "'$ENDPOINT_ID'",
    "input_hash": "encrypted_input_hash_from_client",
    "encryption_key_id": "key_abc123",
    "request_type": "real_time"
  }'

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440700",
  "status": "completed",
  "encrypted_output": "encrypted_result_blob...",
  "latency_ms": 45,
  "created_at": "2026-01-23T14:00:00Z"
}
```

**Visual Encrypted Inference:**

```
┌─────────────────────────────────────────────────────────────┐
│                   ENCRYPTED INFERENCE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐         ┌─────────────┐         ┌────────┐ │
│  │   Client    │         │   Server    │         │ Client │ │
│  │             │         │             │         │        │ │
│  │ Raw Data    │ ──────> │ Encrypted   │ ──────> │ Decrypt│ │
│  │     │       │ Encrypt │   Model     │ Predict │    │   │ │
│  │     ▼       │         │     │       │         │    ▼   │ │
│  │ Encrypted   │         │     ▼       │         │ Result │ │
│  │   Input     │         │ Encrypted   │         │        │ │
│  │             │         │   Output    │         │        │ │
│  └─────────────┘         └─────────────┘         └────────┘ │
│                                                              │
│  [!] Server NEVER sees raw data or decrypted results        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 11: View Data Quality Assessment

```bash
# Check data quality dashboard
curl -X GET http://localhost:8000/api/v2/data-quality/dashboard/ \
  -H "Authorization: Bearer $TOKEN_A"

# Response
{
  "total_assessments": 3,
  "average_score": 92.5,
  "open_alerts": 1,
  "active_rules": 5,
  "score_distribution": {
    "excellent": 2,
    "good": 1,
    "fair": 0,
    "poor": 0
  },
  "recent_assessments": [
    {
      "id": "...",
      "overall_score": 95.0,
      "status": "completed",
      "created_at": "2026-01-23T10:30:00Z"
    }
  ]
}
```

**Visual Quality Dashboard:**

```
┌─────────────────────────────────────────────────────────────┐
│                  DATA QUALITY DASHBOARD                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Overall Score: 92.5 / 100                                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ██████████████████████████████████████████░░░░░░░░ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Score Breakdown:                                            │
│  ┌────────────────┬────────────────┬────────────────┐       │
│  │  Completeness  │  Consistency   │   Accuracy     │       │
│  │     95.0%      │     91.0%      │    93.0%       │       │
│  │  █████████░    │  █████████░    │  █████████░    │       │
│  └────────────────┴────────────────┴────────────────┘       │
│                                                              │
│  Distribution:      Alerts:                                  │
│  Excellent: 2       ⚠ 1 Open Alert                          │
│  Good: 1            - "Duplicate records in Insurance C"    │
│  Fair: 0                                                     │
│  Poor: 0                                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 12: View Compliance Status

```bash
# Check compliance dashboard
curl -X GET http://localhost:8000/api/v2/compliance/reports/?consortium=$CONSORTIUM_ID \
  -H "Authorization: Bearer $TOKEN_A"

# Response
{
  "count": 1,
  "results": [
    {
      "id": "...",
      "framework": "HIPAA",
      "overall_score": 98,
      "status": "compliant",
      "passed_controls": 45,
      "failed_controls": 1,
      "pending_controls": 0,
      "generated_at": "2026-01-23T09:00:00Z"
    }
  ]
}
```

**Visual Compliance Report:**

```
┌─────────────────────────────────────────────────────────────┐
│                  COMPLIANCE STATUS                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  HIPAA Compliance Score: 98 / 100  ✓ COMPLIANT              │
│                                                              │
│  Controls Status:                                            │
│  ┌───────────────────────────────────────────────────┐      │
│  │ ████████████████████████████████████████████████░ │      │
│  │ 45 Passed                              1 Failed   │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
│  Key Controls:                                               │
│  ✓ Access Control (164.312(a))                              │
│  ✓ Audit Controls (164.312(b))                              │
│  ✓ Integrity (164.312(c))                                   │
│  ✓ Transmission Security (164.312(e))                       │
│  ⚠ Automatic Logoff (164.312(a)(2)(iii)) - Needs Review     │
│                                                              │
│  Frameworks Enabled:                                         │
│  [✓] HIPAA  [✓] SOC2  [ ] GDPR  [ ] PCI-DSS                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────┐
│                   SECURITY LAYERS                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Transport Security                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ HTTPS (TLS 1.3) + HSTS Preload + Secure Cookies     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Layer 2: Authentication                                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ JWT (HS256) - Access: 30min / Refresh: 7 days       │    │
│  │ API Keys (SHA-256 hashed) - Rate limited            │    │
│  │ django-axes - Brute force protection (5 attempts)   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Layer 3: Authorization                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ IsAuthenticated (default)                           │    │
│  │ IsCompanyMember (resource isolation)                │    │
│  │ IsResourceOwner (object-level permissions)          │    │
│  │ Role-based access (owner/admin/contributor/observer)│    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Layer 4: Data Protection                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ FHE Encryption (128/192/256-bit security)           │    │
│  │ No raw data storage (hashes only)                   │    │
│  │ JSON serialization (no pickle)                      │    │
│  │ Audit logging (immutable hash chain)                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Security Headers

```python
# Configured in settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
```

---

## 8. Database Schema

### Entity Relationship Diagram (Simplified)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    User      │       │   Company    │       │   APIKey     │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (UUID)    │──────>│ id (UUID)    │<──────│ id (UUID)    │
│ email        │       │ name         │       │ key_hash     │
│ password     │       │ industry     │       │ permissions  │
│ company_id   │       │ is_verified  │       │ company_id   │
└──────────────┘       └──────────────┘       └──────────────┘
                              │
                              │
                              ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ Consortium   │<──────│ Consortium   │<──────│ Contribution │
│              │       │ Member       │       │ Proof        │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (UUID)    │       │ id (UUID)    │       │ id (UUID)    │
│ name         │       │ consortium_id│       │ consortium_id│
│ owner_id     │       │ company_id   │       │ company_id   │
│ status       │       │ role         │       │ data_hash    │
│ model_type   │       │ status       │       │ verified     │
└──────────────┘       └──────────────┘       └──────────────┘
       │
       │
       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Proposal   │<──────│    Vote      │       │ AuditEvent   │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (UUID)    │       │ id (UUID)    │       │ id (UUID)    │
│ consortium_id│       │ proposal_id  │       │ consortium_id│
│ type         │       │ voter_id     │       │ event_type   │
│ status       │       │ support      │       │ event_hash   │
│ yes/no_votes │       │ weight       │       │ previous_hash│
└──────────────┘       └──────────────┘       └──────────────┘
       │
       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   MLModel    │<──────│ TrainingRun  │       │  Checkpoint  │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (UUID)    │       │ id (UUID)    │       │ id (UUID)    │
│ consortium_id│       │ model_id     │       │ model_id     │
│ model_type   │       │ status       │       │ epoch        │
│ params (JSON)│       │ epochs       │       │ weights_enc  │
│ status       │       │ metrics      │       │ loss         │
└──────────────┘       └──────────────┘       └──────────────┘
```

### Total Tables: 39

| Module | Tables |
|--------|--------|
| Core | User, Company, APIKey, AuditLog |
| Consortiums | Consortium, ConsortiumMember, ContributionProof, ConsortiumInvitation |
| Governance | Proposal, Vote, AuditEvent, RewardDistribution |
| Models | MLModel, TrainingRun, PredictionLog, ModelCheckpoint |
| Compliance | ComplianceFramework, ConsortiumCompliance, ComplianceCheck, ComplianceReport, Attestation, DataProcessingRecord |
| Federated | InferenceEndpoint, InferenceRequest, InferenceResult, FederatedModel, EdgeNode |
| Marketplace | Category, MarketplaceModel, Deployment, Review |
| Data Quality | QualityAssessment, QualityRule, QualityAlert |
| Competitive | IndustryBenchmark, CompanyMetric, CompetitiveReport |
| Ensemble | Ensemble, EnsembleModel, EnsemblePrediction, EnsembleEvaluation |
| Explainability | ExplanationRequest, FeatureImportance, ModelInsight |

---

## Appendix A: Environment Variables

```bash
# Required
DJANGO_SECRET_KEY=your-256-bit-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0

# Optional
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend.com
JWT_SIGNING_KEY=separate-jwt-signing-key
FHE_SECURITY_LEVEL=128  # 128, 192, or 256
SENTRY_DSN=https://...@sentry.io/...
```

## Appendix B: API Response Format

### Success Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "field1": "value1",
  "field2": "value2",
  "created_at": "2026-01-23T10:00:00Z"
}
```

### Paginated Response

```json
{
  "count": 100,
  "total_pages": 2,
  "current_page": 1,
  "page_size": 50,
  "next": "http://api/resource/?page=2",
  "previous": null,
  "results": [...]
}
```

### Error Response (RFC 7807)

```json
{
  "error": {
    "code": "validation_error",
    "message": "Human-readable message",
    "status": 400,
    "details": {
      "field_name": ["Error description"]
    }
  }
}
```

---

**Document Version:** 2.0.0
**Generated:** January 2026
**Maintained by:** Xcapit Engineering Team
