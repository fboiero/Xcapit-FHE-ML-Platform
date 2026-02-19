# Xcapit Privacy — Roadmap 2026

> **Last updated:** February 2026
>
> **Previous roadmap:** See [PLATFORM_ROADMAP.md](PLATFORM_ROADMAP.md) for the feature-tier roadmap (completed, kept as historical reference).

12-month roadmap (Feb 2026 - Jan 2027) for evolving from MVP to production-grade Data Consortium Platform.

---

## Q1 2026 (Feb-Mar): Foundation

**Goal:** Production-harden the frontend, reposition messaging, and validate technical foundation.

| Item | Status | Notes |
|------|--------|-------|
| Frontend production hardening | In Progress | Replace console.* with Sentry, retry logic, meta tags |
| Messaging repositioning | In Progress | Consortium-first positioning across all copy |
| Deploy contracts to Arbitrum Sepolia | Planned | ConsortiumGovernanceV2, ModelRegistryV2, ComputationVerifierV2 |
| Evaluate FHE library migration | Planned | TenSEAL vs Concrete ML vs OpenFHE — benchmark latency, model support, maintenance |
| Document real FHE limitations per model | Planned | Throughput, latency, precision loss by model type |

**Metrics:**
- 0 console.log/warn/error in frontend
- Contracts deployed and verified on Sepolia
- FHE evaluation document published

---

## Q2 2026 (Apr-Jun): First Pilots

**Goal:** Land 2-3 fintech pilot customers in LATAM for fraud detection consortium.

| Item | Status | Notes |
|------|--------|-------|
| Pilot: 2-3 fintechs LATAM (fraud detection) | Planned | Focus on logistic regression model |
| Dashboard connected to real API | Planned | Eliminate demo mode for pilot users |
| End-to-end FHE pipeline for 2 models | Planned | Logistic Regression + KMeans validated |
| Prometheus/Grafana monitoring | Planned | Backend observability stack |
| LinkedIn Ads validation | Planned | $1,500 budget, 3 verticals (fintech, healthcare, government) |
| API rate limiting + abuse prevention | Planned | Production-grade throttling |

**Metrics:**
- 2+ pilot agreements signed
- End-to-end FHE working for 2 model types
- Ad campaign: measure CTR by vertical, CPC < $5

**Budget:** ~$3,000 (ads + infrastructure)

---

## Q3 2026 (Jul-Sep): Mainnet & Enterprise

**Goal:** Go to mainnet, add enterprise features, prepare for compliance.

| Item | Status | Notes |
|------|--------|-------|
| Arbitrum One mainnet deployment | Planned | Multi-sig governance, gas optimization |
| Enterprise SSO (SAML/OIDC) | Planned | Azure AD, Okta integration |
| SOC 2 Type I preparation | Planned | Policies, procedures, evidence collection |
| SDK v1.0 stable release | Planned | Public API freeze, semantic versioning |
| Data residency controls | Planned | Region-locked encryption contexts |
| Pilot results published | Planned | Case study with anonymized pilot data |

**Metrics:**
- Mainnet contracts live with multi-sig
- SSO working with at least 1 IdP
- SOC 2 readiness assessment > 80%

**Team needed:** +1 security engineer (part-time or contractor)

---

## Q4 2026 - Q1 2027 (Oct-Jan): Scale

**Goal:** Scale to 10+ active consortiums, build billing, complete SOC 2.

| Item | Status | Notes |
|------|--------|-------|
| Kubernetes auto-scaling | Planned | Handle variable FHE compute load |
| Billing/metering system | Planned | Per-consortium, per-compute pricing |
| SOC 2 Type II audit | Planned | 3-month observation window |
| Partner program | Planned | System integrators, consulting firms |
| SDK ecosystem (Python, JS, Go) | Planned | Community contributions |
| Advanced models (Random Forest on FHE) | Planned | Pending FHE library evaluation results |

**Metrics:**
- 10+ active consortiums
- $50-100K ARR
- SOC 2 Type II report issued
- 3+ partner integrations

**Budget:** ~$15,000-25,000 (audit + infrastructure + partners)

---

## Risk Matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| FHE performance too slow for production | High | Medium | Evaluate Concrete ML/OpenFHE; offer hybrid mode (FHE + TEE) |
| No pilot customers by Q2 | High | Low | Expand to healthcare vertical; offer free pilot period |
| TenSEAL maintenance abandoned | Medium | Medium | Migration plan to OpenFHE/Concrete ML ready by Q2 |
| Competitor launches similar product | Medium | Low | Speed to market; deep LATAM relationships; consortium governance as moat |
| SOC 2 audit delays | Medium | Medium | Start preparation Q2; hire security contractor |

---

## Team Requirements

| Phase | Role | Type |
|-------|------|------|
| Q1-Q2 | Full-stack developer | Core team |
| Q2-Q3 | Security engineer | Contractor (part-time) |
| Q2+ | Sales/BD (LATAM fintech) | Core team or contractor |
| Q3+ | DevOps engineer | Contractor or part-time |

---

## Key Decisions Pending

1. **FHE Library:** TenSEAL vs Concrete ML vs OpenFHE — decide by end of Q1 2026
2. **Pricing Model:** Per-consortium flat fee vs per-compute metering — decide by Q3 2026
3. **Open Source Strategy:** Which components to open source for community growth — decide by Q2 2026
