#!/usr/bin/env python

import pprint

from novaclient.v1_1 import client
from credentials import get_nova_creds
creds = get_nova_creds()
nova = client.Client(**creds)
sg = nova.security_groups.list()
print "Security groups"
for sec in sg:
	print sec
img = nova.images.list()
print "Virtual machine images"
for i in img:
	print i
ips = nova.floating_ips.list()
print "Available public IPs"
for ip in ips:
	print ip
