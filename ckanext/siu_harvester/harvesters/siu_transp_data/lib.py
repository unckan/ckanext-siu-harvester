# -*- coding: utf-8 -*-
import csv
import json
import logging
import os
import requests
from slugify import slugify

logger = logging.getLogger(__name__)


class SIUTranspQueryFile:
    """ Cada uno de los archivos para consultar al portal de transparencia """

    def __init__(self, harvest_source, path, params={}, timeout=5):
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
        self.timeout = timeout
        self.errors = []
        self.requests = []  # lista de todas las queries hechas
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
            if "sub_list" in self.params['iterables']:
                sub_list = self.params['iterables']['sub_list']
                self.iterate_sublist(sub_list=sub_list)
        else:
            data = self.harvest()
            if self.data_is_empty(data):
                logger.info('Dataset vacío: {}'.format(self.params['name']))
                return
            title = self.params['title'].encode('utf-8')
            notes = self.params['notes'].encode('utf-8')
                    
            full = {
                'name': self.params['name'],
                'title': title,
                'notes': notes,
                'data': data,
                'tags': self.build_tags(tags=self.params.get('tags', []))
            }
            full['resources'] = self.save_data(full)
            self.datasets.append(full)
        
    def iterate_sublist(self, sub_list={}):
        """ Iterar por una sub-lista de una query que lo requiere
            Esta funcion carga sel.datasets con todos los datos 
                encontrados que no estén vacios.
            La sublista debe ser definida de la forma
            {
                "help": "No requerido pero util para documentar",
                "name": "lala",
                "params": {
                    "paramprm_tablero_visible": "18",
                    "dataAccessId": "param_ua_cargos"
                    }
            }
            """
        name = sub_list['name']
        logger.info('Iterando sublista: {}'.format(name))
        # agregar los nuevos parámetros para la sublista tomando como base la lista original del archivo JSON.
        params = self.params['params'].copy()
        # pisar con los valores requeridos para la sub lista
        params.update(sub_list['params'])
        # quitar el parametro que despues se va a aplicar
        apply_to = sub_list['apply_to']
        del params[apply_to]
        sub_list['params'] = params
        data = self.request_data(query=sub_list)
        # aca recibimos un JSON como en los datasets.
        # interpretamos que resultset tendrá una lista de los valores que buscamos
        if data is None:  # tiene que ser algun error
            elementos = []
        else:
            elementos = data.get('resultset', [])

        # estos valores deben ser pasados al parametro definido en 'apply_to'
        apply_to = sub_list['apply_to']

        for elem in elementos:
            # aqui esperamos una lista de un solo elemento
            value = elem[0]
            logger.info('Buscando datos para la sublista: {}'.format(value))
            # ahora estoy listo para la cosecha de los datos
            # cada valor obtenido debe pasarse al campo definido en 'apply_to'
            # y cosecharse
            self.params['params'][apply_to] = value

            data = self.harvest()
            if self.data_is_empty(data):
                logger.info('Dataset vacío: {} {}'.format(name, value))
                continue
            logger.info('Datos obtenidos para: {}'.format(value))
            title = self.params['title'].encode('utf-8')
            notes = self.params['notes'].encode('utf-8')
            
            # TODO analizar como transformar algunos valores no válidos 
            # para ser usados como nombres
            if value == '1-TODAS':
                name_value = 'completo'
                title_value = 'Completo'
            else:
                name_value = slugify(value)
                title_value = value
                
            full = {
                'name': '{}-{}'.format(self.params['name'], name_value),
                'title': '{} {}'.format(title, title_value),
                'notes': notes,
                'data': data,
                'tags': self.build_tags(tags=self.params.get('tags', []))
            }
            full['resources'] = self.save_data(full)
            self.datasets.append(full)

    def request_data(self, query=None):
        """ consultar la URL con los parámetros definidos 
            y devolver el resultado.
            No se requiere en general cargar el parámetro 
            'query' porque se usan los parámetros locales 
            (self.params). Solo se usa para consultas especiales
            (por ejemplo para obetner sublistas) """
        
        if query is None:
            query = self.params
        
        if len(query.keys()) == 0:
            error = 'Error: Intentando leer datos sin los parámetros no cargados'
            logger.error(error)
            self.errors.append(error)
            return None

        name = query['name']
        logger.info('Request data from Query File {}'.format(name))
        
        base_url = self.harvest_source.source.url
        username = self.harvest_source.source_config.get('username')
        password = self.harvest_source.source_config.get('password')
        params = query['params']
        
        p = self.get_request_uid(params)
        logger.info('Request URL {}, PARAMS: {}'.format(base_url, params))        
        try:
            resp = requests.post(base_url, auth=(username, password), data=params, timeout=self.timeout)  #, headers=headers)
        except Exception, e:
            error = '{} Error en request para obtener datos. Error: {}'.format(p, e)
            logger.error(error)
            self.errors.append(error)
            self.requests.append('{} ERROR request'.format(p))
            return None
        
        try:
            data = resp.json()
        except Exception, e:
            error = '{} JSON error. \n\tResponse: {}\n\tError: {}'.format(p, resp.text, e)
            logger.error(error)
            self.errors.append(error)
            self.requests.append('{} ERROR JSON'.format(p))
            return None
        
        rows = len(data.get('resultset', []))
        self.requests.append('{} OK ROWS {}'.format(p, rows))
        self.requests.append(req)

        return data
    
    def get_request_uid(self, params):
        """ obtener un resumen identificador de una consulta """
        path = params.get('path', '/no-path')
        upath = path.split('/')[-1]
        udaci = params.get('dataAccessId', 'no-access-id')
        extras = ['{}:{}'.format(k, v) for k, v in params.items() if k.startswith('paramprm')]
        uextras = ' '.join(extras)
        uid = '{} {} {}'.format(upath, udaci, uextras)
        return uid

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

    def harvest(self):
        """ Lanzar el proceso de cosecha y guardar los resultados para un año específico """
        
        data = self.request_data()
        return data

    def data_is_empty(self, data):
        """ a veces iteramos sobre elementos que dan resultados vacios
            No crear datasets en esos casos """
        
        is_empty = False
        if data is None:  # No hay un JSON para este query
            is_empty = True
        elif len(data.get('resultset', [])) == 0:
            is_empty = True

        return is_empty

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
