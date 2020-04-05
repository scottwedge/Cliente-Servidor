"""
    Primera implementacion de sockets usando zeroMQ
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
"""

import time
import zmq

def extraer_valores(message):
    #oper = ""
    number = ""
    numbers = []
    opers = []
    for letter in message:
        
        if letter in ['+', '-', '*', '/', '^']:
            if number == "":
                if (letter == '+' or letter == '-'):
                    number += letter
            else:
                opers.append(letter)
                numbers.append(int(number))
                number = ""
        else:
            number += letter
    if number != "":
        numbers.append(int(number))
    return numbers, opers

def realizarOperacion(numbers, opers, oper):
    while oper in opers:
        index = opers.index(oper)
        opers.remove(oper)
        if oper == '^':
            numbers[index] = numbers[index] ** numbers[index+1]
        elif oper == '*':
            numbers[index] = numbers[index] * numbers[index+1]
        else:
            numbers[index] = numbers[index] / numbers[index+1]
        
        numbers.pop(index+1)
    return (numbers, opers)

def operar(numbers, opers):
    """
    En esta funcion se realizan las operaciones de la expresion, 
    primero se operan potencias, luego multiplicaciones y por ultimo
    divisiones, sumas y srestas, para realizar las operaciones de potencia, 
    division y multiplicacion, se usa la funcion realizar operacion
    """
    if len(numbers) - 1 != len(opers):
        return "Error"
    numbers, opers = realizarOperacion(numbers, opers, '^')
    numbers, opers = realizarOperacion(numbers, opers, '*')
    numbers, opers = realizarOperacion(numbers, opers, '/')

    i = 0
    while i < len(opers):
        oper = opers[i]
        opers.pop(i)
        if oper == '+':
            numbers[i] = numbers[i] + numbers[i+1]
        else:
            numbers[i] = numbers[i] - numbers[i+1]
        numbers.pop(i+1)
    return numbers[0]
 

context = zmq.Context()  #Para crear un socket se necesita un contexto 
socket = context.socket(zmq.REP) #Con el contexto, creamos el socket
                                 # que es de tipo REPLY 
socket.bind("tcp://*:5555") #Enlazamos el socket a un interfaz de red 
                            #en este caso es * (La que tiene por defecto el SO)
                            #y a un puerto, en este caso es 5555

while True: #Como es el servidor, para que siempre este a la escucha de un cliente
            #ponemos el 'while True'


    #  Wait for next request from client
    message = socket.recv() #Retorna el mensaje que recibio de algun cliente, 
                            # este proceso es SINCRONO, quiere decir que se 
                            #bloquea ahi hasta que le llegue algun mensaje

    message = message.decode("utf-8")
   
    numbers, opers = extraer_valores(message)
    print(numbers, opers)
    result = operar(numbers, opers)

    print("Received request: %s" % message) #Muestra el mensaje

    #  Do some 'work'
    time.sleep(1) #Para efectos practicos, lo realentizamos un segundo

    #  Send reply back to client
    result = str(result)
    socket.send(result.encode("utf-8")) #Por el mismo socket que recibio, puede enviarle 
                          #una respuesta al cliente, le enviamos la representacion
                          # de 'World' en forma de byte 
    
    #socket.send(b"Hola")