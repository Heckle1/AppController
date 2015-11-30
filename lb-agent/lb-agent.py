#-*- coding:utf-8 -*-
"""
Haproxy controller.
This service waits for a HTTP request request on:
        url: http://this-machine-address/reloadHaproxy
        in: POST Method
        with: Haproxy configuration file in the HTTP request body

requires:
    pip install bottle
"""
from bottle import route, run, request
import shutil
import logging
import subprocess
import time
import os

# -------- Bottle API Parameters ------------
API_HOST = '0.0.0.0'
API_PORT = 6666

# --------- HAPROXY Parameters -------------
HAPROXY_CONFIG_FILE = "/etc/haproxy/haproxy.cfg"
HAPROXY_INIT_SCRIPT = "/etc/init.d/haproxy"

LOGGER = logging.getLogger(__name__)


def __write_configuration(request, configuration):
    """Erase Haproxy configuration with configuration
    :param request: Bottle request object
    :type request: bottle.request
    :param configuration: Contains Haproxy configuration file
    :type configuration: StringIO
    :returns: None
    """
    # Write the new haproxy configuration file
    with open(HAPROXY_CONFIG_FILE, 'w') as fi:
        shutil.copyfileobj(configuration, fi)
    logging.info('New haproxy configuration file: done')

def __reload_haproxy_configuration():
    """
    Reload HAPROXY service via /etc/init.d/haproxy or via sytemctl
    :raises subprocess.CalledProcessError:
    :returns: None
    """
    # Reload HAPROXY process
    logging.info('Reloading haproxy...')
    try:
        if os.path.isfile(HAPROXY_INIT_SCRIPT):
            subprocess.check_call([HAPROXY_INIT_SCRIPT, 'reload'])
        else:
            subprocess.check_call(['service', 'haproxy', 'reload'])
    except subprocess.CalledProcessError as err:
        logging.error('Can not reload haproxy process because : {0}'.format(err))
    except OSError as err:
        logging.error('Can not reload haproxy process because : {0}\nPlease verify haproxy is present in systemctl or /etc/init.d/haproxy'.format(err))
    else:
        logging.info('...Haproxy reloaded with success!')

@route('/reloadHaproxy', method='POST')
def reload_haproxy():
    """
    Bottle API Method waiting for a request to replace haproxy configuration file
    then reload Haproxy service
    :raises subprocess.CalledProcessError:
    :returns: None
    """
    logging.info('[Reload Haproxy configuration]')
    __write_configuration(request, request.body)
    time.sleep(0.1)
    __reload_haproxy_configuration()

if __name__ == '__main__':
    """
    Listen with bottle
    """
    logging.info('Haproxy controller says HELLO !')
    run(host=API_HOST, port=API_PORT)
    logging.info('Haproxy controller says GOODBYE !')
