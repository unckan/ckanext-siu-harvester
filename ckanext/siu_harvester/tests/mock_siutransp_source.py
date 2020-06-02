from __future__ import print_function

import json
import logging
import os
import pkg_resources
import SimpleHTTPServer
import SocketServer
from threading import Thread

log = logging.getLogger("harvester")
PORT = 8971

class MockRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_POST(self, *args, **kwargs):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length)
        
        query_components = dict(qc.split("=") for qc in post_data.split("&"))
        log.info('POST mock at: {}\n\t{}\n\t{}'.format(self.path, self.headers, query_components))
        
        self.test_name = None
        self.sample_json_file = None

        path = query_components.get('path')
        if path.find('5_academica.cda') > 0:
            anio = query_components['paramprm_ej_academ']
        elif path.find('1_presupuesto.cda') > 0:
            anio = query_components['paramprm_ej_presup']
        else:
            raise Exception('Unknown source {}'.format(path))

        log.info('POST anio {}'.format(anio))

        if anio == '2018':
            self.sample_json_file = '2018.json'
            self.test_name = '2018'
        elif anio == '2019':
            self.sample_json_file = '2019.json'
            self.test_name = '2019'
        elif anio == '2020':
            self.sample_json_file = '2020.json'
            self.test_name = '2020'
        elif anio in ['2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010', '2009']:
            self.sample_json_file = '2010.json'
            self.test_name = '2010'
        elif anio == '404':
            self.test_name = 'e404'
            self.respond('Not found', status=404)
        elif anio == '500':
            self.test_name = 'e500'
            self.respond('Error', status=500)

        if self.sample_json_file is not None:
            log.info('return json file {}'.format(self.sample_json_file))
            self.respond_json_sample_file(file_path=self.sample_json_file)

        if self.test_name is None:
            self.respond('Mock DataJSON doesnt recognize that call', status=400)

    def respond_json(self, content_dict, status=200):
        return self.respond(json.dumps(content_dict), status=status,
                            content_type='application/json')

    def respond_json_sample_file(self, file_path, status=200):
        pt = pkg_resources.resource_filename(__name__, "/sample_responses/{}".format(file_path))
        data = open(pt, 'r')
        content = data.read()
        log.info('mock respond {}'.format(content[:90]))
        return self.respond(content=content, status=status,
                            content_type='application/json')

    def respond(self, content, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        self.wfile.write(content)
        self.wfile.close()


def serve(port=PORT):
    '''Runs a CKAN-alike app (over HTTP) that is used for harvesting tests'''

    class TestServer(SocketServer.TCPServer):
        allow_reuse_address = True

    httpd = TestServer(("", PORT), MockRequestHandler)

    info = 'Serving test HTTP server at port {}'.format(PORT)
    print(info)
    log.info(info)

    httpd_thread = Thread(target=httpd.serve_forever)
    httpd_thread.setDaemon(True)
    httpd_thread.start()
