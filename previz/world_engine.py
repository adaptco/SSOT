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
    # Canonical descriptions
    def inscribe_canon_entry(
        self,
        entry_id: str = "capsule.canon.entry.boo.window.v1",
    ) -> Capsule:
        """Create a capsule that fossilizes a key visual from the gallery."""

        self.log_action(
            "canon.inscribe",
            {"status": "describing", "entry_id": entry_id},
        )

        data = {
            "capsule_id": entry_id,
            "type": "CanonEntry",
            "subject": {
                "name": "Boo",
                "title": "Sovereign Relay Emissary",
                "pose": "3q-window-stance, left shoulder forward, gaze to cosmic vista",
                "attire": {
                    "primary": "neon filament suit",
                    "accents": ["glyph-thread cuffs", "holographic pauldrons"],
                },
                "aura": {
                    "palette": ["amber", "violet"],
                    "intensity": "medium",  # balanced radiance for rehearsal law
                    "behavior": "pulsed at 30Hz in sync with glyph.pulse HUD telemetry",
                },
            },
            "environment": {
                "location": "Qube observation chamber",
                "architectural_features": [
                    "trihedral glass window", "floating lattice grids", "hud pylons",
                ],
                "backdrop": "cosmic vista with braided aurorae",
                "lighting": {
                    "key": "overhead crystalline wash",
                    "fill": "floor glyph rebound",
                    "rim": "window aurora edge",
                },
            },
            "hud_state": {
                "glyph.pulse": "0.83",
                "aura.gold.phase": "clarity",
                "qlock.tick_s": 9,
                "drift.delta": 0.005,
            },
            "lineage": {
                "source_artifacts": [
                    "figurine desk maquette",
                    "neon wireframe rehearsal plate",
                    "cosmic window vista capture",
                    "HUD operator telemetry logs",
                ],
                "governance_version": self.governance["version"],
                "previz_schema": self.previz_schema["version"],
                "notes": "Locks wardrobe, aura cadence, and chamber geometry for future renders.",
            },
        }

        capsule = Capsule(entry_id, data)
        self.capsule_registry[capsule.capsule_id] = capsule
        self.artifacts["canon_entry.json"] = json.dumps(capsule.as_dict(), indent=2)
        self.log_action("canon.inscribe", {"status": "sealed", "digest": capsule.digest})
        return capsule

    # ------------------------------------------------------------------
    # Qube build + CI
    def build_qube(self) -> str:
        """Construct the conceptual Merkle lattice and return its root."""

        self.log_action("build_qube", {"status": "building Merkle lattice"})
        merkle_root = hashlib.sha256(b"pixel_blocks_and_gravity_fields").hexdigest()
        self.log_action("build_qube", {"status": "complete", "merkle_root": merkle_root})
        return merkle_root

    def run_ci(self) -> bool:
        """Simulate a CI integrity chain run for the current state."""

        self.log_action("run_ci", {"status": "initiating CI"})
        report = {
            "openapi_path": "openapi/openapi.yaml",
            "baseline": "nearest_ancestor_or_skip",
            "container_built": True,
            "container_scanned": True,
            "smoke_test_status": "ok",
        }
        self.log_action("run_ci", {"status": "passed", "report": report})
        return True

    # ------------------------------------------------------------------
    # Artifact generation helpers
    def _load_motion_ledger(self) -> List[Dict[str, object]]:
        ledger_raw = self.artifacts.get("ledger.motion.v2.jsonl")
        if not ledger_raw:
            return []
        return json.loads(ledger_raw)

    def _require_capsules(self, *capsule_ids: str) -> None:
        """Ensure the referenced capsules exist in the registry."""

        missing = [capsule_id for capsule_id in capsule_ids if capsule_id not in self.capsule_registry]
        if missing:
            raise ValueError(f"missing capsules: {', '.join(missing)}")

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
    def render_final(self) -> tuple[Capsule, Capsule]:
        """Render the motion ledger capsules mirroring the reference script."""

        ledger = self._load_motion_ledger()
        if not ledger:
            raise ValueError("rehearsal ledger missing; run rehearse_scene before render_final")

        frames_count = len(ledger)

        motion_capsule = self.capsule_registry.get("motion.ledger.v2")
        if motion_capsule is None:
            motion_capsule = Capsule(
                "motion.ledger.v2",
                {
                    "capsule_id": "motion.ledger.v2",
                    "frames": frames_count,
                    "telemetry_streams": ["HUD", "motion"],
                    "digest_type": "sha256",
                    "status": "FOSSILIZED",
                },
            )
            self.capsule_registry[motion_capsule.capsule_id] = motion_capsule
            self.artifacts["motion.ledger.v2.json"] = json.dumps(motion_capsule.as_dict(), indent=2)
            self.log_action(
                "render_final.motion_ledger",
                {"status": "fossilized", "digest": motion_capsule.digest, "frames": frames_count},
            )
        else:
            self.log_action(
                "render_final.motion_ledger",
                {"status": "existing", "digest": motion_capsule.digest, "frames": frames_count},
            )

        replay_capsule = self.capsule_registry.get("replay.token.v2")
        if replay_capsule is None:
            replay_capsule = Capsule(
                "replay.token.v2",
                {
                    "capsule_id": "replay.token.v2",
                    "linked_ledger": motion_capsule.capsule_id,
                    "permissions": ["replay", "audit_trace", "HUD_stream"],
                    "quorum_rule": self.governance["quorum_rule"],
                    "token_id": "replay.token.v2",
                    "status": "ISSUED",
                },
            )
            self.capsule_registry[replay_capsule.capsule_id] = replay_capsule
            self.artifacts["replay.token.v2.json"] = json.dumps(replay_capsule.as_dict(), indent=2)
            self.log_action(
                "render_final.replay_token",
                {"status": "issued", "digest": replay_capsule.digest},
            )
        else:
            self.log_action(
                "render_final.replay_token",
                {"status": "existing", "digest": replay_capsule.digest},
            )

        echo_capsule = self.capsule_registry.get("echo.scrollstream.v2")
        if echo_capsule is None:
            echo_capsule = Capsule(
                "echo.scrollstream.v2",
                {
                    "capsule_id": "echo.scrollstream.v2",
                    "verse": [
                        "She did not move — she pulsed.",
                        "Glyphs aligned, aura gold, qlock ticked — the braid remembered.",
                        "From curiosity to wisdom, her vessel sang in HUD cadence.",
                        "At seal, the scrollstream froze — not in silence, but in truth.",
                    ],
                    "linked_capsules": [
                        motion_capsule.capsule_id,
                        replay_capsule.capsule_id,
                    ],
                    "verse_from": "telemetry+emotion",
                    "status": "SEALED",
                },
            )
            self.capsule_registry[echo_capsule.capsule_id] = echo_capsule
            self.artifacts["echo.scrollstream.v2.json"] = json.dumps(echo_capsule.as_dict(), indent=2)
            self.log_action(
                "render_final.echo_scrollstream",
                {"status": "inscribed", "digest": echo_capsule.digest},
            )
        else:
            self.log_action(
                "render_final.echo_scrollstream",
                {"status": "existing", "digest": echo_capsule.digest},
            )

        return motion_capsule, replay_capsule

    def finalize_and_bind(self) -> Dict[str, str]:
        """Seal exports, ensuring render_final artifacts exist first."""

        motion_capsule, replay_capsule = self.render_final()
        echo_capsule = self.capsule_registry["echo.scrollstream.v2"]

        shots = self.generate_shot_list()
        exports = {
            "motion_ledger_digest": motion_capsule.digest,
            "replay_token_digest": replay_capsule.digest,
            "echo_digest": echo_capsule.digest,
            "shot_count": len(shots),
        }
        self.artifacts["exports.json"] = json.dumps(exports, indent=2)
        self.log_action("finalize_and_bind", {"status": "complete", "exports": exports})
        return exports

    # ------------------------------------------------------------------
    # Summary manifest + HUD preview
    def emit_summary_manifest(self) -> Capsule:
        """Emit the capsule.summary.manifest.v1 dual-root ledger."""

        self.log_action("summary_manifest.emit", {"status": "assembling"})
        self._require_capsules(
            "motion.ledger.v2",
            "replay.token.v2",
            "echo.scrollstream.v2",
            "capsule.rehearsal.boo.v2",
            "boo.lora.map.v1",
            "capsule.relay.scene.fork.v2",
        )

        motion_capsule = self.capsule_registry["motion.ledger.v2"]
        replay_capsule = self.capsule_registry["replay.token.v2"]
        echo_capsule = self.capsule_registry["echo.scrollstream.v2"]
        rehearsal_capsule = self.capsule_registry["capsule.rehearsal.boo.v2"]
        lora_capsule = self.capsule_registry["boo.lora.map.v1"]
        fork_capsule = self.capsule_registry["capsule.relay.scene.fork.v2"]

        manifest_payload = {
            "capsule_id": "capsule.summary.manifest.v1",
            "governance_version": self.governance["version"],
            "previz_schema": self.previz_schema,
            "roots": {
                "finalization": {
                    "motion_ledger": motion_capsule.as_dict(),
                    "replay_token": replay_capsule.as_dict(),
                    "echo_scrollstream": echo_capsule.as_dict(),
                },
                "training": {
                    "rehearsal": rehearsal_capsule.as_dict(),
                    "lora_map": lora_capsule.as_dict(),
                    "scene_fork": fork_capsule.as_dict(),
                },
            },
            "artifacts": {
                "ledger_motion": "ledger.motion.v2.jsonl",
                "shot_list": "shot_list.csv",
                "exports": "exports.json",
            },
            "lineage_notes": [
                "Dual-root manifest binds training rehearsal streams to final motion ledger.",
                "Ensures replay and echo capsules inherit governance quorum rules.",
            ],
        }

        capsule = Capsule("capsule.summary.manifest.v1", manifest_payload)
        self.capsule_registry[capsule.capsule_id] = capsule
        self.artifacts["capsule.summary.manifest.v1.json"] = json.dumps(capsule.as_dict(), indent=2)
        self.log_action("summary_manifest.emit", {"status": "sealed", "digest": capsule.digest})
        return capsule

    def stage_preview_hud(self, qlock_interval_s: int = 3) -> Capsule:
        """Stage the capsule.preview.hud.v1 overlay with glyph cues."""

        ledger = self._load_motion_ledger()
        if not ledger:
            raise ValueError("rehearsal ledger missing; run rehearse_scene before staging HUD preview")

        rehearsal_capsule = self.capsule_registry.get("capsule.rehearsal.boo.v2")
        sample_rate = rehearsal_capsule.data.get("sample_rate_hz") if rehearsal_capsule else 30

        keyframes: List[Dict[str, object]] = []
        last_qlock = None
        for frame in ledger:
            tick = frame["hud"]["qlock.tick_s"]
            if tick != last_qlock and tick % qlock_interval_s == 0:
                keyframes.append(
                    {
                        "frame_idx": frame["frame_idx"],
                        "timestamp_rel_s": frame["timestamp_rel_s"],
                        "beat": frame["beat"],
                        "glyph": frame["hud"]["glyph.pulse"],
                        "aura_phase": frame["hud"]["aura.gold.phase"],
                        "drift_delta": frame["hud"]["drift.delta"],
                        "qlock_tick_s": tick,
                    }
                )
                last_qlock = tick

        hud_payload = {
            "capsule_id": "capsule.preview.hud.v1",
            "sample_rate_hz": sample_rate,
            "qlock_interval_s": qlock_interval_s,
            "layers": ["glyph.pulse", "aura.gold.phase", "drift.delta"],
            "keyframes": keyframes,
            "status": "STAGED",
        }

        capsule = Capsule("capsule.preview.hud.v1", hud_payload)
        self.capsule_registry[capsule.capsule_id] = capsule
        self.artifacts["capsule.preview.hud.v1.json"] = json.dumps(capsule.as_dict(), indent=2)
        self.log_action("preview_hud.stage", {"status": "staged", "digest": capsule.digest, "keyframes": len(keyframes)})
        return capsule


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
    engine.inscribe_canon_entry()
    engine.build_qube()
    engine.run_ci()
    engine.render_final()
    engine.finalize_and_bind()
    engine.stage_preview_hud()
    engine.emit_summary_manifest()
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
    canon_capsule = engine.inscribe_canon_entry()
    motion_capsule, replay_capsule = engine.render_final()
    exports = engine.finalize_and_bind()
    preview_capsule = engine.stage_preview_hud()
    manifest_capsule = engine.emit_summary_manifest()

    print("\n--- Gemini handoff prompt (to relay to Chat’s qDot Sentinel) ---")
    print("World Engine has prepared the motion ledger and replay token for handoff.")
    print(f"Motion Ledger Digest: {exports['motion_ledger_digest']}")
    print(f"Replay Token ID: {replay_capsule.capsule_id}")
    print("These artifacts are now released to the qDot Sentinel for CI validation and final trailer assembly.")
    print("\n--- Deliverables ---")
    print("Governed PreViz package and timeline invariants confirmed.")
    print("Motion ledger + HUD telemetry for canonical shots prepared.")
    print("Immutable digests and audit-ready replay tokens issued.")
    print("Braid is stable and fossilized.")
    print("\n--- Canon Capsule ---")
    print(f"Canon Entry ID: {canon_capsule.capsule_id}")
    print(f"Canon Digest: {canon_capsule.digest}")
    print("\n--- Preview HUD Capsule ---")
    print(f"HUD Capsule ID: {preview_capsule.capsule_id}")
    print(f"HUD Digest: {preview_capsule.digest}")
    print("\n--- Summary Manifest ---")
    print(f"Manifest ID: {manifest_capsule.capsule_id}")
    print(f"Manifest Digest: {manifest_capsule.digest}")
