# Analisis de Queries pendientes

Estas consultas no están cargadas al sistema todavía

## En el código

Se peude ver esta lista

```
// RR. HH.
'16': 'Distribución de cargos activos por escalafón',
'17': 'Distribución de cargos activos por dependencia',
'18': 'Evolución de cargos activos por escalafón',
'19': 'Evolución de cargos activos por dependencia',
'20': 'Evolución de cargos activos por género',
// ACADEMICA
'21': 'Evolución de alumnos por año',
'211': 'Distribución de alumnos por facultad',
'22': 'Distribución de alumnos por carrera en el año',
'23': 'Evolución de ingresantes por año',
'24': 'Distribución de nuevos ingresantes por facultad',
'241': 'Distribución de nuevos ingresantes por carrera',
'25': 'Evolución de egresados por año',
'26': 'Distribución de egresados por facultad',
'261': 'Distribución de egresados por carrera' 
```

## Configuracion

Fecha de actualziacion (asumimos que es la del portal)
 - path: /home/SIU-Wichi/Portal Transparencia/cda/0_configuracion.cda
   - dataAccessId: fecha_actualizacion
   - {"queryInfo":{"totalRows":"1"},"resultset":[["19/07/2019"]],"metadata":[{"colIndex":0,"colType":"String","colName":"fecha"}]}
        "outputIndexId": 1,
        "pageSize": 0,
        "pageStart": 0,
        "sortBy": "" 

# Pendienes


path                dataAccessId        extra param                 Obs                 
0_configuracion.cda fecha_actualizacion                             Fecha actualizacion 
1_presupuesto.cda   param_anios_presup  paramprm_tablero_visible:1  Lista de años con presupuesto

Lista de los niveles académicos disponibles
  {"queryInfo":{"totalRows":"4"},"resultset":[["1-TODOS"],["Grado"],["Posgrado"],["Pregrado"]],"metadata":[{"colIndex":0,"colType":"String","colName":"?column?"}]}

  path: /home/SIU-Wichi/Portal Transparencia/cda/5_academica.cda
  dataAccessId: param_nivel_academ
  paramprm_tablero_visible: 211


### Años disponibles con presupuestos

 - paramprm_tablero_visible: 1
   - path: /home/SIU-Wichi/Portal Transparencia/cda/1_presupuesto.cda
      dataAccessId: param_anios_presup
      {"queryInfo":{"totalRows":"15"},"resultset":[[2016],[2015],[2014],[2013],[2012],[2011],[2010],[2009],[2008],[2007],[2006],[2005],[2004],[2003],[2002]],"metadata":[{"colIndex":0,"colType":"Integer","colName":"anio"}]}
      outputIndexId: 1 pageSize: 0 pageStart: 0 sortBy: paramsearchBox: 


## Academico

  {"queryInfo":{"totalRows":"11"},"resultset":[["HUMANISTICAS",9051,22.89],["ADMINISTRACION Y ECONOMIA",6552,16.57],["EXACTAS Y NATURALES",5802,14.67],["VETERINARIAS Y SALUD ANIMAL",5184,13.11],["INGENIERIA",3087,7.81],["DERECHO Y SOCIALES",2622,6.63],["AGRARIAS Y FORESTALES",2208,5.58],["PERIODISMO",1791,4.53],["CINE Y TV",1737,4.39],["MEDICINA",1401,3.54],["INSTITUTO DE INVESTIGACION",114,0.29]],"metadata":[{"colIndex":0,"colType":"String","colName":"dependencia"},{"colIndex":1,"colType":"Numeric","colName":"total_alumnos"},{"colIndex":2,"colType":"Numeric","colName":"porcentaje"}]}

  paramprm_ej_academ: 2016
  paramprm_nivel_academ: 1-TODOS
  path: /home/SIU-Wichi/Portal Transparencia/cda/5_academica.cda
  dataAccessId: tablero_211
  outputIndexId: 1
  pageSize: 0
  pageStart: 0
  sortBy: 2D


  Lista de los niveles académicos disponibles
  {"queryInfo":{"totalRows":"4"},"resultset":[["1-TODOS"],["Grado"],["Posgrado"],["Pregrado"]],"metadata":[{"colIndex":0,"colType":"String","colName":"?column?"}]}

  path: /home/SIU-Wichi/Portal Transparencia/cda/5_academica.cda
  dataAccessId: param_nivel_academ
  paramprm_tablero_visible: 211
  outputIndexId: 1
  pageSize: 0
  pageStart: 0
  sortBy: 
  paramsearchBox: 