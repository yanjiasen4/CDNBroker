#-*- coding: UTF-8 -*-
import socket
import select
import sys
import threading
import requests
import json
import random
import time

from threading import Timer

from tester import TestLoader, TestClient
from solver import broker, random_method, single_method, minimal_cost_method, CDNs

ipParserUrl = 'http://api.ip138.com/query/?datatype=jsonp&token=c7fbe6a2583ed6c76847560e89960e82&ip='

monitorPort = 8000  # broker get client status from 8000
defaultPort = 3128  # client squid listening port
nodePool = {}

interval_15min = 900000  # 15min
interval_30min = 2 * interval_15min
interval_1hour = 4 * interval_15min

addrTable = [
    ['美国'], ['中国', '上海'], ['中国', '广东']
]

requestsData = [[]]

optimalValue = randomValue = singleValue = minimalValue = []

optimalRes = []
randomRes = []
singleRes = []
minimalRes = []

op_sum = rd_sum = sg_sum = mc_sum = 0

testInfo = []

latencyData = [
    [
        (230, 144, 128),
        (258, 162, 110),
        (224, 150, 116)
    ]
]
limitData = [
    (250, 152, 120)
]
CDNUsage = {}
for CDN in CDNs:
    CDNUsage[CDN] = 0

class CDNNode(object):
    def __init__(self, ip, addr, maxt):
        self.ip = ip
        self.port = defaultPort
        self.addr = addr
        self.maxTransmit = maxt
        self.currTransmit = 0
        self.status = 'working'

    def __cmp__(self, other):
        for i in range(min(len(self.addr, other, addr))):
            if self.addr[i] > other.addr[i]:
                return 1
            elif self.addr[i] == other.addr[i]:
                continue
            else:
                return -1
        return 0

    def __str__(self):
        return str(self.ip) + ':' + str(self.port)

    def update(self):
        r = requests.get(self.ip + ':' + str(monitorPort))
        if r.status_code == 200:
            self.currTransmit = float(r.text)
        else:
            self.status = 'error'

    '''
    The larger return value is, the more closer 2 nodes are.
    lower bound is 0
    '''

    def cmpRegion(self, other, maxlevel=None):
        value = 0
        cmpLevel = min(len(self.addr), len(other.addr))
        if maxlevel is not None:
            cmpLevel = min(cmpLevel, maxlevel)
        for i in range(cmpLevel):
            if self.addr[i] == other.addr[i]:
                value += 1
            else:
                break
        return value

    '''
    whetehr 2 nodes are in a same region.
    maxlevel denote the compare level for address.
    '''

    def inSameRegion(self, other, maxlevel=None):
        addrLevel = len(self.addr)
        if addrLevel != len(other.addr):
            return Fasle
        if maxlevel is not None:
            addrLevel = maxlevel
        value = self.cmpRegion(other, maxlevel=addrLevel)
        return value == addrLevel

    def addrcmp(self, addr, maxlevel=None):
        cmpLevel = min(len(self.addr), len(other.addr))
        if maxlevel is not None:
            cmpLevel = min(cmpLevel, maxlevel)
        for i in range(cmpLevel):
            if self.addr[i] != addr[i]:
                return False

        return True

    '''
    Weather a CDN node is overloaded.
    '''

    def isOverloaded(self):
        return self.currTransmit >= self.maxTransmit or self.status != 'working'


class ClientListener(threading.Thread):
    def __init__(self, threadID, name, port):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.port = port

    def run(self):
        self.connectClient(self.port)
        self.updateClient()

    def connectClient(self, port):
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.bind(('', port))
        while True:
            data, addr = skt.recvfrom(1024)
            addr = ('120.24.71.4', 8000)  # local test
            r = requests.get(ipParserUrl + addr[0])
            print('Recived:', str(data, encoding='utf-8'),
                  'from', addr)
            data = eval(r.text)
            addr = tuple(data['data'][:2])
            node = CDNNode(data['ip'], data['data'], 1024)
            addNode2Pool(node, addr)
            print(str(node) + '添加成功，所属区域' + str(addr))

    def updateClient(self):
        while(True):
            time.sleep(10)
            for nd in nodePool:
                nd.update()


class Tester(threading.Thread):
    def __init__(self, threadID, name, loader):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.loader = loader
        self.currentOptRes = [[0 for i in range(self.loader.urlNum)] for j in range(self.loader.addrNum)]

    def run(self):
        lastEntryTime = 0
        delay = 5  # wait for last request finished
        pCount = 0
        for period in self.loader.requestsDataInfo:
            for entry in period:
                lastEntryTime = float(entry[0] / 1000)
                t = Timer(lastEntryTime, self.executeTestEntry,
                          args=(entry, pCount))
                t.start()
            print(self.loader.countInterval * pCount / 1000)
            solver = Timer(self.loader.countInterval * pCount / 1000, self.solve,  args=(pCount,))
            solver.start()
            pCount += 1
        recorder = Timer(lastEntryTime + delay, self.saveTest)

    def saveTest(self):
        with open('res.log', 'w+') as f:
            for data in testInfo:
                f.writelines(str(data) + '\n')
            f.close()

    def solve(self, period):
        # calculate requests total size
        mutex.acquire()
        for (akey, addr) in self.loader.addrList[period].items():
            addrIndex = addr['index']
            for (ukey, url) in self.loader.urlList[period].items():
                urlIndex = url['index']
                urlSize = url['size']
                self.loader.requestsData[period][addrIndex][urlIndex] *= int(urlSize)
                print(self.loader.requestsData[period][addrIndex][urlIndex])

        dataInput = self.loader.requestsData[period]
        mutex.release()

        print(dataInput)
        op_value, op_result = broker(
            dataInput, latencyData[0], limitData[0], CDNUsage)
        print(op_value)
        print(op_result)
        optimalValue.append(op_value)
        optimalRes.append(op_result)
        for i in range(self.loader.addrNum):
            for j in range(self.loader.urlNum):
                self.currentOptRes[i][j] = op_value[i*self.loader.urlNum + j]
        print(self.currentOptRes)

    def executeTestEntry(self, requestsInfo, period):
        timestamp = int(requestsInfo[0])
        url = requestsInfo[1]
        addr = tuple(requestsInfo[2])
        ret = findNode(addr)
        res = {}
        if ret:
            res = accessViaPCDN(url, ret)
            if res['success']:
                mutex.acquire()
                testInfo.append(res)
                addrIndex = self.loader.addrList[period][addr]['index']
                urlIndex = self.loader.urlList[period][url]['index']
                if 'size' not in self.loader.urlList[period][url].keys():
                    self.loader.urlList[period][url]['size'] = res['contentLength']
                self.loader.requestsData[period][urlIndex][addrIndex] -= 1
                mutex.release()
        else:
            addrIndex = self.loader.addrList[period][addr]['index']
            urlIndex = self.loader.urlList[period][url]['index']
            cdn = choiceByPercentage(self.currentOptRes[addrIndex][urlIndex], CDNs)
            res = accessViaCDN(url, cdn)
        res['time'] = timestamp
        print(res)

def choiceByPercentage(percentage, obj):
    accum_p = []
    current_p = 0
    for p in percentage:
        accum_p.append(current_p + p)
        current_p += p
    sd = random.random()
    index = 0
    for p in accum_p:
        if sd > p:
            index += 1
    if index >= len(obj): return None
    return obj[index]

def accessViaCDN(url, CDN):
    data = access(url)
    data['pCDN'] = None
    CDNUsage[CDN] += data['contentLength']
    return data


def accessViaPCDN(url, pCDN):
    proxies = {'http': str(pCDN)}
    data = access(url, proxies)
    data['pCDN'] = str(pCDN)
    return data


def access(url, proxies=None):
    r = requests.get(url, proxies=proxies)
    res_data = {}
    res_data['url'] = url
    if r.status_code == 200:  # OK
        res_data['success'] = True
        if 'Content-Length' in r.headers:
            res_data['contentLength'] = int(r.headers['Content-Length'])
        else:
            res_data['contentLength'] = int(len(r.text))
        if 'X-Cache' in r.headers:
            res_data['cache'] = r.headers['X-Cache']
            if 'HIT' in res_data['cache']:
                res_data['hit'] = True
            else:
                res_data['hit'] = False
        res_data['elspsed'] = r.elapsed.microseconds
    else:
        res_data['success'] = False
    return res_data


def findNode(taraddr):
    for (addr, nodes) in nodePool.items():
        if addr == taraddr:
            return nodes[0]
    return None


def addNode2Pool(node, addr):
    if not addr in nodePool:
        nodePool[addr] = []
    nodePool[addr].append(node)


mutex = threading.Lock()

if __name__ == '__main__':
    threads = []

    listener = ClientListener(0, 'listener', 9800)
    testLoader = TestLoader('test')
    testLoader.countData(interval_15min)
    tester = Tester(1, 'tester', testLoader)

    listener.start()

    time.sleep(10)
    tester.start()

    threads.append(listener)
    threads.append(tester)

    # requestsData = [
    #     [
    #         [120, 800, 680],
    #         [45, 250, 300],
    #         [280, 114, 108]],
    #     [
    #         [112, 850, 720],
    #         [42, 340, 320],
    #         [250, 120, 84]],
    #     [
    #         [104, 860, 660],
    #         [60, 280, 280],
    #         [320, 118, 120]],
    #     [
    #         [60, 820, 700],
    #         [28, 320, 280],
    #         [48, 278, 318]]
    # ]
    # latencyData = [
    #     [
    #         (230, 144, 128),
    #         (258, 162, 110),
    #         (224, 150, 116)
    #     ]
    # ]
    # limitData = [
    #     (250, 152, 120)
    # ]
    # # result = optimal(requestsData[0], latencyData[0], limitData[0])
    # # print(result)

    # testLoader = TestLoader('test')
    # testLoader.countData(900000)
    # print(testLoader.requestsData)

    # for p in range(testLoader.total_period):
    #     op_value, op_result = broker(
    #         testLoader.requestsData[p], latencyData[0], limitData[0])
    #     rd_value, rd_result = random_method(testLoader.requestsData[p])
    #     sg_value, sg_result = single_method(testLoader.requestsData[p], 1)
    #     mc_value, mc_result = minimal_cost_method(testLoader.requestsData[p])

    #     print(op_result)
    #     print(mc_result)

    #     op_sum += op_value
    #     rd_sum += rd_value
    #     sg_sum += sg_value
    #     mc_sum += mc_value

    # print('total cost compare:\noptimal: {0} | random: {1} | single {2} | minimal {3}'.format(
    #     op_sum, rd_sum, sg_sum, mc_sum))
