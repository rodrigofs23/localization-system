import paho.mqtt.client as mqtt
import json
import time
from statistics import mean
from collections import deque
import mysql.connector
from numpy import *
from numpy.linalg import inv
from numpy.random import randn
from numpy.linalg import det

tabela = {}
ultimoTempo = {}

posReceivers ={'F45EAB08A2A5':(136,600),    # Ponto-1
               '8030DCC6D0A8':(627,1755),   # Ponto-2
               '8030DCC8C854':(2009,100),   # Ponto-3
               'F45EAB097ADA':(2376,1145),  # Ponto-4
               'E0E5CFC3D48B':(2746,1152),  # Ponto-5
               'D0B5C2F3C421':(2954,100)}   # Ponto-6

def escreveBD(pos, beacon):
    con = mysql.connector.connect(host='127.0.0.1', user='sergiool', password='kedma256', db='ibeacon')
    cursor = con.cursor()
    cursor.execute('INSERT INTO position (mac, x, y) VALUES (%s, %s, %s)', (beacon, pos[0], pos[1]))
    con.commit()
    cursor.close()
    con.close()

def calculaPosicao(beacon):
   if len(tabela[beacon]) < 4:
       return 0,0
   sorted_x = sorted(tabela[beacon].items(), key=lambda x: converteRSSI(mean(x[1])))
   receiver1 = sorted_x[1][0]
   receiver2 = sorted_x[2][0]
   receiver3 = sorted_x[3][0]
       
   R1 = posReceivers[receiver1]
   R2 = posReceivers[receiver2]
   R3 = posReceivers[receiver3]
   d1 = converteRSSI(mean(tabela[beacon][receiver1]))
   d2 = converteRSSI(mean(tabela[beacon][receiver2]))
   d3 = converteRSSI(mean(tabela[beacon][receiver3]))

   A = R1[0]**2 + R1[1]**2 - d1**2
   B = R2[0]**2 + R2[1]**2 - d2**2
   C = R3[0]**2 + R3[1]**2 - d3**2
   X32 = R3[0] - R2[0]
   X13 = R1[0] - R3[0]
   X21 = R2[0] - R1[0]

   Y32 = R3[1] - R2[1]
   Y13 = R1[1] - R3[1]
   Y21 = R2[1] - R1[1]

   x = (A * Y32 + B * Y13 + C * Y21)/(2.0*(R1[0]*Y32 + R2[0]*Y13 + R3[0]*Y21))
   y = (A * X32 + B * X13 + C * X21)/(2.0*(R1[1]*X32 + R2[1]*X13 + R3[1]*X21))

   return x, y;

def converteRSSI(rssi):
   rssi0 = -58.0
   return (10**(abs(rssi-rssi0)/20.0))*100
       
def na_conexao(cliente, dados, flags, retorno):
    print('Conectado. Codigo de retorno:' + str(retorno))
# Topico assinado na conexao. Caso desconecte e seja necessario reconectar, o topico e assinado novamente
    client.subscribe('beacons')
    
# Funcao callback que trata a chegada de um beacon
def na_publicacao(cliente, dados, msg):
    json_data = json.loads(msg.payload.decode())
    receiver = json_data['id']
    raw_data = json_data['raw_beacons_data']
    beacon = raw_data[:12]
    rssi = int(raw_data[56:58], 16) - 255
    if (not beacon in tabela):
        tabela.update({beacon:{}})
        ultimoTempo.update({beacon:time.time()})  
    if (not receiver in tabela[beacon]):
        tabela[beacon].update({receiver:deque([], 20)})
    tabela[beacon][receiver].append(rssi)
    if (ultimoTempo[beacon] < time.time() - 3): # So escreve no BD a cada 3 s
       pos = calculaPosicao(beacon)
       escreveBD(pos, beacon)
       ultimoTempo[beacon] = time.time()
  
client = mqtt.Client()
client.on_connect = na_conexao
client.on_message = na_publicacao
client.username_pw_set('cap_iot_', 'iotiot256') 
client.connect('broker.shiftr.io', 1883, 60)
client.loop_forever()

