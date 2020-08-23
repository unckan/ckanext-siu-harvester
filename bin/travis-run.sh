#!/bin/sh -e

echo "NO_START=0\nJETTY_HOST=127.0.0.1\nJETTY_PORT=8983\nJAVA_HOME=$JAVA_HOME" | sudo tee /etc/default/jetty
sudo cp ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml
sudo service jetty restart

nosetests --ckan \
          --debug=ckanext.siu_harvester \
          --with-pylons=subdir/test.ini \
          ckanext/siu_harvester/tests


# local test inside docker 
# docker-compose -f docker-compose.yml -f docker-compose-dev.yml exec ckan bash
# cd src_extensions/ckanext-siu-harvester/
# pip install -r dev-requirements.txt
# nosetests --ckan --nologcapture --with-pylons=test.ini ckanext/siu_harvester/tests