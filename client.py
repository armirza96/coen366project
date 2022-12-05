import socket

UPLOAD_FOLDER = "to_upload"
UPLOAD_FOLDER_DESTINATION = "uploads"

IP = socket.gethostbyname(socket.gethostname())
PORT = 8080  
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024

def open_connection(command):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
 
    file = open("data/yt.txt", "r")
    data = file.read()
 
    """ Sending the filename to the server. """
    client.send("yt.txt".encode(FORMAT))
    msg = client.recv(SIZE).decode(FORMAT)
    print(f"[SERVER]: {msg}")
 
    """ Sending the file data to the server. """
    client.send(data.encode(FORMAT))
    msg = client.recv(SIZE).decode(FORMAT)
    print(f"[SERVER]: {msg}")
 
    """ Closing the file. """
    file.close()
 
    """ Closing the connection from the server. """
    client.close()


def do_command(command):
    vals = command.split(" ")
    cmd = vals[0]
    
    match cmd:
        case 1:
            filename = vals[1]
            
        case 2:
        case 3:
        case 4:
        case _:
            print("unsupported command")
if __name__ == "__main__":
    
    userInput = 0
    print("Before starting, please ensure the files you would like to interact with are in the associated folders. ")
    while userInput != "5":
        print("1. Upload file. Ex: put filename.extension ")
        print("2. Get file. Ex: get filename.extension ")
        print("3. change filename. Ex: change oldfilename newfilename")
        print("4. Help. Ex: help -> will get available commands from server. ")
        print("5. Exit. Ex: exit -> will exit the client server protocol. ")

        userInput = input("\nPlease input the command you would like to execute: ")
        
        print(f"User inputted: {userInput}")
        
        do_command(userInput)
    print("Exiting client")