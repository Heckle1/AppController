# lb-agent
This program is an agent who runs on a VM with an haproxy load balancer.
It waits for incoming HTTP requests that contains HAPROXY configuration file in parameter then tt rewrites the Haproxy configuration then it reload the Haproxy service.


# Setup haproxy
Install haproxy via your system package manager.


# Python requirements
You need to install bottle (http://bottlepy.org/docs/dev/index.html)
pip install bottle==0.12.9


# lb-agent configuration
Please configure lb-agent with lb-agent.cfg file

* Configuration explanation
  - default_backend: is the name of your backend which contains scaling nodes in haproxy configuration file
  - socket_path: file path to haproxy unix socket (must be the same as you haproxy configuration file)
 You also must choose the way the lb-agent reloads the haproxy daemon. Only one of those options is needed.
  - systemv_init_path: file path to the haproxy init.d file when you are in a system V system
  - sytemd_service_name: service name used by systemd for haproxy



# Setup the supervisord
- Install supervisord (via system package manager or via pip).
- Edit (if needed) then copy etc/supervisord.d/lb-agent.ini in /etc/supervisord.d/lb-agent.ini
- Run "$>supervisorctl reread" then "$>supervisorctl start lb-agent"
- Done
