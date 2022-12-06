import socket
import os
import sys

UPLOAD_FOLDER = "to_upload"

SEPARATOR = "<SEPERATOR>"
BUFFER_SIZE = 4096

IP = socket.gethostbyname(socket.gethostname())
PORT = 8080  
ADDR = (IP, PORT)

def send_file(filename):
    filepath = f"{UPLOAD_FOLDER}/{filename}"
    filesize = os.path.getsize(filepath)

    client = socket.socket()
    client.connect(ADDR)

    send_data = f"{filename}{SEPARATOR}{filesize}".encode('utf-8')
    
    print(f"{filepath} {filesize} {send_data}")
    print(sys.getsizeof(send_data))
    client.send(send_data)
    
    with open(filepath, "rb") as f:
        while True:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            else:
                client.sendall(bytes_read) #(f"{SEPARATOR}{bytes_read}".encode('utf-8')) #
    client.close()


def do_command(command):
    vals = command.split(" ")
    cmd = vals[0]
    
    if cmd == "put":
        filename = vals[1]
        send_file(filename)
    elif cmd == "get":
        filename = vals[1]
    elif cmd == "change":
        oldFileName = vals[1]
        newFileName = vals[2]
        
    elif cmd == "help":
        print("Getting help")
    else:
        print("unsupported command")
    
if __name__ == "__main__":
    userInput = 0
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