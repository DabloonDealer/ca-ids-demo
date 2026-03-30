import sys

import numpy as np
import os
import serial

sys.path.insert(0, r"C:\Users\Amiltha M\IDS_Hardware")

PORT = "COM4"
BAUD = 115200

sample = np.load(r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training\sample_caids.npy")
print("Sample shape:", sample.shape)
print("Sample values (channels-first, 6x10):")
print(sample)

# Flatten channels-first, cast to int8 then uint8 for byte packing
payload = sample.flatten(order="C").astype(np.int8).astype(np.uint8)
print("\nPayload (60 bytes as uint8):")
print(payload)

seq = 0
payload_bytes = bytes(payload.tolist())
crc = seq
for b in payload_bytes:
    crc ^= b
packet = bytes([0xA5, 0x5A, seq]) + payload_bytes + bytes([crc & 0xFF])
assert len(packet) == 64, f"Wrong packet length: {len(packet)}"

print("\nSending synthesiser sample input to board...")
with serial.Serial(PORT, BAUD, timeout=5) as s:
    s.write(packet)
    response = s.readline()
    decoded = response.decode(errors="replace").strip()
    print(f"Board response: {decoded}")

sample_out = r"C:\Users\Amiltha M\IDS_Hardware\model\caids\sampleoutput.h"
if os.path.exists(sample_out):
    with open(sample_out) as f:
        print("\nsampleoutput.h:")
        print(f.read())
else:
    print("\nNo sampleoutput.h found")
