# -*- coding: utf-8 -*-

import csv
import logging
import os
# from .lib import SIUTranspQueryFile
from ckanext.siu_harvester.harvesters.siu_transp_data.lib import SIUTranspQueryFile


logger = logging.getLogger(__name__)


class SIUPoratlTransparenciaData:
    """ Clase general de administracion de datos del 
        portal de transparencia de SIU. """

    def __init__(self, base_url=None,
                       username=None,
                       password=None):
        # URL de base para los endpoints, 
        # ejemplo: https://portal.edu.ar/pentaho/plugin/cda/api/doQuery
        self.base_url = base_url
        # usuario para las llamadas API 
        self.username = username
        # clave para las llamadas API
        self.password = password
        # archivos de consulta
        self.query_files = []
        # metadata de cada una de los archivos de consutla
        self.query_metadata = {}

    def get_query_files(self, base_folder_path):
        """ Generador para obtener cada uno de los archivos con 
            datos para cosechar. Se espera un directorio con archivos
            JSON que documentan los endpoint del API del portal de 
            Transparencia de SIU """
        logger.info('Getting query files')
        
        self.query_files = []

        for f in os.listdir(base_folder_path):
            logger.info('Get query file {}'.format(f))
            path = os.path.join(base_folder_path, f)
            if os.path.isfile(path):
                ext = f.split('.')[-1]
                if ext != 'json':
                    continue
                self.query_files.append(path)
        
        return self.query_files
    
    def load_all_data(self):
        """ read all query files and get all metadata """

        for qf in self.query_files:
            logger.info('Gather SIU Transp FILE {}'.format(qf))
            stqf = SIUTranspQueryFile(path=qf)
            # open to read query params
            query_metadata = stqf.open()

            self.query_metadata[query_metadata['name']] = query_metadata

    def save_metadata(self, path):
        """ save a CSV report of all query files """
        rows = []
        for query_name, query_metadata in self.query_metadata:
            sublist = query_metadata.get('iterables', {}).get('sub_list', {})
            sublist_name = sublist.get('name', '')
            sublist_help = sublist.get('help', '')
            tags = query_metadata.get('tags', [])
            # llenar con vacios para tene 5 tags
            tags5 = tags + ['']*(5 - len(tags))
            data_access_id = query_metadata['params']['dataAccessId']
            cda_path = query_metadata['params']['path']
            cda = cda_path.split('/')[-1]
            row = {
                'CDA': cda,
                'path CDA': cda_path,
                'Data Access ID': data_access_id,
                'nombre': query_name,
                'titulo': query_metadata['title'],
                'descripcion': query_metadata['notes'],
                'observaciones internas': query_metadata['internals'],
                'nombre sublista': sublist_name,
                'ayuda sublista': sublist_help,
                'tag 1': tags5[0],
                'tag 2': tags5[1],
                'tag 3': tags5[2],
                'tag 4': tags5[3],
                'tag 5': tags5[4]
            }
            rows.append(row)
        
        # escribir a disco
        field_names = row.keys()
        
        f = open(path, 'w')
        wr = csv.DictWriter(f, fieldnames=field_names)
        wr.writeheader()

        for row in rows:
            wr.writerow(row)
        f.close()

"""
from siudata import *
s = SIUPoratlTransparenciaData()
s.get_query_files('queries')
s.load_all_data()
"""