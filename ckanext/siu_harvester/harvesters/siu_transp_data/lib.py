# -*- coding: utf-8 -*-
import csv
import json
import logging
import os
import requests


logger = logging.getLogger(__name__)


class SIUTranspQueryFile:
    """ Cada uno de los archivos para consultar al portal de transparencia """

    def __init__(self, harvest_source, path, params={}):
        """ inicializar un archivo de consulta al portal de transparencia
            Params:
                harvest_source (SIUTransparenciaHarvester): Origen que llama a esta consulta
                path (str): Path al archivo de consulta
                params (dict): Parámetros de la consulta, se consiguen en 
                    general en la funcion open pero podrían inicializarse aquí
                """
        self.harvest_source = harvest_source
        real_path = os.path.join(harvest_source.queries_path, path)
        self.path = real_path
        self.params = params
        self.errors = []
        self.datasets = []  # resultados de todos (puede haber más de uno si hay iterables) los requests hacia el origen
    
    def open(self):
        """ Abrir el archivo y cargar sus parámetros """
        logger.info('Opening Query File {}'.format(self.path))
        try:
            f = open(self.path, 'r')
        except Exception, e:
            error = 'Error abriendo el archivo {}: {}'.format(self.path, e)
            logger.error(error)
            self.errors.append(error)
            return None
        try:
            query = json.load(f)
        except Exception, e:
            error = 'Error parseando a JSON el archivo {}: {}'.format(self.path, e)
            logger.error(error)
            self.errors.append(error)
            return None
        
        f.close()
        self.params = query
        return query
    
    def request_all(self):
        """ iterar por todos los datos. Usar los iterables definidos.
            Carga self.datasets 
            TODO se podría separar en gather y fetch a futuro"""
        self.datasets = []
        logger.info('Request All from Query File {}'.format(self.params['name']))
        
        if 'iterables' in self.params:
            if "anio_param" in self.params['iterables']:
                anios = range(2020, 2009, -1)  # TODO, definir otra forma más dinámica
                for anio in anios:
                    # definir un nombre personalizado para cada recurso
                    data = self.harvest(anio=anio)
                    if self.data_is_empty(data):
                        logger.info('Dataset vacío: {} {}'.format(self.params['name'], anio))
                        continue
                    title = self.params['title'].encode('utf-8')
                    notes = self.params['notes'].encode('utf-8')
                    full = {
                        'name': '{}-{}'.format(self.params['name'], anio),
                        'title': '{} {}'.format(title, anio),
                        'notes': notes,
                        'data': data,
                        'tags': self.build_tags(tags=self.params.get('tags', []))
                    }
                    full['resources'] = self.save_data(full)
                    self.datasets.append(full)

        else:
            data = self.harvest()
            if self.data_is_empty(data):
                logger.info('Dataset vacío: {}'.format(self.params['name']))
                return
            title = self.params['title']
            notes = self.params['notes']
                    
            full = {
                'name': self.params['name'],
                'title': title,
                'notes': notes,
                'data': data,
                'tags': self.build_tags(tags=self.params.get('tags', []))
            }
            full['resources'] = self.save_data(full)
            self.datasets.append(full)

    def request_data(self, anio=None):
        """ consultar la URL con los parámetros definidos y devolver el resultado """
        
        if len(self.params.keys()) == 0:
            error = 'Error: Intentando leer datos sin los parámetros no cargados'
            logger.error(error)
            self.errors.append(error)
            return None

        query = self.params
        name = query['name']
        logger.info('Request data from Query File {}, anio: {}'.format(name, anio))
        
        base_url = self.harvest_source.source.url
        username = self.harvest_source.source_config.get('username')
        password = self.harvest_source.source_config.get('password')
        params = query['params']
        # revisar los iterables y actualizar a lo que corresponda
        if anio is not None:
            anio_param = self.params['iterables']['anio_param']
            params[anio_param] = anio

        try:
            resp = requests.post(base_url, auth=(username, password), data=params)  #, headers=headers)
        except Exception, e:
            error = 'Error en request para obtener datos. URL: {}. Params: {}. Error: {}'.format(base_url, params, e)
            logger.error(error)
            self.errors.append(error)
            return None
            
        data = resp.json()
        return data
    
    def get_metadata(self):
        """ obtener metadatos del proceso de harvesting para actualizar """
        name = self.params['name']
        filename = '{}-metadata.json'.format(name)
        path = os.path.join(self.harvest_source.results_path, filename)
        if not os.path.isfile(path):
            # inicializar los metadatos
            # "global" es para todos los procesos, podría haber iterables con datos separados
            metadata = {
                'name': name,
                'global': {
                    'harvest_count': 0                    
                }
            }
        else:
            f = open(path, 'r')
            metadata = json.load(f)
            f.close()
        
        self.metadata = metadata 
        return metadata

    def harvest(self, anio=None):
        """ Lanzar el proceso de cosecha y guardar los resultados para un año específico """
        
        self.errors = []  # reiniciar los errores para este proceso
        
        metadata = self.get_metadata()
        metadata['global']['harvest_count'] += 1
        
        data = self.request_data(anio=anio)

        if anio is not None:
            if anio not in metadata:
                metadata[anio] = {
                    'harvest_count': 1,
                    'last_harvest_ok': data is not None, 
                    'last_errors': self.errors
                }
            
        self.metadata = metadata
        self.save_metadata()
        
        return data

    def data_is_empty(self, data):
        """ a veces iteramos sobre elementos que dan resultados vacios
            No crear datasets en esos casos """
        
        return len(data['resultset']) == 0

    def save_metadata(self):
        """ grabar los metadatos (personalizados, el harvester ya guarda algunos) de este proceso de cosecha """
        data_str = json.dumps(self.metadata, indent=4)
        name = self.params['name']
        filename = '{}-metadata.json'.format(name)
        save_to = os.path.join(self.harvest_source.results_path, filename)
        f = open(save_to, 'w')
        f.write(data_str)
        f.close()

    def save_data(self, full):
        """ grabar los datos a disco """        
        name = full['name']
        title = full['title']
        data = full['data']
        data_str = json.dumps(data, indent=4)
        filename = '{}.json'.format(name)
        save_to = os.path.join(self.harvest_source.results_path, filename)
        f = open(save_to, 'w')
        f.write(data_str)
        f.close()
        res_json = {
            'title': '{} JSON'.format(title),
            'name': '{}-json'.format(name),
            'upload': save_to,  # TODO no se puede mandar el path en el dict para que se cree solo :(
            'format': 'json'
        }

        # grabar tambien en CSV
        filename = '{}.csv'.format(name)
        save_to = os.path.join(self.harvest_source.results_path, filename)
        self.json_to_csv(data=data, save_path=save_to)
        res_csv = {
            'title': '{} CSV'.format(title),
            'name': '{}-csv'.format(name),
            'upload': save_to,  # TODO no se puede mandar el path en el dict para que se cree solo :(
            'format': 'csv'
        }

        # return CKAN resurces
        resources = [res_csv, res_json]

        return resources
    
    def json_to_csv(self, data, save_path=None):
        """ transformar los datos JSON a CSV """
        logger.info('JSON to CSV {}'.format(save_path))
        metadata = data['metadata']
        field_names = [md['colName'] for md in metadata]
        field_names_utf8 = [fn.encode('utf-8') for fn in field_names]
        rows = data['resultset']

        if save_path is not None:
            f = open(save_path, 'w')
            wr = csv.writer(f)
            wr.writerow(field_names_utf8)

            rows_utf8 = []
            for row in rows:
                row_utf8 = []
                for field in row:
                    if isinstance(field, basestring):
                        field = field.encode('utf-8')
                    row_utf8.append(field)
                rows_utf8.append(row_utf8)
            
            for row in rows_utf8:
                wr.writerow(row)
            f.close()

        return field_names_utf8, rows_utf8 
    
    def build_tags(self, tags):
        return [{'name': tag} for tag in tags] 

data_sample = {
    "queryInfo": {"totalRows": "5"}, 
    "resultset": [
        ["5 - TRANSFERENCIAS", 394565, 0.78], 
        ["4 - BIENES DE USO", 18801654.11, 37.16], 
        ["3 - SERVICIOS NO PERSONALES", 27873452.41, 55.09], 
        ["2 - BIENES DE CONSUMO", 3521613.99, 6.96], 
        ["1 - GASTOS EN PERSONAL", 1946.47, 0]
    ], 
    "metadata": [
        {"colType": "String", "colIndex": 0, "colName": "inciso"}, 
        {"colType": "Numeric", "colIndex": 1, "colName": "total_devengado"}, 
        {"colType": "Numeric", "colIndex": 2, "colName": "porcentaje"}
    ]
}
        

