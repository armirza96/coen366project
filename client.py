import socket
import os
import sys

UPLOAD_FOLDER = "to_upload"
DOWNLOAD_FOLDER_DESTINATION = "downloads"
FILE_INFO_SIZE = 1 # in bytes

IP = socket.gethostbyname(socket.gethostname())
PORT = 8080
DEBUG = True

def send_file(client, filename) -> str:
    filepath = f"{UPLOAD_FOLDER}/{filename}"
    filesize = os.path.getsize(filepath)
    opcode = '{:03b}'.format(0)#'0b000'#'{0:03b}'.format(0)
    # opcode1 = '{:03b}'.format(1)#'0b000'#'{0:03b}'.format(0)
    # opcode2 = '{:03b}'.format(2)#'0b000'#'{0:03b}'.format(0)
    # opcode3 = '{:03b}'.format(3)#'0b000'#'{0:03b}'.format(0)
    #fileNameLength = format(5, (len(filename)))
    fileNameBits = '{:05b}'.format(len(filename))


    send_data = opcode + fileNameBits

    if DEBUG:
        print(f"{opcode} {fileNameBits} {filesize} {filesize.to_bytes(4, 'little')}")

    amtOfBitsSentForFileInfo = client.send(bytes([int(send_data, 2)]))
    amtOfBitsSentForFileName = client.send(filename.encode("utf-8"))
    amtOfBitsSentForFileSize = client.send(filesize.to_bytes(4, 'little'))

    if DEBUG:
        print(f"AMount of bytes sent {amtOfBitsSentForFileInfo} {amtOfBitsSentForFileName} {amtOfBitsSentForFileSize}")

    with open(filepath, "rb") as f:
        bytes_sent = 0
        while bytes_sent < filesize:
            chunk = f.read(min(filesize - bytes_sent, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            bytes_sent = bytes_sent + len(chunk)
            client.send(chunk)

    response = client.recv(FILE_INFO_SIZE)

    return response

def get_file_response(client, filename) -> str:
    opcode = '{:03b}'.format(1)

    fileNameBits = '{:05b}'.format(len(filename))

    send_data = opcode + fileNameBits

    if DEBUG:
        print(f"{opcode} {fileNameBits}")

    amtOfBitsSentForFileInfo = client.send(bytes([int(send_data, 2)]))
    amtOfBitsSentForFileName = client.send(filename.encode("utf-8"))

    if DEBUG:
        print(f"AMount of bytes sent {amtOfBitsSentForFileInfo} {amtOfBitsSentForFileName}")

    response = client.recv(FILE_INFO_SIZE)

    return response

def get_file(client, filename, receivedFileSize):
    filepath = f"{DOWNLOAD_FOLDER_DESTINATION}/{filename}"

    if DEBUG:
        print(f"FILE PATH: {filepath}")

    with open(filepath, "wb") as f:
        bytes_recd = 0
        while bytes_recd < receivedFileSize:
            chunk = client.recv(min(receivedFileSize - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            bytes_recd = bytes_recd + len(chunk)
            f.write(chunk)

    response = client.recv(1)
    return response

def change_file_name(client, oldfilename, newfilename) -> str:
    opcode = '{:03b}'.format(2)

    oldfileNameBits = '{:05b}'.format(len(oldfilename))
    newfileNameBits = '{:08b}'.format(len(newfilename))

    send_data = opcode + oldfileNameBits

    if DEBUG:
        print(f"{opcode} {oldfileNameBits}")

    amtOfBitsSentForFileInfo = client.send(bytes([int(send_data, 2)]))
    amtOfBitsSentForFileName = client.send(oldfilename.encode("utf-8"))

    amtOfBitsSentForOldFileNameLength = client.send(bytes([int(newfileNameBits, 2)]))
    amtOfBitsSentForNewFileName = client.send(newfilename.encode("utf-8"))

    if DEBUG:
        print(f"AMount of bytes sent {amtOfBitsSentForFileInfo} {amtOfBitsSentForFileName} {amtOfBitsSentForOldFileNameLength} {amtOfBitsSentForNewFileName}")

    response = client.recv(1)

    return response

def get_help(client) -> str:
    opcode = '{:03b}'.format(3)
    padding = '{:05b}'.format(0)

    send_data = opcode + padding

    if DEBUG:
        print(f"{send_data}")

    client.send(bytes([int(send_data, 2)]))

    response = client.recv(1)

    return response

def unsupported_cmd(client) -> str:
    opcode = '{:03b}'.format(4)
    padding = '{:05b}'.format(0)

    send_data = opcode + padding

    if DEBUG:
        print(f"{send_data}")

    client.send(bytes([int(send_data, 2)]))

    response = client.recv(1)

    return response

def do_command(command):
    vals = command.split(" ")
    cmd = vals[0]

    client = socket.socket()
    client.connect(ADDR)

    response = ""
    if cmd == "put":
        filename = vals[1]
        response = send_file(client, filename)
    elif cmd == "get":
        filename = vals[1]

        response = get_file_response(client, filename)
    elif cmd == "change":
        oldFileName = vals[1]
        newFileName = vals[2]

        response = change_file_name(client, oldFileName, newFileName)
    elif cmd == "help":
        response = get_help(client)
    else:
        response = unsupported_cmd(client)

    if DEBUG:
        print(f"RESPONSE FROM SERVER: {response}")

    work_with_response(client, response)

    client.close()

def work_with_response(client, response):
    byteInfo = int.from_bytes(response, sys.byteorder)
    rescode = byteInfo >> 0b101

    if DEBUG:
        print(f"Byte Info: {response}, RESPONSE CODE {rescode}")

    if rescode == 0:
        print("Operation completed successfully!")
    elif rescode == 1:
        filenameSize = byteInfo & 0b00011111
        receivedFileName = client.recv(filenameSize).decode('utf-8')
        receivedFileSize = int.from_bytes(client.recv(4), sys.byteorder)

        # response = client.recv(1)
        # byteInfo = int.from_bytes(response, sys.byteorder)
        # rescode = byteInfo >> 0b101
        # print(f"Get File: {rescode}")
        # if rescode == 2:
        #     print("Error: File not found")
        # else:
        response = get_file(client, receivedFileName, receivedFileSize)

        print(f"{receivedFileName} has been downloaded successfully.")
    elif rescode == 2:
       print("Error: File not found")
    elif rescode == 3:
        print("Error: Unknown request")
    elif rescode == 5:
        print("Error: Unsuccessful change")
    elif rescode == 6:
        helpLength = byteInfo & 0b00011111
        help = client.recv(helpLength).decode('utf-8')
        print(help)

if __name__ == "__main__":
    print(sys.argv)
    if 3 < len(sys.argv): # will be 3 < 4 as script_name IP PORT DEBUG gives a lenght of 4
        IP = sys.argv[1]
        PORT = int(sys.argv[2])
        DEBUG = bool(int(sys.argv[3]))

    print(f"Assuming values for ip: {IP}, port: {PORT} and debug: {DEBUG}")

    ADDR = (IP, PORT)

    userInput = 0
    print(" ")
    print("Before starting, please ensure the files you would like to interact with are in the associated folders. ")

    while True:
        print("1. Upload file. Ex: put filename.extension ")
        print("2. Get file. Ex: get filename.extension ")
        print("3. change filename. Ex: change oldfilename newfilename")
        print("4. Help. Ex: help -> will get available commands from server. ")
        print("5. Exit. Ex: exit -> will exit the client server protocol. ")

        userInput = input("\nPlease input the command you would like to execute: ")

        if DEBUG:
            print(f"USER INPUTTED: {userInput}")

        if userInput == "exit":
            break

        do_command(userInput)

        print(" ")
    print("Exiting client")
