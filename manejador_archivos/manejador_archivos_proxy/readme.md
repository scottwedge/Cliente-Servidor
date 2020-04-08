# Manejador de archivos con un proxy 

## Implementacion: 

Manejador de archivos distribuidos con un servidor que hace el balanceo de carga para otros servidores que seran de almacenamiento. 

Cuando un cliente quiere subir un archivo, el proxy enviara una lista de direcciones que seran los servidores de almacenamiento a los que debe subir cada oarte del archivo. 

Para descargarlo, como el proxy almacena la metadata y sabe donde estan las partes de cada archivo, este le envia una lista de direcciones que son los servidores que tienen cada parte del archivo. 

EL cliente se conecta ya sea oara subir o bajar los archivos de los servidores de almacenamiento. 

Se balancea la carga de almacenamiento y de peticiones, ya que a los servidores de almacenamiento no les llegara peticiones de archivos que no contienen 

### Para correrlo 

#### python server_proxy.py 

* Ip del servidor de almacenamiento
* Puerto del server
* Folder donde guardara los archivos(debe existir)
#### python server.py 127.0.0.1 5556 s1


* Acciones a realizar: upload, download, o list
* -f si va a descargar o cargar
* Nombre del archivo a subir o bajar
#### python client.py [action] -f [fileName]
