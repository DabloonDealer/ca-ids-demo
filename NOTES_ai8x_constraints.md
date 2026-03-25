# NOTES ai8x Constraints

Phase B1 deliverable for Section 5 of the V3 execution plan.

Scope:
- Read-only compatibility research against `ai8x-training`
- No architecture code changes in this phase

Sources reviewed:
- `ai8x-training/README.md`
- `ai8x-training/ai8x.py`
- Current model: `training/model.py`

## Compatibility Matrix

| Constraint | Question to Answer | Finding |
| --- | --- | --- |
| Supported layer types | Which Conv, BN, Pool, Linear variants are supported? | `ai8x-training` supports `Conv1d`, `Conv2d`, `Linear`, `MaxPool1d/2d`, `AvgPool1d/2d`, fused pool+conv variants, fused `ReLU` and `Abs` variants, and BatchNorm-fused variants for conv layers. It also includes direct `Conv1d` support, so our current 1D CNN is not blocked on operator availability. |
| Activation restrictions | Is ReLU the only option? Clamp values? | Supported explicit activations are `ReLU`, `Abs`, or `None`. Even with `None`, 8-bit outputs are still clamped, so there is an implicit non-linearity. Our current ReLU-based model fits this requirement. |
| Padding restrictions | Which padding modes are valid per layer? | Padding is zero-padding only. For MAX78000 `Conv1d`, valid padding values are `0`, `1`, or `2`; for `Conv2d`, valid padding is `0`, `1`, or `2`. Our current `Conv1d(kernel_size=3, padding=1)` is within the supported range. |
| Channel count alignment | Must channel counts be multiples of 4, 8, or 64? | There is no hard global rule that all channels must be multiples of 8 or 64. Hardware uses 64 processors, and the README recommends multiples of 4 for efficiency in multi-pass processor mapping; NAS guidance recommends multiples of 64 for search efficiency, not as a general hard constraint. Current hidden widths `24` and `48` are acceptable and already multiples of 4. |
| Quantization bit-widths | Which layers support 8-bit vs other widths? | Data and activations are 8-bit by default on hardware. Weight and bias quantization options in `ai8x.py` are `1`, `2`, `4`, or `8` bits, and the README adds `binary` as a MAX78002-only alternative. The final layer can optionally be trained with `wide=True` and emitted as 32-bit output. |
| Input tensor layout | Expected layout for 1D input: channels-first or last? | For PyTorch training modules, `Conv1d` uses channels-first tensors (`N, C, L`). Internally, the hardware stores data in HWC groups of four channels, and the YAML/network description uses `in_channels` plus a 1D `in_dim` value. For CAIDS, the natural training shape remains `6 x 10`, i.e. 6 channels and length 10. |
| Conv1d support | Is Conv1d (1D convolution) directly supported? | Yes. `ai8x.py` defines `Conv1d`, fused `Conv1dReLU`, fused `Conv1dBNReLU`, plus fused max-pool and avg-pool 1D variants. This is the key reason the current architecture can be adapted instead of replaced. |
| Kernel size restrictions | Any limits on kernel size or dilation? | For MAX78000 `Conv1d`, kernel sizes `1` through `9` are supported. On MAX78000, stride must be `1` for `Conv1d`. Conv1d dilation is allowed subject to `(kernel_size - 1) * dilation < 9` or a smaller no-padding case; our current `kernel_size=3`, `stride=1`, `dilation=1` is fully safe. |

## Recommendation

ADAPT current model

Reason:
- The current CAIDS architecture is a small sequential 1D CNN with `Conv1d`, BatchNorm, ReLU, flatten, and Linear layers.
- `ai8x-training` directly supports this operator family on MAX78000.
- The current model already uses ai8x-friendly kernel size, padding, stride, and channel widths.
- No source in B1 indicates that Conv1d is forbidden or that a 2D redesign is required.

## Exact Structural Changes Needed If Adapting

1. Replace the custom PyTorch conv blocks in `training/model.py` with ai8x module equivalents, most likely `ai8x.FusedConv1dBNReLU` for the two convolution blocks.
2. Keep the same logical topology: two 1D conv blocks, flatten, hidden linear layer, output linear layer.
3. Keep the input contract as 6 channels by length 10; represent that in ai8x as `in_channels: 6` and 1D `in_dim: 10` in the network description.
4. Keep `kernel_size=3`, `padding=1`, `stride=1` for the conv layers because these settings are directly compatible with MAX78000 Conv1d support.
5. Preserve current hidden widths `24` and `48`; they are already multiples of 4 and do not force a width redesign.
6. Fold BatchNorm through the ai8x/QAT flow instead of carrying standalone BatchNorm to deployment. This is supported automatically during QAT.
7. Treat Dropout as training-only. It can be used during training, but it should not be relied on as a deployment operator.
8. Verify whether the final output should stay 8-bit or move to `wide=True` / 32-bit output for synthesis, depending on whether Phase B2 wants software softmax or extra final-layer precision.

## Current Model vs ai8x Risk Summary

Low risk:
- `Conv1d` availability
- `ReLU` activation
- `Linear` layers sized well below the `<=1024` in/out feature assertion in `ai8x.py`
- `kernel_size=3`, `padding=1`, `stride=1`
- Channel widths `24` and `48`

Moderate attention items for Phase B2:
- Replace generic PyTorch/QAT flow with ai8x-native module definitions and training entrypoints
- Confirm final output-width choice for synthesis
- Confirm the exact YAML/network description needed for the 1D CAIDS input contract

## Binary Gate For Phase B2

Decision: ADAPT current model

Phase B2 can proceed by converting the current CAIDS Conv1d network into an ai8x-native Conv1d architecture, without a from-scratch redesign.
