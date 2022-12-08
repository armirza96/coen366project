##
# @file client.py
#
# @brief TCP Client logic and algorithm
#
#
# @section author_doxygen_example Author(s)
# - Created by Kevin de Oliveira on 04/01/2022.
# - Student ID: 40054907
#
# Copyright (c) 2022 Kevin de Oliveira.  All rights reserved.

import socket as sok
import sys
from threading import Thread
from types import FunctionType
from typing import Callable, List, Optional, Tuple
from interpreter.message import  Util, Message
from interpreter.message_type import MessageType, MethodType, RequestType, ResponseType
from interpreter import arguments

import signal
class TcpClient():
    _DEFAULT_PORT = 1025
    _MAX_BUFFER = 65574

    def __init__(self, ip_addr, **kwargs) -> None:
        """!
        TCP Client interface that creates a new socket given the ip address provided for FTP communication

        @param ip_addr: str     IP address which the TCP service would be listening to
        @param -p: int          Port value which socket will bind its connection
        @param -a: str          IP address that TCP service will be using

        @return TcpClient
        """
        self._debug = False
        self.thread = None
        self.socket = sok.socket(sok.AF_INET, sok.SOCK_STREAM)

        for k,v in kwargs.items():
            if "-p" in k:
                self._DEFAULT_PORT = int(v)
            elif "-a" in k:
                ip_addr = v
            elif "-d" in k:
                self._debug = True
        self.ip_address = ip_addr
        self._is_connected = False
        self.create_message_functions : List[Tuple[MethodType, FunctionType] ] = []
        self.on_response_functions: List[Tuple[MethodType, FunctionType]] = []

        signal.signal(signal.SIGINT, self.handler)


    def connect(self):
        """!
        Creates a TCP socket bounded to the given IP address and port provided. 
        Object creates a new thread where each new connection will respond to.

        @return None
        """
        try:
            
            self.socket.connect( (self.ip_address, self._DEFAULT_PORT) )
            self._is_connected = True
            self.thread = Thread(target = self.handle_connection, args=())
            self.thread.start()
            if self.thread:
                self.thread.join()

        except ConnectionRefusedError:
            # @brief Implement timeout or repetition
            print("Unable to connect to server, try again")
        except KeyboardInterrupt:
            self.socket.close()
            self._is_connected = False            
        except Exception:
            return

    
    def handle_connection(self):
        """!
        Internal function which handles all single client-server communication
        Method is responsible for parsing any incoming and outgoing message sent through the TCP socket

        @return None
        """
        lcls = locals()
        cmd_format : RequestType or None = None
        if self._debug:
            print("Debug mode ON")
        while self._is_connected:
            try:
                msg = self.cin()
                if len(msg):
                    try:
                        # @brief Dynamically converts the input string to local MethodType variable 
                        exec("cmd_format_lcls = RequestType.%s" % msg[0].upper(), globals(), lcls)
                        cmd_format = lcls["cmd_format_lcls"]
                        for x in self.create_message_functions:
                            if(x[0] == cmd_format):
                                _data_send = x[1](msg, cmd_format)
                                if self._debug:
                                    print("[DEBUG]", _data_send)

                                if len(_data_send) > self._MAX_BUFFER:
                                    raise ValueError("error: size of message is bigger than the maximum allowed of 64 Kb")

                                self.socket.send( _data_send )
                    except (AttributeError ,SyntaxError, IndexError) as e:
                        # @brief self.socket.send not necessary as the client application should be aware of the supported commands (eg. offline). However, due to requirements empty message is sent.
                        if msg[0] == "bye":
                            raise KeyboardInterrupt()

                        self.socket.send(
                            " ".join(msg).encode("utf-8")
                        )
                    except OSError as e:
                        print("OS Error occured: ",e)
                        return
                    except ValueError as e:
                        print(e)
                        continue
                    
                    # @brief Socket is only able to receive MAX_BUFFER;
                    # In order to guarantee efficiency of sockets, longer buffers will be stripped to fit the maximum sendable buffer size
                    # Therefore, ensure that maximum packet sent is no longer then _MAX_BUFFER or set socket to nonblocking -> socket.setblocking(False)
                    # Otherwise, wait for any possible subsequent packet receival (parallel or different loop)
                    recv = self.socket.recv(self._MAX_BUFFER)


                    if self._debug:
                        print("[DEBUG]", recv)
                    if recv:
                        
                        res = self.check_response(recv)
                        if type(res.type) is ResponseType:
                            for x in self.on_response_functions:
                                if res.type == x[0]:
                                    x[1](res)
                        else:
                            self._is_connected = False 
                    else:
                        self._is_connected = False

            except (KeyboardInterrupt, OSError):
                return
            except ValueError as e:
                #@brief In case of large incming packet, self.socke.recv will raise an Exception for invalid header byte
                print("invalid response", e)

    def check_response(self, data : bytes) -> Message:
        """!
        Deserialize the incoming message

        @param data: bytes  Byte object received by the socket
        
        @return Deserialized message object
        """
        return Util.deserialize(data, MessageType.RESPONSE)


    def on_send(self, *args: Tuple[ MethodType ,Callable[[List[str], MethodType], bytes]]):
        """!
        Attach a callback that is called when a message is sent

        @param *args: List[Tuple[ MethodType ,Callable[[List[str], MethodType], bytes]]]    List of callable objects containing its Method type and respective callback function

        @return None
        """
        for x in args:
            self.create_message_functions.append(x)

    def on_response(self, *args: Tuple[MethodType,  Callable[[Message], None ]] ):
        """!
        Attach a callback that is called when a message is received

        @param *args: List[Tuple[MethodType,  Callable[[Message], None ]]]  List of callable objects containing its Method type and respective callback function

        @return None
        """
        for x in args:
            self.on_response_functions.append(x)


    def cin(self) -> List[str]:
        """!
        Reads stdin from command-line. By default prints 'ftp>' before reading input.
        Note that default input function is a blocking stdin command.

        @return List[str] List of message inputs
        """
        try:
            msg = input("ftp> ")
            return msg.strip().split()
        except EOFError:
            raise KeyboardInterrupt



    def handler(self, signum , frame):
        """!
        Internal funtion used to define a signal handler that is called when a SIGINT signal is raised by this process
        """
        
        #stdin is locking. Hence after SIGINT the application will still hang
        #probable solution would be implementing the thread as daemon

        print("\nClosing FTP Connection. Press [ENTER] to finish")
        self._is_connected = False
        self.socket.close()
        
        # sys.stdin.close()



#!/usr/bin/python3.8

##
# @file tcp_client.py
#
# @brief Main TCP client application which contains the implementation of the client-end of this FTP service. All protocols and file handling is defined in this file. 
#
#
# @section author_doxygen_example Author(s)
# - Created by Kevin de Oliveira on 04/01/2022.
# - Student ID: 40054907
#
# Copyright (c) 2022 Kevin de Oliveira.  All rights reserved.

import os
from typing import List
import bitarray
from bitarray import util
from interpreter.message import Message, Util

from interpreter.packet import packet

from interpreter.message_type import MessageType, MethodType, RequestType, ResponseType
client_dir = "client"

BASE_DIR = os.getcwd() + os.sep + "dir" + os.sep + client_dir + os.sep




def on_send_put(inp : List[str], type: MethodType) -> bytes:
    message = Message(3, type)

    try:
        with open(BASE_DIR + inp[1], "rb") as f:
            payload = f.read()
            size = os.path.getsize(BASE_DIR + inp[1])
    except IndexError:
        # @brief if exception occurs during parsing of input, return as if the command syntax as invalid
        raise ValueError("invalid command")
    except Exception as e:
        raise ValueError("cannot send file")

    
    file_data = Util.str2bit(inp[1], message.data[1].size, with_count=True)
    file_size = bitarray.util.int2ba(size, length=32, endian='big').to01()

    message.parse(
    file_data + file_size
    )

    
    message.add_payload(payload)

    

    
    
    return Util.serialize(message)


def on_send_get(inp : List[str], type: MethodType) -> bytes:
    try:
        message = Message(3, type)
        file_data = Util.str2bit(inp[1], message.data[1].size, with_count=True)
        message.parse(file_data)
        return Util.serialize(message)
    except IndexError:
        # @brief if exception occurs during parsing of input, return as if the command syntax as invalid
        raise ValueError("invalid command")


def on_send_change(inp : List[str], type: MethodType) -> bytes:
    message = Message(3, type)
    file_data_old = Util.str2bit(inp[1], message.data[1].size, with_count=True)
    file_data_new = Util.str2bit(inp[2], message.data[3].size, with_count=True, size_count=8)
    message.parse(
    file_data_old + file_data_new
    )

    return Util.serialize(message)

def on_send_help(inp : List[str], type: MethodType) -> bytes:
    message = Message(3, type)

    message.parse("00000")

    return Util.serialize(message)



def on_response_put_change(message : Message) :
    return

def on_response_get(message: Message) :
    val = Util.bit2byte(message)

    file_name = val[1].decode("utf-8").replace(chr(0), "")
    ch : str = ''
    with os.scandir(BASE_DIR) as dir:
        flag : bool = False
        for x in dir:
            if x.name == file_name:
                flag = True
        
        ##
        # @brief Checks if file already exists
        #

        if flag:
            while ch not in ["y", "n"]:
                ch = input(file_name + " already exists. Do you want to overwrite? (y/n) ")
    try:
        if ch == "y" or not flag:
            with open(BASE_DIR + file_name, "wb") as f:
                f.write(val[-1])

    except Exception as e:
        print(e)

def on_response_help(message: Message):
    val = Util.bit2byte(message)
    print(val[1].decode("utf-8").replace(chr(0), ""))

def on_response_unknown(message: Message):
    print("unknown command")

def on_response_not_found(message: Message):
    print("file not found")

def on_response_no_change(mesage : Message):
    print("operation failed")



arg_helper = """usage: tcp_client [-a address] [-p port] [-f base_folder] [-F absolute_folder] [-v | --version] [-h | --help | -?]

This are the commands used:
\t-d\t\t Activate debug mode
\t-a address\t\t Set address of this client (default: 127.0.0.1)
\t-p port\t\t\t Set port number of this client (default: 1025)
\t-f base_folder\t\t Set relative base path of the FTP client (default: /dir/client)
\t-F absolute_folder\t Set absolute base path of the FTP client (default: $pwd)"""

from interpreter import arguments

if __name__ == "__main__":
    cmd = arguments.ParserArgs(helper = arg_helper, version="tcp_server version 1.0")

    cmd.get_args()

    params = cmd.parameters(["-a", "-p", "-f", "-F", "-d"])

    if "-f" in params:
        client_dir = params["-f"]
    elif "-F" in params:
        BASE_DIR = params["-F"]
    


    client = TcpClient("127.0.0.1", **params)

    client.on_send(
    (RequestType.PUT, on_send_put),
    (RequestType.GET, on_send_get),
    (RequestType.CHANGE, on_send_change),
    (RequestType.HELP, on_send_help),
    )

    client.on_response(
    (ResponseType.OK_PUT_CHANGE, on_response_put_change),
    (ResponseType.OK_GET, on_response_get),
    (ResponseType.HELP, on_response_help),
    (ResponseType.ERROR_UNKNOWN, on_response_unknown),
    (ResponseType.ERROR_NOT_FOUND, on_response_not_found),
    (ResponseType.ERROR_NO_CHANGE, on_response_no_change),
    )
    client.connect()


