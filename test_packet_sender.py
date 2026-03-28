import serial

PORT = "COM4"
BAUD = 115200
CLASS_NAMES = ["Normal", "DoS", "Spoofing", "Replay", "Fuzzing"]

def build_packet(seq, payload_bytes):
    assert len(payload_bytes) == 60
    crc = seq
    for b in payload_bytes:
        crc ^= b
    return bytes([0xA5, 0x5A, seq]) + bytes(payload_bytes) + bytes([crc])


def send_and_receive(packet):
    with serial.Serial(PORT, BAUD, timeout=5) as s:
        s.write(packet)
        response = s.readline()
    return response.decode().strip()


def run_test(seq, payload, description, expect_alert=False):
    packet = build_packet(seq, payload)
    assert len(packet) == 64
    response = send_and_receive(packet)
    print(f"[{description}] Board response: {response}")

    if expect_alert:
        if response.startswith("ALERT,"):
            parts = response.split(",")
            print(f"  ALERT detected - class: {parts[1]}, score: {parts[2]}")
            return True
        print(f"  FAILED - expected ALERT, got: {response}")
        return False

    if response.startswith("OK,"):
        print(f"  Normal traffic confirmed - score: {response.split(',')[1]}")
        return True

    print(f"  FAILED - expected OK, got: {response}")
    return False


p_normal = bytearray(60)
r1 = run_test(0, p_normal, "Normal payload", expect_alert=False)

# Shared packet contract is channels-first, so feature 3 occupies bytes 30..39.
p_dos = bytearray(60)
for t in range(10):
    p_dos[3 * 10 + t] = 127
r2 = run_test(1, p_dos, "DoS payload", expect_alert=True)

print()
if r1 and r2:
    print("Task 4 PASS CHECK: COMPLETE")
else:
    print("Task 4 PASS CHECK: FAILED - check responses above")
