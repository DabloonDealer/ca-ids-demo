import serial

PORT = "COM4"
BAUD = 115200

# All-zeros payload = Normal class (class 0) expected.
seq = 0
payload = bytes(60)

crc = seq
for b in payload:
    crc ^= b

packet = bytes([0xA5, 0x5A, seq]) + payload + bytes([crc])
assert len(packet) == 64

with serial.Serial(PORT, BAUD, timeout=3) as s:
    s.write(packet)
    response = s.readline()
    decoded = response.decode().strip()
    print("Board response:", decoded)
    if "PARSE_OK,0" in decoded and "CLASS=" in decoded:
        class_idx = int(decoded.split("CLASS=")[1])
        classes = ["Normal", "DoS", "Spoofing", "Replay", "Fuzzing"]
        print(f"Predicted class: {classes[class_idx]} ({class_idx})")
        print("Task 3 PASS CHECK: COMPLETE")
    else:
        print(f"Task 3 PASS CHECK: FAILED - got: {decoded}")
