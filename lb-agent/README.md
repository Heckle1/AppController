# lb-agent
This program is an agent who runs on a VM with an haproxy load balancer.
It waits for incoming HTTP requests :
- reload haproxy: (/reloadHaproxy) send a request that contains HAPROXY configuration file in parameter then tt rewrites the Haproxy configuration then it reload the Haproxy service.
- get backends status: (/getBackends) send a request with no parameters

## Setup lb-agent
Please configure lb-agent with lb-agent.cfg file

* Configuration explanation
  - default_backend: is the name of your backend which contains scaling nodes in haproxy configuration file
  - socket_path: file path to haproxy unix socket (must be the same as you haproxy configuration file)
 You also must choose the way the lb-agent reloads the haproxy daemon. Only one of those options is needed.
  - systemv_init_path: file path to the haproxy init.d file when you are in a system V system
  - sytemd_service_name: service name used by systemd for haproxy


# Setup haproxy
Install haproxy via your system package manager.


# Python requirements
You need to install bottle (http://bottlepy.org/docs/dev/index.html)
pip install bottle==0.12.9



# Setup the supervisord
- Install supervisord (via system package manager or via pip).
- Edit (if needed) then copy etc/supervisord.d/lb-agent.ini in /etc/supervisord.d/lb-agent.ini
- Run "$>supervisorctl reread" then "$>supervisorctl start lb-agent"
- Done



# How to send a request to the lb-agent ?
## To get backends status
import requests
resp = requests.post('http://127.0.0.1:6666/getBackends')
print resp.json()


## How to reload haproxy configuration ?
import requests

HAPROXY_TEMPLATE = """\
global
    log         127.0.0.1 local2
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     4000
    user        haproxy
    group       haproxy
    daemon

    stats socket /var/lib/haproxy/stats

defaults
    mode                    http
    log                     global
    option                  httplog
    option                  dontlognull
    option http-server-close
    option forwardfor       except 127.0.0.0/8
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m
    timeout server          1m
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 300


frontend  main *:5000
    default_backend             scaling_nodes


#---------------------------------------------------------------------
# round robin balancing between the various backends
#---------------------------------------------------------------------
backend scaling_nodes
    balance     roundrobin
"""


HAPROXY_TEMPLATE = '\n'.join([HAPROXY_TEMPLATE,
                              'server  node1 127.0.0.1:8081 check',
                              'server  node2 127.0.0.1:8081 check',
                              'server  node3 127.0.0.1:5004 check',
                              '\n'])

resp = requests.post('http://127.0.0.1:6666/getBackends', data=HAPROXY_TEMPLATE)
print resp.json()
