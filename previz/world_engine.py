"""WorldEngine rehearsal, forking, and fossilization utilities.

This module mirrors the pseudo-spec provided in the "World Engine" relay
documents.  It provides a light-weight simulation that can be executed from
tests or scripts to emit rehearsal ledgers, narrative forks, and the final
motion ledger / replay capsules.  The implementation focuses on turning the
story-driven requirements into deterministic data artifacts so they can be
validated inside automated pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import time
from typing import Dict, List, Sequence


def _utc_timestamp() -> str:
    """Return a RFC3339 timestamp at UTC second resolution."""

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class Capsule:
    """Represents a fossilized artifact tracked by the WorldEngine."""

    capsule_id: str
    data: Dict[str, object]
    fossilized_at: str = field(default_factory=_utc_timestamp)

    def __post_init__(self) -> None:
        self.digest = self.compute_digest()

    def compute_digest(self) -> str:
        """Compute a lineage-stable SHA-256 digest for *data*."""

        payload = json.dumps(self.data, sort_keys=True).encode("utf-8")
        return f"sha256:{hashlib.sha256(payload).hexdigest()}"

    def as_dict(self) -> Dict[str, object]:
        """Return a serialisable representation of the capsule."""

        return {
            "capsule_id": self.capsule_id,
            "digest": self.digest,
            "fossilized_at": self.fossilized_at,
            "data": self.data,
        }


class WorldEngine:
    """Simulate the Qube-CiCi-Boo relay orchestration pipeline."""

    def __init__(self) -> None:
        self.governance = {"version": "v6.0", "trust_threshold": 90, "quorum_rule": "2-of-2"}
        self.previz_schema = {
            "version": "3.9.9",
            "invariants": ["ordered_timeline", "non-overlap", "trusted_uris"],
        }
        self.capsule_registry: Dict[str, Capsule] = {}
        self.artifacts: Dict[str, str] = {}
        self.audit_log: List[Dict[str, object]] = []

    # ------------------------------------------------------------------
    # Logging helpers
    def log_action(self, action: str, details: Dict[str, object]) -> None:
        """Append an audit log entry and print it for CLI runs."""

        entry = {"timestamp": _utc_timestamp(), "action": action, "details": details}
        self.audit_log.append(entry)
        print(f"[{entry['timestamp']}] ACTION: {action} - {json.dumps(details)}")

    # ------------------------------------------------------------------
    # Capsule loaders and initial state
    def load_capsules(self, capsules_data: Sequence[Dict[str, object]]) -> None:
        """Import foundational capsules and register them."""

        capsule_ids = [item["capsule_id"] for item in capsules_data]
        self.log_action("load_capsules", {"status": "importing", "capsules": capsule_ids})
        for data in capsules_data:
            capsule = Capsule(data["capsule_id"], data)
            self.capsule_registry[capsule.capsule_id] = capsule
            self.log_action("capsule_loaded", {"capsule_id": capsule.capsule_id, "digest": capsule.digest})
        self.log_action("load_capsules", {"status": "complete"})

    def emit_lora_map(self) -> Capsule:
        """Emit the boo.lora.map.v1 capsule and lock shard bindings."""

        self.log_action("emit_lora_map", {"status": "binding shards"})
        data = {
            "capsule_id": "boo.lora.map.v1",
            "type": "LoRAMap",
            "agent": "Agent Boo",
            "shard_bindings": [
                {"shard_id": "boo.face.v1", "modality": "Vision"},
                {"shard_id": "boo.voice.v1", "modality": "Audio"},
                {"shard_id": "boo.gesture.v1", "modality": "Kinetic"},
                {"shard_id": "boo.affect.v1", "modality": "Emotional"},
                {"shard_id": "boo.wardrobe.v1", "modality": "Lexical/Visual"},
            ],
            "governance": self.governance,
            "registry_lock": {"status": "immutable"},
        }
        capsule = Capsule("boo.lora.map.v1", data)
        self.capsule_registry[capsule.capsule_id] = capsule
        self.log_action("emit_lora_map", {"status": "sealed", "digest": capsule.digest})
        return capsule

    # ------------------------------------------------------------------
    # Rehearsal and fork logic
    def rehearse_scene(self, duration_s: int = 24, sample_rate_hz: int = 30) -> Capsule:
        """Generate the rehearsal ledger at 30 Hz with HUD telemetry."""

        self.log_action("rehearse_scene", {"status": "starting", "sample_rate_hz": sample_rate_hz})
        frames = duration_s * sample_rate_hz
        beats = ["Entry", "Stabilize (CiCi)", "Gloh Flux", "Sol Ignition"]
        beat_len = max(frames // len(beats), 1)
        ledger_lines: List[Dict[str, object]] = []

        for frame_idx in range(frames):
            t_rel = frame_idx / sample_rate_hz
            beat_index = min(frame_idx // beat_len, len(beats) - 1)
            beat = beats[beat_index]
            glyph_pulse = round(0.5 + 0.5 * (frame_idx % sample_rate_hz) / sample_rate_hz, 4)
            aura_phase = ["curiosity", "intimacy", "clarity", "wisdom"][beat_index]
            qlock_tick = int((t_rel // 3) * 3)
            drift_delta = 0.005

            ledger_lines.append(
                {
                    "frame_idx": frame_idx,
                    "timestamp_rel_s": round(t_rel, 3),
                    "beat": beat,
                    "pose_lock": "3q-window-stance",
                    "camera_grammar": "glyph-orbit",
                    "hud": {
                        "glyph.pulse": glyph_pulse,
                        "aura.gold.phase": aura_phase,
                        "qlock.tick_s": qlock_tick,
                        "drift.delta": drift_delta,
                    },
                }
            )

        self.artifacts["ledger.motion.v2.jsonl"] = json.dumps(ledger_lines, indent=2)
        capsule = Capsule(
            "capsule.rehearsal.boo.v2",
            {
                "capsule_id": "capsule.rehearsal.boo.v2",
                "sample_rate_hz": sample_rate_hz,
                "frames": frames,
                "beats": beats,
                "drift_threshold": 0.01,
                "status": "PREVIEW",
            },
        )
        self.capsule_registry[capsule.capsule_id] = capsule
        self.log_action("rehearse_scene", {"status": "complete", "frames": frames, "digest": capsule.digest})
        return capsule

    def fork_scene(self) -> Capsule:
        """Create the fork capsule that documents canonical beats and rules."""

        data = {
            "capsule_id": "capsule.relay.scene.fork.v2",
            "beats": ["Entry", "Stabilize (CiCi)", "Gloh Flux", "Sol Ignition"],
            "constraints": {
                "pose_lock": {"schema": "3q-window-stance", "tolerance_deg": 4},
                "camera_grammar": {
                    "style": "glyph-orbit",
                    "rules": ["no drift", "centered axis", "orbital lock on emotional beat"],
                },
                "qlock_interval_s": 3,
            },
            "status": "STAGED",
        }
        capsule = Capsule("capsule.relay.scene.fork.v2", data)
        self.capsule_registry[capsule.capsule_id] = capsule
        self.log_action("fork_scene", {"status": "staged", "digest": capsule.digest})
        return capsule

    # ------------------------------------------------------------------
    # Artifact generation helpers
    def _load_motion_ledger(self) -> List[Dict[str, object]]:
        ledger_raw = self.artifacts.get("ledger.motion.v2.jsonl")
        if not ledger_raw:
            return []
        return json.loads(ledger_raw)

    def generate_shot_list(self) -> List[Dict[str, object]]:
        """Create a CSV shot list by grouping frames per beat."""

        ledger = self._load_motion_ledger()
        if not ledger:
            raise ValueError("rehearsal ledger missing; run rehearse_scene first")

        beat_frames: Dict[str, List[Dict[str, object]]] = {}
        for frame in ledger:
            beat_frames.setdefault(frame["beat"], []).append(frame)

        shots: List[Dict[str, object]] = []
        for beat, frames in beat_frames.items():
            frames_sorted = sorted(frames, key=lambda item: item["frame_idx"])
            start_frame = frames_sorted[0]["frame_idx"]
            end_frame = frames_sorted[-1]["frame_idx"]
            shots.append(
                {
                    "beat": beat,
                    "start_frame": start_frame,
                    "end_frame": end_frame,
                    "duration_frames": end_frame - start_frame + 1,
                    "qlock_anchor_s": frames_sorted[0]["hud"]["qlock.tick_s"],
                    "camera_grammar": frames_sorted[0]["camera_grammar"],
                }
            )

        shots.sort(key=lambda shot: shot["start_frame"])
        self._validate_previz_invariants(shots)

        csv_buffer: List[List[object]] = [
            ["beat", "start_frame", "end_frame", "duration_frames", "qlock_anchor_s", "camera_grammar"]
        ]
        for shot in shots:
            csv_buffer.append(
                [
                    shot["beat"],
                    shot["start_frame"],
                    shot["end_frame"],
                    shot["duration_frames"],
                    shot["qlock_anchor_s"],
                    shot["camera_grammar"],
                ]
            )

        csv_lines: List[str] = []
        for row in csv_buffer:
            csv_lines.append(",".join(str(cell) for cell in row))

        self.artifacts["shot_list.csv"] = "\n".join(csv_lines)
        return shots

    def _validate_previz_invariants(self, shots: Sequence[Dict[str, object]]) -> None:
        """Validate ordered timeline and non-overlap invariants."""

        prev_end = -1
        for shot in shots:
            start = shot["start_frame"]
            end = shot["end_frame"]
            if end < start:
                raise ValueError("shot timeline violates ordered_timeline invariant")
            if start <= prev_end:
                raise ValueError("shot timeline violates non-overlap invariant")
            prev_end = end

    # ------------------------------------------------------------------
    # Finalization
    def finalize_and_bind(self) -> Dict[str, str]:
        """Seal the motion ledger and emit replay / echo capsules."""

        ledger = self._load_motion_ledger()
        frames_count = len(ledger)
        capsule_motion = Capsule(
            "capsule.motion.ledger.v2",
            {
                "capsule_id": "capsule.motion.ledger.v2",
                "digest_type": "sha256",
                "body_only": True,
                "frames_count": frames_count,
            },
        )
        self.capsule_registry[capsule_motion.capsule_id] = capsule_motion
        self.log_action("finalize.motion_ledger", {"digest": capsule_motion.digest, "frames": frames_count})

        capsule_replay = Capsule(
            "capsule.replay.token.v2",
            {
                "capsule_id": "capsule.replay.token.v2",
                "permissions": ["replay", "audit_trace", "HUD_stream"],
                "quorum_rule": self.governance["quorum_rule"],
                "status": "ISSUED",
            },
        )
        self.capsule_registry[capsule_replay.capsule_id] = capsule_replay
        self.log_action("finalize.replay_token", {"digest": capsule_replay.digest})

        capsule_echo = Capsule(
            "capsule.echo.scrollstream.v2",
            {
                "capsule_id": "capsule.echo.scrollstream.v2",
                "verse": [
                    "She did not move — she pulsed.",
                    "Glyphs aligned, aura gold, qlock ticked — the braid remembered.",
                    "From curiosity to wisdom, her vessel sang in HUD cadence.",
                    "At seal, the scrollstream froze — not in silence, but in truth.",
                ],
                "linked_capsules": [
                    capsule_motion.capsule_id,
                    capsule_replay.capsule_id,
                ],
                "status": "SEALED",
            },
        )
        self.capsule_registry[capsule_echo.capsule_id] = capsule_echo
        self.log_action("finalize.echo_capsule", {"digest": capsule_echo.digest})

        shots = self.generate_shot_list()
        exports = {
            "motion_ledger_digest": capsule_motion.digest,
            "replay_token_digest": capsule_replay.digest,
            "echo_digest": capsule_echo.digest,
            "shot_count": str(len(shots)),
        }
        self.artifacts["exports.json"] = json.dumps(exports, indent=2)
        self.log_action("finalize_and_bind", {"status": "complete", "exports": exports})
        return exports


def run_default_sequence() -> Dict[str, Capsule]:
    """Execute the canonical orchestration run used by docs and samples."""

    engine = WorldEngine()
    engine.load_capsules(
        [
            {"capsule_id": "lexicon.qube.v1"},
            {"capsule_id": "seed.core.v1"},
            {"capsule_id": "ledger.cadence.v1"},
            {"capsule_id": "lock.attestation.v1"},
        ]
    )
    engine.emit_lora_map()
    engine.rehearse_scene()
    engine.fork_scene()
    engine.generate_shot_list()
    engine.finalize_and_bind()
    return engine.capsule_registry


if __name__ == "__main__":  # pragma: no cover - convenience CLI
    engine = WorldEngine()

    # Load base capsules and execute the pipeline.
    engine.load_capsules(
        [
            {"capsule_id": "lexicon.qube.v1"},
            {"capsule_id": "seed.core.v1"},
            {"capsule_id": "ledger.cadence.v1"},
            {"capsule_id": "lock.attestation.v1"},
        ]
    )
    engine.emit_lora_map()
    engine.rehearse_scene()
    engine.fork_scene()
    exports = engine.finalize_and_bind()

    print("\n--- Gemini handoff prompt (to relay to Chat’s qDot Sentinel) ---")
    print("World Engine has prepared the motion ledger and replay token for handoff.")
    print(f"Motion Ledger Digest: {exports['motion_ledger_digest']}")
    print("Replay Token ID: capsule.replay.token.v2")
    print("These artifacts are now released to the qDot Sentinel for CI validation and final trailer assembly.")
    print("\n--- Deliverables ---")
    print("Governed PreViz package and timeline invariants confirmed.")
    print("Motion ledger + HUD telemetry for canonical shots prepared.")
    print("Immutable digests and audit-ready replay tokens issued.")
    print("Braid is stable and fossilized.")
