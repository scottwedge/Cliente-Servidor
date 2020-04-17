# Normalizando 

Este folder es usado para normalizar datasets y no complicar el codigo
de k_means

## Para correrlo 



### Ventilator 
1. El nombre del dataset, debe estar en el folder padre en la carpeta datasets 
2. La direccion del ventilator para los workers 
4. La direccion del ventilator para el sink
5. La direccion del sink 
6. El numero de datos que tiene el dataset
7. Si el dataset tiene tags, se le pone -t para que no lea la ultima columna 

#### python Ventilator.py 4c2f.csv 127.0.0.1:5555 127.0.0.1:5556 127.0.0.1:5557 1000 [-t]

### Worker 
1. Direccion del ventilator 
2. Direccion del sink 

#### python worker.py 127.0.0.1:5555 127.0.0.1:5557

### Sink 
1. Direccion del sink 
2. DIreccion del ventilator 
#### python Sink.py 127.0.0.1:5557 127.0.0.1:5556
