# Analisis de Queries pendientes

Estas consultas no están cargadas al sistema todavía

## En el código

Se peude ver esta lista

```
// PRESUPUESTO
'1': 'Gastos por fuentes de financiamiento',
'2': 'Evolución del crédito por ejercicio y fuente de financiamiento',
'3': 'Evolución del gasto por ejercicio',
'4': 'Distribución de gasto por dependencia',
'5': 'Distribución de gasto por inciso',
// COMPRAS
'6': 'Evolución del total comprado por ejercicio',
'7': 'Total comprado por dependencia',
'8': 'Top 10 de proveedores adjudicados por monto',
'9': 'Top 1 de proveedores adjudicados por rubro',
'10': 'Total de compras por rubro',
// PATRIMONIO
'11': 'Altas patrimoniales por dependencia',
'12': 'Valuación patrimonial por dependencia',
'13': 'Evolución de valuación patrimonial',
'14': 'Altas patrimoniales por partida parcial',
'15': 'Valuación patrimonial por partida parcial',
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

## Presupuesto

### Años disponibles con presupuestos

 - paramprm_tablero_visible: 1
   - path: /home/SIU-Wichi/Portal Transparencia/cda/1_presupuesto.cda
      dataAccessId: param_anios_presup
      {"queryInfo":{"totalRows":"15"},"resultset":[[2016],[2015],[2014],[2013],[2012],[2011],[2010],[2009],[2008],[2007],[2006],[2005],[2004],[2003],[2002]],"metadata":[{"colIndex":0,"colType":"Integer","colName":"anio"}]}
      outputIndexId: 1 pageSize: 0 pageStart: 0 sortBy: paramsearchBox: 

### Gastos por fuente de financiamiento

 - path: /home/SIU-Wichi/Portal Transparencia/cda/1_presupuesto.cda
   - dataAccessId: tablero_01
   - {"queryInfo":{"totalRows":"3"},"resultset":[["TESORO NACIONAL",1043455131.19,90.44],["REMANENTES EJERCICIOS ANTERIORES",40559927.01,3.52],["RECURSOS PROPIOS",69762037.29,6.05]],"metadata":[{"colIndex":0,"colType":"String","colName":"fuente_financiamiento"},{"colIndex":1,"colType":"Numeric","colName":"total_devengado"},{"colIndex":2,"colType":"Numeric","colName":"porcentaje"}]}
    paramprm_ej_presup: 2015 outputIndexId: 1 pageSize: 0 pageStart: 0 sortBy:  paramsearchBox: 

### Evolución del crédito por ejercicio y fuente de financiamiento 

 - path: /home/SIU-Wichi/Portal Transparencia/cda/1_presupuesto.cda
   - dataAccessId: tablero_02
   {"queryInfo":{"totalRows":"44"},"resultset":[["CREDITO EXTERNO",2007,117200.48],["RECURSOS CON AFECTACION ESPECIFICA",2007,52224.76],["RECURSOS PROPIOS",2007,15095069.9],["REMANENTES EJERCICIOS ANTERIORES",2007,16177660.12],["TESORO NACIONAL",2007,112759703.69],["CREDITO EXTERNO",2008,0],["RECURSOS CON AFECTACION ESPECIFICA",2008,30684.78],["RECURSOS PROPIOS",2008,22815250.32],["REMANENTES EJERCICIOS ANTERIORES",2008,15374251.76],["TESORO NACIONAL",2008,149648017.52],["TRANSFERENCIAS INTERNAS",2008,1601260.16],["CREDITO EXTERNO",2009,0],["RECURSOS CON AFECTACION ESPECIFICA",2009,31707.18],["RECURSOS PROPIOS",2009,21951297.96],["REMANENTES EJERCICIOS ANTERIORES",2009,11956074.26],["TESORO NACIONAL",2009,222269914.84],["TRANSFERENCIAS INTERNAS",2009,1162214.04],["CREDITO EXTERNO",2010,2108043.96],["RECURSOS CON AFECTACION ESPECIFICA",2010,33050.5],["RECURSOS PROPIOS",2010,18017042.83],["REMANENTES EJERCICIOS ANTERIORES",2010,19362072.61],["TESORO NACIONAL",2010,285338702.99],["TRANSFERENCIAS INTERNAS",2010,1998521.08],["CREDITO EXTERNO",2011,0],["RECURSOS PROPIOS",2011,25935320.19],["REMANENTES EJERCICIOS ANTERIORES",2011,29782639.74],["TESORO NACIONAL",2011,369320011.59],["CREDITO INTERNO",2012,0],["RECURSOS PROPIOS",2012,24716020.2],["REMANENTES EJERCICIOS ANTERIORES",2012,41698336.43],["TESORO NACIONAL",2012,473935587.99],["RECURSOS PROPIOS",2013,57845317.63],["REMANENTES EJERCICIOS ANTERIORES",2013,41546910.67],["TESORO NACIONAL",2013,579172125.5],["RECURSOS CON AFECTACION ESPECIFICA",2014,0],["RECURSOS PROPIOS",2014,89941191.3],["REMANENTES EJERCICIOS ANTERIORES",2014,40930987.15],["TESORO NACIONAL",2014,803743629.97],["RECURSOS PROPIOS",2015,116499070.11],["REMANENTES EJERCICIOS ANTERIORES",2015,70124683.43],["TESORO NACIONAL",2015,1109806252.18],["RECURSOS PROPIOS",2016,75249188.64],["REMANENTES EJERCICIOS ANTERIORES",2016,160352177.77],["TESORO NACIONAL",2016,1130203551.6]],"metadata":[{"colIndex":0,"colType":"String","colName":"fuente_financiamiento"},{"colIndex":1,"colType":"Integer","colName":"ejercicio"},{"colIndex":2,"colType":"Numeric","colName":"total_credito"}]}
outputIndexId: 1 pageSize: 0 pageStart: 0 sortBy: 

### Evolución del gasto por ejercicio

 - path: /home/SIU-Wichi/Portal Transparencia/cda/1_presupuesto.cda
   - dataAccessId: tablero_03
   {"queryInfo":{"totalRows":"10"},"resultset":[[2007,132828584.45],[2008,180289722.13],[2009,246560712.38],[2010,310743362.95],[2011,383339637.82],[2012,498111387.32],[2013,636040887.28],[2014,856467715.19],[2015,1153777095.49],[2016,407067182.64]],"metadata":[{"colIndex":0,"colType":"Integer","colName":"ejercicio"},{"colIndex":1,"colType":"Numeric","colName":"total_devengado"}]}
outputIndexId: 1 pageSize: 0 pageStart: 0 sortBy: 

### Distribución de gasto por dependencia 

 - path: /home/SIU-Wichi/Portal Transparencia/cda/1_presupuesto.cda
   - paramprm_ej_presup: 2016
   - dataAccessId: tablero_04
outputIndexId: 1 pageSize: 0 pageStart: 0 sortBy: 2D

"queryInfo":{"totalRows":"12"},"resultset":[["RECTORADO",157494120.05,38.69],["EXACTAS Y NATURALES",36363000.16,8.93],["VETERINARIAS Y SALUD ANIMAL",36176162.24,8.89],["HUMANISTICAS",35849340.58,8.81],["INGENIERIA",32738158.37,8.04],["ADMINISTRACION Y ECONOMIA",27851765.6,6.84],["AGRARIAS Y FORESTALES",25515479.55,6.27],["PERIODISMO",16728428.52,4.11],["CINE Y TV",16071479.8,3.95],["MEDICINA",12325299.99,3.03],["DERECHO Y SOCIALES",9232234.93,2.27],["INSTITUTO DE INVESTIGACION",721712.85,0.18]],"metadata":[{"colIndex":0,"colType":"String","colName":"dependencia"},{"colIndex":1,"colType":"Numeric","colName":"total_devengado"},{"colIndex":2,"colType":"Numeric","colName":"porcentaje"}]}


