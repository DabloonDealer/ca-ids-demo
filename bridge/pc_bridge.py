import serial
import struct

# Match the COM port from your Device Manager
ser = serial.Serial('COM3', 115200) 

def send_telemetry(speed, rpm, throttle, brake, gear, steering):
    # Pack 6 integers into a binary format
    packet = struct.pack('6i', speed, rpm, throttle, brake, gear, steering)
    ser.write(packet)