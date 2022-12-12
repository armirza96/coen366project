import socket
import os
import sys

# device's IP address
IP = "0.0.0.0" 
PORT = 8080
DEBUG = True
# receive 4096 bytes each time
BUFFER_SIZE = 4096
FILE_INFO_SIZE = 1 # in bytes
UPLOAD_FOLDER_DESTINATION = "uploads"

def put_file(client, filename, receivedFileSize) -> str:
    # remove absolute path if there is
    filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
    
    #print(f"{filepath} {filesize}")
    
    with open(filepath, "wb") as f:
        #chunks = []
        bytes_recd = 0
        while bytes_recd < receivedFileSize:
            chunk = client.recv(min(receivedFileSize - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            #chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
            f.write(chunk)
        # while True:
        #     # read 1024 bytes from the socket (receive)
        #     bytes_read = client.recv(BUFFER_SIZE)
        #     print(bytes_read)
        #     if not bytes_read:    
        #         # nothing is received
        #         # file transmitting is done
        #         break

            
            
    return '{:03b}'.format(0)

def get_file(client, filename) -> str:
    filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
    filesize = 0
    
    try:
        filesize = os.path.getsize(filepath)
    except:
        return '{:03b}'.format(5) 
    
    amtOfBitsSentForFileSize = client.send(filesize.to_bytes(4, 'little'))
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

                    client.send(bytes_read)
            
            return '{:03b}'.format(1)
        else:
            return '{:03b}'.format(2)     

def change_name(filename, oldfilename) -> str:
    with os.scandir(UPLOAD_FOLDER_DESTINATION) as dir:
       # filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
        found = False
        for x in dir:
            if x.name == filename:
                found = True

        if found:
            try:
                os.rename(f"{UPLOAD_FOLDER_DESTINATION}/{filename}", f"{UPLOAD_FOLDER_DESTINATION}/{oldfilename}")
                return '{:03b}'.format(0)
            except:
               return '{:03b}'.format(5) 
        else:
            return '{:03b}'.format(2)
        
def help() -> str:
    return  '{:03b}'.format(5) 

if __name__ == "__main__":
    if 2 < len(sys.argv): # will be 2 < 3 as script_name PORT DEBUG gives a lenght of 3
        PORT = int(sys.argv[1])
        DEBUG = bool(sys.argv[1])
    else:
        print("Assuming default values for port and debug")
        
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        receivedFileInfo = client_socket.recv(FILE_INFO_SIZE)
        byteInfo = int.from_bytes(receivedFileInfo, sys.byteorder)
        #filename, filesize = received.split(SEPARATOR)
        print(f"RECEIVED: {receivedFileInfo}")
        opcode = byteInfo >> 0b101

        response = ""
        
        if opcode == 0:
            filenameSize = byteInfo & 0b00011111
            receivedFileName = client_socket.recv(filenameSize).decode('utf-8') # will read n bytes in for filename
            receivedFileSize = int.from_bytes(client_socket.recv(4), sys.byteorder)
           # print(f"TEXT {opcode} {filenameSize} {receivedFileName} {receivedFileSize}")
            response = put_file(client_socket, receivedFileName, receivedFileSize)
            
            
            amtOfBitsSent = client_socket.send(bytes([int(response, 2)]))
            
            print(f"Response {response} {amtOfBitsSent}")
        elif opcode == 1:
            filenameSize = byteInfo & 0b00011111
            receivedFileName = client_socket.recv(filenameSize).decode('utf-8') # will read n bytes in for filename
            fileNameBits = '{:05b}'.format(len(receivedFileName))

            send_data = response + fileNameBits
            amtOfBitsSentForFileInfo = client_socket.send(bytes([int(send_data, 2)]))
            amtOfBitsSentForFileName = client_socket.send(receivedFileName.encode("utf-8"))
            
            
            response = get_file(client_socket, receivedFileName)
        elif opcode == 2:
            oldfilenameSize = byteInfo & 0b00011111
            oldreceivedFileName = client_socket.recv(oldfilenameSize).decode('utf-8') # will read n bytes in for filename
            
            newfilenameSize = client_socket.recv(FILE_INFO_SIZE)
            newreceivedFileName = client_socket.recv(newfilenameSize).decode('utf-8') # will read n bytes in for filename
            
            response = change_name(client_socket, oldreceivedFileName, newreceivedFileName)
        elif opcode == 3:
            response = help()
            fileNameBits = '{:05b}'.format(len("put get change help exit"))

            send_data = response + fileNameBits
            
            amtOfBitsSentForFileInfo = client_socket.send(bytes([int(send_data, 2)]))
            amtOfBitsSentForFileName = client_socket.send("put get change help exit".encode("utf-8"))
        else:
            response = '{:03b}'.format(3)

        
        # close the client socket
        client_socket.close()
    # close the server socket
    s.close()