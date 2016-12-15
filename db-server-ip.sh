#!/bin/bash

SERVERIP="`/usr/bin/curl -m 60 -s http://169.254.169.254/openstack/latest/meta_data.json | /usr/bin/jq -r '.meta.dbserverip'`"
echo "dbserverip=${SERVERIP}"
