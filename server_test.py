####################################### PART 1: Command Line #####################################################
import sys
from typing import List, Tuple

class commands:

    def __init__(self, **kwargs) -> None:
       
        self.argv : list = []
        self.argn : int = 0

        if kwargs.__len__ == 0 :
            return

    def get_args(self, args : List[str] or None = None) -> Tuple[list, int]:
        
        if args is None or args.__len__ <= 1 :
            self.argv = sys.argv[1:]
            self.argn = len(sys.argv)
            return (self.argv, self.argn)

        self.argv = args[1:]
        self.argn = len(args)

        return (self.argv, self.argn)

    def parameters(self, format : List[str] or None = None) -> dict:
       
        temp = {}

        for i,x in enumerate(self.argv):
    
            if format and x in format and i < self.argn - 1:
                    temp.update({
                        x: self.argv[i + 1]
                    })
            else:
                sys.exit("unknown option: "+x+"\n")
        
        return temp

########################################### PART 2: ENCODING THE COMMANDS  ########################################

import enum
from typing import List

class MessageType(enum.Enum):
   
    REQUEST = 0
    RESPONSE = 1

class MethodType(enum.Enum):
    def get_format(self) -> List[int]:
        pass
    

class RequestType(MethodType):

    PUT = "000"
    GET = "001"
    CHANGE = "010"
    HELP = "011"

    def get_format(self):
       
        if self == RequestType.PUT:
            return [5, 32 * 8, 4 * 8]
        elif self == RequestType.GET:
            return [5, 32*8]
        elif self == RequestType.CHANGE:
            return [5, 32 * 8, 8, 32 * 8]
        elif self == RequestType.HELP :
            return [5]
        else:
            return []

class ResponseType(MethodType):
    OK_PUT_CHANGE = "000"
    OK_GET = "001"
    ERROR_NOT_FOUND = "010"
    ERROR_UNKNOWN = "011"
    ERROR_NO_CHANGE = "101"
    HELP = "110"

    def get_format(self):
        if self == ResponseType.OK_PUT_CHANGE:
            return [5]
        elif self == ResponseType.OK_GET:
            return [5, 32*8, 4*8]
        elif self == ResponseType.ERROR_NOT_FOUND:
            return [5]
        elif self == ResponseType.ERROR_UNKNOWN:
            return [5]
        elif self == ResponseType.ERROR_NO_CHANGE:
            return [5]
        elif self == ResponseType.HELP :
            return [5, 32 * 8]
        else:
            return []

####################################### PART 3: CONVERTING STRING INPUT TO BINARY ENCODING ###########################################
import math
from typing import List, Tuple
import bitarray
from bitarray import util
from packet import packet

class Message:
    def __init__(self, header_size : int, type: MethodType) -> None:
       
        self.header = packet(header_size)
        
        self.data : list[packet] = []
        self.type : MethodType = type

        self.header(self.type.value)

        self.size = header_size

        self.payload : packet or None = None



        self._token(
            self.type.get_format()
        )
        
    
    def _token(self, format : List[int]):
      
        if len(format) == 0:
            return None

        
        for x in format:
            self.data.append(
                packet(x)
            )
        
        self.size += sum(format)
        

    def parse(self, value : str) -> Tuple[packet, List[packet]] or None:
    
        if(value.__len__ == 0 or len(value) > self.size):
            return None
                       
        if not len(self.data):
            return None

        ind = 0
        
        for i, x in enumerate(self.data):
            x(value[ind :  ind + x.size ])            
            ind += x.size


        return (self.header, self.data)

    def add_payload(self, value : str or bytes, encode : str = "utf-8" or "bytes") -> None:
     
        temp = bitarray.util.hex2ba( value.hex() ).to01()

        self.payload = packet(len(temp))
        self.payload(temp)

    def has_payload(self) -> bool:
        
        return self.payload is not None

    

    def __repr__(self) -> str:
        temp = "["+ self.header.__str__() +"]"
        for x in self.data:
            temp += x.__str__()
        return  temp
        
    def __str__(self) -> str:
        temp = "["+ self.header.__str__() +"]"
        for x in self.data:
            temp += x.__str__()
        return  temp


class Util:

    @staticmethod
    def serialize(msg : Message) -> bytes:
     
        binary : bitarray.bitarray = bitarray.bitarray(endian="big")
        
        binary.extend(
            msg.header.body
        )


        for x in msg.data:
            binary.extend(
                x.body
            )
        
        if msg.has_payload():
            binary.extend(
                msg.payload.body
            )


        return util.serialize(binary)


    @staticmethod
    def deserialize(binary : bytes, type : MessageType) -> Message:
       
        temp : bitarray.bitarray = util.deserialize(binary)
        
        if type == MessageType.REQUEST:
            msg = Message(3, RequestType(temp.to01()[:3]))

            if msg.type == RequestType.PUT:
                msg.parse(
                    temp.to01()[3:msg.size]
                )
                pk = packet(len(temp.to01()[msg.size:]))
                pk(temp.to01()[msg.size:])
                msg.payload = pk
            else:
                
                msg.parse(
                    temp.to01()[3:]
                )

            return msg

        elif type == MessageType.RESPONSE:
            msg = Message(3, ResponseType(temp.to01()[:3]))
            if msg.type == ResponseType.OK_GET:
                msg.parse(
                    temp.to01()[3:msg.size]
                )
                pk = packet(len(temp.to01()[msg.size:]))
                pk(temp.to01()[msg.size:])
                msg.payload = pk

            else:
                msg.parse(
                    temp.to01()[3:]
                )
        
            return msg
        
        else:
            raise ValueError("Incorrect Message type")
        



    @staticmethod
    def str2bit(val : str, size : int, with_count : bool = True, size_count : int or None = None ) -> str:
      
        val = val.strip()

        data : str = util.hex2ba( val.encode("utf-8").hex() ).to01()

        if(len(data) > size): raise ValueError("Value passed is too big")


        if(len(data) < size):
            for _ in range(0, size - len(data)):
                data = "0" + data


        if with_count:
            count : int = util.int2ba(len(val)).to01()
            
            if size_count:
                count_size = size_count
            else:
                count_size = int( math.log2( int(size / 8) ) ) 

            if(len(count) < count_size):
                for _ in range(0, count_size - len(count)):
                    count = "0" + count

            return count + data
        else:
            return data
    @staticmethod
    def bit2byte(msg : Message) -> List[bytes]:
        temp : list[bytes] = []
        for x in msg.data:
            temp.append(
                x.body.tobytes()
            )
        if msg.has_payload():
            temp.append(
                msg.payload.body.tobytes()
            )

        return temp

##################################### PART 4: SETTING UP SERVER TCP ###################################    
from ast import arg
import socket as sok
import sys
from threading import Thread
from types import FunctionType
from typing import Any, Callable, List, Tuple
from bitarray import util

class TcpServer():
    _DEFAULT_PORT = 1025
    _MAX_BUFFER = 65574

    def __init__(self, ip_addr, **kwargs) -> None:
    
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
    
        return """-- FTP Server initializing on {ip}:{port}""".format(ip = self.ip_address, port = self._DEFAULT_PORT)

    def listen(self):
       
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

            except KeyboardInterrupt:
                    print("Closing server")
                    self.is_connected = False
                    self.socket.close()
                    return
            except BlockingIOError:
                print("EAGAIN error")
                continue

        

    def handle_listen(self, conn : sok.socket, addr : sok.AddressInfo):
       
        print("""> New connection {addr}:{port}""".format(addr = addr[0], port=addr[1]))

        while self.is_connected:
            try:              
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
       
        for x in args:
            self.recv_functions.append(x)

    @staticmethod
    def parse_packet(data : bytes) -> Message:
    
        return Util.deserialize(data, MessageType.REQUEST)

############################ PART 5: CREATING TCP CLIENT ###############################
import os
from re import S
from socket import socket
import bitarray

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
    val = Util.str2bit("bye change get help put",ResponseType.HELP.get_format()[1])
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

        return response_error_no_change()

    return response_ok()


def on_receive_get(addr, data : Message) -> bytes:

    result = Util.bit2byte(data)

    file_name = BASE_DIR + result[1].decode("utf-8")
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


if __name__ == "__main__":

    cmd = commands(version="tcp_server version 1.0")

    cmd.get_args()

    params = cmd.parameters(["-a", "-p", "-f", "-F", "-d"])

    if "-f" in params:
        server_dir = params["-f"]
    elif "-F" in params:
        BASE_DIR = params["-F"]
    
    tcp_server = TcpServer("0.0.0.0", **params)

    

    tcp_server.on_receive(
    (RequestType.PUT , on_receive_put),
    (RequestType.GET, on_receive_get),
    (RequestType.CHANGE, on_receive_change),
    (RequestType.HELP, on_receive_help),
    )

    tcp_server.listen()