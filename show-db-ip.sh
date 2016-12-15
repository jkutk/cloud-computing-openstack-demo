SERVERIP="`/usr/bin/curl -m 60 -s http://169.254.169.254/openstack/latest/meta_data.json | /usr/bin/jq -r '.meta.dbserverip'`"

/usr/bin/curl -m 60 -s http://169.254.169.254/openstack/latest/meta_data.json >> /tmp/meta_data.json

echo "<html><head><title>DB Server Private IP</title></head><body>${SERVERIP}</body></html>" > /var/www/html/ip.html
