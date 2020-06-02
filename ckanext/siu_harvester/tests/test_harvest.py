"""Tests for plugin.py."""
import logging
import json

from ckan.tests import helpers
import ckan.model as model
import ckan.plugins as p
from ckan.logic import NotFound, ValidationError
from random import randint


log = logging.getLogger(__name__)


class TestSIUHarvester:

    def test_harvest(self):
        self.create_harvest_sources()
            
    @classmethod
    def setup_class(cls):
        
        if not p.plugin_loaded('siu'):
            log.info("Loading plugin")
            p.load('siu')
        
    def setup(self):
        self.user = helpers.call_action('get_site_user')
        self.context = {'user': self.user['name']}
        self.create_harvest_sources()
    
    def teardown(self):
        self.clean()
    
    @classmethod
    def teardown_class(cls):

        log.info("Unloading plugin")
        p.unload('siu')

    def create_harvest_sources(self):
        """ create harvest source to test. """
        print " ********** Creating test harvest source"
        
        self.o1 = self.get_or_create_org(title='Organization 01')
        
        self.h1 = self.get_or_create_harvest_source(title='SIU test 01',
                                                    org=self.o1,
                                                    url='http://wichi.siu.edu.ar/pentaho/plugin/cda/api/doQuery',
                                                    source_type='siu_transp',
                                                    config={'username': 12345, 'password': 12345}
                                             )
        hss = helpers.call_action('harvest_source_list', context=self.context)
        print('We have {} harvest sources: {}'.format(len(hss), hss))

        assert len(hss) == 1
        
    def clean(self):
        print 'Clean test data'
        
        print('Deleting {}'.format(self.h1['title']))
        ctx = self.context.copy()
        ctx['clear_source'] = True
        helpers.call_action("harvest_source_delete", context=ctx, id=self.h1['id'])

        print('Deleting ORG: {}'.format(self.o1['title']))
        helpers.call_action('organization_purge', id=self.o1['id'])

    def get_or_create_org(self, title):
        name = title.lower().replace(' ', '-')
        try:
            org = helpers.call_action("organization_create", 
                                      title=title,
                                      context=self.context,
                                      name=name,
                                      state='active',
                                      approval_status='approved')
            
        except ValidationError, e:
            if 'already exists in database' not in str(e):
                raise
            else:
                org = helpers.call_action("organization_show", id=name, context=self.context)
        
        print 'Org name:{} id:{} type:{} is_org: {}'.format(org['name'], org['id'], org['type'], org['is_organization'])

        # see what happened
        org_readed = helpers.call_action("organization_show", context=self.context, id=name)
        print('  - Validating {} {}'.format(org_readed['name'], org_readed['id']))
        assert org_readed['name'] == name
        assert org_readed['id'] == org['id']

        return org_readed

    def get_or_create_harvest_source(self, title, org, url, source_type='siu_transp', config={}):

        name = title.lower().replace(' ', '-')
        sconfig =json.dumps(config, indent=4)
        
        try:
            pkg = helpers.call_action(
                "harvest_source_create", context=self.context, name=name, 
                title=title, owner_org=org['name'], url=url, 
                source_type=source_type, config=sconfig)
        except Exception, e:
            pkg = helpers.call_action(
                "harvest_source_update", context=self.context, name=name,
                title=title, owner_org=org['name'], url=url, 
                source_type=source_type, config=sconfig)
            
        pkg_readed = helpers.call_action("harvest_source_show", context=self.context, id=name)
        print('  - Validating \n\tname {}={} \n\tid {} \n\towner {}'.format(name, pkg_readed['name'], pkg_readed['id'], pkg_readed['owner_org']))
        assert pkg_readed['name'] == name
        assert pkg_readed['owner_org'] == org['id']

        return pkg_readed
