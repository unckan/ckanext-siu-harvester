# SIU Harvester
Esta extensión de CKAN permite cosechar (_harvest_) datos expuestos en sistemas [SIU](https://www.siu.edu.ar/).  
El **Sistema de Información Universitaria** es un [conjunto de aplicaciones](https://www.siu.edu.ar/como-obtengo-los-sistemas/) que permite de manera gratuita a las Universidades argentinas contar con las herramientas de software para su gestión integral.

Esta extensión de CKAN esta pensada para obtener estos datos y publicarlos en formatos reutilizables para darles mayor accesibilidad al público general.

## Portal de transparencia

SIU incluye un [portal de transparencia](http://documentacion.siu.edu.ar/wiki/SIU-Wichi/Version6.6.0/portal_transparencia) que incluye un API.  
Estos datos se toman de la base SIU-Wichi, que contiene datos provenientes de los módulos SIU-Pilaga (Presupuesto), SIU-Mapuche (RRHH), SIU-Diaguita (Compras y Patrimonio) y SIU-Araucano (Académicos).

### Instalacion

```
pip install ckanext-siu-harvester
```

### Configuración

Para conectarse es requisito que para cada _harvest source_ definir una configuración.  
Ejemplo:

```json
{
    "username": "user",
    "password": "password"    
}
```