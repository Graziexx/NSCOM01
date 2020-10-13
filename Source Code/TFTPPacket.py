#Imports
from datetime import datetime #works with dates as date objects
import os, traceback #operating system interfaces, printing and retrieving tracebacks

#For logging purposes
DEV = True
LOG = True
LOGFILE = "TFTPLog.txt" #Outputs into a textfile all the file transfers

#IMPLEMENTATION OF RFC 1350
TFTPModes = {
    "unknown"   : 0,
    "netascii"  : 1,
    "octet"     : 2,
    "mail"      : 3
}

TFTPOpcodes = {

    "UNK"   : 0, #Unknown
    "RRQ"   : 1, #Read Request
    "WRQ"   : 2, #Write Request
    "DATA"  : 3, #Data
    "ACK"   : 4, #Acknowledgement
    "ERROR" : 5, #Error
    "OACK"  : 6  #Option Acknowledgement
}

#Creating TFTP Packets
class TFTPPacket(object):

    #Constructor
    def __init__(self):
        #Initializations
        self.log = TFTPLogging #Initializes log of file transfers
        self.opcodes = TFTPOpcodes #Initializes Opcodes
        self.modes = TFTPModes #Initializes Modes
        self.toInt = lambda args: [ord(a) for a in args] #Initializes convertion into integer representing unicode
        self.toBytes = bytearray #Initializes bytearray conversion

    #Creates the Packet
    def create(self, *args):

        result = [] #Initializes array result

        try:
            for arg in args: #appends to result every argument from parameter args that may have many arguments
                if not isinstance(arg, list):
                    arg = [arg]
                result += arg
        except Exception as err:
            print("Create", err)

        return result #returns the joint arguments (Created Packet)
    
    #Generates RRQ/WRQ Request Packet of Default blkSize 512
    def RequestDefPacket(self, filename, mode, opcode):

        try:
            # Following TFTP RRQ/WRQ Format
            # 2 bytes     string    1 byte     string   1 byte 
            # ------------------------------------------------
            #| Opcode |  Filename  |   0  |    Mode    |   0  |
            # ------------------------------------------------
            return self.toBytes(self.create(0, opcode, self.toInt(filename), 0, self.toInt(mode), 0))
        except Exception as err:
            print("RequestPacket", err)
            self.log("RequestPacket", params=(filename, mode, opcode), msg="Err: %s" % err)

    #Generates RRQ/WRQ Request Packet of option blksize modified
    def RequestOptPacket(self, filename, mode, opcode, blksize):

        try:
            # Following TFTP RRQ/WRQ Format
            # 2 bytes     string    1 byte     string   1 byte   string    1 byte    string    1 byte
            # ----------------------------------------------------------------------------------------
            #| Opcode |  Filename  |   0  |    Mode    |   0  |  blksize  |   0  |   #octets   |   0  |
            # ----------------------------------------------------------------------------------------
            return self.toBytes(self.create(0, opcode, self.toInt(filename), 0, self.toInt(mode), 0, self.toInt("blksize"), 0, self.toInt(str(blksize)), 0))
        except Exception as err:
            print("RequestPacket", err)
            self.log("RequestPacket", params=(filename, mode, opcode, blksize), msg="Err: %s" % err)

    #Generates ACK Packet
    def ACKPacket(self, blkNum):

        try:
            # Following TFTP ACK Format
            #  2 bytes     2 bytes
            #  ---------------------
            # | Opcode |   Block #  |
            #  ---------------------
            ########################################################(shift 8 bites and AND with 0xff(255)
            return self.toBytes(self.create(0, self.opcodes['ACK'], ((blkNum >> 8) & 0xff), (blkNum & 0xff)))
        except Exception as err:
            print("ACKPacket", err)
            print(self.create(0, self.opcodes['ACK'], ((blkNum >> 8) & 0xff), (blkNum & 0xff)))
            self.log("ACKPacket", params=(blkNum), msg="Creating ack packet: {0}\nErr: {1}".format(buffer, err))

    #Generates OACK Packet
    def OACKPacket(self, blksize):

        try:
            # Following TFTP ACK Format
            #  2 bytes     2 bytes
            #  -----------------------------------------
            # | Opcode |  blksize  |   0  |   #octets   |
            #  -----------------------------------------
            ########################################################(shift 8 bites and AND with 0xff(255)
            return self.toBytes(self.create(0, self.opcodes['OACK'], self.toInt("blksize"), self.toInt(str(blksize))))
        except Exception as err:
            print("OACKPacket", err)
            print(self.create(0, self.opcodes['OACK'], self.toInt("blksize"), self.toInt(str(blksize))))
            self.log("OACKPacket", params=(blksize), msg="Creating oack packet: {0}\nErr: {1}".format(buffer, err))
    
    #Generates DATA Packet
    def DATAPacket(self, blkNum, buffer):

        try:
            # utf-8 default with latin1 as backup
            encoding = 'latin1'

            #  Following TFTP DATA Format
            #  2 bytes     2 bytes      n bytes
            #  ----------------------------------
            # | Opcode |   Block #  |   Data     |
            #  ----------------------------------
            #########################################################(shift 8 bites and AND with 0xff(255)
            return self.toBytes(self.create(0, self.opcodes['DATA'], (blkNum >> 8) & 0xff, blkNum & 0xff, self.toInt(buffer.decode(encoding))))
        except Exception as err:
            print("DATAPacket", err)
            try:
                #Prints the data packet that caused the exception
                print(self.create(0, self.opcodes['DATA'], (blkNum >> 8) & 0xff, blkNum & 0xff, self.toInt(buffer.decode(encoding))))
            except:
                pass
            self.log("DATAPacket", params=(blkNum, buffer), msg="Calling data packet, data: {0}\nErr: {1}, traceback: {2}".format(buffer, err, traceback.format_exc()))

#Exception Messages
class TFTPException(Exception):

    def initialize(self, message):
        self.message = message

    def stringMssg(self):
        return str(self.message)

#For loggin the file transfers
class TFTPLogging():

    def __init__(self, action, msg=None, params=None):
        self.log(action, msg, params)
    
    # can be called without instatiating an instance of <TFTPClient>
    @staticmethod
    def log(action, msg=None, params=None):
        self.log(action, msg, params)

    # helper function to log behavior
    def log(self, action, msg=None, params=None):
        if LOG:
            try:
                ft_message = "Logged action: {0}\nDate: {1}\nParams: {2}\nMessage: {3}\n\n".format(action, datetime.today(), params, msg)
                if DEV:
                    print(ft_message)
                
                with open(LOGFILE, 'a+') as logfile:
                    logfile.write(ft_message)

            except Exception as logex:
                print("Logex: %s" % (logex))
