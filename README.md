[![Build Status](https://travis-ci.org/avdata99/ckanext-siu-harvester.svg?branch=master)](https://travis-ci.org/avdata99/ckanext-siu-harvester)
# SIU Harvester
Esta extensión de CKAN permite cosechar (_harvest_) datos expuestos en sistemas [SIU](https://www.siu.edu.ar/).  
El **Sistema de Información Universitaria** es un [conjunto de aplicaciones](https://www.siu.edu.ar/como-obtengo-los-sistemas/) que permite de manera gratuita a las Universidades argentinas contar con las herramientas de software para su gestión integral.

Esta extensión de CKAN esta pensada para obtener estos datos y publicarlos en formatos reutilizables para darles mayor accesibilidad al público general.

## Portal de transparencia

SIU incluye un [portal de transparencia](http://documentacion.siu.edu.ar/wiki/SIU-Wichi/Version6.6.0/portal_transparencia) que incluye un API.  
Estos datos se toman de la base SIU-Wichi, que contiene datos provenientes de los módulos SIU-Pilaga (Presupuesto), SIU-Mapuche (RRHH), SIU-Diaguita (Compras y Patrimonio) y SIU-Araucano (Académicos).

### Instalacion

Disponible en [Pypi](https://pypi.org/project/ckanext-siu-harvester/) o vía GitHub.  

```
pip install ckanext-siu-harvester
or
pip install -e git+https://github.com/avdata99/ckanext-siu-harvester.git#egg=ckanext-siu-harvester

And
pip install -r https://raw.githubusercontent.com/avdata99/ckanext-siu-harvester/master/requirements.txt

```

### Agregar origen

La URL los _harvest sources_ de este tipo son de la forma:
```
http://wichi.siu.edu.ar/pentaho/plugin/cda/api/doQuery
```

Debe elegir la URL de la instancia de la que desea obtener datos

### Configuración

Para conectarse es requisito que para cada _harvest source_ definir una configuración.  
Ejemplo:

```json
{
    "username": "user",
    "password": "password"    
}
```

### Datos a extraer

Estos endpoints pueden incluir multiples recursos. Cada recurso es un _query_ al endpoint ya listo para usar.  
Estos ya están configurados en el directorio `ckanext/siu_harvester/harvesters/siu_transp_data/queries/`

Por ejemplo `egresados-pos-facultad.json`

```
{
    "name": "distribucion-de-egresados-por-facultad",
    "title": "Distribución de egresados por facultad",
    "notes": "Esta es la cantidad de egresados por facultad de este año",
    "iterables": {
        "anio_param": "paramprm_ej_presup"
    },
    "tags": [
        "Egresados"
    ],
    "params": {
        "paramprm_ej_academ": 2020,
        "path": "/home/SIU-Wichi/Portal Transparencia/cda/5_academica.cda",
        "dataAccessId": "tablero_26",
        "outputIndexId": 1,
        "pageSize": 0,
        "pageStart": 0,
        "sortBy": "2D",
        "paramsearchBox": null}
 }
```

De esta forma este _harvester_ va a iterar por los años disponibles y creará un dataset para cada año.  
Es posible agregar más _queries_ para consumir más datos.

