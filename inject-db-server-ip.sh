SERVERIP="`curl -m 10 -s http://169.254.169.254/openstack/latest/meta_data.json | jq -r '.meta.dbserverip'`"
cp /usr/share/phpmyadmin/config.sample.inc.php /usr/share/phpmyadmin/config.inc.php
perl -pi -e 's/localhost/"${SERVERIP}"/g' /usr/share/phpmyadmin/config.inc.php
