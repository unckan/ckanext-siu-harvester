# -*- coding: utf-8 -*-
import json
import logging
import os
import requests
from werkzeug.datastructures import FileStorage

from ckan import plugins as p
from ckan import model
from ckan.lib.helpers import json
from ckan import logic

from ckanext.harvest.harvesters.base import HarvesterBase
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.helpers import get_harvest_source
from ckanext.siu_harvester.harvesters.siu_transp_data.lib import SIUTranspQueryFile


logger = logging.getLogger(__name__)


class SIUTransparenciaHarvester(HarvesterBase):

    def set_paths(self):
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.environ.get('CKAN_STORAGE_PATH', here)
        self.data_path = os.path.join(base, 'siu_transp_data')
        self.queries_path = os.path.join(self.data_path, 'queries')
        self.results_path = os.path.join(self.data_path, 'results')
        if not os.path.isdir(self.results_path):
            os.mkdir(self.results_path)

    ## IHarvester
    def info(self):
        '''
        :returns: A dictionary with the harvester descriptors
        '''
        return {
            'name': 'siu_transp',
            'title': 'SIU Portal de transparencia',
            'description': 'Extraer y publicar datos del portal de transparecnia de SIU',
            'form_config_interface': 'Text'
        }


    def validate_config(self, config):
        '''

        [optional]

        Harvesters can provide this method to validate the configuration
        entered in the form. It should return a single string, which will be
        stored in the database. Exceptions raised will be shown in the form's
        error messages.

        :param config: Config string coming from the form
        :returns: A string with the validated configuration options
        '''

        if not config:
            raise ValueError('Set up the required configuration settings')

        try:
            config_obj = json.loads(config)
        except ValueError as e:
            raise e

        required_cfg = ['username', 'password']  # , 'owner_org']
        faileds = []
        for req in required_cfg:
            if req not in config_obj:
                faileds.append(req)

        if len(faileds) > 0:
            raise ValueError('Missing configs: {}'.format(faileds))

        return config

    def gather_stage(self, harvest_job):
        '''
        analyze the source, return a list of IDs
            and create one HarvestObject per dataset 
        '''
        logger.info('Starts Gather SIU Transp')
        # load paths
        self.set_paths()
        self.get_query_files()

        # basic things you'll need
        self.source = harvest_job.source
        self.source_config = json.loads(self.source.config)

        # ####################################
        # get previous harvested packages
        pfr = self.get_packages_for_source(harvest_source_id=self.source.id)
        prev_names = [pkg['name'] for pkg in pfr['results']]
        logger.info('Get previous harvested objects {}'.format(prev_names))
        # ####################################
        
        object_ids = []  # lista de IDs a procesar, esto se devuelve en esta funcion
        
        self.source_dataset = get_harvest_source(self.source.id)
        owner_org = self.source_dataset.get('owner_org')
        logger.info('Gather SIU Transp to ORG {}'.format(owner_org))
        
        # Iterar por cada query para obtener diferentes conjuntos de datos
        # Por cada archivo en siu_transp_data/queries se generarán múltiples datasets para publicar
        
        logger.info('Iter files')
        for qf in self.query_files:
            logger.info('Gather SIU Transp FILE {}'.format(qf))
            stqf = SIUTranspQueryFile(harvest_source=self, path=qf)
            # open to read query params
            stqf.open()
            # request all data
            stqf.request_all()

            for dataset in stqf.datasets:
                if dataset['name'] in prev_names:
                    action = 'update'
                    # leave this list just with packages to remove
                    prev_names.remove(dataset['name'])
                else:
                    action = 'create'
                logger.info('Dataset {} to {}'.format(dataset['name'], action))
                ho_dict = {
                    'title': dataset['title'],
                    'name': dataset['name'],
                    'owner_org': owner_org,
                    'notes': dataset['notes'],
                    'tags': dataset['tags'],
                    'resources': dataset['resources'],
                    'action': action
                }

                # Each harvest object will be passed to other stages in harvest process
                obj = HarvestObject(guid=dataset['name'],
                                    job=harvest_job,
                                    content=json.dumps(ho_dict))
                obj.save()
                logger.info('Objects ID appends {}'.format(obj.id))
                object_ids.append(obj.id)

        # TODO compare with previous harvested data to remove dataset no more at harvest source

        return object_ids
    
    def fetch_stage(self, harvest_object):
        ''' donwload and get what you need before import to CKAN
            Already downloaded in Gather stage '''
        logger.info('Fetching {}'.format(harvest_object.id))
        
        return True
    
    def import_stage(self, harvest_object):
        ''' save to CKAN '''
        logger.info('Importing {}'.format(harvest_object.id))
        self.set_paths()
        
        package_dict = json.loads(harvest_object.content)
        action = package_dict.pop('action')
        extras = package_dict.get('extras', [])

        extras = self.update_extras(extras, harvest_object)
        
        package_dict['extras'] = extras

        # remove resources, we are not able to upload in the create/upload pkg functs
        resources = package_dict.get('resources', [])
        for resource in resources:
            # This should work but fails
            # upload_from = resource.pop('upload')
            # # resource['upload'] = FileStorage(filename=upload_from)
            # resource['files'] = [('upload', file(upload_from))]
            resource['url'] = ''
            
        # Save (create or update) to CKAN
        # Using base class function ._create_or_update_package
        #   seems no useful to deal with resources
        user_name = self._get_user_name()
        context = {'model': model, 'session': model.Session, 'user': user_name}
        
        if action == 'create':
            try:
                pkg = p.toolkit.get_action('package_create')(context, package_dict)
            except Exception, e:
                logger.error('Error creating package {}'.format(str(e)))
                # TODO, no debería suceder
                if str(e).find('already in use') > 0:
                    action = 'update'
                else:
                    raise

        if action == 'update':
            pkg = p.toolkit.get_action('package_update')(context, package_dict)
        
        if action not in ['create', 'update']:
            raise Exception('Unexpected action {}'.format(action))
            
        logger.info('Package {} {}'.format(action, json.dumps(pkg, indent=4)))

        # actualizar los recursos para que se suban los arvhivos locales
        resources = pkg['resources']
        for resource in resources:
            logger.info('Updating resource {}'.format(json.dumps(resource, indent=4)))
            # fn = p.toolkit.get_action('resource_update')
            # res = fn(context, resource)
            # logger.info('Resource updated {}'.format(json.dumps(res, indent=4)))
            upload = resource['upload']
            # TODO debería poder agregarse desde resource_create pero parece que no se puede
            user_harvest = p.toolkit.get_action('user_show')(context, {'id': user_name})
            api_key = user_harvest['apikey']
            requests.post('http://0.0.0.0:5000/api/action/resource_update',
                data={'id':resource['id']},
                headers={'X-CKAN-API-Key': api_key},
                files=[('upload', file(upload))])
            
            # re-send to XLOADER
            # xs = p.toolkit.get_action('xloader_submit')(None, {'resource_id': resource['id']})

            final_resource = p.toolkit.get_action('resource_show')(context, {'id': resource['id']})
            logger.info('Final resource {}'.format(json.dumps(final_resource, indent=4)))
            
        # Mark previous objects as not current
        previous_object = model.Session.query(HarvestObject) \
                            .filter_by(guid=harvest_object.guid) \
                            .filter_by(current=True) \
                            .first()
        if previous_object:
            logger.info('Previous HO as False')
            previous_object.current = False
            previous_object.save()

        logger.info('Link Harvest object and package {}, {}'.format(harvest_object.id, pkg['id']))
        harvest_object.package_id = pkg['id']
        harvest_object.current = True
        harvest_object.add()
        harvest_object.save()

        return True

    def get_query_files(self):
        """ Generador para obtener cada uno de los archivos con datos para cosechar """
        logger.info('Getting query files')
        
        self.query_files = []

        for f in os.listdir(self.queries_path):
            logger.info('Get query file {}'.format(f))
            path = os.path.join(self.queries_path, f)
            if os.path.isfile(path):
                ext = f.split('.')[-1]
                if ext != 'json':
                    continue
                self.query_files.append(f)
        
        return self.query_files
    
    def get_packages_for_source(self, harvest_source_id):
        '''
        Returns the current packages list for datasets associated with the given source id
        '''
        fq = '+harvest_source_id:"{}"'.format(harvest_source_id)
        search_dict = {'fq': fq}
        context = {'model': model, 'session': model.Session}
        result = p.toolkit.get_action('package_search')(context, search_dict)
        return result
    
    def update_extras(self, extras, harvest_object):
        extras = self.update_extra(extras, 'harvest_object_id', harvest_object.id)
        extras = self.update_extra(extras, 'harvest_source_id', harvest_object.source.id)
        extras = self.update_extra(extras, 'harvest_source_title', harvest_object.source.title)
        logger.info('Updated extras {}'.format(extras))
        
        return extras

    def update_extra(self, extras, key, value):
        updated = False
        ret = []
        for extra in extras:
            if extra['key'] == key:
                extra.value = value
            ret.append(extra)
        if not updated:
            ret.append({'key': key, 'value': value})
        
        return ret

