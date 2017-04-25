from http.server import HTTPServer, BaseHTTPRequestHandler
import io
import shutil
import urllib


class MonitorServer(BaseHTTPRequestHandler):
    def do_GET(self):
        result = self.get_net_stat()
        enc = 'UTF-8'
        encoded_res = ''.join(result).encode(enc)
        f = io.BytesIO()
        f.write(encoded_res)
        f.seek(0)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(encoded_res)))
        self.end_headers()

        shutil.copyfileobj(f, self.wfile)

    def get_net_stat(self):
        net = []
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


httpd = HTTPServer(('', 8000), MonitorServer)
print('Server started on localhost, port 8000')
httpd.serve_forever()
