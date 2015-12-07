#-*- coding:utf-8 -*-
"""
Load Balancer agent.
This agent receive HTTP messages and
This service waits for a HTTP request request on:
        url: http://this-machine-address/reloadHaproxy
        in: POST Method
        with parameter: Haproxy configuration file in the HTTP request body
#
        url: http://this-machine-address/getBackends
        in: POST Method
        with parameter: no parameters

requires:
    pip install bottle
"""
from bottle import route, run, request
from haproxy_controller import Haproxy
import ConfigParser
import logging

# -------- DEBUG CONFIGURATION -----
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# -------- Configurtion file path ------------
CONFIGURATION_FILE = './lb-agent.cfg'

# -------- Logging setup ------------
LOGGER = logging.getLogger(__name__)

# -------- global variables ------------
load_balancer = None


def load_haproxy_configuration():
    """
    Load haproxy configuration file CONFIGURATION_PATH and returns configuration
    :raises: HaError when neither haproxy systemV file of systemd name is configured
    """
    # ----------- Loading configuration -----
    config = ConfigParser.ConfigParser(allow_no_value=True)
    config.read(CONFIGURATION_FILE)

    # -- Looking for system V or systemd daemon
    systemv_init_path = None
    systemd_service_name = None
    try:
        systemv_init_path = config.get('haproxy', 'systemv_init_path')
        if systemv_init_path == '':
            raise ConfigParser.NoOptionError()
    except ConfigParser.NoOptionError:
        logging.info('No "systemv_init_path" configured.')
        try:
            systemd_service_name = config.get('haproxy', 'systemd_service_name')
        except ConfigParser.NoOptionError:
            logging.info('No "systemd_service_name" configured.')
        else:
            logging.info('systemv_init_path {0} will be used'.format(systemd_service_name))
    else:
        logging.info('systemv_init_path {0} will be used'.format(systemv_init_path))
    return config, systemv_init_path, systemd_service_name

@route('/reload', method='POST')
def reload():
    """
    API call to reload Load balancer configuration
    """
    global load_balancer

    if load_balancer.reload(request.body) is True:
        return {"success": True, "message": "Load Balancer up to date"}
    return {"success": False, "error": "Can not write haproxy configuration"}

@route('/getBackends', method='POST')
def get_backends():
    """
    API Call returns list of backends with their state
    :returns: Boolean
    """
    global load_balancer
    try:
        backends = load_balancer.get_backends_state()
    except:
        {"success": False, "error": "Can get haproxy backends"}
    return {"success": True, "message": backends}

if __name__ == '__main__':
    """
    Listen with bottle
    """
    logging.info('Load Balancer controller says HELLO !')

    config, systemv_init_path, systemd_service_name = load_haproxy_configuration()

    # ------- Load Balancer controller -------
    # Haproxy is used here
    load_balancer = Haproxy(config.get('haproxy', 'config_file_path'),
                            config.get('haproxy', 'default_backend'),
                            config.get('haproxy', 'socket_path'),
                            config.getint('haproxy', 'socket_buffer_size'),
                            config.getint('haproxy', 'socket_timeout'),
                            systemv_init_path=systemv_init_path,
                            systemd_service_name=systemd_service_name)


    # -------- API run -------------
    run(host=config.get('lb-agent', 'host'),
        port=config.getint('lb-agent', 'port'))

    logging.info('Load Balancer controller says GOODBYE !')
