# IDS_Hardware Change Log

Purpose: keep a running, chronological record of meaningful structural and code changes in this project, including the reason or diagnosis behind each change.

Important note:
- This workspace is not a Git repository, so entries before 2026-03-23 are reconstructed from file timestamps and code inspection.
- Reconstructed entries are marked as `Inferred`.
- New work from this point onward should be appended here immediately after significant changes.
- Security note: repo links are kept relative, and machine-specific absolute paths are replaced with placeholders such as `<repo-root>`, `<msdk-root>`, and `<cfs-root>`.

## Chronological Record

### 2026-03-16 22:11 `Inferred`
Change:
- Added [bridge/send_features.py](bridge/send_features.py) as an early PC-side bridge component.

Reason / diagnosis:
- The project needed a host-side path to move feature windows toward embedded inference or UART transport.

### 2026-03-16 22:17 `Inferred`
Change:
- Added [firmware/main.c](firmware/main.c).

Reason / diagnosis:
- Introduced the firmware application entry point so the IDS pipeline could exist on the embedded target, even though the file is currently empty and likely served as a placeholder/start point.

### 2026-03-16 22:18 `Inferred`
Change:
- Added [bridge/pc_bridge.py](bridge/pc_bridge.py).

Reason / diagnosis:
- Expanded the host-side bridge tooling, likely to separate transport orchestration from raw feature sending.

### 2026-03-17 11:49 `Inferred`
Change:
- Added [tests/test_contract_parity.py](tests/test_contract_parity.py).

Reason / diagnosis:
- The project needed a parity guard around the feature contract so training-side and bridge-side preprocessing stayed aligned.

### 2026-03-17 11:50 `Inferred`
Change:
- Added [training/requirements.txt](training/requirements.txt).

Reason / diagnosis:
- Training dependencies were formalized so the model and evaluation workflow could be reproduced.

### 2026-03-17 11:51 `Inferred`
Change:
- Added [bridge/pipeline.py](bridge/pipeline.py).
- Centralized sliding-window buffering, normalization, tensor conversion, and UART packet generation behind `FeaturePipeline`.

Reason / diagnosis:
- Raw feature rows needed to be accumulated into the fixed 10-step model input contract and emitted consistently for both software simulation and hardware transport.

### 2026-03-17 12:04 `Inferred`
Change:
- Added [bridge/loopback.py](bridge/loopback.py).

Reason / diagnosis:
- A loopback harness was needed to validate the host pipeline and quantized model without depending on real hardware during bring-up.

### 2026-03-23 09:56 `Inferred`
Change:
- Added or substantially updated [training/model.py](training/model.py).
- Added or substantially updated [training/training_utils.py](training/training_utils.py).
- Introduced the `CAIDS_CNN` quantization-aware 1D CNN with two Conv1d blocks, flatten, hidden linear layer, dropout, and classifier head.

Reason / diagnosis:
- The project needed a compact architecture that matched the CAN feature shape `(6, 10)` while remaining compatible with QAT and eventual MAX78000 deployment.

### 2026-03-23 10:03 `Inferred`
Change:
- Added [shared/feature_contract.py](shared/feature_contract.py).
- Centralized `FEATURE_ORDER`, input dimensions, normalization statistics, clipping, class names, and UART packet framing.

Reason / diagnosis:
- The system needed a single source of truth for preprocessing and packet layout to stop training, bridge, and deployment code from drifting apart.

### 2026-03-23 10:04 `Inferred`
Change:
- Added or substantially updated [training/train.py](training/train.py).
- Defined the QAT training loop, class reweighting, validation tracking, scheduler behavior, and TorchScript export of the quantized model.

Reason / diagnosis:
- The model required a reproducible path from synthetic dataset generation to deployable quantized artifact.

### 2026-03-23 10:30 `Inferred`
Change:
- Added or substantially updated [training/dataset.py](training/dataset.py).
- Added or substantially updated [training/simulator.py](training/simulator.py).

Reason / diagnosis:
- The training stack needed synthetic CAN traffic generation and labeled scenarios to train and exercise the IDS before full hardware integration.

### 2026-03-23 10:32 `Inferred`
Change:
- Produced [training/caids_q8.pth](training/caids_q8.pth).

Reason / diagnosis:
- Quantized model export was required to verify the training pipeline and to provide a deployable artifact for simulation and downstream conversion.

### 2026-03-23 10:40 `Inferred`
Change:
- Added or substantially updated [training/evaluate.py](training/evaluate.py).
- Produced [training/confusion_matrix.png](training/confusion_matrix.png).

Reason / diagnosis:
- The project needed post-training evaluation and class-level error visibility to diagnose residual confusion between traffic classes.

### 2026-03-23 11:55 `Inferred`
Change:
- Added [NOTES_ai8x_constraints.md](NOTES_ai8x_constraints.md).

Reason / diagnosis:
- The team needed a read-only compatibility check before porting the current CNN into the ai8x/MAX78000 toolchain.

### 2026-03-23 17:08 `Inferred`
Change:
- Produced [model/caids_q8.pth.tar](model/caids_q8.pth.tar).

Reason / diagnosis:
- The ai8x synthesis flow required a checkpoint-format artifact suitable for conversion into MAX78000 deployment code.

### 2026-03-23 17:20 `Inferred`
Change:
- Added generated deployment artifacts under [model/caids](model/caids), including generated `cnn.c`, `cnn.h`, `weights.h`, sample data/output headers, build files, and launch/debug settings.
- Added generated top-level copies [model/cnn.c](model/cnn.c) and [model/cnn.h](model/cnn.h).
- Current generated network shape shows a 4-layer 1D CNN mapped to MAX78000 with outputs for 5 classes.

Reason / diagnosis:
- The project reached the hardware-deployment stage and needed generated accelerator code from ai8x synthesis.
- This stage also surfaced a likely mismatch risk: [model/cnn.h](model/cnn.h) declares `CNN_NUM_OUTPUTS 3`, while [model/cnn.c](model/cnn.c) unloads 5 outputs and the shared contract defines 5 classes. That should be treated as a deployment-consistency issue until verified or regenerated.

### 2026-03-23 17:xx
Change:
- Added [chage_log.md](chage_log.md), [command_log.md](command_log.md), and [adr.md](adr.md).

Reason / diagnosis:
- Persistent project memory was missing. These records were introduced so structural changes, executed commands, and architectural decisions are documented in one place and can be extended in later work.

### 2026-03-23 `Inferred current-session`
Change:
- Implemented Phase C Task 1 foundation in [firmware/main.c](firmware/main.c).
- Added a UART packet parser state machine for the shared 64-byte framing contract: `SOF(0xA5,0x5A)`, sequence byte, 60-byte payload, XOR CRC.
- Added payload repacking from channel-first packet order into the ai8x HWC SRAM layout expected by the generated CAIDS network.
- Integrated the generated CNN wrapper flow from [model/caids/main.c](model/caids/main.c) so valid packets trigger `cnn_init`, `cnn_configure`, input load, `cnn_start`, `cnn_unload`, and result printing.

Reason / diagnosis:
- Phase C needed the first real firmware-side ingestion path from bridge packets into accelerator inference.
- The ai8x synthesis project already provided the correct wrapper sequence, so the safest approach was to reuse that integration template and only replace sample-input loading with parsed UART payload loading.
- The packet payload needed explicit repacking because the bridge transmits 60 signed bytes in channel-first order while the generated CNN input memory expects timestep-wise HWC packing.

### 2026-03-24
Change:
- Fixed `CNN_NUM_OUTPUTS` from `3` to `5` in [model/caids/cnn.h](model/caids/cnn.h) and [model/cnn.h](model/cnn.h) to match the generated unload path and the shared 5-class contract.
- Updated [firmware/main.c](firmware/main.c) to rely on the generated `CNN_NUM_OUTPUTS` constant instead of a local workaround.
- Staged generated deployment sources into [firmware/cnn.c](firmware/cnn.c), [firmware/cnn.h](firmware/cnn.h), [firmware/weights.h](firmware/weights.h), [firmware/Makefile](firmware/Makefile), and [firmware/project.mk](firmware/project.mk).

Reason / diagnosis:
- Build preparation confirmed that the generated header was stale after synthesis: [model/caids/cnn.c](model/caids/cnn.c) documents a `(5, 1, 1)` output shape while the paired header still declared `3`.
- The mismatch had to be fixed at the source before compilation so firmware, generated code, and the shared feature contract agree at compile time.
- The next planned step, a local MSDK build, is currently blocked because `arm-none-eabi-gcc` and `make` are not available on `PATH` in this environment.

### 2026-03-24
Change:
- Validated that [firmware/Makefile](firmware/Makefile) uses `AUTOSEARCH ?= 1` and `SRCS += $(wildcard $(addsuffix /*.c, $(VPATH)))`, so the staged [firmware/cnn.c](firmware/cnn.c) will be compiled automatically from the project root.
- Confirmed the Phase 2 SDK environment exists at `<msdk-root>` and that `setenv.bat` is present.
- Verified that the SDK environment exposes `make`, `arm-none-eabi-gcc`, and `openocd` once `setenv.bat` runs.
- Attempted the firmware build from [firmware](firmware).

Reason / diagnosis:
- The exact `&&`-chained Phase 2 command sequence does not progress on this machine because `setenv.bat` returns exit code `1`, even though it sets the expected environment variables.
- The first real build failure is not a firmware compile error yet: `make` resolves to `<msdk-root>\\Tools\\MSYS2\\usr\\bin\\make.exe`, which aborts immediately with `*** fatal error - couldn't create signal pipe, Win32 error 5`.
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

### 2026-03-27
Change:
- Replaced [firmware/main.c](firmware/main.c) with the user-supplied UART/CNN firmware implementation.
- Added packet framing constants, `receive_packet()`, UART startup prints, CNN bring-up calls, inference wait logic, result unload, argmax classification, and `SEQ`/`CLASS` serial output.
- Preserved the placeholder note indicating the CNN input-loading call still needs to be replaced with the project-specific implementation.

Reason / diagnosis:
- The firmware entry point needed to match the provided reference implementation exactly so the embedded runtime follows the requested UART packet receive and CNN inference flow.
- The logging step was also explicitly requested as a required part of future edits, so this change is recorded here immediately.

### 2026-03-27
Change:
- Replaced [firmware/main.c](firmware/main.c) again with the user-supplied UART-write variant.
- Removed `stdio.h` usage and replaced `printf`-based status/result output with direct `MXC_UART_Write` calls through `uart_print()` and `uart_print_uint8()`.
- Added explicit `CRC_FAIL` reporting on packet checksum mismatch and reset `cnn_time` to `0` after each inference wait completes.

Reason / diagnosis:
- The firmware needed to stop depending on formatted stdio output and instead emit serial status directly through UART0 writes.
- This keeps the code closer to bare-metal bring-up expectations and matches the requested serial-output behavior exactly.

### 2026-03-27
Change:
- Replaced [firmware/main.c](firmware/main.c) with the explicit Phase C Task 1 UART parser state machine.
- Implemented the required parser states `WAIT_SOF1 -> WAIT_SOF2 -> READ_SEQ -> READ_PAYLOAD -> READ_CRC -> VALIDATE`.
- Changed Task 1 behavior to echo `PARSE_OK,<seq>\n` for valid packets and `CRC_FAIL,<seq>\n` for failed CRC validation.
- Simplified `main()` to UART bring-up plus `run_parser()` so the firmware now targets the Task 1 parser pass check only.

Reason / diagnosis:
- The prior implementation had SOF detection and CRC checking, but it did not satisfy the plan's required state-machine structure or the exact Task 1 pass-check output.
- Phase C Task 1 needs the board to act as a packet parser verifier before later CNN integration tasks are layered on top.

### 2026-03-27
Change:
- Attempted the Phase C Task 1 build command against [firmware](firmware) using the CodeFusion Studio toolchain paths provided by the user.
- Verified that `make.exe`, `openocd.exe`, and `putty.exe` are present on this machine and that PuTTY can be launched for `COM4`.
- Confirmed that [firmware/build/firmware.elf](firmware/build/firmware.elf) does not exist yet, so the flash step is currently blocked.

Reason / diagnosis:
- The first build attempt failed because it was launched from the repo root instead of [firmware](firmware).
- The corrected build attempt then failed inside the MSDK makefiles because the workspace path was being split at the space in the username, producing malformed make targets.
- A `cmd.exe` retry from the short-path form changed the failure mode but still did not compile, reporting `Makefile:354: <cfs-root>/SDK/MAX: Permission denied` and stopping before any ELF was produced.

### 2026-03-27
Change:
- Replaced [firmware/main.c](firmware/main.c) with the user-supplied UART-flush parser variant.
- Added `uart_flush()` using `MXC_UART_GetActive(MXC_UART0) == E_BUSY` and now flush after each `MXC_UART_Write()` inside `uart_print()`.
- Kept the explicit Task 1 parser state machine and `PARSE_OK,<seq>` / `CRC_FAIL,<seq>` serial responses unchanged apart from the transmit-flush behavior.

Reason / diagnosis:
- This rewrite is intended to address the reported UART TX buffering / flashing issue by waiting for the UART peripheral to finish transmitting each message before continuing.
- It preserves the Task 1 parser pass-check behavior while making serial output more deterministic during board-side verification.

### 2026-03-27
Change:
- Replaced [firmware/main.c](firmware/main.c) with the delay-based UART flush version.
- Added `#include "mxc_delay.h"` and changed `uart_flush()` to `MXC_Delay(MXC_DELAY_MSEC(10))`.
- Kept the Task 1 parser state machine and `PARSE_OK,<seq>` / `CRC_FAIL,<seq>` protocol unchanged while swapping the transmit-completion workaround.

Reason / diagnosis:
- The previous flush strategy using `MXC_UART_GetActive()` was replaced with a fixed post-write delay to better address the observed UART TX buffer / flashing issue on hardware.
- This keeps the parser logic stable while using a simpler, timing-based transmit completion guard at `115200` baud.

### 2026-03-27
Change:
- Updated [firmware/main.c](firmware/main.c) to use blocking byte-at-a-time UART transmit via `MXC_UART_WriteCharacter()` instead of `MXC_UART_Write()`.
- Changed `uart_flush()` to wait on `MXC_UART_ReadyForSleep(MXC_UART0)` so the UART fully drains before returning.
- Added a `500 ms` startup delay before the boot banner so the USB-UART bridge / PuTTY has time to attach after reset.

Reason / diagnosis:
- The garbled startup text pattern (`CA-IDS fiTask 1: u`) is more consistent with partial/interleaved early boot transmission than with parser logic failure.
- Local MAX/SDK examples use blocking per-byte console writes and FIFO/sleep readiness checks, which is a better fit for reliable short control messages on MAX78000 than the previous buffered-write helpers.
- Opening PuTTY after OpenOCD resets the board can still miss the beginning of the banner, so the startup delay is intended to reduce that race as well.

### 2026-03-28
Change:
- Updated [firmware/main.c](firmware/main.c) for Phase C Task 2 ring-buffer handling.
- Added `rx_buf[64]` to retain one full validated packet and `window[10][6]` to hold the parsed feature window.
- Added `uart_print_int8()` and `load_window()` so validated payload bytes are copied into the `(10 x 6)` feature window and the first decoded feature can be reported.
- Changed the valid-packet response to `PARSE_OK,<seq> W[0][0]=<value>` and updated the boot banner to `Task 2: Ring buffer active`.
- Replaced [test_packet_sender.py](test_packet_sender.py) with the Task 2 pass-check script that sends a packet where `window[0][0] = 42`.

Reason / diagnosis:
- The Phase C plan requires the firmware to keep one packet buffer plus a decoded `10 x 6` signed feature window before later CNN input integration.
- A deterministic pass check was needed to prove that payload bytes are being copied into the window with the expected indexing and signed interpretation.
- Using a known first-feature value of `42` gives a simple board-side verification that the parser, packet storage, and window loading all succeeded end-to-end.

### 2026-03-28
Change:
- Updated [firmware/main.c](firmware/main.c) for Phase C Task 3 CNN integration.
- Added CNN bring-up in `main()` with `cnn_enable()`, `cnn_init()`, `cnn_load_weights()`, `cnn_load_bias()`, and `cnn_configure()` before entering the parser loop.
- Added `load_cnn_input()` to repack the buffered `(10 x 6)` window into the ai8x-generated HWC SRAM layout across `0x50400000` and `0x50408000`.
- Added `run_inference()` to start the accelerator, wait for `cnn_time`, unload outputs, and return the argmax class index.
- Changed the valid-packet response to `PARSE_OK,<seq> CLASS=<idx>` and replaced [test_packet_sender.py](test_packet_sender.py) with the Task 3 class-index pass-check script.

Reason / diagnosis:
- Phase C Task 3 requires a valid buffered window to flow all the way into the generated MAX78000 CNN runtime and produce a class index without crashing.
- The generated CAIDS network does not consume a flat byte stream directly; it expects HWC-packed input words in two SRAM regions, so the Task 2 buffer had to be repacked before `cnn_start()`.
- Reusing the generated `cnn.c` / `cnn.h` runtime interface and matching its documented memory layout is the safest path for hardware inference bring-up.

### 2026-03-28
Change:
- Updated [firmware/main.c](firmware/main.c) for Phase C Task 4 result output formatting.
- Added `CLASS_NAMES`, `uart_print_uint32()`, and `send_result()` so inference results are emitted as `OK,<score>` for Normal traffic and `ALERT,<class_name>,<score>` for attack classes.
- Changed `run_inference()` to return the predicted label while filling the caller-provided output buffer used for score reporting.
- Replaced [test_packet_sender.py](test_packet_sender.py) with the Task 4 host-side pass-check script that validates both a normal response and an alert response.

Reason / diagnosis:
- Phase C Task 4 requires the board to publish a host-consumable result line immediately after `cnn_unload()` rather than a debug-oriented class index.
- The existing Task 3 CNN input path was kept intact because the generated CAIDS network still expects the shared channels-first payload to be repacked into ai8x HWC SRAM layout before inference.
- The host-side attack test keeps the shared packet contract as the source of truth by writing the RPM spike into the feature-3 channels-first payload slice.

### 2026-03-28
Change:
- Added [bridge/loopback_hitl.py](bridge/loopback_hitl.py) for Phase C Task 5 hardware-in-the-loop roundtrip validation.
- The new script opens a live serial port, sends normalized windows to the board using the shared packet contract, runs the same windows through the desktop TorchScript model, and compares predictions packet-by-packet.
- Added handling for `OK,<score>`, `ALERT,<class>,<score>`, timeouts, CRC failures, per-class counts, and final agreement reporting against the `>= 95%` pass criterion.

Reason / diagnosis:
- Task 5 is a laptop-side integration step; the Task 4 firmware already provides the required on-board inference and result-line protocol.
- The repo's trained artifact at [training/caids_q8.pth](training/caids_q8.pth) is a TorchScript-exported quantized model, so the HITL loopback should load it the same way as the existing desktop evaluation path.
- Using the shared packet builder and simulator/injector pipeline keeps board and desktop inputs aligned so any disagreement reflects inference drift rather than transport-format mismatch.

### 2026-03-28
Change:
- Fixed [shared/feature_contract.py](shared/feature_contract.py) packet serialization for signed int8 payloads.
- Changed `build_packet()` to emit the normalized payload via the NumPy int8 byte buffer directly instead of converting negative values through `bytes(payload.tolist())`.

Reason / diagnosis:
- The new Task 5 HITL loopback exposed a Python-side serialization bug: normalized feature payloads commonly contain negative int8 values such as `-127`, and Python's `bytes([...])` rejects integers outside `0..255`.
- The firmware expects raw two's-complement payload bytes on UART, so serializing the NumPy int8 buffer directly is the correct transport representation.

### 2026-03-29
Change:
- Updated [firmware/main.c](firmware/main.c) to document and lock in the confirmed Task 5 CNN input layout from [model/caids/sampledata.h](model/caids/sampledata.h).
- Kept the channels-first payload decode in `load_window()` and clarified `load_cnn_input()` so features `0..3` are packed into `0x50400000` and features `4..5` into `0x50408000` per timestep in little-endian order.
- Removed the now-unused `uart_print_int32()` helper and updated the boot banner to `Task 5: Correct input layout active`.

Reason / diagnosis:
- HITL parity work narrowed the remaining investigation to exact accelerator input layout rather than UART framing or parser correctness.
- The generated ai8x sample data confirms the per-timestep packing scheme, so the firmware should state that layout explicitly to avoid future regressions.
- Cleaning up the unused integer-print helper removes a build warning while keeping the Task 4/5 result-output behavior unchanged.

