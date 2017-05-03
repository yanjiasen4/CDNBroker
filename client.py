#-*- coding: UTF-8 -*-
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import io
import shutil
import urllib
import socket
import platform
import wmi


brokerServerIP = 'localhost'
brokerServerPort = 9800


class MonitorServer(BaseHTTPRequestHandler):
    def do_GET(self):
        result = self.get_net_stat()
        enc = 'UTF-8'
        global transmitBytesPerSec
        threadLock.acquire()
        encoded_res = ''.join(str(transmitBytesPerSec)).encode(enc)
        threadLock.release()
        f = io.BytesIO()
        f.write(encoded_res)
        f.seek(0)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(encoded_res)))
        self.end_headers()

        shutil.copyfileobj(f, self.wfile)


class ServerThread(threading.Thread):
    def __init__(self, threadID, name, monitorServer):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.monitorServer = monitorServer

    def run(self):
        self.connectInit()
        self.monitorServer.serve_forever()

    def connectInit(self):
        #clientIP = socket.gethostbyname(socket.gethostname())
        clientIP = '59.78.22.135'  # test
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.sendto(bytes(clientIP, encoding='utf-8'),
                   (brokerServerIP, brokerServerPort))


class MonitorThread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.interval = interval
        self.last_transmitBytes = 0

    def run(self):
        while(True):
            time.sleep(self.interval)
            threadLock.acquire()
            global transmitBytesPerSec
            netstat = self.get_net_stat()
            curr_transmitBytes = sum(float(iface['TransmitBytes']) for iface in netstat) / 1024 / 8
            diff_transmitBytes = curr_transmitBytes - self.last_transmitBytes
            transmitBytesPerSec = diff_transmitBytes / self.interval
            self.last_transmitBytes = curr_transmitBytes
            print(transmitBytesPerSec)
            threadLock.release()

    def get_net_stat(self):
        net = []
        os = platform.system()

        if os == 'Windows':
            c = wmi.WMI()
            for iface in c.Win32_PerfRawData_Tcpip_TCPv4():
                sentflow = float(iface.SegmentsSentPersec)  # 已发送的流量
                intf = {}
                intf['interface'] = iface.name
                intf['TransmitBytes'] = sentflow

                net.append(intf)

        elif os == 'Linux':
            f = open("/proc/net/dev")
            lines = f.readlines()
            f.close()
            for line in lines[2:]:
                con = line.split()
                """ 
                intf = {} 
                intf['interface'] = con[0].lstrip(":") 
                intf['ReceiveBytes'] = int(con[1]) 
                intf['ReceivePackets'] = int(con[2]) 
                intf['ReceiveErrs'] = int(con[3]) 
                intf['ReceiveDrop'] = int(con[4]) 
                intf['ReceiveFifo'] = int(con[5]) 
                intf['ReceiveFrames'] = int(con[6]) 
                intf['ReceiveCompressed'] = int(con[7]) 
                intf['ReceiveMulticast'] = int(con[8]) 
                intf['TransmitBytes'] = int(con[9]) 
                intf['TransmitPackets'] = int(con[10]) 
                intf['TransmitErrs'] = int(con[11]) 
                intf['TransmitDrop'] = int(con[12]) 
                intf['TransmitFifo'] = int(con[13]) 
                intf['TransmitFrames'] = int(con[14]) 
                intf['TransmitCompressed'] = int(con[15]) 
                intf['TransmitMulticast'] = int(con[16]) 
                """
                intf = dict(
                    zip(
                        ('interface', 'ReceiveBytes', 'ReceivePackets',
                        'ReceiveErrs', 'ReceiveDrop', 'ReceiveFifo',
                        'ReceiveFrames', 'ReceiveCompressed', 'ReceiveMulticast',
                        'TransmitBytes', 'TransmitPackets', 'TransmitErrs',
                        'TransmitDrop', 'TransmitFifo', 'TransmitFrames',
                        'TransmitCompressed', 'TransmitMulticast'),
                        (con[0].rstrip(":"), int(con[1]), int(con[2]),
                        int(con[3]), int(con[4]), int(con[5]),
                        int(con[6]), int(con[7]), int(con[8]),
                        int(con[9]), int(con[10]), int(con[11]),
                        int(con[12]), int(con[13]), int(con[14]),
                        int(con[15]), int(con[16]), )
                    )
                )

                net.append(intf)

        return net


interval = 10
transmitBytesPerSec = 0
threadLock = threading.Lock()
threads = []
httpd = HTTPServer(('', 8000), MonitorServer)

print('Server started on localhost, port 8000')

monitor = ServerThread(1, 'Monitor', httpd)
server = MonitorThread(2, 'Server')

monitor.start()
server.start()

threads.append(monitor)
threads.append(server)
