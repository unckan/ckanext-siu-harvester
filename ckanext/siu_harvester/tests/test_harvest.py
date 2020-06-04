"""Tests for plugin.py."""
import logging
import json
from mock import patch
import mock_siutransp_source
from random import randint

import ckan.logic as logic
import ckan.model as model
import ckan.plugins as p
from ckan.logic import NotFound, ValidationError
from ckanext.harvest.model import HarvestObject, HarvestSource, HarvestJob
import ckanext.harvest.queue as queue


log = logging.getLogger(__name__)


class TestSIUHarvester:

    def test_harvest(self):
        
        # make sure queues/exchanges are created first and are empty
        consumer = queue.get_gather_consumer()
        consumer_fetch = queue.get_fetch_consumer()
        consumer.queue_purge(queue=queue.get_gather_queue_name())
        consumer_fetch.queue_purge(queue=queue.get_fetch_queue_name())

        context = {'model': model, 'session': model.Session,
                   'user': self.user['name'], 'api_version': 3,
                   'ignore_auth': True}

        job_create_f = logic.get_action('harvest_job_create')
        data = {'source_id': self.harvest_source['id'], 'run': True}
        harvest_job = job_create_f(context, data)
        job_id = harvest_job['id']

        assert harvest_job['status'] == u'Running'

        job_show_f = logic.get_action('harvest_job_show')
        data = {'id': job_id}
        jobsh = job_show_f(context, data)
        assert jobsh['status'] == u'Running'

        # pop on item off the queue and run the callback
        reply = consumer.basic_get(queue='ckan.harvest.gather')
        log.info('Gather consumer {}'.format(reply))

        # source = HarvestSource.get(self.harvest_source['id'])
        job = HarvestJob.get(job_id)

        queue.gather_callback(consumer, *reply)
        all_objects = model.Session.query(HarvestObject) \
            .filter_by(job=job) \
            .all()

        log.info('all_objects 01 {}: {}'.format(len(all_objects), all_objects))
        assert len(all_objects) == 6
        for r in range(0, 6):
            log.info(' - HObjects 01: {}: {}'.format(all_objects[r].guid, all_objects[r].content))
            assert all_objects[r].state == 'WAITING'
        
        for _ in range(0, 6):
            reply = consumer_fetch.basic_get(queue='ckan.harvest.fetch')
            queue.fetch_callback(consumer_fetch, *reply)
        
        count = model.Session.query(model.Package) \
            .filter(model.Package.type == 'dataset') \
            .count()
        
        log.info('datasets 01 {}: {}'.format(len(all_objects), all_objects))
        assert count == 6
        all_objects = model.Session.query(HarvestObject) \
            .filter_by(job=job) \
            .all()

        assert len(all_objects) == 6
        for r in range(0, 6):
            log.info('HObjects 02: {}: {}'.format(all_objects[r].guid, all_objects[r].content))
            assert all_objects[r].state == 'COMPLETE'
            assert all_objects[r].report_status == 'added'
        
        # fire run again to check if job is set to Finished
        logic.get_action('harvest_jobs_run')(
            context,
            {'source_id': self.harvest_source['id']}
        )

        harvest_job = logic.get_action('harvest_job_show')(
            context,
            {'id': job_id}
        )

        assert harvest_job['status'] == u'Finished'
        assert harvest_job['stats'] == {'added': 6, 'updated': 0, 'not modified': 0, 'errored': 0, 'deleted': 0}

        harvest_source_dict = logic.get_action('harvest_source_show')(
            context,
            {'id': self.harvest_source['id']}
        )

        assert harvest_source_dict['status']['last_job']['stats'] == {
            'added': 6, 'updated': 0, 'not modified': 0, 'errored': 0, 'deleted': 0}
        assert harvest_source_dict['status']['total_datasets'] == 6
        assert harvest_source_dict['status']['job_count'] == 1

        # Second run
        harvest_job = logic.get_action('harvest_job_create')(
            context,
            {'source_id': self.harvest_source['id'], 'run': True}
        )

        job_id = harvest_job['id']
        assert logic.get_action('harvest_job_show')(
            context,
            {'id': job_id}
        )['status'] == u'Running'

        # pop on item off the queue and run the callback
        reply = consumer.basic_get(queue='ckan.harvest.gather')
        queue.gather_callback(consumer, *reply)

        all_objects = model.Session.query(HarvestObject) \
            .filter_by(job=job) \
            .all()

        log.info('all_objects 02 {}: {}'.format(len(all_objects), all_objects))
        for r in range(0, len(all_objects)):
            log.info('HObjects 02: {}'.format(all_objects[r].guid))
        
        assert len(all_objects) == 6

        for r in range(0, 6):
            reply = consumer_fetch.basic_get(queue='ckan.harvest.fetch')
            queue.fetch_callback(consumer_fetch, *reply)
        
        count = model.Session.query(model.Package) \
            .filter(model.Package.type == 'dataset') \
            .count()
        assert count == 6

        all_objects = model.Session.query(HarvestObject) \
            .filter_by(job=job) \
            .filter_by(report_status='added') \
            .all()
        assert len(all_objects) == 6

        all_objects = model.Session.query(HarvestObject) \
            .filter_by(job=job) \
            .filter_by(report_status='updated') \
            .all()
        assert len(all_objects) == 0

        all_objects = model.Session.query(HarvestObject) \
            .filter_by(job=job) \
            .filter_by(report_status='deleted') \
            .all()
            
        assert len(all_objects) == 0

        # run to make sure job is marked as finshed
        logic.get_action('harvest_jobs_run')(
            context,
            {'source_id': self.harvest_source['id']}
        )

        harvest_job = logic.get_action('harvest_job_show')(
            context,
            {'id': job_id}
        )

        # If you run 2 times, it updates all
        assert harvest_job['stats']['added'] in [0, 6]
        assert harvest_job['stats']['updated'] in [0, 6] 
        assert harvest_job['stats']['not modified'] in [0, 6]
        assert harvest_job['stats']['errored'] == 0
        assert harvest_job['stats']['deleted'] == 0

        harvest_source_dict = logic.get_action('harvest_source_show')(
            context,
            {'id': self.harvest_source['id']}
        )

        # If you run 2 times, it updates all
        assert harvest_source_dict['status']['last_job']['stats']['added'] in [0, 6]
        assert harvest_source_dict['status']['last_job']['stats']['updated'] in [0, 6] 
        assert harvest_source_dict['status']['last_job']['stats']['not modified'] in [0, 6]
        assert harvest_source_dict['status']['last_job']['stats']['errored'] == 0
        assert harvest_source_dict['status']['last_job']['stats']['deleted'] == 0
        assert harvest_source_dict['status']['total_datasets'] == 6
        # assert harvest_source_dict['status']['job_count'] == 1

            
    @classmethod
    def setup_class(cls):
        
        # start mock server
        mock_siutransp_source.serve()

        if not p.plugin_loaded('siu'):
            log.info("Loading plugin")
            p.load('siu')
        
    def setup(self):
        self.context = {"model": model, "session": model.Session, "ignore_auth": True}
        self.user = logic.get_action('get_site_user')(self.context, {})
        self.context['user'] = self.user['name']

        self.org = self.get_or_create_org(title='Organization test')
        
        self.harvest_source = self.get_or_create_harvest_source(
            title='SIU harvest test',
            org=self.org,
            url='http://127.0.0.1:{}/pentaho/plugin/cda/api/doQuery'.format(mock_siutransp_source.PORT),
            source_type='siu_transp',
            config={'username': 'user', 'password': 'pass'}
        )
        
    def teardown(self):
        self.clean()
    
    @classmethod
    def teardown_class(cls):

        log.info("Unloading plugin")
        p.unload('siu')
    
    def clean(self):
        log.info('Clean test data')
        
        ctx = self.context.copy()
        ctx['clear_source'] = True
        logic.get_action("harvest_source_delete")(context=ctx, data_dict={'id': self.harvest_source['id']})

        log.info('Deleting ORG: {}'.format(self.org['title']))
        logic.get_action('organization_purge')(context=self.context, data_dict={'id': self.org['id']})

    def get_or_create_org(self, title):
        name = title.lower().replace(' ', '-')
        data = {
            'title':title,
            'context': self.context,
            'name': name,
            'state': 'active',
            'approval_status': 'approved'
        }
        try:
            org = logic.get_action("organization_create")(self.context, data_dict=data)
            
        except ValidationError, e:
            if 'already exists in database' not in str(e):
                raise
            else:
                org = logic.get_action("organization_show")(context=self.context, data_dict={'id': name})
        
        log.info('Org name:{} id:{} type:{} is_org: {}'.format(org['name'], org['id'], org['type'], org['is_organization']))

        # see what happened
        org_readed = logic.get_action("organization_show")(context=self.context, data_dict={'id': name})
        log.info('  - Validating {} {}'.format(org_readed['name'], org_readed['id']))
        assert org_readed['name'] == name
        assert org_readed['id'] == org['id']

        return org_readed

    def get_or_create_harvest_source(self, title, org, url, source_type='siu_transp', config={}):

        name = title.lower().replace(' ', '-')
        sconfig =json.dumps(config, indent=4)
        
        hscf = logic.get_action('harvest_source_create')
        data = {'name': name,  'title': title, 'owner_org': org['id'],
                'url': url, 'active': True,  'source_type': source_type,
                'config': sconfig, 'status': 'active'}
        try:
            hscf(context=self.context, data_dict=data)
        except Exception, e:
            log.error('Error creating harvest source {}'.format(e))
        
        hssf = logic.get_action('harvest_source_show')
        data = {'url': url}
        log.info('HS show {}'.format(data))
        pkg_readed = hssf(context=self.context, data_dict=data)
        log.info('  - Validating \n\tname {}={} \n\tid {} \n\towner {}={}'.format(
            name, 
            pkg_readed['name'], 
            pkg_readed['id'], 
            pkg_readed['owner_org'], 
            org['id']))
        assert pkg_readed['name'] == name
        assert pkg_readed['owner_org'] == org['id']

        return pkg_readed
