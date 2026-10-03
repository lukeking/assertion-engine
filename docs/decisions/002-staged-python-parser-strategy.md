# 002: Stage Python first and handwrite the parser

**Status:** Accepted

**Date:** 2026-09-29

## Context

M0 needs a deterministic telemetry simulator, rendered playback and CI. The repository must also choose a direction for the later real-time Evaluator and DSL parser without importing another drone project's performance assumptions or paying for two runtimes before latency exists to measure.

The project is capability-building work. C++ and parsing theory are skills to acquire, but an unfinished two-language skeleton produces neither a complete system nor trustworthy real-time evidence.

## Decision

### Runtime staging

M0 uses CPython 3.14, uv and one Python `src`-layout package. Simulator artifacts are language-neutral canonical JSON so later components do not inherit a Python-only storage contract.

The project does not promise Python forever. After M2 provides a real Evaluator and the 10-rule corpus, it measures p50/p95/p99/max latency and GC pauses against the project-specific ladder. A C++20 hot path is introduced only when E1 evidence shows that max engine latency exceeds the active event interval or GC pauses cause missed evaluation windows.

The initial implementation does not add CMake, bindings or a second test runner.

### Parser strategy

M1 uses a handwritten recursive-descent/Pratt parser in Python. Before grammar implementation, at least 10 real rules must cover comparisons, Boolean combinations, temporal constraints and trend extrapolation.

The grammar is checked in using an EBNF-like notation. Every grammar rule maps visibly to a parsing function, and the real-rule corpus is the parser regression suite.

Lark or ANTLR is reconsidered only when the corpus demonstrates grammar ambiguity/backtracking that cannot remain clear in handwritten code, or required diagnostics and recovery dominate parser work.

## Consequences

- M0 has one runtime and build workflow, so Simulator and playback can reach complete acceptance evidence first.
- The canonical artifact boundary preserves a later C++ path without adding bindings now.
- Tail-latency suitability remains unproven until E1 benchmarks exist; all interim ladder values stay labeled E2/E3 and cannot become Gates.
- Handwriting the parser increases learning value and traceability but accepts weaker built-in error recovery than Lark or ANTLR.
- Grammar work cannot begin early as scaffolding; the corpus is a hard prerequisite.

## Revisit when

- E1 Evaluator results miss an event-interval budget or attribute missed windows to GC pauses;
- the real-rule corpus cannot be expressed cleanly with RD/Pratt parsing;
- error recovery becomes a user-facing acceptance requirement that dominates parser implementation;
- a real integration mandates a non-Python runtime or artifact format.

## Evidence

The weighted comparisons, evidence tiers and official references are recorded in `specs/001-telemetry-simulator/research.md`.
