# This is the default puppet manifest for provisioning an http (Apache) and db (MySQL) server

# Use the following class to add a proxy configuration for your organisation
# Use of a Proxy server is highly recommended especially when rolling out a high number of nodes
$use_proxy=true
class yumproxyserver {
	if $use_proxy {
		exec { 'proxy-server':
			command => '/bin/echo proxy=http://proxy.uni-linz.ac.at:3128 >> /etc/yum.conf'
		}
	}
}

# Some tools we want on every machine
class tools {
	# Set message of the day 
	file { 'motd':
                name => '/etc/motd',
                mode => '0664',
                owner   => 'root',
                group   => 'root',
                content => "\n\nWelcome to ${::fqdn} - this node is controlled by puppet\nThe machine was provisioned in class through a fully automatic software driven process\n\n\n"
        }

	# NTP service
	package { 'ntp':
		name   => "ntp",
		ensure => present
	}
 	service { 'ntp-services':
		name   => "ntpd",
		ensure => running,
		require => Package[ntp] 
	}

	# Some other packages we need
	$cmdtools = [ "screen", "vim-enhanced", "htop" ]
	package { $cmdtools:
		ensure  => present
	}

	# Disable iptables firewalls
	exec { 'disable-iptables':
		command => '/sbin/service iptables save && /sbin/service iptables stop && /sbin/chkconfig iptables off'	
	}
}

# This class can be used to configure a MySQL database server
class dbserver {
	
	class { 'yumproxyserver' : }
	class { 'tools' : }

	package { "mysql-server.x86_64":
		ensure => present
	}
	service { "mysqld":
		enable => true,
		ensure => running,
		require => Package[ "mysql-server.x86_64" ]
	}

	exec { 'grant-remote-root':
		command => "/bin/echo \"GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'root';\" | /usr/bin/mysql -u root mysql",
		require => Service[ 'mysqld' ]
	}
}

# This class provisions an Apache HTTP server
class webserver {

	class { 'yumproxyserver' : }
	class { 'tools' : }	

	package { "httpd.x86_64":
		ensure => present
	}

	exec { 'disable-selinux':
		command => "/usr/sbin/setenforce 0"
	}

	$phpmyadmintools = [ "php", "php-mysql", "phpMyAdmin" ]
	package { $phpmyadmintools:
		ensure => present,
		notify => Service[ 'httpd' ]
	}

	file { 'phpMyAdmin-http-conf':
		path => '/etc/httpd/conf.d/phpMyAdmin.conf',
		owner => 'root', group => 'root',
		mode => '0644',
		source => 'file:///tmp/phpMyAdmin.conf',
		notify => Service[ 'httpd' ]
	}

	service { "httpd":
		enable => true,
		ensure => running,
		require => Package[ "httpd.x86_64" ]
	}

	package { "jq.x86_64":
		ensure => present
	}

	file { 'phpMyAdmin-config.inc.php-config-dir':
		path => '/etc/phpMyAdmin',
		ensure => 'directory',
		owner => 'root', group => 'root',
		mode => '0755'
	}

	file { 'phpMyAdmin-config.inc.php':
		path => '/etc/phpMyAdmin/config.inc.php',
		owner => 'root', group => 'root',
		mode => '0664',
		content => inline_template("<?php\n\$cfg['Servers'][1]['host'] = '$dbserverip';")
	}
}

node demo-mysql-db {
	class { 'dbserver' : }
}

node demo-apache {
	class { 'webserver' : }
}
