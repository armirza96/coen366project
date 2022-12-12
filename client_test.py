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

##################################### PART 4: SETTING UP CLIENT TCP ###################################    
import socket as sok
import sys
from threading import Thread
from types import FunctionType
from typing import Callable, List, Optional, Tuple
import signal

class TcpClient():
    _DEFAULT_PORT = 1025
    _MAX_BUFFER = 65574

    def __init__(self, ip_addr, **kwargs) -> None:
    
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
     
        try:
            
            self.socket.connect( (self.ip_address, self._DEFAULT_PORT) )
            self._is_connected = True
            self.thread = Thread(target = self.handle_connection, args=())
            self.thread.start()
            if self.thread:
                self.thread.join()

        except ConnectionRefusedError:
           
            print("Unable to connect to server, try again")
        except KeyboardInterrupt:
            self.socket.close()
            self._is_connected = False            
        except Exception:
            return

    
    def handle_connection(self):

        lcls = locals()
        cmd_format : RequestType or None = None
        if self._debug:
            print("Debug mode ON")
        while self._is_connected:
            try:
                msg = self.cin()
                if len(msg):
                    try:
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
                print("invalid response", e)

    def check_response(self, data : bytes) -> Message:
      
        return Util.deserialize(data, MessageType.RESPONSE)


    def on_send(self, *args: Tuple[ MethodType ,Callable[[List[str], MethodType], bytes]]):
      
        for x in args:
            self.create_message_functions.append(x)

    def on_response(self, *args: Tuple[MethodType,  Callable[[Message], None ]] ):
      
        for x in args:
            self.on_response_functions.append(x)

    def cin(self) -> List[str]:
    
        try:
            msg = input("myftp> ")
            return msg.strip().split()
        except EOFError:
            raise KeyboardInterrupt

    def handler(self, signum , frame):
        self._is_connected = False
        self.socket.close()
        
############################ PART 5: CREATING TCP CLIENT ###############################
import os
from typing import List
import bitarray
from bitarray import util

client_dir = "client"

BASE_DIR = os.getcwd() + os.sep + "dir" + os.sep + client_dir + os.sep




def on_send_put(inp : List[str], type: MethodType) -> bytes:
    message = Message(3, type)

    try:
        with open(BASE_DIR + inp[1], "rb") as f:
            payload = f.read()
            size = os.path.getsize(BASE_DIR + inp[1])
    except IndexError:
    
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


if __name__ == "__main__":
    cmd = commands(version="tcp_server version 1.0")

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