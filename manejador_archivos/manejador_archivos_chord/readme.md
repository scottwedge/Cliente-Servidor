# Chord 

## Explicacion:
Se implementa un almacenamiento de archivos distribuido, donde un archivo es dividido en muchas partes, a las cuales se les saca un hash, con esta lista de hashes, el hash gobal y el nombre del archivo se crea un archivo .json de metadata.

El archivo con metadata y las partes del archivo se ingresan en el anillo donde existen muchos servidores responsables de un rango de llaves, este rango de llaves es sacado ya que cada nodo esta identificado con un hash, que se extrajo al concatenar la direccion MAC con una cadena de 40 caracteres aleatirios.

El rango de llaves de cada servidor es (llave de otro servidor, llave propia]. Tambien, un servidor tendra el rango de tipo
(llave de otro servidor, maximo de llaves] U [0, llave propia]

Para buscar un archivo, un cliente se conecta a un servidor del anillo y le pregunta si es responsable de la llave que esta buscando, si lo es le envia el archivo, si no lo es, le envia la direccion del sucesor para que continue su busqueda. 

La operacion anterior es igual para cuando un servidor se conecta al anillo, este se conecta a un nodo del anillo y le pregunta si es responsable por la llave que el tiene, si si es responsable, este nodo se volvera su sucesor, el cual cambia su rango de llaves y le envia los archivos que ya no son responsabilidad de el, tambien arregla su antecesor y envia su antiguo antecesor para configurarlo en el nuevo nodo.

Cuando un nodo se desconecta, le envia todos los archivos a su sucesor y le da el antecesor para que lo cambie.

Para descargarlo no sera con el nombre del archivo, sino que sera con el hash del archivo de metadata para asi tener un manejo de archivos anonimo. 

## Para correrlo 

### Cliente:

* El servidor del anillo al que se conectara
* La acción: upload download
* -f 
* El nombre del archivo que quiere subir o el hash si va a bajar
#### python client.py 127.0.0.1:5555 [action] -f [fileName | hash]

### Servidor 

Cabe recalcar que hay dos tipos de servidores, el inicial, que este no preguntara a nadie su responsabilidad por el anillo porque no existe, entonces este crea el anillo. Y el servidor que se va a conectar a un anillo ya existente
* La ip
* El puerto
* El nombre de la carpeta donde va a guardar los archivos (debe existir)
#### python initialServer.py 127.0.0.1 5555 s1


* La ip
* El puerto
* El nombre de la carpeta donde va a guardar los archivos (debe existir)
* La direccion del servidor que ya esta en el anillo por el cual va a entrar 
#### python initialServer.py 127.0.0.1 5556 s1 127.0.0.1:5555
