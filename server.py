#-*- coding: UTF-8 -*-
import socket,select
import sys
import _thread
import requests

if __name__=='__main__':      
    proxies = { "http": "http://23.83.247.144:3128" }
    r = requests.get("http://cdnbroker.tech",  proxies=proxies) 
    print(r.elapsed)


