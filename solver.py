from pymprog import model
from loader import Loader

configFile = 'config.yaml'
ld = Loader(configFile)
N = [ 12000, 14800, 13600 ]
P = ld.priceData
C = ld.capacityData
tm = 3600
S = [ ( 0.8, 1.1, 0.7),
      ( 1.2, 1.5, 0.9),
      ( 0.6, 1.2, 0.8) ] # latency data get from CDN
L = ld.limitData
p = model('basic')
p.verbose(True)
x = p.var('x', 9)
for i in range(9):
  x[i] <= 1
p.minimize(sum(sum(P[i][j]*x[3*j+i]*N[j] for i in range(3)) for j in range(3)), 'Minimize CDN Cost')
for i in range(3):
  x[3*i] + x[3*i+1] + x[3*i+2] == 1 
  sum(S[i][j]*x[3*i+j] for j in range(3)) <= L[i] # latency limit
  sum(x[i+3*j] for j in range(3))*N[i]/tm <= C[i] # capacity limit
  
p.solve() # solve the model
p.sensitivity() # sensitivity report

p.end()