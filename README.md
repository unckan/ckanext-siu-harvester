[![Build Status](https://travis-ci.org/avdata99/ckanext-siu-harvester.svg?branch=master)](https://travis-ci.org/avdata99/ckanext-siu-harvester)
[![Docker Pulls](https://img.shields.io/docker/pulls/avdata99/ckan-env.svg)](https://hub.docker.com/r/avdata99/ckan-env/tags)
[![Docker Automated](https://img.shields.io/docker/automated/avdata99/ckan-env.svg)](https://hub.docker.com/r/avdata99/ckan-env/tags)
[![](https://img.shields.io/pypi/implementation/ckanext-siu-harvester)](https://pypi.org/project/ckanext-siu-harvester/)
[![](https://img.shields.io/pypi/pyversions/ckanext-siu-harvester)](https://pypi.org/project/ckanext-siu-harvester/)
[![](https://img.shields.io/pypi/wheel/ckanext-siu-harvester)](https://pypi.org/project/ckanext-siu-harvester/)
[![](https://img.shields.io/pypi/:period/ckanext-siu-harvester)](https://pypi.org/project/ckanext-siu-harvester/)
[![](https://img.shields.io/pypi/format/ckanext-siu-harvester)](https://pypi.org/project/ckanext-siu-harvester/)
[![](https://img.shields.io/pypi/status/ckanext-siu-harvester)](https://pypi.org/project/ckanext-siu-harvester/)
[![](https://img.shields.io/pypi/l/ckanext-siu-harvester)](https://pypi.org/project/ckanext-siu-harvester/)
[![](https://img.shields.io/pypi/v/ckanext-siu-harvester)](https://pypi.org/project/ckanext-siu-harvester/)

# SIU Harvester
Esta extensión de CKAN permite cosechar (_harvest_) datos expuestos en sistemas [SIU](https://www.siu.edu.ar/).  
El **Sistema de Información Universitaria** es un [conjunto de aplicaciones](https://www.siu.edu.ar/como-obtengo-los-sistemas/) que permite de manera gratuita a las Universidades argentinas contar con las herramientas de software para su gestión integral.

Esta extensión de CKAN esta pensada para obtener estos datos y publicarlos en formatos reutilizables para darles mayor accesibilidad al público general.

## Portal de transparencia

SIU incluye un [portal de transparencia](http://documentacion.siu.edu.ar/wiki/SIU-Wichi/Version6.6.0/portal_transparencia) que incluye un API.  
Estos datos se toman de la base SIU-Wichi, que contiene datos provenientes de los módulos SIU-Pilaga (Presupuesto), SIU-Mapuche (RRHH), SIU-Diaguita (Compras y Patrimonio) y SIU-Araucano (Académicos).

### Consultas

Las consultas a la base de datose se definen en archivos CDA

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CDADescriptor>
   <DataSources>
      <Connection id="myconnection" type="sql.jndi">
         <Jndi>transparencia</Jndi>
      </Connection>
   </DataSources>

   <DataAccess 
       access="public" 
       cache="true" 
       cacheDuration="7200" 
       connection="myconnection" 
       id="IdParaUsarComDataAccessID" 
       type="sql">
      <Columns/>

      <Parameter name="prm_anio" type="Numeric" default="0"/>
      
      <Query>SELECT field_a, field_b, field_c 
                      FROM xtable
                      where field_a = ${anio}
      </Query>

   </DataAccess>
</CDADescriptor>
```

Este harvester lee los enpoints del API que expone cada archivo CDA.
Los archivos CDA incluidos en el Portal de Transparencia ya están cubiertos 
en este harvester. Esta listo para consumir y republicar datos.

Es posible tambien definir archivos CDA personalizados y 
[agregarlos al harvester](https://github.com/avdata99/ckanext-siu-harvester/issues/20)
para consumir estos datos de manera automtizada y periódicamente.

### Instalación

Disponible en [Pypi](https://pypi.org/project/ckanext-siu-harvester/) o vía GitHub.  

```
pip install ckanext-siu-harvester
ó
pip install -e git+https://github.com/avdata99/ckanext-siu-harvester.git#egg=ckanext-siu-harvester

+
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
La configuración mínima y bigatoria es solo el usuario y a contraseña del API del portal de 
transparencia al que este _harvester_ se va a conectar

```json
{
    "username": "user",
    "password": "password"    
}
```

### Datos a extraer

Estos endpoints pueden incluir multiples recursos. Cada recurso es un _query_ al endpoint ya listo para usar.  
Estos ya están configurados en el directorio `queries` de la librería [siu-data](https://pypi.org/project/siu-data/)

Por ejemplo `egresados-pos-facultad.json`

```
{
    "name": "evolucion-de-cargos-activos-por-escalafon",
    "title": "Evolución de cargos activos por escalafón",
    "notes": "",
    "internals": "Describir mejor",
    "iterables": {
        "sub_list": {
            "help": "Necesitamos primero obtener la lista de unidades académicas con otra consulta",
            "name": "lista-de-unidades-academicas",
            "params": {
                "paramprm_tablero_visible": "18",
                "dataAccessId": "param_ua_cargos",
                "sortBy": ""
            },
            "apply_to": "paramprm_ua_cargos"
        }
    },
    "tags": [
        "Cargos", "Personal"
    ],
    "params": {
        "paramprm_ua_cargos": "",
        "path": "/home/SIU-Wichi/Portal Transparencia/cda/4_rrhh.cda",
        "dataAccessId": "tablero_18",
        "outputIndexId": 1,
        "pageSize": 0,
        "pageStart": 0,
        "sortBy": "2D"
        }
}
```

De esta forma este _harvester_ va a iterar por los años disponibles y creará un dataset para cada año.  
Es posible agregar más _queries_ para consumir más datos.

## Configuraciones adicionales

### Limitar los archivos de _queries_ usadas

La [librería siu-data](https://github.com/avdata99/pySIUdata) a la que se conecta este _harvester_ incluye todos los 
[archivos de consulta disponibles](https://github.com/avdata99/pySIUdata/tree/master/siu_data/queries) 
(descriptos más abajo).  
De manera predeterminada todos los archivos se usarán pero es posible limitar los archivos 
usados en la configuracion con `only_files` de esta forma:  

```js
"only_files": [
    "1-PRESUPUESTO-tablero_01.json",
    "1-PRESUPUESTO-tablero_02.json"
    ]
```
Los archivos a usar se identifican con la propiedad `name` de cada archivo de consulta.

### Sobreescribir configuraciones

Los archivos de consulta permiten definir _tags_, _grupos_ y otros metadatos que cada dataset cosechado va a usar.  
Es tambien posible configurar cambios desde la configuracion del harvester.  
Ejemplo:  

```js
"override": {
    "1-PRESUPUESTO-tablero_01.json": {
        "notes": "Esta es una nueva descripcion para todos los datasets cosechados desde este archivo",
        "tags": ["nuevo_tag_01", "nuevo_tag_02"]
    },
    "1-PRESUPUESTO-tablero_02.json": {
        "tags": ["nuevo_tag_02", "nuevo_tag_03"],
        "groups": ["group_01", "group_02"]
    }
}
```

### Agregar extras a los datasets

Si se requiere que en cada cosecha (además de los tags, grupos, notas, etc) se agreguen más 
metadatos a los datasets cosechados 

```js
"override": {
    "4-RRHH-tablero_18.json": {

        "extras": {
            "my_custom_extra": "999",
            "dataset_preview": {
                "chart": {
                    "height": "250",
                    "chart_type": "Column",
                    "chart_color": "#30AA71",
                    "fields": "['Facultad', 'cantidad de empleados']", 
            
                }
            }
        },

        "notes": "Nueva descripcion",
        "tags": ["nuevo_tag_09", "nuevo_tag_12"]
    }
}
```

## Ejemplo configuracion final

```json
{
"username": "usuario",
"password": "clave",
"only_files": ["4-RRHH-tablero_18.json"],
"override": {
    "4-RRHH-tablero_18.json": {
        "extras": {
            "my_custom_extra": "999",
            "dataset_preview": {
                "chart": {
                    "height": "250",
                    "chart_type": "Column",
                    "chart_color": "#30AA71",
                    "fields": "['fuente_financiamiento' ,'total_devengado]", 
                    }
                }
            },
        "notes": "Nueva descripcion",
        "tags": ["nuevo_tag_09", "nuevo_tag_12"],
        "groups": ["group_01", "group_02"]
        }
    }
}
```
## Tests 

Locally

```
docker-compose exec ckan bash -c \
    "cd src_extensions/ckanext-siu-harvester && \
        nosetests --ckan --nologcapture --with-pylons=test.ini ckanext/siu_harvester/tests"
```
