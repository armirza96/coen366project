import socket
import os
import sys

# device's IP address
IP = "0.0.0.0" 
PORT = 8080
DEBUG = True

FILE_INFO_SIZE = 1 # in bytes
UPLOAD_FOLDER_DESTINATION = "uploads"

def put_file(client, filename, receivedFileSize) -> str:
    # remove absolute path if there is
    filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
    
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
                 
    return '{:03b}'.format(0) +'{:05b}'.format(0)

def get_file(client, filesize, filepath) -> str:
    client.send(filesize.to_bytes(4, 'little'))
    with open(filepath, "rb") as f:
        bytes_sent = 0
        while bytes_sent < filesize:
            chunk = f.read(min(filesize - bytes_sent, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            #chunks.append(chunk)
            bytes_sent = bytes_sent + len(chunk)
            client.send(chunk)
        
        return '{:03b}'.format(1) + '{:05b}'.format(0)

def change_name(client, filename, oldfilename) -> str:
    with os.scandir(UPLOAD_FOLDER_DESTINATION) as dir:
       # filepath = f"{UPLOAD_FOLDER_DESTINATION}/{filename}"
        found = False
        for x in dir:
            if x.name == filename:
                found = True

        if found:
            try:
                os.rename(f"{UPLOAD_FOLDER_DESTINATION}/{filename}", f"{UPLOAD_FOLDER_DESTINATION}/{oldfilename}")
                return '{:03b}'.format(0) + '{:05b}'.format(0)
            except:
               return '{:03b}'.format(5) + '{:05b}'.format(0)
        else:
            return '{:03b}'.format(2)+ '{:05b}'.format(0)
        
def help() -> str:
    return  '{:03b}'.format(6) 

if __name__ == "__main__":
    if 2 < len(sys.argv): # will be 2 < 3 as script_name PORT DEBUG gives a lenght of 3
        PORT = int(sys.argv[1])
        DEBUG = bool(sys.argv[1])
    
    print(f"Assuming default values for ip: {IP}, port: {PORT} and debug: {DEBUG}")
        
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
        
        opcode = byteInfo >> 0b101

        if DEBUG:
            print(f"Byte Info: {byteInfo}, RESPONSE CODE {opcode}")
        
        response = ""
        if opcode == 0:
            filenameSize = byteInfo & 0b00011111
            receivedFileName = client_socket.recv(filenameSize).decode('utf-8') 
            receivedFileSize = int.from_bytes(client_socket.recv(4), sys.byteorder)
           
            response = put_file(client_socket, receivedFileName, receivedFileSize)
 
            amtOfBytesSent = client_socket.send(bytes([int(response, 2)]))
            
            if DEBUG:
                print(f"Recieved file name: {receivedFileName},  AMT OF Bytes SENT: {amtOfBytesSent}")
        elif opcode == 1:
            filenameSize = byteInfo & 0b00011111
            receivedFileName = client_socket.recv(filenameSize).decode('utf-8') 
            
            filepath = f"{UPLOAD_FOLDER_DESTINATION}/{receivedFileName}"
            filesize = 0
            
            try:
                filesize = os.path.getsize(filepath)
            except:
                response ='{:03b}'.format(2) + '{:05b}'.format(0)
                
            if filesize != 0:
                fileNameLength = '{:05b}'.format(len(receivedFileName))
                rescode = '{:03b}'.format(1)
                send_data = rescode + fileNameLength
                
                amtOfBytesSentForFileInfo = client_socket.send(bytes([int(send_data, 2)]))
                amtOfBytesSentForFileName = client_socket.send(receivedFileName.encode("utf-8"))


                response = get_file(client_socket, filesize, filepath) 
            else:
                response ='{:03b}'.format(2) + '{:05b}'.format(0)

            amtOfBytesSent = client_socket.send(bytes([int(response, 2)]))
            
            if DEBUG:
                print(f"Recieved file name: {receivedFileName}, AMT OF Bytes SENT: {amtOfBytesSent}")
        elif opcode == 2:
            oldfilenameSize = byteInfo & 0b00011111
            oldreceivedFileName = client_socket.recv(oldfilenameSize).decode('utf-8') 
            
            newfilenameSize = int.from_bytes(client_socket.recv(FILE_INFO_SIZE), sys.byteorder)
            newreceivedFileName = client_socket.recv(newfilenameSize).decode('utf-8') 
            
            response = change_name(client_socket, oldreceivedFileName, newreceivedFileName)
            
            if DEBUG:
                print(f"Recieved file names: {oldreceivedFileName} {newreceivedFileName}")
        elif opcode == 3:
            response = help()
            helpLengthBits = '{:05b}'.format(len("put get change help exit"))

            send_data = response + helpLengthBits
            
            amtOfBytesSentForInfo = client_socket.send(bytes([int(send_data, 2)]))
            amtOfBytesSentForHelpString = client_socket.send("put get change help exit".encode("utf-8"))
            
            if DEBUG:
                print(f"SENT DATA: {send_data}, AMOUNT OF BITS SENT: {amtOfBytesSentForInfo} {amtOfBytesSentForHelpString}")
        else:
            response = '{:03b}'.format(3)
            padding = '{:05b}'.format(0)

            send_data = response + padding
            
            amtOfBytesSentForUnsupportedCMD = client_socket.send(bytes([int(send_data, 2)]))
            
            if DEBUG:
                print(f"SENT DATA: {send_data}, AMOUNT OF BITS SENT: {amtOfBytesSentForUnsupportedCMD}")

        if DEBUG:
            print(f"RESPONSE SENT TO CLIENT: {response}")
            
        # close the client socket
        client_socket.close()
    # close the server socket
    s.close()