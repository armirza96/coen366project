import socket
import os
import sys

# device's IP address
IP = "0.0.0.0" 
PORT = 8080
DEBUG = True
# receive 4096 bytes each time
BUFFER_SIZE = 4096
FILE_INFO_SIZE =  54
SEPARATOR = "<SEPERATOR>"
UPLOAD_FOLDER_DESTINATION = "uploads"
 
def put_file(client, filename) -> str:
    # remove absolute path if there is
    filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
    # convert to integer
    #print(f"{filepath} {filesize}")
    filesize = int(filesize)
    
    #print(f"{filepath} {filesize}")
    
    with open(filepath, "wb") as f:
        while True:
            # read 1024 bytes from the socket (receive)
            bytes_read = client.recv(BUFFER_SIZE)
            print(bytes_read)
            if not bytes_read:    
                # nothing is received
                # file transmitting is done
                break

            f.write(bytes_read)
            
    return "UPLOAD SUCCESSFUL"

def get_file(client, filename) -> str:
    with os.scandir(UPLOAD_FOLDER_DESTINATION) as dir:
        found = False
        for x in dir:
            if x.name == filename:
                found = True

        if found:
            # remove absolute path if there is
            filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
            with open(filepath, "wb") as f:
                while True:
                    # read 1024 bytes from the socket (receive)
                    bytes_read = f.read(BUFFER_SIZE)
                    print(bytes_read)
                    if not bytes_read:    
                        # nothing is received
                        # file transmitting is done
                        break

                    client.sendall(bytes_read)
            
            return "Retrieval Successful of file " + filename
        else:
            return f"{filename} not found!"       

def change_name(filename, oldfilename) -> str:
    with os.scandir(UPLOAD_FOLDER_DESTINATION) as dir:
       # filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
        found = False
        for x in dir:
            if x.name == filename:
                found = True

        if found:
            os.rename(f"{UPLOAD_FOLDER_DESTINATION}/{filename}", f"{UPLOAD_FOLDER_DESTINATION}/{oldfilename}")
            return "Change name Successful of file " + filename
        else:
            return f"{filename} not found!" 
        
def help(filename, oldfilename) -> str:
    return "[PUT, GET, CHANGE, HELP]"

if __name__ == "__main__":
    if 2 < len(sys.argv): # will be 2 < 3 as script_name PORT DEBUG gives a lenght of 3
        PORT = int(sys.argv[1])
        DEBUG = bool(sys.argv[1])
    else:
        print("Assuming default values for port and debug")
        
    s = socket.socket()
    s.bind((IP, PORT))
    
    s.listen(2) 
    print(f"[*] Listening as {IP}:{PORT}")
    
    while True:
        # accept connection if there is any
        client_socket, address = s.accept() 
        # if below code is executed, that means the sender is connected
        print(f"[+] {address} is connected.")
        
        
        # receive the file infos
        # receive using client socket, not server socket
        received = client_socket.recv(FILE_INFO_SIZE).decode('utf-8')
        #filename, filesize = received.split(SEPARATOR)
        vals = received.split(SEPARATOR)
        filename = vals[0]
        filesize = vals[1]
        # text = vals[2]
        
        # print(f"TEXT {text}")
        
        response = put_file(client_socket, filename)
        
        print("Sendin Response")
        #client_socket.send("UPLOAD SUCCESSFUL".encode('utf-8')) # doesnt work
        # close the client socket
        client_socket.close()
    # close the server socket
    s.close()