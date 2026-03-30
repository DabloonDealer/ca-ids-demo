# IDS_Hardware

Embedded CAN intrusion detection pipeline targeting the Analog Devices MAX78000. This project trains a compact 1D CNN on synthetic vehicle telemetry, converts it into ai8x/MAX78000 deployment artifacts, and wires the model into firmware that can receive feature windows over UART for on-device inference.

## What this repo contains

- A shared feature contract for preprocessing, class labels, and UART packet framing
- A Python training pipeline for a quantization-aware CAN IDS model
- Host-side bridge utilities for building feature windows and sending them toward hardware
- Generated ai8x synthesis output for MAX78000 deployment
- Firmware sources for the MAX78000 EV kit

The current class set is:

- `Normal`
- `DoS`
- `Spoofing`
- `Replay`
- `Fuzzing`

The model input contract is fixed at `6` features over `10` timesteps, arranged as `(channels=6, length=10)`.

## Repository layout

```text
.
|- firmware/           MAX78000 firmware project and generated CNN sources
|- bridge/             PC-side feature buffering and UART helpers
|- shared/             Source of truth for feature order, normalization, classes, packet format
|- training/           Dataset generation, QAT training, evaluation, exported model
|- model/              ai8x-generated deployment artifacts and checkpoints
|- ai8x-synthesis/     Local ai8x synthesis toolchain copy
|- ai8x-training/      Local ai8x training toolchain copy
|- tests/              Contract/parity tests
```

## End-to-end flow

1. Synthetic CAN-like telemetry is generated in `training/`.
2. The model is trained with quantization-aware training and exported as `training/caids_q8.pth`.
3. The checkpoint is converted into MAX78000 CNN code using the ai8x toolchain.
4. `bridge/` utilities normalize telemetry into the shared `(6, 10)` input contract and pack UART frames.
5. `firmware/` receives packets and runs inference on the MAX78000 CNN accelerator.

## Core files

- `shared/feature_contract.py`: feature order, normalization stats, clipping range, class names, UART framing
- `training/model.py`: compact QAT-ready 1D CNN
- `training/train.py`: training entry point
- `training/evaluate.py`: evaluation script and confusion matrix export
- `bridge/pipeline.py`: sliding-window buffering and packet generation
- `bridge/loopback.py`: software-only inference sanity check
- `bridge/loopback_hitl.py`: hardware-in-the-loop comparison between board and desktop predictions
- `firmware/main.c`: embedded entry point for UART-fed inference
- `test_packet_sender.py`: quick host-side packet/result check for the board

## Python workflow

Create or activate a Python environment, then install the local training dependencies:

```powershell
pip install -r training/requirements.txt
```

Train the model:

```powershell
python training/train.py
```

Evaluate the exported quantized model:

```powershell
python training/evaluate.py
```

Run the software loopback check:

```powershell
python bridge/loopback.py --model training/caids_q8.pth --samples 200
```

Run the hardware-in-the-loop roundtrip check:

```powershell
python bridge/loopback_hitl.py --port COM4 --samples 100
```

Run the simple board packet/result smoke test:

```powershell
python test_packet_sender.py
```

Run the parity tests:

```powershell
pytest tests/test_contract_parity.py
```

## Firmware / hardware notes

The embedded target is set up as a standard MSDK project for `MAX78000` on `EvKit_V1`. The firmware project expects the Analog Devices / Maxim SDK toolchain to be installed and available through the MSDK environment.

Important notes:

- `firmware/` contains generated CNN sources staged for the firmware build.
- The project is built around UART input at `115200` baud.
- The shared UART framing contract is defined in `shared/feature_contract.py`.
- The current firmware validates the 64-byte packet, repacks the `(10 x 6)` window into the ai8x input layout, runs CNN inference, and returns either `OK,<score>` or `ALERT,<class>,<score>`.
- Local project notes indicate that command-line builds on this machine were blocked by SDK shell/tooling issues, so CodeFusion Studio may be the easiest way to build/flash if the plain `make` flow is unstable.

## Model summary

- Input: `6 x 10`
- Architecture: 2 x `Conv1d` -> flatten -> hidden linear -> classifier
- Quantization: PyTorch QAT for deployment-friendly export
- Output classes: `5`
- Target device: `MAX78000`

Generated ai8x artifacts are included under `model/` and mirrored into `firmware/` for integration.

## Project status

This repository already includes:

- A trained quantized model at `training/caids_q8.pth`
- An evaluation output image at `training/confusion_matrix.png`
- ai8x-generated CNN sources under `model/` and `firmware/`
- UART packet parsing, CNN input repacking, and result-line output in `firmware/main.c`
- Host-side board verification utilities in `test_packet_sender.py` and `bridge/loopback_hitl.py`

Some bridge scripts are still prototype-level and may need cleanup before production use, but the shared contract and training path are in place.

## Upload notes

Before pushing this repository to GitHub, you may want to review whether large generated or local-only folders should stay in version control, especially:

- `venv/`
- `__pycache__/`
- large generated model artifacts if you prefer Git LFS
- local SDK/toolchain copies if they are already available elsewhere

## License

This repository contains project code plus vendor/generated content from the ai8x / MAX78000 toolchain. Review the license headers inside vendored and generated directories before publishing or redistributing the full repository.
