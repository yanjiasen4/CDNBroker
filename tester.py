#-*- coding: UTF-8 -*-
import requests

class TestClient(object):
    def __init__(self, id, addr):
        self.id = id
        self.addr = addr
        self.bechmark = []
        self.result = []
        self.hitCount = 0
        self.testCount = 0

    def loadbechmark(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                self.bechmark.append(line)
                self.testCount += 1
            f.close()

    '''
    access test url via personal CDN node
    record elspsed time
    '''
    def accessViaPCDN(self, url, accNode):
        r = requests.get(url, proxies=accNode)
        res_data = {}
        res_data['url'] = url
        res_data['isPCDN'] = True
        res_data['accNode'] = accNode
        if r.status_code == 200: # OK
            if 'Content-Length' in r.headers:
                res_data['contentLength'] = int(r.headers['Content-Length'])
            if 'X-Cache' in r.headers:
                res_data['cache'] = r.headers['X-Cache']
                if 'HIT' in res_data['cache']:
                    res_data['hit'] = True
                    self.hitCount += 1
                else:
                    res_data['hit'] = False
            res_data['elspsed'] = r.elapsed.microseconds
    
    '''
    access test url via professional CDN
    use solver to dispatch requests
    '''
    def accessViaCDN(self, url, accNode):
        r = requests.get(url)
        res_data = {}
        res_data['url'] = url
        res_data['isPCDN'] = False
        res_data['accNode'] = accNode
        if r.status_code == 200: # OK
            if 'Content-Length' in r.headers:
                res_data['contentlength'] = int(r.headers['Content-Length'])
            res_data['elspsed'] = r.elapsed.microseconds
            res_data['cost'] = accNode.price[self.addr] * res_data['contentlength']
            
