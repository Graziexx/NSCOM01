#Imports
from socket import socket, setdefaulttimeout, AF_INET, SOCK_DGRAM, gethostname, gethostbyname #For connection
from TFTPPacket import * #TFTPacket imports
import os, traceback, time #operating system interfaces, printing and retrieving tracebacks, time access and conversions
import os.path

class TFTPClient(object):

    #Constants
    NOTFOUND = 'File not found.'
    TIMEOUT = 'Connection timed out.'
    MAXRETRY = 0xff # 255 max retry count during transmission
    MAXRUNS = 0xffffffff # 4294967295 total write() runs before shutting down prog
    MAXTRANSFER = 2 << 14 # 32768 bytes is max transfer
    HEADERSIZE = 2 << 1 # 4 bytes for header

    #Constructor
    def __init__(self, host, port=None):

        #Initializations

        self.modes = TFTPModes
        self.opcodes = TFTPOpcodes

        setdefaulttimeout(3) #2secs default timeout

        self.address = (host, 69) #address info: server address, port 69
        self.socket = socket(AF_INET, SOCK_DGRAM) #datagram socket for UDP
        self.log = TFTPLogging #logging info

        packet = TFTPPacket() #Instantiate class TFTPPacket
        self.ackpacket = packet.ACKPacket #Instantiate ack packet without invoking
        self.oackpacket = packet.OACKPacket #Instantiate oack packet without invoking
        self.defpacket = packet.RequestDefPacket #Instantiate default request packet without invoking
        self.optpacket = packet.RequestOptPacket #Instantiate option request packet without invoking
        self.datapacket = packet.DATAPacket #Instantiate data packet without invoking

    def __str__(self):

        return "%s:%s" % (self.address)

    def __del__(self):
        if hasattr(self, 'log'):
            self.log("Ending Connection...", msg="Connection Closed.")
        
        if hasattr(self, 'socket'):
            self.socket.close()

    #For downloading file
    def download(self, blksize, ogFileName, prefFilename=None, mode='octet'):

        oackflag = 0 #flag if oack is needed

        try:
            if not self.socket: #If there is no existing socket, create a socket
                self.socket = socket(AF_INET, SOCK_DGRAM)

            #Sets blksize
            self.DATASIZE = blksize
            self.BLKSIZE = self.DATASIZE + self.HEADERSIZE

            flag = False

            #Checks if oack flag shall be raised
            if self.DATASIZE == 512:
                oackflag = 0
            else:
                oackflag = 1

            fnf = 0 #for file not found

            if not ogFileName: #If there is no provided remote filename, raise an exception
                raise TFTPException("Input remote filename.")

            if not prefFilename: #If there is no provided preffered filename, set it same as the remote filename
                prefFilename = ogFileName

            self.log("DOWNLOAD \n", params=(blksize, ogFileName, prefFilename, mode), msg="Initiating RRQ request to: %s port: %s" % (self.address))

            opcode = self.opcodes["RRQ"] #Opcode set to WRQ (1)
            blkNum = 1 #Starts blkNum with 1

            if oackflag == 0: #If oack flag not raised, create default request packet of blksize 512
                sendBuffer = self.defpacket(ogFileName, mode, opcode)
            else: #If oack flag is raised, create request packet with optional blksize
                sendBuffer = self.optpacket(ogFileName, mode, opcode, self.DATASIZE)

            #Send the first RRQ Packet
            self.socket.sendto(sendBuffer, self.address) #Opens connection and and send request packet to server
            (rcvBuffer, (host, port)) = self.socket.recvfrom(self.BLKSIZE) #Gets the server response and new transaction identifier (TID)
            rcvTotal = len(rcvBuffer)
            retry_count = 0 #Initializes number of retries to 0

            # Exec time of program
            start_time = time.time()

            # open a stream to write
            with open(prefFilename, 'wb+') as f:
                while True:
                    try:
                        if blkNum % 5000 == 0:
                                print("Total {0} received: {1}, execution time: {2} sec".format('KB', rcvTotal / 1024, time.time() - start_time))
                                
                        if not host and port: #Checks validity of host and port
                            raise TFTPException("Host and port are invalid: %s:%s" % (host, port))

                        if rcvBuffer[1] == self.opcodes['OACK']:
                            #Creates ACK for the OACK received
                            sendBuffer = self.ackpacket(0)    
                            self.socket.sendto(sendBuffer, (host, port))  

                            f.write(rcvBuffer[4:]) #Write the DATA block, excluding the header 

                            #Receives DATA packet and new transaction identifier TID
                            (rcvBuffer, (host, port)) = self.socket.recvfrom(self.BLKSIZE) #Gets the server response and new transaction identifier (TID)
                            rcvTotal += len(rcvBuffer) #Adds to the total packets received

                            continue

                        if rcvBuffer[1] == self.opcodes['ERROR']: #Checks for an error through opcode
                            raise TFTPException(rcvBuffer[4:]) #Raise as exception the data that caused the error
                            break

                        if (((rcvBuffer[2] << 8) & 0xff00) + rcvBuffer[3]) == blkNum & 0xffff:
                            f.write(rcvBuffer[4:]) #Write the DATA block, excluding the header

                            #If DATA block is less than the expected blksize (blksize + header), then that was the last packet
                            if self.BLKSIZE > len(rcvBuffer):    
                                #Creates ACK for the last packet
                                sendBuffer = self.ackpacket(blkNum)    
                                self.socket.sendto(sendBuffer, (host, port))                                 
                                break                                                                   

                            #Continues to read from the server if it is not yet the last packet
                            else:
                                #Creates ACK packet
                                sendBuffer = self.ackpacket(blkNum)                                  
                                blkNum += 1

                                #Opens connection and send ACK packet to server
                                self.socket.sendto(sendBuffer, (host, port))

                                #Receives DATA packet and new transaction identifier TID
                                (rcvBuffer, (host, port)) = self.socket.recvfrom(self.BLKSIZE) #Gets the server response and new transaction identifier (TID)
                                rcvTotal += len(rcvBuffer) #Adds to the total packets received
                            
                    except Exception as err:
                        message = "BlkNum: {0}, retry count: {1}, header: {2}, error: {3}"
                        self.log("DOWNLOAD", params=(blksize, ogFileName, prefFilename, mode), msg="File not found.")
                        fnf = 1 #Raises flag for file not found
                        break
                        
                            
                        if self.TIMEOUT in err.args:
                            retry_count += 1
                       
                            if retry_count >= self.MAX_RETRY_COUNT:
                                print("Retried max {0} times. Terminating Transfer".format(retry_count))
                                break
                            else:
                                self.log("DOWNLOAD: Timeout exception", params=(blksize, ogFileName, prefFilename, mode), msg=message.format(blkNum, retry_count, rcvBuffer[:4], err))

                        elif self.NOTFOUND in err.args:
                            print("File %s does not exist!" % ogFileName)

                        # Unknown exception
                        else:
                            self.log("DOWNLOAD", params=(blksize, ogFileName, prefFilename, mode), msg="Unknown exception: %s" % err)
            
            if fnf == 0: #If file was found, download success
                flag = True
                self.log("DOWNLOAD SUCCESS:", params=(blksize, ogFileName, prefFilename, mode), msg="File {0} from host {1}, \ntotal bytes received: {2}, \ntotal retry counts: {3}, \nexecution time: {4} seconds".format(ogFileName, self.address, rcvTotal, retry_count, time.time() - start_time))
                            
        except TFTPException as terr: # only catch TFTP specific err
            self.log("DOWNLOAD FAILED: TFTP Exception", params=(blksize, ogFileName, prefFilename, mode), msg="Error {0}".format(terr))
            
        except Exception as err:
            self.log("DOWNLOAD FAILED: Could not connect to the server.", params=(blksize, ogFileName, prefFilename, mode), msg="Error {0}".format(err))
        
        finally:
            pass

        return flag
    
    def upload(self, blksize, ogFileName, prefFilename=None, mode='octet'):

        oackflag = 0 #Flag if oack is needed

        try:
            if not self.socket: #If there is no existing socket, create a socket
                self.socket = socket(AF_INET, SOCK_DGRAM)

            #Sets the blksize
            self.DATASIZE = blksize
            self.BLKSIZE = self.DATASIZE + self.HEADERSIZE

            flag = False

            #Checks if oack flag shall be raised
            if self.DATASIZE == 512:
                oackflag = 0
            else:
                oackflag = 1

            if not ogFileName: #If there is no provided remote filename, raise an exception
                raise TFTPException('Input remote filename.')

            if not prefFilename: #If there is no provided preffered filename, set it same as the remote filename
                prefFilename = ogFileName

            #Get buffer from file handle
            if os.path.exists(ogFileName): #Checks for the availability of the file
                file = open(ogFileName, 'rb+')
                fileBuffer = file.read()

                self.log('UPLOAD', params=(blksize, ogFileName, prefFilename, mode), msg="Initiating WRQ request {0}/{1} of size {2} KB.".format(self.address, prefFilename, round(len(fileBuffer)/1024)))
                
                opcode = self.opcodes["WRQ"] #Opcode set to WRQ (2)
                blkNum = 0 #Starts blkNum with 0

                if oackflag == 0: #If oack flag not raised, create default request packet of blksize 512
                    sendBuffer = self.defpacket(prefFilename, mode, opcode)
                else: #If oack flag not raised, create default request packet of optional blksize
                    sendBuffer = self.optpacket(prefFilename, mode, opcode, self.DATASIZE)

                #Send the first WRQ Packet
                self.socket.sendto(sendBuffer, self.address) #Opens connection and send request packet to server
                (rcvBuffer, (host, port)) = self.socket.recvfrom(self.BLKSIZE) #Gets the server response and new transaction identifier (TID)
                rcvTotal = len(rcvBuffer)
                retry_count = 0 #Initializes number of retries to 0
                start = 0 #Initializes start to 0
                totalRuns = 0 #Initializes number of runs to 0
                timeout = False #Initalizes connection timeout to false

                #Execution time of program
                start_time = time.time()

                while True:
                    try:
                        if totalRuns == self.MAXRUNS: #If 4294967295 runs was already done, stop the program
                            print("Maximum runs reached.")

                        if not host and port: #Checks validity of host and port
                            raise TFTPException("Host and port are invalid: %s:%s" % (host, port))
                                
                        if rcvBuffer[1] == self.opcodes['ERROR']: #Checks for an error through opcode
                            raise TFTPException(rcvBuffer[4:]) #Raise as exception the data that caused the error

                        if rcvBuffer[1] == self.opcodes['OACK']:
                            if not timeout: #If connection did not timeout
                                #Get next DATA block to send
                                buffer = fileBuffer[ start : (self.DATASIZE + start) ]
                                blkNum += 1

                                #Create DATA packet
                                sendBuffer = self.datapacket(blkNum, buffer)
                                
                                #Opens connection and send DATA packet to server
                                self.socket.sendto(sendBuffer, (host, port)) 
                                
                                #Receive ACK packet from server
                                (rcvBuffer, (host, port)) = self.socket.recvfrom(self.BLKSIZE)
                                
                                timeout = False
                                start += self.DATASIZE

                        # Verify ACK packet(4) and masks 4 bytes                                        # 0xffff - 0xff00 == 0xff
                        if rcvBuffer[1] == self.opcodes['ACK'] and (((rcvBuffer[2] << 8) & 0xff00) + rcvBuffer[3]) == blkNum & 0xffff:
                                
                            if not timeout: #If connection did not timeout
                                #Get next DATA block to send
                                buffer = fileBuffer[ start : (self.DATASIZE + start) ]
                                blkNum += 1

                                #Create DATA packet
                                sendBuffer = self.datapacket(blkNum, buffer)
                                
                                #Opens connection and send DATA packet to server
                                self.socket.sendto(sendBuffer, (host, port)) 
                                
                                #Receive ACK packet from server
                                (rcvBuffer, (host, port)) = self.socket.recvfrom(self.BLKSIZE)
                                
                                timeout = False
                                start += self.DATASIZE

                        #If DATA block is less than 516 bytes (512 + header), then that was the last packet
                        if len(sendBuffer) < self.BLKSIZE:
                            self.log("Last Packet Reached", msg="Terminating write...")
                            break

                        totalRuns += 1 #Increments the number of runs

                    except Exception as err:

                        message = "BlkNum: {0}, retry count: {1}, header: {2}, error: {3}"
                        self.log("UPLOAD: exception", params=(blksize, ogFileName, prefFilename, mode), msg=message.format(blkNum, retry_count, rcvBuffer[:4], err))

                        if self.TIMEOUT in err.args: #If connection timed out, increase number of retries

                            timeout = True
                            retry_count += 1

                            if retry_count >= self.MAXRETRY: #If retry counts exceeds 255
                                print("Retried max {0} times. Terminating transfer.".format(retry_count))
                                break
                            else:
                                self.log("UPLOAD: Timeout exception", params=(blksize, ogFileName, prefFilename, mode), msg=message.format(blkNum, retry_count, rcvBuffer[:4], err))
                
                flag = True
                self.log("UPLOAD SUCCESS:", params=(blksize, ogFileName, prefFilename, mode), msg="File {0} to host {1}, \ntotal bytes sent: {2}, \ntotal retry counts: {3}, \nexecution time: {4} seconds".format(ogFileName, self.address, rcvTotal, retry_count, time.time() - start_time))

            else: 
                self.log("UPLOAD", params=(blksize, ogFileName, prefFilename, mode), msg="File not found.")
                        
        except TFTPException as terr: #Only catches specific TFTP Exceptions
            self.log("UPLOAD: TFTP Exception", params=(blksize, ogFileName, prefFilename, mode), msg="Error: {0}".format(err))
            
        except Exception as err:
            self.log("UPLOAD FAILED: Could not connect to the server.", params=(blksize, ogFileName, prefFilename, mode), msg="Error {0}".format(err))
        
        finally:
            pass #Terminate

        return flag
