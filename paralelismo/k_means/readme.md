# K_means 

Dentro de esta carpeta se tienen varias implementaciones 

1. K means que solo funciona con 3 clusters y 2 caracteristicas en un cuaderno de jupiter, esto para mostrar iteracion por iteracion como los clusters se van moviendo

2. K means secuencial

3. K means paralelizado haciendo que un worker calcule las distancias de todos los puntos a un cluster en especifico, y que mueva el centroide de ese cluster (1 worker -> 1 cluster)

4. K means paralelizado donde cada worker calcula la distancia de un numero de datos determinado a todos los clusters, asigna cada punto a un cluster y suma los puntos que le llegaron (1 worker -> n data)

Se usa la arquitectura Ventilator - Worker - Sink, donde el ventilator recoge la operacion global y la parte, el sink une las operaciones de los workers y las envia otra vez al ventilator 

