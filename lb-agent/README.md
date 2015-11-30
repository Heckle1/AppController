# lb-agent
This program is an agent who runs on a VM with an haproxy load balancer.
It waits for incoming HTTP requests that contains HAPROXY configuration file in parameter then tt rewrites the Haproxy configuration then it reload the Haproxy service.


# Setup haproxy
Install haproxy via your system package manager.


# Python requirements
You need to install bottle (http://bottlepy.org/docs/dev/index.html)
pip install bottle==0.12.9


# lb-agent configuration
You might have to configure lb-agent parameters. Note: If you are running on centos6 or centos7 you should not have to change the configuration.
Edit lb-agent/lb-agent.py file to configure Bottle and Haproxy.


# Setup the supervisord
- Install supervisord (via system package manager or via pip).
- Edit (if needed) then copy etc/supervisord.d/lb-agent.ini in /etc/supervisord.d/lb-agent.ini
- Run $>supervisorctl and run "reread" command. Check lb-agent service status then you can leave supervisorctl prompt.

