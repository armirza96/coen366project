import socket
import os
# device's IP address
IP = socket.gethostbyname(socket.gethostname())
PORT = 8080
# receive 4096 bytes each time
BUFFER_SIZE = 4096
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
    received = client_socket.recv(BUFFER_SIZE).decode()
    filename, filesize = received.split(SEPARATOR)
   
    # remove absolute path if there is
    filename = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
    # convert to integer
    filesize = int(filesize)
    print(f"{filename} {filesize}")
    
    with open(filename, "wb") as f:
        bytes_read = client_socket.recv(BUFFER_SIZE)
        while bytes_read:
            # read 1024 bytes from the socket (receive)
            bytes_read = client_socket.recv(BUFFER_SIZE)
            f.write(bytes_read)

        # close the client socket
        client_socket.close()
        # close the server socket
        s.close()