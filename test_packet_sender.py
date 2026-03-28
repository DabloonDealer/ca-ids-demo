import serial

PORT = "COM4"
BAUD = 115200

seq = 0
payload = bytes(60)  # all zeros

crc = seq
for b in payload:
    crc ^= b

packet = bytes([0xA5, 0x5A, seq]) + payload + bytes([crc])
assert len(packet) == 64, f"Packet length wrong: {len(packet)}"

with serial.Serial(PORT, BAUD, timeout=3) as s:
    s.write(packet)
    response = s.readline()
    decoded = response.decode().strip()
    print("Board response:", decoded)
    if decoded == "PARSE_OK,0":
        print("Task 1 PASS CHECK: COMPLETE")
    else:
        print("Task 1 PASS CHECK: FAILED — expected PARSE_OK,0")
