# AMD AI Workload Doctor

An agentic AI system that analyzes, optimizes, benchmarks, and verifies AI workloads for AMD Instinct GPUs using ROCm.

## Vision

AI developers should be able to give an AI workload to an autonomous engineering agent and receive:

- A diagnosis of performance problems
- An optimization plan
- Automatically applied improvements
- Benchmark results
- Verification that the workload still works correctly
- A clear before/after performance report

## Core Workflow

Workload
→ Analyze
→ Diagnose
→ Plan
→ Optimize
→ Test
→ Benchmark
→ Verify
→ Report

## Initial Development Strategy

The first version will be developed locally using Python and small test workloads.

AMD Developer Cloud and AMD Instinct GPUs will be introduced later for real ROCm-based benchmarking and optimization experiments.

## Project Status

AMD-01 — Local Project Setup

Status: In progress


## AMD-03.8 — State System of Record (SSoR)

Implemented a local JSON-backed State System of Record for governed AI workload optimization cases.

### SSoR records

- Workload identity
- Workload analysis
- Optimization candidate
- Evidence
- Human approval state
- Execution details
- Before/after benchmarks
- Correctness and performance verification
- Final outcome
- Provenance
- Timestamped lifecycle events

### SSoR components

- `ssor/case_record.py` — structured optimization case record
- `ssor/case_store.py` — JSON persistence and case recovery
- `ssor/provenance.py` — evidence/source provenance
- `tests/test_ssor.py` — SSoR persistence, state, and provenance tests

### Governance architecture

The project now distinguishes:

- **KSoR** — governed knowledge, policies, methods, and standards
- **SSoR** — governed case history, evidence, decisions, and state
- **DSoR** — governed execution, authorization, approval, and action controls

SSoR enables a workload optimization case to be persisted and recovered without depending on previous chat history.

### Validation

AMD-03.8 integration completed with:

- **31/31 tests passing**
- SSoR persistence validated
- Provenance recording validated
- Pipeline integration validated
- AMD-03.7 execution, verification, acceptance, and rollback tests preserved
