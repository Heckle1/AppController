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

    def __init__(self, name, address, port):
        """
        :param name: node name
        :type name: str
        :param address: scm node address
        :type address: str
        :param port: scm node port
        :param type: str
        """
        self.name = name
        self.address = address
        self.port = port
        self.cpu_load = -1
        self.ram_load = -1
        logging.debug('New node created')
        self.update()

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
            logging.error('Can not update node {0} information because: {1}'.format(self.name, err))
            return False
        logging.debug('Node {0} with cpu={0} and ram={1}'.format(self.cpu_load, self.ram_load))
        return True


class Nodes(object):
    """
    Nodes collection
    """

    def __init__(self):
        self.nodes = []


    def add_node(self, name, address, port):
        """
        Add a node
        :param : node name used in load balancer configuration
        :type : str
        :param : node url or ip to be used by the load balancer
        :type : str
        :param : node port to be used by the load balancer
        :type : str
        """
        self.append(Node(name, address, port))

    def remove_node(self, name):
        """
        :param name: node name
        :type name: str
        Remove a node by its name
        """
        node = [node for node in self.nodes if node.name == name]
        if not node:
            logging.warning('Can not remove node {0}'.format(name))
            raise NodeErr('No {0} known'.format(name))

    def update_nodes_status(self):
        """
        Each node is called to get its state
        """
        for node in self.nodes:
            node.update()
