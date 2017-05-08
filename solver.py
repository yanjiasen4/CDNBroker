#from pymprog import *
from loader import Loader
import random

configFile = 'config.yaml'
ld = Loader(configFile)
P = ld.priceData
C = ld.capacityData
tm = 3600
S = [(0.8, 1.1, 0.7),
     (1.2, 1.5, 0.9),
     (0.6, 1.2, 0.8)]  # latency data get from CDN

from pulp import *

def getOptimalValue(variables):
    ret = [0 for i in range(len(variables))]
    for var in variables:
        index = int(var.name[1:])
        ret[index] = var.varValue
    return ret


'''
requestsData:
    a 2D array, means whole requests for each objects in a period.
    example,
    requestsData = [
        (100,200,300),
        (50,400,200),
        (420,300,320)
    ]
    means there are requests from 3 address for 3 objects. 100 from addr1 request for object1...
latencyData:
    a 2D array
'''


def broker(requestsData, latencyData, limitData):

    N = requestsData
    S = latencyData
    L = limitData
    objectNum = len(requestsData)
    addrNum = len(requestsData[0])
    objectCyc = addrNum * addrNum
    variableNum = objectCyc * addrNum
    prob = LpProblem("min cost", LpMinimize)
    x = [LpVariable('x' + str(i), lowBound=0, upBound=1)
         for i in range(variableNum)]
    prob += sum(sum(sum(P[i][j] * x[objectCyc * k + addrNum * j + i] * N[k][j] for i in range(addrNum))
                    for j in range(addrNum)) for k in range(objectNum)), "Total Cost of CDN"
    for k in range(objectNum):
        for i in range(addrNum):
            prob += lpSum(x[objectCyc * k + addrNum * i + j]
                          for j in range(addrNum)) == 1, ""
            prob += lpSum(S[i][j] * x[objectCyc * k + addrNum * i + j]
                          for j in range(addrNum)) <= L[i], ""
            prob += lpSum(x[objectCyc * k + i + addrNum * j]
                          for j in range(addrNum)) * N[k][i] / tm <= C[i], ""

    prob.writeLP("CDNCostModel.lp")

    solveCount = 5
    minValue = -1
    optimalSolution = []
    currentSolution = []
    prob.solve()
    while True:
        prob.resolve()
        currentSolution = getOptimalValue(prob.variables())
        currValue = sum(sum(sum(P[i][j] * currentSolution[objectCyc * k + addrNum * j + i] * N[k][j]
                                for i in range(addrNum)) for j in range(addrNum)) for k in range(objectNum))
        if minValue < 0:
            minValue = currValue
            optimalSolution = currentSolution
        elif minValue > 0:
            if minValue > currValue:
                minValue = currValue
                optimalSolution = currentSolution
        if LpStatus[prob.status] == 'Optimal':
            solveCount += 1
        if solveCount >= 1:
            break

    print('optimal method: ' + str(minValue))
    return minValue, optimalSolution

# minimal cost (do not consider performance)

def minimal_cost_method(requestsData):
    N = requestsData
    objectNum = len(requestsData)
    addrNum = len(requestsData[0])
    objectCyc = addrNum * addrNum
    variableNum = objectCyc * addrNum
    prob = LpProblem("min cost", LpMinimize)
    x = [LpVariable('x' + str(i), lowBound=0, upBound=1, cat=LpContinuous)
         for i in range(variableNum)]
    prob += sum(sum(sum(P[i][j] * x[objectCyc * k + addrNum * j + i] * N[k][j] for i in range(addrNum))
                    for j in range(addrNum)) for k in range(objectNum)), "Total Cost of CDN"
    for k in range(objectNum):
        for i in range(addrNum):
            prob += lpSum(x[objectCyc * k + addrNum * i + j]
                          for j in range(addrNum)) == 1, ""

    prob.writeLP("CDNCostModelWithoutPerformance.lp")

    solveCount = 5
    minValue = -1
    optimalSolution = []
    currentSolution = []
    prob.solve()
    while True:
        prob.resolve()
        currentSolution = getOptimalValue(prob.variables())
        currValue = sum(sum(sum(P[i][j] * currentSolution[objectCyc * k + addrNum * j + i] * N[k][j]
                                for i in range(addrNum)) for j in range(addrNum)) for k in range(objectNum))
        if minValue < 0:
            minValue = currValue
            optimalSolution = currentSolution
        elif minValue > 0:
            if minValue > currValue:
                minValue = currValue
                optimalSolution = currentSolution
        if LpStatus[prob.status] == 'Optimal':
            solveCount += 1
        if solveCount >= 1:
            break

    print('minimal cost: ' + str(minValue))

    return minValue, optimalSolution


# randomly choice CDN to serve requests


def random_method(requestsData):
    N = requestsData
    objectNum = len(requestsData)
    addrNum = len(requestsData[0])
    objectCyc = addrNum * addrNum
    variableNum = objectCyc * addrNum

    x = [random.random() for i in range(variableNum)]
    for i in range(0, variableNum, addrNum):
        totalValue = sum(x[i + j] for j in range(0, addrNum))
        for k in range(0, addrNum):
            x[i + k] /= totalValue

    value = sum(sum(sum(P[i][j] * x[objectCyc * k + addrNum * j + i] * N[k][j] for i in range(addrNum))
                    for j in range(addrNum)) for k in range(objectNum))

    #print('random method: ' + str(value))
    return value, x

# choice single CDN to serve all requests


def single_method(requestsData, cdnid):
    N = requestsData
    objectNum = len(requestsData)
    addrNum = len(requestsData[0])
    objectCyc = addrNum * addrNum
    variableNum = objectCyc * addrNum
    amounts = [sum(N[i][k] for i in range(objectNum)) for k in range(addrNum)]

    value = sum(P[cdnid][j] * amounts[j] for j in range(addrNum))

    x = [0 for i in range(variableNum)]
    for i in range(0, variableNum, objectCyc):
        for j in range(0, objectCyc, addrNum):
            x[i + j + cdnid] = 1

    #print('single method: ' + str(value))
    return value, x
