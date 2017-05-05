#-*- coding: UTF-8 -*-
import socket
import select
import sys
import threading
import requests
import json
import random

from tester import TestLoader, TestClient
from solver import broker, random_method, single_method, minimal_cost_method

ipParserUrl = 'http://api.ip138.com/query/?datatype=jsonp&token=c7fbe6a2583ed6c76847560e89960e82&ip='

nodePool = {}

addrTable = [
    ['美国'], ['中国', '上海'], ['中国', '广东']
]


class CDNNode(object):
    def __init__(self, ip, addr, maxt):
        self.ip = ip
        self.addr = addr
        self.maxTransmit = maxt
        self.currTransmit = 0

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
        return str(self.ip)

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

    def isOverloaded(self):
        return self.currTransmit >= self.maxTransmit


class ClientListener(threading.Thread):
    def __init__(self, threadID, name, port):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.port = port

    def run(self):
        self.connectClient(self.port)

    def connectClient(self, port):
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.bind(('', port))
        while True:
            data, addr = skt.recvfrom(1024)
            r = requests.get(ipParserUrl + addr[0])
            print('Recived:', str(data, encoding='utf-8'),
                  'from', addr)
            data = eval(r.text)
            print(data)
            addr = tuple(data['data'][:2])
            node = CDNNode(data['ip'], data['data'], 1024)
            addNode2Pool(node, addr)
            print(str(node) + '添加成功，所属区域' + str(addr))


class Tester(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def excute(testFile):
        pass


def access(url, proxies):
    r = requests.get(url, proxies=proxies)


def addNode2Pool(node, addr):
    if not addr in nodePool:
        nodePool[addr] = []
    nodePool[addr].append(node)


if __name__ == '__main__':
    # threads = []

    # listener = ClientListener(0, 'listener', 9800)

    # listener.start()

    # threads.append(listener)
    # testLoader = TestLoader('test')

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
    # result = optimal(requestsData[0], latencyData[0], limitData[0])
    # print(result)

    testLoader = TestLoader('test')
    testLoader.countData(900000)
    print(testLoader.requestsData)
    op_sum = rd_sum = sg_sum = mc_sum = 0
    for p in range(testLoader.total_period):
        op_value, op_result = broker(testLoader.requestsData[p], latencyData[0], limitData[0])
        rd_value, rd_result = random_method(testLoader.requestsData[p])
        sg_value, sg_result = single_method(testLoader.requestsData[p], 1)
        mc_value, mc_result = minimal_cost_method(testLoader.requestsData[p])

        print(op_result)
        print(mc_result)

        op_sum += op_value
        rd_sum += rd_value
        sg_sum += sg_value
        mc_sum += mc_value

    print('total cost compare:\noptimal: {0} | random: {1} | single {2} | minimal {3}'.format(op_sum, rd_sum, sg_sum, mc_sum))
        
        
