#!/usr/bin/env python

import time
import os

from novaclient.v2 import client
from functions import *
from credentials import get_nova_creds
creds = get_nova_creds()
nova = client.Client(**creds)

ssh_pub_key = os.path.expanduser('~/.ssh/id_rsa.pub')
ssh_prv_key = os.path.expanduser('~/.ssh/id_rsa')

class Error(Exception):
	pass

# See if our ssh keypair is already uploaded
keypair = None
avail_keypairs = nova.keypairs.list()
for cur_keypair in avail_keypairs:
	if cur_keypair.id == 'matthias-mbp':
		keypair = cur_keypair

# Upload ssh keypair if necessary
if keypair is None:
	f = open(ssh_pub_key,'r')
	publickey = f.readline()[:-1]
	keypair = nova.keypairs.create('matthias-mbp',publickey)
	f.close()

print 'Keypair "' + keypair.name + '" is properly configured'

# Check the list of floating ips
ips = nova.floating_ips.list()
for cur_ip in ips:
	if cur_ip.instance_id is None:
		ip = cur_ip
		break

print 'Public IP ' + ip.ip + ' is available for use'

# Find the network we are using for our instances
network = nova.networks.find(label='private')
nics = [{'net-id': network.id}]

print 'Machines can be connected to private network "' + network.label + '"' 

# Find the security groups we are using
sg_ssh = None
sg_https = None
sgs = nova.security_groups.list()
for sg in sgs:
	if sg.name == 'ssh-only':
		sg_ssh = sg
	if sg.name == 'http-https':
		sg_https = sg

if sg_ssh is None or sg_https is None:
	raise Error('Security groups not found')

print 'Security groups for SSH, HTTP, and HTTPS are available'

# Falvor
flavor = nova.flavors.find(name='m1.medium')
print 'Flavor m1.medium is available'

# MySQL image
dbimage = nova.images.find(name='CentOS 6.6 64bit Puppet')
print 'VM image for DB server is available'

# Create DB server
dbserver = nova.servers.create(name = 'demo-mysql-db',
		image = dbimage.id,
		flavor = flavor.id,
		nics = nics,
		key_name = keypair.name)

print 'Created server demo-mysql-db, provisioning ....'

# Capture the servers private IP
while True:
	dbserver = nova.servers.get(dbserver.id)
	time.sleep(5)
	if dbserver.status == 'ACTIVE':
		break
dbserverip = dbserver.addresses['private'][0]['addr']

# Provision the DB Server
dbserver.add_floating_ip(ip)
dbserver.add_security_group(sg_ssh.id)

wait_for_port(ip.ip, 22)
scp_file(ip.ip, ssh_prv_key, 'default.pp', '/tmp/default.pp')
execute_ssh(ip.ip, ssh_prv_key, 'sudo puppet apply /tmp/default.pp')

dbserver.remove_security_group(sg_ssh.id)
dbserver.remove_floating_ip(ip)

print 'demo-mysql-db successfully provisioned'

# Meta data for webserver
meta = {'dbserverip': dbserverip}

# Web Server
webimage = nova.images.find(name='CentOS 6.6 64bit Puppet')
print 'VM image for web-server is available'

# Create Web Server
webserver = nova.servers.create(name = 'demo-apache',
		image = webimage.id,
		flavor = flavor.id,
		nics = nics,
		meta = meta,
		key_name = keypair.name)

print 'Created server demo-apache, provisioning ....'

# Assign a floating ip
while True:
	webserver = nova.servers.get(webserver.id)
	time.sleep(5)
	if webserver.status == 'ACTIVE':
		break

webserver.add_floating_ip(ip)
webserver.add_security_group(sg_ssh.id)
webserver.add_security_group(sg_https.id)

wait_for_port(ip.ip, 22)
scp_file(ip.ip, ssh_prv_key, 'db-server-ip.sh', '/tmp/db-server-ip.sh')
scp_file(ip.ip, ssh_prv_key, 'phpMyAdmin.conf', '/tmp/phpMyAdmin.conf')
execute_ssh(ip.ip, ssh_prv_key, 'sudo yum -y install jq && sudo mkdir -p /etc/facter/facts.d && sudo mv /tmp/db-server-ip.sh /etc/facter/facts.d/db-server-ip.sh && sudo chmod +x /etc/facter/facts.d/db-server-ip.sh')
scp_file(ip.ip, ssh_prv_key, 'default.pp', '/tmp/default.pp')
execute_ssh(ip.ip, ssh_prv_key, 'sudo puppet apply /tmp/default.pp')

print 'demo-apache successfully provisioned'

print 'Apache Webserver now available at: http://' + ip.ip + '/'
print 'MySQL DB private IP is shown at: http://' + ip.ip + '/ip.html'
print 'phpMyAdmin available: http://' + ip.ip + '/phpMyAdmin/'

