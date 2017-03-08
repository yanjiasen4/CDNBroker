import sys
import yaml

class Loader:
    priceData = []
    limitData = []
    capacityData = []
    priceKey = 'price'
    limitKey = 'limit'
    capacityKey = 'capacity'

    def __init__(self, filename):
        configFile = open(filename)
        configYaml = yaml.load(configFile)
        configFile.close()
        for key in configYaml[self.priceKey]:
            self.priceData.append(configYaml[self.priceKey][key])
        for key in configYaml[self.limitKey]:
            self.limitData.append(configYaml[self.limitKey][key])
        for key in configYaml[self.capacityKey]:
            self.capacityData.append(configYaml[self.capacityKey][key])

    def printData(self):
        print self.priceData
        print self.limitData
        print self.capacityData


