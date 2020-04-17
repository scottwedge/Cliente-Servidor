# Para correrlo 

## Ventilator
1. Direccion del ventilator para los workers
2. Direccion del ventilator para el sink
3. Direccion del sink
4. Nombre del dataset (debe estar en la carpeta datasets)
6. Numero de clusters 
5. Opcional: Si el dataset lleva tags se pone -t
### python ventilator.py 127.0.0.1:5555 127.0.0.1:5556 127.0.0.1:5557 hola.csv  4 [-t] [euclidean|angular]

## Sink 
1. Direccion del sink
2. Direccion correspondiente del ventilator

### python sink.py 127.0.0.1:5557 127.0.0.1:5556

## Worker 

1. Direccion correspondiente del ventilator
2. Direccion del sink 

### python worker.py 127.0.0.1:5555 127.0.0.1:5557


## Si se desea crear un dataset 

1. Nombre del archivo que se generara en datasets 
2. Número de clusters 
3. Número de caracteristicas 
4. Número de muestras
### python createBlobs.py nombre.csv 3 2 1000

# Elbow method 

Este metodo se usa para calcular el k óptimo, lo que hace es sumar la distorsión 
de todos los puntos con respecto a su cluster 

## Para correrlo 

Cabe recalcar que:
* Debe estar corriendo el kmeans paralelizado normal con sus workers y sink
* En cada iteracion, cuando se cambia el numero de clsters, el sink normal debe reiniciarse 

### Ventilator elbow
1. Direccion del ventilator para los workers
2. Direccion del ventilator para el sink
3. Direccion del sink
4. Nombre del dataset (debe estar en la carpeta datasets)
6. Número de clusters mínimo
8. Número de clusters máximo
5. Opcional: Si el dataset lleva tags se pone -t
#### python ventilator_elbow.py 127.0.0.1:6565 127.0.0.1:6566 127.0.0.1:6567 hola.csv  2 6 [-t] [euclidean|angular]

### Sink  elbow
1. Direccion del sink
2. Direccion correspondiente del ventilator

#### python sink_elbow.py 127.0.0.1:6567 127.0.0.1:6566

### Worker elbow

1. Direccion correspondiente del ventilator
2. Direccion del sink 

#### python worker_elbow.py 127.0.0.1:6565 127.0.0.1:6567