import random


def random_pick(sample, probabilites):
    x = random.uniform(0, 1)
    cumuprob = 0.0
    for item, item_prob in zip(sample, probabilites):
        cumuprob += item_prob
        if x < cumuprob:
            break
    return item


class TestMaker(object):
    def __init__(self):
        self.bechmark = {}

    '''
    generate a bechmark with format: timestamp, addr, url
    name: test name
    length: total time(ms) of this bechmark
    amounts: total requests number
    urls: list of urls to access by test
    urlsdr: distribution of urls
    addrs: list of address of accessor
    addrsdr: distribution of address
    '''

    def genTest(self, name, length, amounts, urls, urlsdr, addrs, addrsdr):
        tunit = length / amounts
        test = []
        for t in range(amounts):
            timestamp = int(random.uniform(0, tunit) + t * tunit)
            url = random_pick(urls, urlsdr)
            addr = random_pick(addrs, addrsdr)
            test.append((timestamp, url, addr))
        self.bechmark[name] = test

    def saveTest(self):
        for (key, value) in self.bechmark.items():
            with open(key, 'w+') as f:
                for entry in value:
                    addr = ''
                    for c in entry[2]:
                        addr += (c + ',')
                    addr = addr[:-1]
                    f.writelines('{0};{1};{2}\n'.format(
                        entry[0], entry[1], addr))
                f.close()
                
if __name__ == '__main__':
    testMaker = TestMaker()
    urls = ['http://yanjiasen4.tech', 'http://cdnbroker.tech', 'https://www.python.org']
    urlsdr = [0.3, 0.4, 0.3]
    addr = [['美国'],['中国','上海'],['中国','广东']]
    addrdr = [0.12, 0.56, 0.32]
    length = 60*60*1000 # 1hour
    testMaker.genTest('test', length, 4000, urls, urlsdr, addr, addrdr)
    testMaker.saveTest()
