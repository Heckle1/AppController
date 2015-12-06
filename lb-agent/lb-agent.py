#-*- coding:utf-8 -*-
"""
Haproxy controller.
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
from socket import SOCK_STREAM, AF_UNIX, socket
import ConfigParser
import shutil
import logging
import subprocess
import time
import StringIO
import csv

# -------- DEBUG CONFIGURATION -----
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# -------- Configurtion file path ------------
CONFIGURATION_FILE = './lb-agent.cfg'

# -------- Logging setup ------------
LOGGER = logging.getLogger(__name__)

# -------- global variables ------------
load_balancer = None


class HaError(RuntimeError):
    """
    Generic class for Haproxy errors
    """
    pass


class Haproxy(object):
    """
    Manage haproxy service.
    """

    def __init__(self, configuration_path, default_backend, socket_path='/var/lib/haproxy/stats', buffer_size=4096, socket_timeout=5, systemv_init_path=None, systemd_service_name=None):
        """
        :param configuration_path: path to haproxy configuration file
        :type configuration_path: str
        :param default_backend: name of the backend (# pxname in haproxy configuration file)
        :type default_backend: str
        :param socket_path: path to haproxy unix socket
        :type socket_path: str
        :param buffer_size: buffer size used to communicate with haproxy unix socket
        :type buffer_size: int
        :param socket_timeout: timeout for haproxy unix socket
        :type socket_timeout: int
        :param systemv_init_path: haproxy init file path used by systemV systems
        :type systemv_init_path: str
        :param systemd_service_name: haproxy service name used by systemd
        :type systemd_service_name: str

        """
        self.configuration_path = configuration_path
        self.backend_name = default_backend
        self.systemv_init_path = systemv_init_path
        self.systemd_service_name = systemd_service_name
        self.socket_path = socket_path
        self.buffer_size = buffer_size
        self.socket_timeout = socket_timeout
        self.sock = None
        if not systemv_init_path and not systemd_service_name:
            raise HaError('No haproxy daemon control configured. Please setup systemv_init_path or systemd_service_name in your {0} configuration file'.format(CONFIGURATION_FILE))

    def __connect_socket(self):
        """
        Connection to haproxy unix socket
        """
        self.sock = socket(AF_UNIX, SOCK_STREAM)
        self.sock.connect(self.socket_path)
        self.sock.settimeout(self.socket_timeout)
        logging.debug('Connection to %s', self.socket_path)

    def __send_cmd(self, cmd):
        """
        Send command to haproxy socket
        :param cmd: haproxy command
        :type cmd: str
        """
        try:
            self.__connect_socket()
        except Exception as e:
            logging.error('Can not connect to haproxy socket %s. Reason: %s', self.socket_path, str(e))
            raise

        res = ''
        try:
            self.sock.send(cmd + '\n')
        except Exception as e:
            self.sock.close()
            logging.error('Can not send message to haproxy on %s because %s', self.socket_path, str(e))
            raise

        time.sleep(0.2)  # Protection again any latency with socket communication
        try:
            output = self.sock.recv(self.buffer_size)

            while output:
                res += output
                output = self.sock.recv(self.buffer_size)
        except Exception as e:
            logging.error('Can not send message to haproxy on %s because %s', self.socket_path, str(e))
            raise

        self.sock.close()
        return res

    def __write_configuration(self, request, configuration):
        """Erase Haproxy configuration with configuration
        :param request: Bottle request object
        :type request: bottle.request
        :param configuration: Contains Haproxy configuration file
        :type configuration: StringIO
        :returns: None
        """
        # Write the new haproxy configuration file
        with open(self.configuration_path, 'w') as fi:
            shutil.copyfileobj(configuration, fi)
        logging.info('New haproxy configuration file: done')

    def __reload_haproxy_configuration(self):
        """
        Reload HAPROXY service via /etc/init.d/haproxy or via sytemctl
        :raises subprocess.CalledProcessError:
        :returns: Boolean
        """
    	# Reload HAPROXY process
    	logging.info('Reloading haproxy...')
        if self.systemv_init_path:
            subprocess.check_call([self.configuration_path, 'reload'])
            logging.info('...Haproxy reloaded with success!')
            return True

        if self.systemd_service_name:
            subprocess.check_call(['service', 'haproxy', 'reload'])
            logging.info('...Haproxy reloaded with success!')
            return True

        return False


    def reload_haproxy(self):
        """
        Bottle API Method waiting for a request to replace haproxy configuration file
        then reload Haproxy service
        :returns: Boolean
        """
        logging.info('[Reload Haproxy configuration]')
        try:
            self.__write_configuration(request, request.body)
        except:
            return False
        time.sleep(0.1)
        try:
            self.__reload_haproxy_configuration()
        except Exception as err:
            logging.error('Can not reload Haproxy daemon because {0}'.format(err))
            return False
        return True

    def get_backends_state(self):
        """
        Get stats from loadbalancer and parse it.
        Backends MUST BE configured under "scaling_nodes" pxname in haproxy configuration file
        :returns: dict {'loadbalancername': '', 'instances': [{}, {}, {}]}
                _instances_: type list: of dict representing each back end {'instanceid': <backend_instance_id>, 'state': <InService|OutOfService|Unknown>, 'reasoncode': 'instance'}
        """
        logging.debug('get_stats function')
        output = self.__send_cmd('show stat')
        f = StringIO.StringIO(output)
        reader = csv.DictReader(f)
        logging.debug('Haproxy response %s', output)

        instances_stats = []

        for row in reader:
            if row.get("# pxname") == self.backend_name and row.get('svname') and row['svname'].startswith('i-'):
                instances_stats.append({'description': row.get('last_chk', None),
                                        'instance_id': row.get('svname', None),
                                        'state': row.get('status', None)})

        f.close()
        return instances_stats


def haproxy_controller_configuration():
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

@route('/reloadHaproxy', method='POST')
def reload_haproxy():
    """
    API call to reload haproxy configuration
    """
    global load_balancer

    if load_balancer.reload_haproxy() is True:
        return {"success": True, "message": "Haproxy up to date"}
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
    logging.info('Haproxy controller says HELLO !')

    config, systemv_init_path, systemd_service_name = haproxy_controller_configuration()

    # ------- Haproxy controller -------
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

    logging.info('Haproxy controller says GOODBYE !')
