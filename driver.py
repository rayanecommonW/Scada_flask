#! python3

###########
# IMPORTS #
###########

from pyModbusTCP.client import ModbusClient
from time import sleep

#############
# VARIABLES #
#############

slaveAddress='172.23.224.1'
slavePort=502
arrCount={"b":0,"g":0,"m":0}
arrSleep={"b":2,"g":3,"m":6}

# Input - Reg

sensor=0x0

# Output - Coils

entry_convoyer=0
exit_convoyer=1

arrBelt={"b":2,"g":4,"m":6}
arrTurn={"b":3,"g":5,"m":7}

emitter=8

# Output - Reg

arrCounter={"b":0,"g":1,"m":2}

########
# CODE #
########

client = ModbusClient(slaveAddress,port=slavePort,unit_id=1)
client.open()

if client.is_open:
	print("OK")
else:
	print("KO")

def factoryRun(status):
	client.write_single_coil(entry_convoyer,status)
	client.write_single_coil(emitter,status)

def colorFound(color):
	sleep(0.8)
	factoryRun(0)
	arrCount[color]+=1
	client.write_single_register(arrCounter[color],arrCount[color])
	client.write_single_coil(arrTurn[color],1)
	client.write_single_coil(arrBelt[color],1)
	sleep(arrSleep[color])
	client.write_single_coil(arrTurn[color],0)
	client.write_single_coil(arrBelt[color],0)
	factoryRun(1)
	
client.write_single_coil(exit_convoyer,1)
factoryRun(1)

while 1:
	if client.read_input_registers(sensor)[0] in range(1,4):
		colorFound("b")

	if client.read_input_registers(sensor)[0] in range(4,7):
		colorFound("g")

	if client.read_input_registers(sensor)[0] in range(7,10):
		colorFound("m")

client.close()
