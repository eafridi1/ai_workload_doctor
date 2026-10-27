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


## AMD-03.9 — SSoR Case Recovery and Handoff

Implemented explicit recovery of persisted optimization cases.

### Capabilities

- Load an existing case using its `case_id`.
- Restore saved workload and analysis state.
- Preserve candidate, evidence, approval, benchmark, verification, outcome, and event history.
- Record a `case_recovered` lifecycle event after recovery.
- Reject unknown case IDs with `FileNotFoundError`.
- Support case handoff without relying on previous chat history.

### Implementation

- `core/doctor_pipeline.py` — `load_case(case_id)` recovery method.
- `ssor/case_store.py` — loads persisted JSON case records.
- `ssor/case_record.py` — reconstructs structured case state.
- `tests/test_ssor.py` — tests persistence, provenance, recovery, and missing-case handling.

### Validation

- 33 project tests passed.
- Case recovery and missing-case behavior validated.
- Existing optimization governance, correctness, verification, and rollback tests preserved.


## AMD-03.10: Provenance and Evidence Integrity

Added SHA-256 content hashing to SSoR provenance records.

- Canonical JSON serialization produces deterministic hashes for equivalent JSON-compatible data.
- Provenance records include the hash algorithm and a hash of their recorded details.
- Hash verification detects changes to recorded details when compared against the original expected hash.
- Automated tests cover deterministic hashing, tampering detection, and provenance hash metadata.

Validation:
- Full test suite: 36 tests passed.
- Integrity checks use Python's standard library.

Limitation:
The hash is not a digital signature. If an attacker can modify both the recorded details and their stored hash, this alone cannot prove authenticity. Stronger protection requires a separately trusted hash, signature, or protected audit store.

## AMD-03.11: SSoR Audit Trail Integrity

Added a SHA-256 hash chain to SSoR case events.

- Each new event records a hash of its content and a link to the previous event.
- Event-chain verification detects modified events, reordering, and broken links.
- CaseStore validates event-chain integrity during loading by default.
- Invalid or legacy unverified event chains are rejected by default.
- Legacy cases can be loaded for inspection with `verify_integrity=False`, without claiming they are verified.
- JSON persistence rejects non-standard numeric values such as NaN.

Validation:
- Full test suite: 41 tests passed.
- Tests cover valid chains, modified events, reordered events, valid persisted cases, and tampered persisted cases.

Limitation:
The hash chain is tamper-evident, not tamper-proof. An attacker able to rewrite the complete event chain can recompute its hashes. Stronger guarantees require a trusted external checkpoint, protected audit storage, or digital signatures.

## AMD-03.12: Safe, Atomic SSoR Persistence

Updated CaseStore to use atomic JSON file replacement.

- Writes case data to a temporary file in the destination directory.
- Flushes and synchronizes the temporary file before replacement.
- Uses `os.replace()` to replace the saved case.
- Cleans up temporary files after failed writes or replacements.
- Preserves the previous valid case when replacement fails.
- Retains event-chain integrity verification when loading cases.

Validation:
- Full test suite: 43 tests passed.
- Tests cover successful persistence, event-chain verification, failed replacement, preservation of the previous case, and temporary-file cleanup.

Limitation:
Atomic replacement reduces the risk of partially written case files. It does not guarantee protection against every hardware or filesystem failure, and it does not replace backups or external audit storage.

## AMD-03.13: SSoR Schema Validation

- Added schema validation for required case fields and expected data types.
- Validated ISO timestamps and audit-event structure.
- Enforced schema validation before saving and after loading SSoR cases.
- Prevented saving cases with malformed audit events or broken event chains.
- Preserved atomic persistence and existing event-chain integrity checks.
- Added regression tests for missing fields, invalid types, malformed events, and valid case recovery.

Validation: 54 tests passed.

## AMD-03.15 — SSoR Case History and Revision Audit

- Stores a snapshot for each successfully saved case revision.
- Records revision number, timestamp, change summary, and SHA-256 snapshot hash.
- Exposes read-only revision history through `CaseStore.get_history(case_id)`.
- Validates snapshot hashes, case schemas, and event-chain integrity when reading history.
- Preserves optimistic concurrency checks to reject stale writes.
- Removes a newly written history entry if updating the current case file fails.

Revision snapshots are local audit records, not a tamper-proof security boundary.
A user able to rewrite both a snapshot and its hash can forge the stored history.

## AMD-03.16 — SSoR Revision Comparison and Recovery section documenting:

- Revision preview: inspect a verified historical snapshot without changing the current case.
- Revision comparison: identify changed top-level fields between two saved revisions.
- Revision recovery: restore historical case data as a new revision while preserving the current audit trail.
- Safety: stale recovery requests are rejected, and the existing history-integrity checks remain in place.

## AMD-03.17 — SSoR Revision Audit Interface section documenting the four pipeline methods:
- list_case_revisions()
- preview_case_revision()
- compare_case_revisions()
- recover_case_revision()
- recovery creates a new revision and rejects stale requests.


## AMD-03.18 — SSoR Audit Report Generation

### Capabilities
- Generates a structured, JSON-serializable audit report from SSoR revision history.
- Includes the case ID, UTC report-generation timestamp, revision count, revision range, and per-revision metadata.
- Records each revision's timestamp, change summary, SHA-256 snapshot hash, and governance events.
- Reuses `CaseStore.get_history()` to validate snapshot integrity, case schema, event-chain integrity, and revision metadata before reporting.
- Rejects corrupted history rather than reporting it as verified.
- Supports cases with no saved revisions, returning an empty revision list and null revision boundaries.

### Usage

Generate a report for the active case:

```python
report = pipeline.generate_audit_report()
```

Generate a report for a specific case:

```python
report = pipeline.generate_audit_report(case_id="local-case")
```

The method returns a dictionary suitable for JSON serialization. It does not write a report file, create a new case revision, or intentionally modify the active case or saved history.

### Validation
- Added five tests covering report contents, JSON serialization, read-only behavior, empty history, and corrupted snapshot rejection.
- Full test suite: **82 tests passed**.

### Integrity limitation
The report verifies stored history using existing SSoR integrity checks. SHA-256 hashes and event chains detect inconsistencies, but local records are not tamper-proof against an actor who can rewrite the snapshots and their corresponding hashes.
