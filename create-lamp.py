#!/usr/bin/env python

import time

from novaclient.v2 import client
from credentials import get_nova_creds
creds = get_nova_creds()
nova = client.Client(**creds)

class Error(Exception):
	pass

# See if our ssh keypair is already uploaded
keypair = None
avail_keypairs = nova.keypairs.list()
for cur_keypair in avail_keypairs:
	if cur_keypair.id == 'matthias-demo-key':
		keypair = cur_keypair

# Upload ssh keypair if necessary
if keypair is None:
	f = open('/Users/matthias/Documents/workspace-bigdatadude/vagrant-base/files/ssh_keys/root.key.pub','r')
	publickey = f.readline()[:-1]
	keypair = nova.keypairs.create('matthias-demo-key',publickey)
	f.close()

# Check the list of floating ips
ips = nova.floating_ips.list()
for cur_ip in ips:
	if cur_ip.ip == '140.78.92.57':
		ip = cur_ip

# Check if our ip is alredy used
if not ip.instance_id is None:
	print ip
	raise Error('IP ' + ip.ip + ' alredy in use')

# Find the network we are using for our instances
network = nova.networks.find(label='private')
nics = [{'net-id': network.id}]

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

# Falvor
flavor = nova.flavors.find(name='m1.medium')

# MySQL image
dbimage = nova.images.find(name='CentOS 6.6 64bit Puppet')

# Create DB server
dbserver = nova.servers.create(name = 'demo-mysql-db',
		image = dbimage.id,
		flavor = flavor.id,
		nics = nics,
		key_name = keypair.name)

# Capture the servers private IP
while True:
	dbserver = nova.servers.get(dbserver.id)
	time.sleep(5)
	if dbserver.status == 'ACTIVE':
		break
dbserverip = dbserver.addresses['private'][0]['addr']

# Meta data for webserver
meta = {'dbserverip': dbserverip}

# Web Server
webimage = nova.images.find(name='CentOS 6.6 64bit Puppet')

# Create Web Server
webserver = nova.servers.create(name = 'demo-apache',
		image = webimage.id,
		flavor = flavor.id,
		nics = nics,
		meta = meta,
		key_name = keypair.name)

# Assign a floating ip
while True:
	webserver = nova.servers.get(webserver.id)
	time.sleep(5)
	if webserver.status == 'ACTIVE':
		break

webserver.add_floating_ip(ip)
webserver.add_security_group(sg_ssh.id)
webserver.add_security_group(sg_https.id)

