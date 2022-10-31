# Proxy Inverso + Load Balancer

ANDRÉS SALAZAR GALEANO, JULIÁN DAVID RAMÍREZ LOPERA

## Version Word:
https://docs.google.com/document/d/1_cjGigHmfxXuZReNlV2eocjbcbY9NfRiEBSyd8n_TGo/edit?usp=sharing

## Abstract
Los Proxy son intermediarios entre las máquinas cliente y los servidores que alojan las respuestas. Estos proveen un conjunto de funcionalidades y medios de seguridad que varían dependiendo de los casos de uso.

En la actualidad estos son muy usados, siendo un requerimiento casi que obligatorio a la hora de construir servicios web, aunque este no sea su único uso. 

Entre los más populares están NGINX, Apache, Traefik, entre otros.

## Introducción
En el documento se hablará de la creación de un Proxy Inverso que tiene elementos como balanceador de carga, logger y cache persistente.

En la primera sección del documento discutiremos del problema dado y nuestra propuesta de solución. Seguido de esto, ya hablando propiamente de la implementación, listaremos las tecnologías usadas y el paso a paso de la creación del Proxy y de sus partes. Por último, mostraremos el despliegue del proxy y una discusión del resultado final.

## Problema
Se busca implementar un Proxy Inverso, el cual contenga un balanceador de carga que reparta las peticiones a varios servidores. Este debe tener un caché con registros temporales para recuperarse en caso de algún fallo. Por último, todos los requests y sus respectivos responses deben ser registrados por un logger y sacados por salida estándar.

Las IP de los múltiples servidores deben poder ser leídos desde un archivo junto a otros parámetros. Es decir, el Proxy debe ser configurable desde un archivo externo donde se listen las variables de entorno.

## Solución
### Propuesta
Decidimos realizar una implementación del Proxy en el lenguaje Python, teniendo concurrencia a través de hilos. El caché es de tipo LRU, el cual cada cierto tiempo guarda en un archivo la lista enlazada que usa internamente para usar como persistencia. El load balancer escogido fue Round Robin, que simplemente devuelve la siguiente IP para usar como objetivo.

Para el despliegue vamos a usar una instancia de AWS EC2.

### Diagrama de despliegue
URL: https://lucid.app/lucidchart/88f5ddac-9081-4275-97e7-6cfd68fa03da/edit?view_items=MEf3n6U1fOu3&invitationId=inv_e09f92e6-5e27-4142-b6b3-a4fa06fdcb1f

![image](https://user-images.githubusercontent.com/65835577/198927341-71a5f60b-86c1-48da-af5a-d8904d66211e.png)


## Tecnologías usadas
-Python
-AWS EC2
-Librerías de Python: OS, Threading, …

## Implementación
### Request Handler
Se implementó una clase llamada request handler la cual está encargada de interceptar todas los requests que se dirijan al proxy, y procesarlos concurrentemente.

La concurrencia en este caso se logra utilizando la librería “threading” de python la cual permite realizar el procesamiento en diferentes hilos.

En cada hilo se ejecutan las siguientes acciones de manera sincrónica:

Se recibe la solicitud entrante proveniente del cliente: En este paso, se reciben bytes del cliente hasta encontrar dos saltos de línea. Una vez se encuentra el doble salto de línea, se interpretan los bytes recibidos para leer el header “Content-Length”. Este determinará el número de bytes que contiene el cuerpo del request, y cuando se puede dejar de recibir bytes.
Una vez se tiene el request entrante, este se envía al Cache para revisar si el response correspondiente está presente allí. En caso de estarlo, se envía la respuesta guardada. De lo contrario, se abre una conexión a uno de los servidores, y se envían los bytes.

Después de enviar el request a los servidores, se reciben bytes y se interpretan de manera similar a como se hizo con el cliente, y se envía de vuelta al cliente.

### Load Balancer
Implementamos Round Robin como balanceador. Ya teniendo cargadas las IP del archivo de configuración, se le pasa al LB una lista de estas y cada vez que es llamado, retorna la IP actual de la lista y mueve un puntero que tiene como atributo a la siguiente posición. 

Al no ser infinita la lista de IP, cuando se mueve desde la última posición, este pone el índice de nuevo como 0.

### Cache
El caché implementado es de tipo LRU, o sea que evacuamos los registros más antiguos cuando la memoria designada se llena, metemos registros nuevos que no estén en el caché ya y si ya está lo ponemos al frente de la lista.

El caché fue implementado con una lista doblemente enlazada y un mapa. Como la lista es una librería extra, la implementamos por nuestra cuenta.

[Definición de nodo para la lista enlazada][Guarda el request, response y tiempo de vida]

La lista en sí guarda una referencia a la cabeza, cola y tamaño de sí misma. Tiene un método Add() para añadir nuevos nodos al frente y uno Pop() para eliminar los de atrás. Para actualizar los archivos ya visitados en el caché también se implementó un método To_Front() que mueve un nodo al frente de la lista.

El caché propiamente guarda múltiples atributos. Tenemos las variables de ambiente que son pasadas a la hora de inicializarlo, como la ruta a la persistencia, el tamaño máximo, el delimitador y el TTL para los nodos .

En la parte propia del caché se crea un Lock de threads para crear lecturas y escrituras Thread-Safe. También se define un tamaño actual de tamaño 0, un mapa que guarda cuáles nodos y requests tenemos en memoria en el momento y la lista en sí.

Al final, el método “read_cache()” revisa si el archivo de la persistencia existe. En caso tal de que sea cierto, hacemos un parsing de la entrada, dividiendo por request, response y TTL de cada registro. Esto lo hacemos juntando las líneas del archivo y realizando múltiples splits por separadores al igual que por longitud, esto nos permite encontrar más rápidamente las partes de cada registro.

Además de esto, tenemos métodos para buscar registros, añadir nuevos, almacenar el caché y actualizar los tiempos de vida.

Para buscar, pasamos el request como llave de búsqueda y si este está en el mapa del caché significa que existe y devolvemos él response, refrescamos su TTL y lo movemos al frente del caché.

Si no existe, desde el archivo principal llamamos al método add(), el cual dado el request y response crea un nuevo nodo en la lista con estos datos, pero solo lo hace si la memoria tiene espacio para alojarlo. En caso de que no haya esta disponibilidad, evacuamos archivos hasta poder almacenar el nuevo registro.

Para almacenar el caché, iteramos desde la cabeza de la lista hasta el final de la misma. Para cada registro guardamos las longitudes del request, response y TTL en un formato tipo diccionario (Llave: Valor) y seguido a esto le pegamos los propiamente request, response y TTL.

En último lugar, tenemos la actualización del tiempo. Para este iteramos desde la cola de la lista (El registro más antiguo) y le quitamos a su TTL la diferencia del tiempo actual con la última vez que se accedió. En caso de que un registro tenga TTL igual o menor a 0, este  es evacuado aunque la memoria no este llena. Él cada cuanto lo actualizamos y el TTL se lee desde el config.

### Logging
Para esto basta con usar la librería Logger de Python y poner los registros que se quieran guardar.

No hay que manejar locks para este caso, ya que la librería es thread safe en sí.

## Despliegue

El despliegue de esta aplicación es bastante sencillo. Únicamente se requiere clona este repositorio en cualquier máquina virtual con el intérprete Python3 instalado.

Una vez instalado, basta con correr el comando python3 main.py en root del directorio del repositorio.

Este proxy permite personalizar configuraciones si se provee un archivo “proxy.conf” en el directorio root de la máquina donde se corre.

Las siguientes opciones están disponibles:

-port: puerto sobre el cual corre el proxy
-cache_size: tamaño máximo que puede tomar el cache en bytes
-targets: cadenas de ips junto con puertos sobre los que se interceptan requests.
-ttl: unidad de tiempo máximo que persiste un request en el Caché.
-unit_time: intervalos de tiempo para que se realicen actualizaciones al Caché persistente.
-connection_timeout: tiempo máximo que espera el servidor antes de cerrar una conexión.
-path_to_persistence: ruta en la que se guardará el cache.
-path_to_log: ruta en la que se guardará el log.

## Conclusiones
El caché involucra gran parte del éxito del proxy
El caché implementado en nuestro caso podría mejorar guardando la información como Bytes
Round Robin es un balanceador de carga que, aunque es fácil de implementar, también es muy eficiente.
Para la escritura y lectura concurrente se hace necesario conocer de Threads y Locks debido a la incertidumbre de operaciones tipo I/O no secuenciales.






