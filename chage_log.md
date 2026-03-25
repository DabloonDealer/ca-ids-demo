# IDS_Hardware Change Log

Purpose: keep a running, chronological record of meaningful structural and code changes in this project, including the reason or diagnosis behind each change.

Important note:
- This workspace is not a Git repository, so entries before 2026-03-23 are reconstructed from file timestamps and code inspection.
- Reconstructed entries are marked as `Inferred`.
- New work from this point onward should be appended here immediately after significant changes.

## Chronological Record

### 2026-03-16 22:11 `Inferred`
Change:
- Added [bridge/send_features.py](/c:/Users/Amiltha%20M/IDS_Hardware/bridge/send_features.py) as an early PC-side bridge component.

Reason / diagnosis:
- The project needed a host-side path to move feature windows toward embedded inference or UART transport.

### 2026-03-16 22:17 `Inferred`
Change:
- Added [firmware/main.c](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/main.c).

Reason / diagnosis:
- Introduced the firmware application entry point so the IDS pipeline could exist on the embedded target, even though the file is currently empty and likely served as a placeholder/start point.

### 2026-03-16 22:18 `Inferred`
Change:
- Added [bridge/pc_bridge.py](/c:/Users/Amiltha%20M/IDS_Hardware/bridge/pc_bridge.py).

Reason / diagnosis:
- Expanded the host-side bridge tooling, likely to separate transport orchestration from raw feature sending.

### 2026-03-17 11:49 `Inferred`
Change:
- Added [tests/test_contract_parity.py](/c:/Users/Amiltha%20M/IDS_Hardware/tests/test_contract_parity.py).

Reason / diagnosis:
- The project needed a parity guard around the feature contract so training-side and bridge-side preprocessing stayed aligned.

### 2026-03-17 11:50 `Inferred`
Change:
- Added [training/requirements.txt](/c:/Users/Amiltha%20M/IDS_Hardware/training/requirements.txt).

Reason / diagnosis:
- Training dependencies were formalized so the model and evaluation workflow could be reproduced.

### 2026-03-17 11:51 `Inferred`
Change:
- Added [bridge/pipeline.py](/c:/Users/Amiltha%20M/IDS_Hardware/bridge/pipeline.py).
- Centralized sliding-window buffering, normalization, tensor conversion, and UART packet generation behind `FeaturePipeline`.

Reason / diagnosis:
- Raw feature rows needed to be accumulated into the fixed 10-step model input contract and emitted consistently for both software simulation and hardware transport.

### 2026-03-17 12:04 `Inferred`
Change:
- Added [bridge/loopback.py](/c:/Users/Amiltha%20M/IDS_Hardware/bridge/loopback.py).

Reason / diagnosis:
- A loopback harness was needed to validate the host pipeline and quantized model without depending on real hardware during bring-up.

### 2026-03-23 09:56 `Inferred`
Change:
- Added or substantially updated [training/model.py](/c:/Users/Amiltha%20M/IDS_Hardware/training/model.py).
- Added or substantially updated [training/training_utils.py](/c:/Users/Amiltha%20M/IDS_Hardware/training/training_utils.py).
- Introduced the `CAIDS_CNN` quantization-aware 1D CNN with two Conv1d blocks, flatten, hidden linear layer, dropout, and classifier head.

Reason / diagnosis:
- The project needed a compact architecture that matched the CAN feature shape `(6, 10)` while remaining compatible with QAT and eventual MAX78000 deployment.

### 2026-03-23 10:03 `Inferred`
Change:
- Added [shared/feature_contract.py](/c:/Users/Amiltha%20M/IDS_Hardware/shared/feature_contract.py).
- Centralized `FEATURE_ORDER`, input dimensions, normalization statistics, clipping, class names, and UART packet framing.

Reason / diagnosis:
- The system needed a single source of truth for preprocessing and packet layout to stop training, bridge, and deployment code from drifting apart.

### 2026-03-23 10:04 `Inferred`
Change:
- Added or substantially updated [training/train.py](/c:/Users/Amiltha%20M/IDS_Hardware/training/train.py).
- Defined the QAT training loop, class reweighting, validation tracking, scheduler behavior, and TorchScript export of the quantized model.

Reason / diagnosis:
- The model required a reproducible path from synthetic dataset generation to deployable quantized artifact.

### 2026-03-23 10:30 `Inferred`
Change:
- Added or substantially updated [training/dataset.py](/c:/Users/Amiltha%20M/IDS_Hardware/training/dataset.py).
- Added or substantially updated [training/simulator.py](/c:/Users/Amiltha%20M/IDS_Hardware/training/simulator.py).

Reason / diagnosis:
- The training stack needed synthetic CAN traffic generation and labeled scenarios to train and exercise the IDS before full hardware integration.

### 2026-03-23 10:32 `Inferred`
Change:
- Produced [training/caids_q8.pth](/c:/Users/Amiltha%20M/IDS_Hardware/training/caids_q8.pth).

Reason / diagnosis:
- Quantized model export was required to verify the training pipeline and to provide a deployable artifact for simulation and downstream conversion.

### 2026-03-23 10:40 `Inferred`
Change:
- Added or substantially updated [training/evaluate.py](/c:/Users/Amiltha%20M/IDS_Hardware/training/evaluate.py).
- Produced [training/confusion_matrix.png](/c:/Users/Amiltha%20M/IDS_Hardware/training/confusion_matrix.png).

Reason / diagnosis:
- The project needed post-training evaluation and class-level error visibility to diagnose residual confusion between traffic classes.

### 2026-03-23 11:55 `Inferred`
Change:
- Added [NOTES_ai8x_constraints.md](/c:/Users/Amiltha%20M/IDS_Hardware/NOTES_ai8x_constraints.md).

Reason / diagnosis:
- The team needed a read-only compatibility check before porting the current CNN into the ai8x/MAX78000 toolchain.

### 2026-03-23 17:08 `Inferred`
Change:
- Produced [model/caids_q8.pth.tar](/c:/Users/Amiltha%20M/IDS_Hardware/model/caids_q8.pth.tar).

Reason / diagnosis:
- The ai8x synthesis flow required a checkpoint-format artifact suitable for conversion into MAX78000 deployment code.

### 2026-03-23 17:20 `Inferred`
Change:
- Added generated deployment artifacts under [model/caids](/c:/Users/Amiltha%20M/IDS_Hardware/model/caids), including generated `cnn.c`, `cnn.h`, `weights.h`, sample data/output headers, build files, and launch/debug settings.
- Added generated top-level copies [model/cnn.c](/c:/Users/Amiltha%20M/IDS_Hardware/model/cnn.c) and [model/cnn.h](/c:/Users/Amiltha%20M/IDS_Hardware/model/cnn.h).
- Current generated network shape shows a 4-layer 1D CNN mapped to MAX78000 with outputs for 5 classes.

Reason / diagnosis:
- The project reached the hardware-deployment stage and needed generated accelerator code from ai8x synthesis.
- This stage also surfaced a likely mismatch risk: [model/cnn.h](/c:/Users/Amiltha%20M/IDS_Hardware/model/cnn.h) declares `CNN_NUM_OUTPUTS 3`, while [model/cnn.c](/c:/Users/Amiltha%20M/IDS_Hardware/model/cnn.c) unloads 5 outputs and the shared contract defines 5 classes. That should be treated as a deployment-consistency issue until verified or regenerated.

### 2026-03-23 17:xx
Change:
- Added [chage_log.md](/c:/Users/Amiltha%20M/IDS_Hardware/chage_log.md), [command_log.md](/c:/Users/Amiltha%20M/IDS_Hardware/command_log.md), and [adr.md](/c:/Users/Amiltha%20M/IDS_Hardware/adr.md).

Reason / diagnosis:
- Persistent project memory was missing. These records were introduced so structural changes, executed commands, and architectural decisions are documented in one place and can be extended in later work.

### 2026-03-23 `Inferred current-session`
Change:
- Implemented Phase C Task 1 foundation in [firmware/main.c](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/main.c).
- Added a UART packet parser state machine for the shared 64-byte framing contract: `SOF(0xA5,0x5A)`, sequence byte, 60-byte payload, XOR CRC.
- Added payload repacking from channel-first packet order into the ai8x HWC SRAM layout expected by the generated CAIDS network.
- Integrated the generated CNN wrapper flow from [model/caids/main.c](/c:/Users/Amiltha%20M/IDS_Hardware/model/caids/main.c) so valid packets trigger `cnn_init`, `cnn_configure`, input load, `cnn_start`, `cnn_unload`, and result printing.

Reason / diagnosis:
- Phase C needed the first real firmware-side ingestion path from bridge packets into accelerator inference.
- The ai8x synthesis project already provided the correct wrapper sequence, so the safest approach was to reuse that integration template and only replace sample-input loading with parsed UART payload loading.
- The packet payload needed explicit repacking because the bridge transmits 60 signed bytes in channel-first order while the generated CNN input memory expects timestep-wise HWC packing.

### 2026-03-24
Change:
- Fixed `CNN_NUM_OUTPUTS` from `3` to `5` in [model/caids/cnn.h](/c:/Users/Amiltha%20M/IDS_Hardware/model/caids/cnn.h) and [model/cnn.h](/c:/Users/Amiltha%20M/IDS_Hardware/model/cnn.h) to match the generated unload path and the shared 5-class contract.
- Updated [firmware/main.c](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/main.c) to rely on the generated `CNN_NUM_OUTPUTS` constant instead of a local workaround.
- Staged generated deployment sources into [firmware/cnn.c](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/cnn.c), [firmware/cnn.h](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/cnn.h), [firmware/weights.h](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/weights.h), [firmware/Makefile](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/Makefile), and [firmware/project.mk](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/project.mk).

Reason / diagnosis:
- Build preparation confirmed that the generated header was stale after synthesis: [model/caids/cnn.c](/c:/Users/Amiltha%20M/IDS_Hardware/model/caids/cnn.c) documents a `(5, 1, 1)` output shape while the paired header still declared `3`.
- The mismatch had to be fixed at the source before compilation so firmware, generated code, and the shared feature contract agree at compile time.
- The next planned step, a local MSDK build, is currently blocked because `arm-none-eabi-gcc` and `make` are not available on `PATH` in this environment.

### 2026-03-24
Change:
- Validated that [firmware/Makefile](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/Makefile) uses `AUTOSEARCH ?= 1` and `SRCS += $(wildcard $(addsuffix /*.c, $(VPATH)))`, so the staged [firmware/cnn.c](/c:/Users/Amiltha%20M/IDS_Hardware/firmware/cnn.c) will be compiled automatically from the project root.
- Confirmed the Phase 2 SDK environment exists at `C:\\MaximSDK` and that `setenv.bat` is present.
- Verified that the SDK environment exposes `make`, `arm-none-eabi-gcc`, and `openocd` once `setenv.bat` runs.
- Attempted the firmware build from [firmware](/c:/Users/Amiltha%20M/IDS_Hardware/firmware).

Reason / diagnosis:
- The exact `&&`-chained Phase 2 command sequence does not progress on this machine because `setenv.bat` returns exit code `1`, even though it sets the expected environment variables.
- The first real build failure is not a firmware compile error yet: `make` resolves to `C:\\MaximSDK\\Tools\\MSYS2\\usr\\bin\\make.exe`, which aborts immediately with `*** fatal error - couldn't create signal pipe, Win32 error 5`.
- Because compilation never started, flashing and UART parser verification were not attempted in this session.

### 2026-03-24
Change:
- Exhausted the requested build-launch workarounds without changing firmware source.
- Retried the build from an elevated shell and confirmed the remaining problems are launch-context issues, not firmware C errors.

Reason / diagnosis:
- Elevated Option 1 no longer hits the MSYS2 signal-pipe crash, but the direct command forms either fail to enter the firmware directory correctly or cause `setenv.bat` to set `MAXIM_PATH` to the wrong folder when invoked by absolute path.
- Option 2 is unavailable on this SDK installation because `mingw32-make` is not present in the configured toolchain path.
- The next viable path is Option 3: build in CodeFusion Studio, which should own the environment and working-directory setup internally.

## Update Rule

After every significant change:
1. Append a new dated entry.
2. State exactly what changed.
3. Record the reason, bug, diagnosis, or constraint that motivated it.
4. If chronology is uncertain, mark the entry as `Inferred`.
