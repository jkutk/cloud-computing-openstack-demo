import time
import subprocess
import os.path
import socket

def probe_port(ip, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	result = sock.connect_ex((ip, port))
	return result == 0

# Wait a minute for port becoming available
def wait_for_port(ip, port, tries = 5, info = True):
	while tries > 0:
		if probe_port(ip, port):
			return
		else:
			tries -= 1
			if info:
				print 'service ' + ip + ':' + str(port) + ' not availalbe waiting another 15sec'
			time.sleep(15)
	raise Error('Service ' + ip + ' at port ' + str(port) + ' did not become available in over 5 minutes ... please check stack manually')

# Copy a folder to remote machine through RSYNC
def rsync_folder(ip, private_key, local_folder, remote_folder):
	subprocess.check_call(['rsync', '-azh', local_folder, '-e', 'ssh -i ' + private_key + ' -o StrictHostKeyChecking=no', 'centos@' + ip + ':' + remote_folder])

# Copy a single file to the remote machien through SCP
def scp_file(ip, private_key, local_file, remote_folder):
	subprocess.check_call(['scp', '-i', private_key, '-o', 'StrictHostKeyChecking=no', local_file, 'centos@' + ip + ':' + remote_folder ])

# Execute commands via SSH
def execute_ssh(ip, private_key, command):
	try:
		subprocess.check_call(['ssh', '-q', '-t', '-i', private_key, '-o', 'StrictHostKeyChecking=no', 'centos@' + ip, command])
	except:
		print 'Non zero exit code on ssh command: ' + command + ' please check your cluster manually'
