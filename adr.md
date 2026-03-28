# IDS_Hardware Architecture Decision Record

Purpose: capture the main architectural decisions already visible in this project, plus likely future decision points that should be resolved deliberately.

Important note:
- Because this workspace has no Git history, the "status" and "origin" of past decisions are inferred from current code and timestamps.
- Security note: links are repo-relative so this document can be published without exposing local machine paths.

## Current Decisions

### ADR-001: Use a shared feature contract as the source of truth
Status:
- Accepted

Evidence:
- [shared/feature_contract.py](shared/feature_contract.py)
- [tests/test_contract_parity.py](tests/test_contract_parity.py)
- [bridge/pipeline.py](bridge/pipeline.py)

Decision:
- Keep feature order, input shape, normalization statistics, class names, and UART framing in one shared module.

Reason:
- This prevents preprocessing drift between training, bridge, and deployment stages.

Consequence:
- Any contract change must start in the shared module and be validated everywhere else.

### ADR-002: Model CAN traffic as a 1D CNN over a `(6, 10)` input
Status:
- Accepted

Evidence:
- [training/model.py](training/model.py)
- [shared/feature_contract.py](shared/feature_contract.py)
- [model/cnn.c](model/cnn.c)

Decision:
- Represent each inference window as 6 channels across 10 timesteps and classify it with a compact Conv1d-based network.

Reason:
- The feature contract is naturally sequential, the model stays small, and ai8x research indicates Conv1d is directly supportable on MAX78000.

Consequence:
- All data producers must preserve the row-to-window semantics expected by the Conv1d input layout.

### ADR-003: Use quantization-aware training before deployment
Status:
- Accepted

Evidence:
- [training/model.py](training/model.py)
- [training/train.py](training/train.py)
- [training/caids_q8.pth](training/caids_q8.pth)

Decision:
- Prepare the model for 8-bit deployment using QAT instead of relying on a purely post-training conversion path.

Reason:
- The target accelerator expects quantized execution, and QAT helps reduce accuracy loss when moving to deployment constraints.

Consequence:
- Training code must preserve fusion and observer behavior compatible with export and synthesis.

### ADR-004: Separate host-side bridge logic from training logic
Status:
- Accepted

Evidence:
- [bridge/pipeline.py](bridge/pipeline.py)
- [bridge/loopback.py](bridge/loopback.py)
- [training/simulator.py](training/simulator.py)

Decision:
- Keep real-time buffering/packetization in `bridge/` and keep dataset generation and learning logic in `training/`.

Reason:
- This separation makes it easier to validate the feature path independently from model training and to reuse the bridge in hardware tests.

Consequence:
- Contract synchronization becomes critical, which is why ADR-001 matters so much.

### ADR-005: Use synthetic or simulated traffic during early development
Status:
- Accepted

Evidence:
- [training/dataset.py](training/dataset.py)
- [training/simulator.py](training/simulator.py)
- [bridge/loopback.py](bridge/loopback.py)

Decision:
- Train and validate the IDS using generated vehicle/CAN behavior before full hardware capture or live-stream integration.

Reason:
- It enables rapid iteration and lets the team test model behavior before the embedded path is complete.

Consequence:
- The realism gap between synthetic and real CAN traffic remains a risk that must be revisited later.

### ADR-006: Target MAX78000 deployment through ai8x synthesis artifacts
Status:
- Accepted, with open consistency checks

Evidence:
- [NOTES_ai8x_constraints.md](NOTES_ai8x_constraints.md)
- [model/caids](model/caids)
- [model/cnn.c](model/cnn.c)
- [model/cnn.h](model/cnn.h)

Decision:
- Port the current CAIDS Conv1d architecture into the ai8x/MAX78000 toolchain rather than redesigning the model from scratch.

Reason:
- The compatibility notes indicate the existing operator family and dimensions are already close to ai8x-friendly constraints.

Consequence:
- Generated code and the shared contract must stay synchronized, especially around output count, final-layer sizing, and packet expectations.

## Open Architectural Risks

### RISK-001: Generated output-count drift between deployment files and shared contract
Observed:
- [shared/feature_contract.py](shared/feature_contract.py) defines 5 classes.
- [model/cnn.c](model/cnn.c) unloads 5 outputs.
- [model/cnn.h](model/cnn.h) originally declared `CNN_NUM_OUTPUTS 3`.
- The local generated headers were corrected to `5` on 2026-03-24 to match the generated unload path.

Impact:
- Stale generated headers can cause firmware to allocate the wrong output shape or silently drift from the deployed contract.

Needed decision:
- The next full ai8x regeneration should preserve `5` outputs end-to-end. If the header falls back to `3` again, the synthesis or copy flow needs investigation instead of another manual patch.

### RISK-002: Empty firmware and bridge entry files
Observed:
- [firmware/main.c](firmware/main.c), [bridge/send_features.py](bridge/send_features.py), and [bridge/pc_bridge.py](bridge/pc_bridge.py) are currently empty.

Impact:
- The end-to-end deployment path is not yet captured in executable project code at those boundaries.

Needed decision:
- Decide whether these files are placeholders to be implemented, or whether the real source of truth has moved elsewhere and these should be removed to avoid confusion.

## Future ADRs To Add

### FUTURE-001: Final output precision choice
Question:
- Keep final layer output at 8-bit or move to `wide=True` / higher-precision final output in ai8x synthesis?

Why it matters:
- This affects classification fidelity, synthesis settings, and how post-processing is done on-device.

### FUTURE-002: Deployment inference boundary
Question:
- Should softmax/class decoding happen on the MCU, on the host, or not at all?

Why it matters:
- This changes latency, code size, UART bandwidth, and debugging visibility.

### FUTURE-003: Real-data integration strategy
Question:
- When real CAN traces become available, do they replace synthetic data or augment it with domain adaptation and parity tests?

Why it matters:
- The answer changes dataset design, evaluation methodology, and the trustworthiness of deployed accuracy claims.

### FUTURE-004: Hardware/host packet contract versioning
Question:
- Should UART payloads be versioned explicitly so contract changes are detectable at runtime?

Why it matters:
- Versioning would reduce silent breakage when feature order, scaling, or class count changes.

## Update Rule

When a meaningful architectural decision is made:
1. Add a new ADR entry with a stable ID.
2. Record status as `Proposed`, `Accepted`, `Superseded`, or `Rejected`.
3. Name the decision, reason, and consequences.
4. Link the code or notes that implement or justify it.

