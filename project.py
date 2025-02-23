from flask import Flask, render_template, request, jsonify
from threading import Thread
from time import sleep
from pyModbusTCP.client import ModbusClient

app = Flask(__name__)

# Modbus Connection
slaveAddress = '172.30.128.1'
slavePort = 502
client = ModbusClient(slaveAddress, port=slavePort, unit_id=1)
client.open()

# Registers and Coils
sensor = 0
entry_convoyer = 0
exit_convoyer = 1
emitter = 8
arrCounter = {"b": 0, "g": 1, "m": 2}
arrBelt = {"b": 2, "g": 4, "m": 6}
arrTurn = {"b": 3, "g": 5, "m": 7}
arrSleep = {"b": 2, "g": 3, "m": 6}

arrCount = {"b": 0, "g": 0, "m": 0}

running = False  # Global flag to control the machine thread

def factoryRun(status):
    """Control main factory conveyor and emitter"""
    client.write_single_coil(entry_convoyer, status)
    client.write_single_coil(emitter, status)

def colorFound(color):
    """Process detected colors"""
    sleep(0.8)
    factoryRun(0)  # Stop machine while processing
    arrCount[color] += 1
    client.write_single_register(arrCounter[color], arrCount[color])
    client.write_single_coil(arrTurn[color], 1)
    client.write_single_coil(arrBelt[color], 1)
    sleep(arrSleep[color])
    client.write_single_coil(arrTurn[color], 0)
    client.write_single_coil(arrBelt[color], 0)
    factoryRun(1)  # Restart machine

def colorPush(color):
    arrCount[color] += 1
    client.write_single_register(arrCounter[color], arrCount[color])
    result = client.read_coils(arrBelt[color], 1)
    
    if result and result[0] == 1:
        client.write_single_coil(arrTurn[color], 0)
        client.write_single_coil(arrBelt[color], 0)
    else :
        client.write_single_coil(arrTurn[color], 1)
        client.write_single_coil(arrBelt[color], 1)


def machine_loop():
    """Continuously check sensors while running"""
    global running
    print("Machine Loop Started!")
    client.write_single_coil(exit_convoyer, 1)
    factoryRun(1)

    while running:
        sensor_value = client.read_input_registers(sensor, 1)[0]

        if sensor_value in range(1, 4):
            colorFound("b")
        elif sensor_value in range(4, 7):
            colorFound("g")
        elif sensor_value in range(7, 10):
            colorFound("m")

        sleep(0.5)  # Prevent CPU overload

@app.route('/')
def home():
    """Render web page"""
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start_machine():
    """Start the factory process"""
    global running
    if not running:
        running = True
        t = Thread(target=machine_loop, daemon=True)
        t.start()
        print("Machine Started!")  
        return jsonify({'status': 'Machine Started'})
    return jsonify({'status': 'Already Running'})

@app.route('/stop', methods=['POST'])
def stop_machine():
    """Stop the factory process"""
    global running
    running = False
    
    print("before stoping the convey")
    factoryRun(0)  # Stop the conveyor
    print("after stoping the convey")
    return jsonify({'status': 'Machine Stopped'})
    

@app.route('/convey1', methods=['POST'])
def convey1():
    
    result = client.read_coils(entry_convoyer, 1)
    if result and result[0] == 0:
        client.write_single_coil(entry_convoyer, 1)
        return
    else:
        client.write_single_coil(entry_convoyer, 0)
    return 
    

@app.route('/convey2', methods=['POST'])
def convey2():
    
    result = client.read_coils(exit_convoyer, 1)
    
    if result and result[0] == 0:
        client.write_single_coil(exit_convoyer, 1)
        return 
    else:
        client.write_single_coil(exit_convoyer, 0)
    return

@app.route('/blue', methods=['POST'])
def bluesorter():
    colorPush("b")
    return

@app.route('/green', methods=['POST'])
def greensorter():
    colorPush("g")
    return
    
@app.route('/metal', methods=['POST'])
def metalsorter():
    colorPush("m")
    return
    
    
if __name__ == '__main__':
    app.run(debug=True)
