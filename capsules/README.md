# Capsules

This directory contains declarative capsules that describe the canonical data contracts used by the Qube stack.

## `qube.telemetry.v1`

The `qube.telemetry.v1` capsule defines the cockpit view for the relay triangle (Proof → Flow → Execution). It specifies:

- **Streams** that ingest sealed SSOT roots, orchestrator checkpoints, and Sol.F1 acknowledgements.
- **Field catalog** entries for bundle hashes, avatars, quorum confidence, proof-flow drift, replay tokens, and latency measurements.
- **Dashboard layouts** including the node graph bindings and supporting widgets (time-series, histograms) used by PackNet/TAMS visualizations.
- **Alert guardrails** that trigger Dot rollbacks or council pings when quorum, drift, or replay invariants fall out of tolerance.

Use the schema to validate telemetry payloads and to bootstrap the dashboard configuration for observability tooling. The example embedded in the schema demonstrates how to wire live Kafka, NATS, and HTTPS feeds into a unified cockpit.
