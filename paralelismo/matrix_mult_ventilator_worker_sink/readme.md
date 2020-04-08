# Multiplicacion de matrices de forma paralela

Esta es la primera aproximacion a la arquitectura de ventilator-worker-sink 

Para esta implementacion, se tuvieron dos enfoques
1. A cada worker se le envia una fila de A y una columna de B 
2. A cada worker se le envia una fila de A y toda la matriz B 

## Para correrlo 

* Direccion del sink

#### python sink.py 127.0.0.1:5556


* Direccion del ventilator
* Direccion del sink 
* Nombre del json que contiene las dos matrices a multiplicar, debe estar en la carpeta arrays
* Tipo de enfoque 
#### python main.py 127.0.0.1:5555 127.0.0.1:5556 ej1.json [raw-matrix | raw-col]

* Direccion del ventilator 
* Direccion del sink 

#### python worker.py 127.0.0.1:5555 127.0.0.1:5556