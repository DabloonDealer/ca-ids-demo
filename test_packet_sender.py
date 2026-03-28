import serial

PORT = "COM4"
BAUD = 115200

# Build a packet where window[0][0] = 42 for verification.
seq = 0
payload = bytearray(60)
payload[0] = 42

crc = seq
for b in payload:
    crc ^= b

packet = bytes([0xA5, 0x5A, seq]) + bytes(payload) + bytes([crc])
assert len(packet) == 64

with serial.Serial(PORT, BAUD, timeout=3) as s:
    s.write(packet)
    response = s.readline()
    decoded = response.decode().strip()
    print("Board response:", decoded)
    if "PARSE_OK,0" in decoded and "W[0][0]=42" in decoded:
        print("Task 2 PASS CHECK: COMPLETE")
    else:
        print(f"Task 2 PASS CHECK: FAILED - expected PARSE_OK,0 W[0][0]=42, got: {decoded}")
