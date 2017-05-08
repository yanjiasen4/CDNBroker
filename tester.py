#-*- coding: UTF-8 -*-
import requests
import math


class TestLoader(object):
    # load when init?
    def __init__(self, filename):
        self.tdata = []
        self.urls = []
        self.addrs = []
        with open(filename, 'r+') as f:
            for line in f:
                res = line.split(';')
                url = res[1]
                addr = tuple(res[2][:-1].split(','))
                if url not in self.urls:
                    self.urls.append(url)
                if addr not in self.addrs:
                    self.addrs.append(addr)
                self.tdata.append(
                    (int(res[0]), res[1], res[2][:-1].split(',')))
            f.close()
            # count
            self.length = self.tdata[-1][0]  # ms
            self.amount = len(self.tdata)
            self.urlNum = len(self.urls)
            self.addrNum = len(self.addrs)

    '''
    Statistical test data
    Use interval to slice it into servals period and count requests amounts in each period from each address for each objects
    Note that interval unit is ms
    result:
        total_period: total period slice by interval
        requestsDataInfo: detail requests information slice by interval
        requestsData: 3D array. 3 dimension represent period, object and address respectively.
        urlList: record each urls indices and count in each periods
        addrList: record each addrs indices and count in each periods 
    '''
    def countData(self, interval):
        if not self.tdata or self.tdata[0][0] > interval: return
        tperiod = math.ceil(self.length / interval)
        self.requestsDataInfo = [[] for i in range(tperiod)]
        self.requestsData = [[[0 for k in range(self.addrNum)] for j in range(
            self.urlNum)] for i in range(tperiod)]
        self.urlList = [{} for i in range(tperiod)] 
        self.addrList = [{} for i in range(tperiod)]
        self.total_period = tperiod
        urlNumber = -1  # start at 0
        addrNumber = -1

        period = 0
        for d in self.tdata:
            if d[0] >= (period + 1) * interval:
                period += 1
                urlNumber = -1
                addrNumber = -1
            url = d[1]
            addr = tuple(d[2])
            if url not in self.urlList[period].keys():
                urlNumber += 1
                self.urlList[period][url] = {'index': urlNumber, 'count': 1}
            else:
                self.urlList[period][url]['count'] += 1
            if addr not in self.addrList[period].keys():
                addrNumber += 1
                self.addrList[period][addr] = {'index': addrNumber, 'count': 1}
            else:
                self.addrList[period][addr]['count'] += 1

            curUrlIndex = self.urlList[period][url]['index']
            curAddrIndex = self.addrList[period][addr]['index']
            self.requestsData[period][curUrlIndex][curAddrIndex] += 1

            self.requestsDataInfo[period].append(d)
        

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
        if r.status_code == 200:  # OK
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
        if r.status_code == 200:  # OK
            if 'Content-Length' in r.headers:
                res_data['contentlength'] = int(r.headers['Content-Length'])
            res_data['elspsed'] = r.elapsed.microseconds
            res_data['cost'] = accNode.price[self.addr] * res_data['contentlength']
