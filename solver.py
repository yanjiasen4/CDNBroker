#from pymprog import *
from loader import Loader

configFile = 'config.yaml'
ld = Loader(configFile)
P = ld.priceData
C = ld.capacityData
tm = 3600
S = [(0.8, 1.1, 0.7),
     (1.2, 1.5, 0.9),
     (0.6, 1.2, 0.8)]  # latency data get from CDN
# p = model('basic')
# p.verbose(True)
# x = p.var('x', 9)
# for i in range(9):
#   x[i] <= 1

# p.minimize(sum(sum(P[i][j]*x[3*j+i]*N[j] for i in range(3)) for j in range(3)), 'Minimize CDN Cost')
# for i in range(3):
#   x[3*i] + x[3*i+1] + x[3*i+2] == 1
#   sum(S[i][j]*x[3*i+j] for j in range(3)) <= L[i] # latency limit
#   sum(x[i+3*j] for j in range(3))*N[i]/tm <= C[i] # capacity limit

# p.solve() # solve the model
# p.sensitivity()
# for k in x:
#   print(k.primal)
# cost = sum(sum(P[i][j]*x[3*j+1].primal*N[j] for i in range(3)) for j in range(3))
# print(cost)

# p.end()

from pulp import *


def optimal(requestsData, latencyData, limitData):

    N = requestsData
    S = latencyData
    L = limitData
    prob = LpProblem("min cost", LpMinimize)
    x1 = LpVariable("ChickenPercent", 0, None, LpInteger)
    x2 = LpVariable("BeefPercent", 0)
    x = [LpVariable(str(i), lowBound=0, upBound=1) for i in range(9)]
    prob += sum(sum(P[i][j] * x[3 * j + i] * N[j] for i in range(3))
                for j in range(3)), "Total Cost of CDN"
    for i in range(3):
        prob += lpSum(x[3 * i + j] for j in range(3)) == 1, str(i) + "sum to 1"
        prob += lpSum(S[i][j] * x[3 * i + j]
                      for j in range(3)) <= L[i], str(i) + "latency limit"
        prob += lpSum(x[i + 3 * j] for j in range(3)) * N[i] / \
            tm <= C[i], str(i) + "capacity limit"

    prob.writeLP("CDNCostModel.lp")

    solveCount = 0
    minValue = -1
    optimalSolution = []
    prob.solve()
    while True:
        prob.resolve()
        currValue = sum(sum(P[i][j] * prob.variables()[3 * j +
                                                       i].varValue * N[j] for i in range(3)) for j in range(3))
        if minValue < 0:
            minValue = currValue
            optimalSolution = [v.varValue for v in prob.variables()]
        elif minValue > 0:
            if minValue > currValue:
                minValue = currValue
                optimalSolution = [v.varValue for v in prob.variables()]
        if LpStatus[prob.status] == 'Optimal':
            solveCount += 1
        if solveCount >= 1:
            break

    return optimalSolution
