

import time
import zmq


def operar(operacion):
    op1 = int(operacion[0])
    op2 = int(operacion[1])
    operador = operacion[2]

    if operador == "+":
        return op1 + op2
    elif operador == "-":
        return op1 - op2
    elif operador == "*":
        return op1 * op2
    elif operador == "/":
        return op1 / op2
    elif operador == "^":
        return op1 ** op2

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
operacion = []
while True:
    
    #  Wait for next request from client
    message = socket.recv_string()
    operacion.append(message)
    print("Received request: %s" % message)

    #  Send reply back to client
    if len(operacion) < 3:
        socket.send_string("Ok" +  str(len(operacion)))
    else:
        result = str(operar(operacion))
        socket.send_string(result)
        operacion = []