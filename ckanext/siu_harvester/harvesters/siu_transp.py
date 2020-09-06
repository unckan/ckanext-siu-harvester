# -*- coding: utf-8 -*-
import json
import logging
import os
import requests
from werkzeug.datastructures import FileStorage

from siu_data.portal_data import SIUPoratlTransparenciaData
from siu_data.query_file import SIUTranspQueryFile

from ckan import plugins as p
from ckan import model
from ckan.lib.helpers import json
from ckan import logic

from ckanext.harvest.harvesters.base import HarvesterBase
from ckanext.harvest.model import HarvestObject, HarvestGatherError, HarvestObjectError
from ckanext.harvest.helpers import get_harvest_source


logger = logging.getLogger(__name__)


class SIUTransparenciaHarvester(HarvesterBase):

    def set_paths(self):
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.environ.get('CKAN_STORAGE_PATH', here)
        self.results_folder_path = os.path.join(base, 'siu-harvester-results')
        if not os.path.isdir(self.results_folder_path):
            os.makedirs(self.results_folder_path)
        
        # librearia que gestiona los datos en el portal de SIU
        self.siu_data_lib = SIUPoratlTransparenciaData()
        
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
        self.siu_data_lib.get_query_files()

        # basic things you'll need
        self.source = harvest_job.source
        self.source_config = json.loads(self.source.config)

        self.siu_data_lib.base_url = self.source.url
        self.siu_data_lib.username = self.source_config['username']
        self.siu_data_lib.password = self.source_config['password']
        
        # ####################################
        # get previous harvested packages
        pfr = self.get_packages_for_source(harvest_source_id=self.source.id)
        prev_names = [pkg['name'] for pkg in pfr['results']]
        logger.info('Get previous harvested objects {}'.format(prev_names))
        # TODO
        # ####################################
        
        object_ids = []  # lista de IDs a procesar, esto se devuelve en esta funcion
        
        self.source_dataset = get_harvest_source(self.source.id)
        owner_org = self.source_dataset.get('owner_org')
        logger.info('Gather SIU Transp to ORG {}'.format(owner_org))
        
        # Iterar por cada query para obtener diferentes conjuntos de datos
        # Por cada archivo en siu_transp_data/queries se generarán múltiples datasets para publicar
        
        report = []  # resumen de todos los resultados
        logger.info('Iter files')
        
        # ver si la config me pide sobreescribir metadatos en los datasets de cada archivo
        override = self.source_config.get('override', None)
        logger.info("General override {}".format(override))
            
        for qf in self.siu_data_lib.query_files:
            only_files = self.source_config.get('only_files', None)
            query_file_name = qf.split('/')[-1]
            if only_files is not None:
                if query_file_name not in only_files:
                    logger.info('Skipping file by config {}'.format(query_file_name))
                    continue
            
            logger.info('Gather SIU Transp FILE {}'.format(qf))
            stqf = SIUTranspQueryFile(portal=self.siu_data_lib, path=qf)
            # open to read query params
            stqf.open()
            # request all data
            stqf.request_all(results_folder_path=self.results_folder_path)
            for err in stqf.errors:
                hgerr = HarvestGatherError(message=err, job=harvest_job)
                hgerr.save()


            # ====== Prepare dict to override datasets metadata ============
            override_this = override.get(query_file_name, {})
            logger.info("To override {}: {}".format(query_file_name, override_this))
            
            # extras need to be {"key": "extra name", "value": "extra value"}
            extras = override_this.get('extras', {})
            new_extras = []
            for extra_key, extra_value in extras.iteritems():
                logger.info("Override extra found {}: {}".format(extra_key, extra_value))
                if not isinstance(extra_value, str):
                    extra_value = str(extra_value)
                new_extras.append({"key": extra_key, "value": extra_value})
            
            if len(new_extras) > 0:
                override_this['extras'] = new_extras

            # tags need to be {"name": "tag name"}
            tags = override_this.get('tags', [])
            new_tags = []
            for tag in tags:
                logger.info("Override tag found {}".format(tag))
                new_tags.append({"name": tag})
            
            if len(new_tags) > 0:
                override_this['tags'] = new_tags

            # groups need to be {"name": "tag name"}
            groups = override_this.get('groups', [])
            new_groups = []
            for group in groups:
                logger.info("Override group found {}".format(group))
                # check if groups must be created
                context = {'model': model, 'session': model.Session, 'user': self._get_user_name()}
                try:
                    p.toolkit.get_action('group_create')(context, {"name": group})
                except Exception as e:
                    logger.error('Error creating group (skipped) {}: {}'.format(group, e))
                    
                new_groups.append({"name": group})
            
            if len(new_groups) > 0:
                override_this['groups'] = new_groups

            # ================================
                
            report += stqf.requests
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

                # fix extras if they exists
                ho_dict.update(override_this)
                logger.info("Overrided ho_dict {}".format(ho_dict))
                    

                # Each harvest object will be passed to other stages in harvest process
                obj = HarvestObject(guid=dataset['name'],
                                    job=harvest_job,
                                    content=json.dumps(ho_dict))
                obj.save()
                logger.info('Objects ID appends {}'.format(obj.id))
                object_ids.append(obj.id)

        # TODO compare with previous harvested data to remove dataset no more at harvest source

        # resumen final
        logger.info('REQUESTS: \n{}'.format('\n\t'.join(report)))
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
        resources = package_dict.pop('resources', [])
        
        # Save (create or update) to CKAN
        # Using base class function ._create_or_update_package
        #   seems no useful to deal with resources
        user_name = self._get_user_name()
        context = {'model': model, 'session': model.Session, 'user': user_name}
        
        if action == 'create':
            try:
                pkg = p.toolkit.get_action('package_create')(context, package_dict)
            except Exception, e:
                logger.error('Error creating package {}: {}'.format(str(e), package_dict))
                # TODO, no debería suceder
                if str(e).find('already in use') > 0:
                    action = 'update'
                else:
                    msg = 'Import error. pkg name: {}. \n\tError: {}'.format(package_dict.get('name', 'unnamed'), e)
                    harvest_object_error = HarvestObjectError(message=msg, object=harvest_object)
                    harvest_object_error.save()
                    return False

        if action == 'update':
            pkg = p.toolkit.get_action('package_update')(context, package_dict)
        
        if action not in ['create', 'update']:
            raise Exception('Unexpected action {}'.format(action))
            
        # logger.info('Package {} {}'.format(action, json.dumps(pkg, indent=4)))

        for resource in resources:
            resource['package_id'] = pkg['id']
            resource['url'] = ''
            upload_from = resource.pop('upload')
            
            if os.path.isfile(upload_from):
                resource['upload'] = FileStorage(filename=upload_from, stream=open(upload_from))
                self.create_resource(context, resource)
            else:
                logger.error('Resource to upload not found {}'.format(upload_from))
            
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
    
    def create_resource(self, context, resource):
        fn = p.toolkit.get_action('resource_create')
        try:
            res = fn(context, resource)
        except Exception, e:
            logger.error('Error creating resource {} {}'.format(resource, e))
            raise
        
        final_resource = p.toolkit.get_action('resource_show')(context, {'id': res['id']})
        logger.info('Final resource {}'.format(final_resource['name']))

        return final_resource

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

