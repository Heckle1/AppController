"""
Load Balancer Controller.
Communicate with lb-agent via HTTP
"""
import requests
import logging

# -------- Logging setup ------------
LOGGER = logging.getLogger(__name__)


class LoadBalancerController(object):

    def __init__(self, lbagent_address, lbagent_port, configuration_template_path):
        """
        :param lbagent_address: lb-agent dns name or ip
        :param lbagent_address: str
        :param lbagent_port: lb-agent port number
        :param lbagent_port: str
        :param configuration_template: path to the load balancer template file
        :param configuration_template: str
        """
        self.lbagent_url = '{0}:{1}'.format(lbagent_address, lbagent_port)
        with open(configuration_template_path, 'r') as fi:
            self.load_balancer_template = fi.readlines()

    def __update_config(self, nodes):
        """
        Update load balancer configuration by sending the whole load balancer config
        """
        try:
            resp = requests.post('http://{0}/reload'.format(self.lbagent_url),
                                 data=self.__build_configuration(nodes)
            ).json()
        except Exception as err:
            logging.error('Can not contact load balancer at {0} because :{1}'.format(self.lbagent_url,
                                                                                   err))
            return False
        if resp.get('success') is False:
            logging.error('Load balancer can be reached, but can not reload load balancer configuration because {0}'.format(resp['success']))
            return False
        logging.info('Load balancer configuration reload with success!')
        return True

    def __build_configuration(self, nodes):
        """
        :param nodes: Nodes collection
        :type nodes: Nodes collection
        :returns: haproxy configuration file updated with nodes
        """
        raise NotImplementedError()

    def __update_backends_lbstate(self, nodes):
        """
        Update nodes state information on load balancer via lb-agent
        :param nodes: Nodes collection
        :type nodes: Nodes collection
        """
        raise NotImplementedError()

    def reload(self, nodes):
        """
        Reload haproxy configuration and each node status as backend in haproxy
        :param nodes: Nodes collection
        :type nodes: Nodes collection
        """
        self.__update_backends_lbstate(nodes)
        self.__update_config(nodes)


class HaproxyController(object):

    def __init__(self, lbagent_address, lbagent_port, configuration_template):
        LoadBalancerController.__init__(lbagent_address, lbagent_port, configuration_template)

    def __build_configuration(self, nodes):
        """
        Build Haproxy configuration. Each node is a single line in the Haproxy configuration.
        Pattern for each node in haproxy configuartion file:
            server <node_name> <node_address>:<node_port> option
        As you can see, haproxy option used is 'check'.
        """
        return self.configuration_template + '\n'.join('server {0} {1}:{2} check'.format(node.name, node.address, node.port) for node in nodes)

    def __update_backends_lbstate(self, nodes):
        """
        Update node informations based on haproxy information about its backends
        """
        resp = requests.post('http://127.0.0.1:6666/getBackends')
        node = []
        for backend in resp.json()['message']:
            # if backend['instance_id'] node match node.instance_id:
            if backend['state'] == 'UP':
                node.setup_backend_up()
            elif backend['state'] == 'DOWN':
                node.setup_backend_down()
            else:
                node.setup_backend_unkown()

            node.lb_description = backend['description']
            # TODO: Update nodes
