import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.ao.quantization as tq

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.feature_contract import CLASS_NAMES, N_FEATURES, N_TIMESTEPS


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Conv1d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU(inplace=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv(x)
        x = self.bn(x)
        return self.relu(x)

    def fuse_model(self) -> None:
        tq.fuse_modules(self, [['conv', 'bn', 'relu']], inplace=True)


class CAIDS_CNN(nn.Module):
    def __init__(self, num_classes: int = len(CLASS_NAMES)):
        super().__init__()
        self.quant = tq.QuantStub()
        self.block1 = ConvBlock(N_FEATURES, 24)
        self.block2 = ConvBlock(24, 48)
        self.fc1 = nn.Linear(48 * N_TIMESTEPS, 48)
        self.relu = nn.ReLU(inplace=False)
        self.drop = nn.Dropout(0.5)
        self.fc2 = nn.Linear(48, num_classes)
        self.dequant = tq.DeQuantStub()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.quant(x)
        x = self.block1(x)
        x = self.block2(x)
        x = torch.flatten(x, start_dim=1)
        x = self.relu(self.fc1(x))
        x = self.drop(x)
        x = self.fc2(x)
        return self.dequant(x)

    def fuse_model(self) -> None:
        self.block1.fuse_model()
        self.block2.fuse_model()
        tq.fuse_modules(self, [['fc1', 'relu']], inplace=True)


def get_qat_ready_model(device: str | torch.device = 'cpu') -> nn.Module:
    model = CAIDS_CNN().to(device)
    model.eval()
    model.fuse_model()
    model.train()
    model.qconfig = tq.get_default_qat_qconfig('fbgemm')
    tq.prepare_qat(model, inplace=True)
    return model

