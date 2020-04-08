# Manejador de archivos cliente servidor normal 

Se tiene un cliente que le envia archivos a un solo servidor, el archivo es enviado por partes para no sobrecargar la RAM o la red. 

El servidor guarda la informacion de los archivos en dos json, uno para mapear del nombre al hash global y el otro para mapear del hash global a la lista de hashes. 
Para correrlo


* La accion que realizara: upload, download o list
* -f si la accion es upload o download 
* El nombre del archivo que se quiere subir o bajar, el archivo si se descarga se guardara en la carpeta archivosDescargados y si se va a subir debe estar en la capeta archivos
### python client.py [action] -f [fileName]

### python server.py