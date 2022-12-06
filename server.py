import socket
import os
# device's IP address
IP = "0.0.0.0" 
PORT = 8080
# receive 4096 bytes each time
BUFFER_SIZE = 4096
FILE_INFO_SIZE =  54
SEPARATOR = "<SEPERATOR>"
UPLOAD_FOLDER_DESTINATION = "uploads"
 
if __name__ == "__main__":
    s = socket.socket()
    s.bind((IP, PORT))
    
    s.listen(2)
    print(f"[*] Listening as {IP}:{PORT}")
    
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
    
    # remove absolute path if there is
    filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
    # convert to integer
    print(f"{filepath} {filesize}")
    filesize = int(filesize)
    
    print(f"{filepath} {filesize}")
    
    with open(filepath, "wb") as f:
        while True:
            # read 1024 bytes from the socket (receive)
            bytes_read = client_socket.recv(BUFFER_SIZE)
            print(bytes_read)
            if not bytes_read:    
                # nothing is received
                # file transmitting is done
                break

            f.write(bytes_read)

    # close the client socket
    client_socket.close()
    # close the server socket
    s.close()