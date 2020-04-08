

#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

import zmq

context = zmq.Context() #Se crea el contexto

#  Socket to talk to server
print("Connecting to hello world server")
socket = context.socket(zmq.REQ) #Con el contexto, creamos un socket de tipo REQUEST
socket.connect("tcp://localhost:5555") #Nos conectamos al servidor, el cual
                                       #En este caso tiene de IP 127.0.0.1 y 
                                       #puerto 5555

#  Do 10 requests, waiting each time for a response
for request in range(10): #Enviaremos 10 request al servidor
    print("Sending request %s " % request)
    msg = input()
    socket.send(msg.encode("utf-8")) 

    #  Get the reply.
    message = socket.recv() #Por el mismo socket que enviamos, recibimos el mensaje del servidor
    message = message.decode("utf-8")
    print(f"Received reply: {message}") #Mostramos el mensaje
