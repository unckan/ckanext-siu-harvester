import json
import logging
import vcr
import ckanext.harvest.model as harvest_model
from ckan import model
from factories import HarvestJobObj, SIUHarvestSourceObj
from nose.tools import assert_equal, assert_in, assert_not_in, assert_raises

try:
    from ckan.tests.helpers import reset_db, call_action
    from ckan.tests.factories import Organization, Group, _get_action_user_name, Sysadmin
except ImportError:
    from ckan.new_tests.helpers import reset_db, call_action
    from ckan.new_tests.factories import Organization, Group, _get_action_user_name, Sysadmin

from ckanext.siu_harvester.harvesters.siu_transp import SIUTransparenciaHarvester


log = logging.getLogger(__name__)

class TestSIUHarvester(object):

    @classmethod
    def setup_class(cls):
        log.info('Starting mock http server')

    @classmethod
    def setup(cls):
        reset_db()
        harvest_model.setup()
        sysadmin = Sysadmin(name='dummy')
        user_name = sysadmin['name'].encode('ascii')
        call_action('organization_create',
                    context={'user': user_name},
                    name='test-org')

    def run_gather(self, url, source_config='{}'):

        source = SIUHarvestSourceObj(url=url,
                                    owner_org='test-org',
                                    config=source_config)
        
        log.info('Created source {}'.format(source))
        self.job = HarvestJobObj(source=source)
        self.harvester = SIUTransparenciaHarvester()
        
        # gather stage
        log.info('GATHERING %s', url)
        obj_ids = self.harvester.gather_stage(self.job)
        log.info('job.gather_errors=%s', self.job.gather_errors)
        
        log.info('obj_ids=%s', obj_ids)
        if obj_ids is None or len(obj_ids) == 0:
            # nothing to see
            return

        self.harvest_objects = []
        for obj_id in obj_ids:
            harvest_object = harvest_model.HarvestObject.get(obj_id)
            log.info('ho guid=%s', harvest_object.guid)
            log.info('ho content=%s', harvest_object.content)
            self.harvest_objects.append(harvest_object)

        # this is a list of harvestObjects IDs. One for dataset
        return obj_ids

    def run_fetch(self):
        # fetch stage
        for harvest_object in self.harvest_objects:
            log.info('FETCHING %s' % harvest_object.id)
            result = self.harvester.fetch_stage(harvest_object)

            log.info('ho errors=%s', harvest_object.errors)
            log.info('result 1=%s', result)
            if len(harvest_object.errors) > 0:
                raise Exception(harvest_object.errors[0])

    def run_import(self):
        # fetch stage
        datasets = []
        for harvest_object in self.harvest_objects:
            log.info('IMPORTING %s' % harvest_object.id)
            result = self.harvester.import_stage(harvest_object)

            log.info('ho errors 2=%s', harvest_object.errors)
            log.info('result 2=%s', result)
            if len(harvest_object.errors) > 0:
                raise Exception(harvest_object.errors[0])

            log.info('ho pkg id=%s', harvest_object.package_id)
            dataset = model.Package.get(harvest_object.package_id)
            datasets.append(dataset)
            log.info('dataset name=%s', dataset.name)

        return datasets

    # TODO hay problemas con este cassete 
    @vcr.use_cassette('ckanext/siu_harvester/tests/test_cassette.yaml', 
                      ignore_hosts=['solr', 'ckan', '127.0.0.1', 'localhost'])
    def test_source_results(self):
        """ harvest waf1/ folder as waf source """

        url = 'http://wichi.siu.edu.ar/pentaho/plugin/cda/api/doQuery'
        # limit to some files only
        
        cfg = {
            "username": "usuario_transparencia",
            "password": "clave_transparencia",
            "only_files": ['1-PRESUPUESTO-tablero_01.json', '1-PRESUPUESTO-tablero_02.json']
            }
        self.config1 = json.dumps(cfg)
        
        self.run_gather(url=url, source_config=self.config1)

        assert_equal(len(self.job.gather_errors), 0)
        self.run_fetch()
        datasets = self.run_import()

        assert_equal(len(datasets), 16)

        for dataset in datasets:
            log.info('Dataset {}'.format(dataset.name))
    

    @vcr.use_cassette('ckanext/siu_harvester/tests/test_cassette.yaml', 
                      ignore_hosts=['solr', 'ckan', '127.0.0.1', 'localhost'])
    def test_source_results(self):
        """ harvest waf1/ folder as waf source """

        url = 'http://wichi.siu.edu.ar/pentaho/plugin/cda/api/doQuery'
        # limit to some files only
        
        cfg = {
            "username": "usuario_transparencia",
            "password": "clave_transparencia",
            "only_files": ['4-RRHH-tablero_18.json'],
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
        self.config1 = json.dumps(cfg)
        log.info('Final config {}'.format(self.config1))

        self.run_gather(url=url, source_config=self.config1)

        assert_equal(len(self.job.gather_errors), 0)
        self.run_fetch()
        datasets = self.run_import()

        assert_equal(len(datasets), 15)

        for dataset in datasets:
            log.info('Dataset {}'.format(dataset.name))
            assert_equal(dataset.notes, "Nueva descripcion")
            
            pkg_dict = dataset.as_dict()
            assert_in("nuevo_tag_09", pkg_dict['tags'])
            assert_in("nuevo_tag_12", pkg_dict['tags'])
            
            extras = pkg_dict['extras']
            assert_in("dataset_preview", extras.keys())
            assert_in("my_custom_extra", extras.keys())
            assert_equal(extras['my_custom_extra'], "999")

            assert_in("group_01", pkg_dict['groups'])
            assert_in("group_02", pkg_dict['groups'])
            