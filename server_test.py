##
# @file server.py
#
# @brief TCP Server logic and algorithm
#
#
# @section author_doxygen_example Author(s)
# - Created by Kevin de Oliveira on 04/01/2022.
# - Student ID: 40054907
#
# Copyright (c) 2022 Kevin de Oliveira.  All rights reserved.

from ast import arg
import pickle
import socket as sok
import sys
from threading import Thread
from types import FunctionType
from typing import Any, Callable, List, Tuple
from bitarray import util

from interpreter.message import Message, Util
from interpreter.message_type import MessageType, RequestType, ResponseType


class TcpServer():
    _DEFAULT_PORT = 1025
    _MAX_BUFFER = 65574

    def __init__(self, ip_addr, **kwargs) -> None:
        """!
        TCP Server interface that creates a new socket given the ip address provided for FTP communication purposes

        @param ip_addr: str     IP address which the TCP service would be listening to
        @param -p: int          Port value which socket will bind its connection
        @param -a: str          IP address that TCP service will be using

        @return TcpServer
        """
        self._debug = False
        self.thread = None
        self.socket = sok.socket(sok.AF_INET, sok.SOCK_STREAM)
        self.socket.setsockopt(sok.SOL_SOCKET, sok.SO_REUSEADDR, 1)
        for k,v in kwargs.items():
            if "-p" in k:
                self._DEFAULT_PORT = int(v)
            elif "-a" in k:
                ip_addr = v
            elif "-d" in k:
                self._debug = True
        self.socket.bind( (ip_addr, self._DEFAULT_PORT) )
        self.ip_address = ip_addr
        self.recv_functions : List[Tuple[RequestType, FunctionType]] = []

        self.is_connected = False

    def _init_app(self) -> str:
        """!
        Initial message printed into command-line when TCP service is initiated
        """
        return """-- FTP Server initializing on {ip}:{port}
-- Version 1.0.0 by Kevin de Oliveira
-- README contains a list of available commands and some concepts guiding""".format(ip = self.ip_address, port = self._DEFAULT_PORT)

    def listen(self):
        """!
        Starts a new threded TCP service by connecting to the respective server.

        @return None
        """
        self.socket.listen()
        print(self._init_app())
        if self._debug:
            print("Debug mode ON")
        while True:
            try:
                conn, addr = self.socket.accept()
                self.thread = Thread(target=self.handle_listen, args=(conn, addr))
                self.is_connected = True
                self.thread.start()

                # For non concurrent connection, join current thread so loop awaits for any active connection to be terminated before connecting any other socket
                # if self.thread:
                #     self.thread.join()
            except KeyboardInterrupt:
                    print("Closing server")
                    self.is_connected = False
                    self.socket.close()
                    return
            except BlockingIOError:
                print("EAGAIN error")
                continue

        

    def handle_listen(self, conn : sok.socket, addr : sok.AddressInfo):
        """!
        Internal function that is responsible for parsing any incoming and outgoing message sent to the TCP socket
        
        @return None
        """
        print("""> New connection {addr}:{port}""".format(addr = addr[0], port=addr[1]))

        while self.is_connected:
            try:
                # Socket is only able to receive MAX_BUFFER;
                # Therefore, ensure that maximum packet sent is no longer then _MAX_BUFFER or set socket to nonblocking -> socket.setblocking(False)
                # Otherwise, wait for any possible subsequent packet receival (parallel or different loop)                
                data = conn.recv(self._MAX_BUFFER)
                if not data:
                    print("Closing connection with:", addr)
                    return None
                if self._debug:
                    print("[DEBUG]", data)
                out = self.parse_packet(data)

                for x in self.recv_functions:
                    if(x[0] == out.type):
                        _data_send = x[1](addr, out)
                        if self._debug:
                            print("[DEBUG]", _data_send)
                        
                        conn.sendto(_data_send[:self._MAX_BUFFER], addr)


            except (BrokenPipeError, ConnectionResetError) as e:
                print(e, addr)
            except ValueError:
                message = Message(3, ResponseType.ERROR_UNKNOWN)
                message.parse("00000")
                conn.sendto( Util.serialize(message) , addr )
            except KeyboardInterrupt:
                return
            

    def on_receive(self, *args : Callable[[sok.AddressInfo, Message], bytes]):
        """!
        Attach a callback that is called when a message is received

        @param *args: List[Callable[[sok.AddressInfo, Message], bytes]] List of callable objects containing its Method type and respective callback function
        """
        for x in args:
            self.recv_functions.append(x)

    @staticmethod
    def parse_packet(data : bytes) -> Message:
        """!
        Deserializes incoming byte received by the TCP socket

        @param data: bytes  Byte object received by socket

        @return Message: object
        """
        return Util.deserialize(data, MessageType.REQUEST)

    


import os
from re import S
from socket import socket

import bitarray
from interpreter import arguments
from interpreter.message_type import MessageType, RequestType, ResponseType
from interpreter.message import Message, Util

server_dir = "server"


BASE_DIR = os.getcwd() + os.sep + "dir" + os.sep + server_dir + os.sep


def response_ok() -> bytes:
    message = Message(3, ResponseType.OK_PUT_CHANGE)
    message.parse("00000")
    return Util.serialize(message)

def response_get(file_name : str, size : int, payload: bytes) -> bytes:
    message = Message(3, ResponseType.OK_GET)
    file_data = Util.str2bit(file_name, ResponseType.OK_GET.get_format()[1], with_count=True)
    file_size = bitarray.util.int2ba(size, length=32, endian="big").to01()
    
    message.parse(
    file_data + file_size
    )

    message.add_payload(payload)
    return Util.serialize(message)

def response_error_not_found():
    message = Message(3, ResponseType.ERROR_NOT_FOUND)
    message.parse("00000")
    return Util.serialize(message)

def response_error_no_change():
    message = Message(3, ResponseType.ERROR_NO_CHANGE)
    message.parse("00000")
    return Util.serialize(message)

def response_ok_help():
    message = Message(3, ResponseType.HELP)
    val = Util.str2bit("get put change bye",ResponseType.HELP.get_format()[1])
    message.parse(val)
    return Util.serialize(message)



def on_receive_put(addr, data : Message) -> bytes:
    
    result = Util.bit2byte(data)

    file_name = result[1].decode("utf-8").replace(chr(0), "")

    try:
        with open(BASE_DIR + file_name, "wb") as f:
            f.write(result[-1])

    except Exception as e:
        print(e)
        # @brief Although no response type is defined for PUT errors in the project description, excpetions may still occur if server has not enough privilege for accessing file or f.write fails.
        # Sending an ERROR_NO_CHANGE response in case the above issue happends
        return response_error_no_change()

    return response_ok()


def on_receive_get(addr, data : Message) -> bytes:

    result = Util.bit2byte(data)

    file_name = BASE_DIR + result[1].decode("utf-8")

    # @brief Remove embedded null pointer coming from raw data
    file_name = file_name.replace(chr(0), "")

    

    try:
        with open(file_name, "rb") as open_file:
            f = open_file.read()
            size = os.path.getsize(file_name)
            
        return response_get(result[1].decode("utf-8").replace(chr(0), ""), size, f)
            
    except Exception as e:
        return response_error_not_found()



def on_receive_change(addr, data : Message) -> bytes:
    result = Util.bit2byte(data)

    file_name_old = BASE_DIR + result[1].decode("utf-8").replace(chr(0), '')
    file_name_new = BASE_DIR + result[3].decode("utf-8").replace(chr(0), '')



    try:
        os.rename(file_name_old, file_name_new)
    except Exception as e:
        return response_error_no_change()


    return response_ok()

def on_receive_help(addr, data : Message) -> bytes:    
    return response_ok_help()




arg_helper = """usage: tcp_server [-a address] [-p port] [-f base_folder] [-F absolute_folder] [-v | --version] [-h | --help | -?]

This are the commands used:
\t-d\t\t Activate debug mode
\t-a address\t\t Set address of this server (default: 127.0.0.1)
\t-p port\t\t\t Set port number of this server (default: 1025)
\t-f base_folder\t\t Set relative base path of the FTP server (default: /dir/server)
\t-F absolute_folder\t Set absolute base path of the FTP server (default: $pwd)"""

if __name__ == "__main__":

    cmd = arguments.ParserArgs(helper = arg_helper, version="tcp_server version 1.0")

    cmd.get_args()

    params = cmd.parameters(["-a", "-p", "-f", "-F", "-d"])

    if "-f" in params:
        server_dir = params["-f"]
    elif "-F" in params:
        BASE_DIR = params["-F"]
    
    tcp_server = TcpServer("127.0.0.1", **params)

    

    tcp_server.on_receive(
    (RequestType.PUT , on_receive_put),
    (RequestType.GET, on_receive_get),
    (RequestType.CHANGE, on_receive_change),
    (RequestType.HELP, on_receive_help),
    )

    tcp_server.listen()