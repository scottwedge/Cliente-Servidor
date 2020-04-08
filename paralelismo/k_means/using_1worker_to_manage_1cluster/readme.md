# Para correrlo 

## Ventilator
1. Direccion del ventilator para los workers
2. Direccion del ventilator para el sink
3. Direccion del sink
4. Numero de clusters
5. Numero de caracteristicas

### python ventilator.py 127.0.0.1:5555 127.0.0.1:5556 127.0.0.1:5557 3 2

## Sink 
1. Direccion del sink
2. Direccion correspondiente del ventilator

### python sink.py 127.0.0.1:5557 127.0.0.1:5556

## Worker 

1. Direccion correspondiente del ventilator
2. Direccion del sink 

### python worker.py 127.0.0.1:5555 127.0.0.1:5557
