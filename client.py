import socket
import os
import sys

UPLOAD_FOLDER = "to_upload"
DOWNLOAD_FOLDER_DESTINATION = "downloads"

BUFFER_SIZE = 4096

IP = socket.gethostbyname(socket.gethostname())
PORT = 8080  

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

    print(f"{opcode} {fileNameBits} {filesize} {filesize.to_bytes(4, 'little')}")

    print(f"BITS in sent data : {send_data}")

    amtOfBitsSentForFileInfo = client.send(bytes([int(send_data, 2)]))
    amtOfBitsSentForFileName = client.send(filename.encode("utf-8"))
    amtOfBitsSentForFileSize = client.send(filesize.to_bytes(4, 'little'))
    
    print(f"Amount of bytes sent {amtOfBitsSentForFileInfo} {amtOfBitsSentForFileName} {amtOfBitsSentForFileSize}")
    
    with open(filepath, "rb") as f:
        while True:
            # read the bytes from the file1
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            else:
                client.send(bytes_read)
   
    response = client.recv(1)

    return response

def get_file(filename) -> str:
    filepath = f"{DOWNLOAD_FOLDER_DESTINATION}/{filename}"
    opcode = '{:03b}'.format(1)

    fileNameBits = '{:05b}'.format(len(filename))
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    send_data = opcode + fileNameBits

    print(f"{opcode} {fileNameBits}")

    amtOfBitsSentForFileInfo = client.send(bytes([int(send_data, 2)]))
    amtOfBitsSentForFileName = client.send(filename.encode("utf-8"))
    
    print(f"AMount of bytes sent {amtOfBitsSentForFileInfo} {amtOfBitsSentForFileName}")
    
    with open(filepath, "wb") as f:
        while True:
            bytes_read = client.recv(BUFFER_SIZE)
            print(bytes_read)
            if not bytes_read:    
                break
            f.write(bytes_read)
    
    print("Receiving Response")    
    response = client.recv(1) # doesnt work
    
    return response

def change_file_name(oldfilename, newfilename) -> str:
    opcode = '{:03b}'.format(2)

    oldfileNameBits = '{:05b}'.format(len(oldfilename))
    newfileNameBits = '{:08b}'.format(len(newfilename))
    client = socket.socket()
    client.connect(ADDR)

    send_data = opcode + oldfileNameBits

    print(f"{opcode} {oldfileNameBits}")

    amtOfBitsSentForFileInfo = client.send(bytes([int(send_data, 2)]))
    amtOfBitsSentForFileName = client.send(oldfilename.encode("utf-8"))
    
    amtOfBitsSentForOldFileNameLength = client.send(bytes([int(newfileNameBits, 2)]))
    amtOfBitsSentForNewFileName = client.send(newfilename.encode("utf-8"))
    
    print(f"Amount of bytes sent {amtOfBitsSentForFileInfo} {amtOfBitsSentForFileName} {amtOfBitsSentForOldFileNameLength} {amtOfBitsSentForNewFileName}")
    
    print("Receiving Response")    
    response = client.recv(1) # doesnt work
    
    return response

def get_help(client) -> str:
    opcode = '{:03b}'.format(3)
    padding = '{:05b}'.format(0)
    client = socket.socket()
    client.connect(ADDR)

    send_data = opcode + padding

    print(f"{send_data}")

    amtOfBitsSent = client.send(bytes([int(send_data, 2)]))

    print(f"Amount of bytes sent {amtOfBitsSent}")
    
    print("Receiving Response")    
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
        
        response = get_file(client, filename)
    elif cmd == "change":
        oldFileName = vals[1]
        newFileName = vals[2]
        
        response = change_file_name(client, oldFileName, newFileName)
    elif cmd == "help":
        response = get_help(client)  
    else:
        print("unsupported command")
    
    print(response)
    
    work_with_response(client, response)
    
    client.close()
    
def work_with_response(client, response):
    byteInfo = int.from_bytes(response, sys.byteorder)
    #filename, filesize = received.split(SEPARATOR)
    print(f"RECEIVED: {response}")
    rescode = byteInfo >> 0b101
    
    if rescode == 0:
        print("Operation completed successfully")
    elif rescode == 1:
        filenameSize = byteInfo & 0b00011111
        receivedFileName = client.recv(filenameSize).decode('utf-8') # will read n bytes in for filename
        fileNameBits = '{:05b}'.format(len(receivedFileName))
        
        response = get_file(client, receivedFileName)
    elif rescode == 2:
       print("Error: File not found")
    elif rescode == 3:
        print("Error: Unknown request")
    elif rescode == 4:
        print("Error: Unsuccessful change")
    else:
        response = '{:03b}'.format(3)
    
if __name__ == "__main__":
    if 3 < len(sys.argv): # will be 3 < 4 as script_name IP PORT DEBUG gives a lenght of 4
        IP = int(sys.argv[1])
        PORT = bool(sys.argv[2])
        DEBUG = bool(sys.argv[3])
    else:
        print("Assuming default values for ip, port and debug")
    
    ADDR = (IP, PORT)
    
    userInput = 0
    print(" ")
    print("Before starting, please ensure the files you would like to interact with are in the associated folders. ")
    
    while userInput != "exit":
        print("1. Upload file. Ex: put filename.extension ")
        print("2. Get file. Ex: get filename.extension ")
        print("3. change filename. Ex: change oldfilename newfilename")
        print("4. Help. Ex: help -> will get available commands from server. ")
        print("5. Exit. Ex: exit -> will exit the client server protocol. ")

        userInput = input("\nPlease input the command you would like to execute: ")
        
        print(f"User inputted: {userInput}")
        
        do_command(userInput)
        
        print(" ")
    print("Exiting client")