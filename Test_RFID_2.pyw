import time, os, re, urllib
import msvcrt
import sys
import argparse
import serial
import struct
import pyperclip
import keyboard
from playsound import playsound
import socket
import configparser
import atexit
import ctypes

parser = argparse.ArgumentParser(prog='Test_RFID.py')
parser.add_argument('--port', type=str, default='COM14', help='The COM port')
parser.add_argument('--baudrate', type=str, default='115200', help='The Baudrate')
parser.add_argument('--tcp_ip', type=str, default='192.168.100.154', help='The TCP IP')
parser.add_argument('--tcp_port', type=str, default='2105', help='The TCP PORT')

opt = parser.parse_args()

config = configparser.RawConfigParser()

if os.path.exists('config.yaml'):
    config.read('config.yaml')
    port = dict(config.items('DEFAULT'))['port']
    baudrate = dict(config.items('DEFAULT'))['baudrate']
    TCP_IP = dict(config.items('DEFAULT'))['tcp_ip']
    TCP_PORT = dict(config.items('DEFAULT'))['tcp_port']
else:
    port = input("INPUT PORT (Default. COM14) : ")
    if port == "":
        port = opt.port

    baudrate = input("INPUT BAUDRATE (Default. 115200) : ")
    if baudrate == "":
        baudrate = opt.baudrate

    TCP_IP = input("INPUT TCP IP (Default. 192.168.100.111) : ")
    if TCP_IP == "":
        TCP_IP = opt.tcp_ip

    TCP_PORT = input("INPUT TCP PORT (Default. 2105) : ")
    if TCP_PORT == "":
        TCP_PORT = opt.tcp_port

if dict(config.items('DEFAULT'))['hide'] == "True":
    kernel32 = ctypes.WinDLL('kernel32')
    user32 = ctypes.WinDLL('user32')
    SW_HIDE = 0
    hWnd = kernel32.GetConsoleWindow()
    user32.ShowWindow(hWnd, SW_HIDE)

wake = [0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xFF, 0x03, 0xFD, 0xD4, 0x14, 0x01, 0x17, 0x00]
ser = serial.Serial(port, baudrate, timeout=1)
ser.write(wake)
time.sleep(0.1)
read_val = ser.read(size=128)
print("response string : " + str(read_val))
ser.close()

read = [0x00, 0x00, 0xff, 0x04, 0xfc, 0xd4, 0x4a, 0x02, 0x00, 0xe0, 0x00]
ser = serial.Serial(port, baudrate, timeout=1)

chck = True

tcp_chck = dict(config.items('DEFAULT'))['tcp_chck']
if tcp_chck == "True":
    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    server_address = (TCP_IP, int(TCP_PORT))
    print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)
    sock.listen(1)
    print('Waiting for TCP Connection')
    connection, client_address = sock.accept()
    print('connection from', client_address , ' established.')

while 1:
    if chck:
        ser.write(read)
        chck = False

    read_val = ser.read(size=32)
    if len(read_val) > 3:
        print("response string : " + str(read_val))

    if len(read_val) > 18:
        print("\n---------------------------------")
        chck = True
        playsound('./rsrc/ring.mp3', False)

        uid_list = []
        for i in read_val:
            uid_list.append(hex(i))
        print("BLOCK : " + str(uid_list))

        ltl_endian = '0x' + uid_list[-3].split('x', 1)[1] + uid_list[-4].split('x', 1)[1] + uid_list[-5].split('x', 1)[
            1] + uid_list[-6].split('x', 1)[1]
        print("UID : " + str(ltl_endian))

        UID_decimal = int(ltl_endian, 16)

        while len(str(UID_decimal)) < 10:
            UID_decimal = '0' + str(UID_decimal)

        print("UID decimal : " + str(UID_decimal))

        pyperclip.copy(str(UID_decimal))

        if dict(config.items('DEFAULT'))['tcp_id'] == "True":
            UID_decimal = str(client_address) + "::" + UID_decimal + "\r\n"
        else:
            UID_decimal = UID_decimal + "\r\n"

        if tcp_chck == "True": connection.send(UID_decimal.encode())

        keyboard.send("ctrl+v")
        keyboard.send("enter")

        print("---------------------------------\n")

        @atexit.register
        def goodbye():
            print("END")
            ser.close()
            connection.close()
