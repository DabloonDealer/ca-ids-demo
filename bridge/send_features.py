Create bridge/send_features.py:
import argparse, csv, struct, threading, time
import serial

SOF = b"\xA5\x5A"
ORDER = ["speed", "throttle", "brake", "rpm", "gear", "steering_angle"]

# Replace ranges with your training-time feature normalization metadata.
RANGES = {
    "speed": (0, 250),
    "throttle": (0, 100),
    "brake": (0, 100),
    "rpm": (0, 8000),
    "gear": (-1, 10),
    "steering_angle": (-540, 540),
}

def q8(v, lo, hi):
    v = max(lo, min(hi, float(v)))
    return int(round((v - lo) * 255.0 / (hi - lo) - 128.0))

def frame(seq, feats):
    payload = struct.pack("<6b", *feats)
    crc = 0
    for b in bytes([seq]) + payload:
        crc ^= b
    return SOF + bytes([seq]) + payload + bytes([crc])

def rx_thread(ser):
    buf = b""
    while True:
        chunk = ser.read(ser.in_waiting or 1)
        if not chunk:
            continue
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            print("MCU:", line.decode(errors="replace").strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--rate-hz", type=float, default=20.0)
    args = ap.parse_args()

    period = 1.0 / args.rate_hz
    with serial.Serial(args.port, args.baud, timeout=0.05) as ser, open(args.csv, newline="") as f:
        threading.Thread(target=rx_thread, args=(ser,), daemon=True).start()
        reader = csv.DictReader(f)
        seq = 0
        for row in reader:
            feats = [q8(row[k], *RANGES[k]) for k in ORDER]
            ser.write(frame(seq, feats))
            seq = (seq + 1) & 0xFF
            time.sleep(period)

if __name__ == "__main__":
    main()
