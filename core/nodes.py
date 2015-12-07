"""
Nodes class represent the current existings scalable nodes
Node communicate with SCM API
"""

import requests
import logging

# -------- SCM API version ------------
SCM_API_VERSION = '0.1'

# -------- Logging setup ------------
LOGGER = logging.getLogger(__name__)


class NodeErr(object):
    """
    Generic error class for Node errors
    """


class Node(object):
    """
    Node class
    """

    def __init__(self, instance_id, address, port):
        """
        :param instance_id: node instance_id
        :type instance_id: str
        :param address: scm node address
        :type address: str
        :param port: scm node port
        :param type: str
        """
        self.instance_id = instance_id
        self.address = address
        self.port = port
        self.lb_state = 'UNKOWN'
        self.lb_description = ''
        self.cpu_load = -1
        self.ram_load = -1
        logging.debug('New node created')
        self.update()

    def setup_backend_up(self):
        logging.info('Setup node {0} to state UP'.format(self.instance_id))
        self.lb_state = 'UP'

    def set_backend_down(self):
        logging.info('Setup node {0} to state DOWN'.format(self.instance_id))
        self.lb_state = 'DOWN'

    def set_backend_unkown(self):
        logging.info('Setup node {0} to state UNKOWN'.format(self.instance_id))
        self.lb_state = 'UNKOWN'

    def update(self):
        """
        Call node to get its current load
        :returns: boolean
        """
        try:
            resp = requests.post('http://{0}:{1}/api/v{2}/all/usage'.format(self.address, self.port, SCM_API_VERSION)).json()
            self.cpu_load = resp['cpu']
            self.ram_load = resp['ram']
        except Exception as err:
            logging.error('Can not update node {0} information because: {1}'.format(self.instance_id, err))
            return False
        logging.debug('Node {0} with cpu={0} and ram={1}'.format(self.cpu_load, self.ram_load))
        return True


class Nodes(object):
    """
    Nodes collection
    """

    def __init__(self):
        self.nodes = []


    def add_node(self, instance_id, address, port):
        """
        Add a node
        :param : node instance_id used in load balancer configuration
        :type : str
        :param : node url or ip to be used by the load balancer
        :type : str
        :param : node port to be used by the load balancer
        :type : str
        """
        self.append(Node(instance_id, address, port))

    def remove_node(self, instance_id):
        """
        :param instance_id: node instance_id
        :type instance_id: str
        Remove a node by its instance_id
        """
        node = [node for node in self.nodes if node.instance_id == instance_id]
        if not node:
            logging.warning('Can not remove node {0}'.format(instance_id))
            raise NodeErr('No {0} known'.format(instance_id))

    def update_nodes_status(self):
        """
        Each node is called to get its state
        """
        for node in self.nodes:
            node.update()
