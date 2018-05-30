#!/bin/bash

set -e

# This script is intended to be called by ADEPT playbooks, from the
# peon_created role.  It requires three command-line arguments as defined
# below.  These are used to print host variables on stdout, depending
# on whether or not the system is reachable by FQDN or not.

IPADDR=$1
FQDN=$2
SSHKEY=$3
SSHOPTS="-i ${SSHKEY} -F /etc/ssh/ssh_config -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o CheckHostIP=no"

die() {
    echo "Error: $2"
    exit $1
}

[[ -n "$IPADDR" ]] || die 1 "Must supply an ip address argument"
[[ -n "$FQDN" ]] || die 2 "Must supply an fully-qualified domain name argument"
[[ -n "$SSHKEY" ]] || die 3 "Must supply complete path to private ssh key file"
[[ -r "$SSHKEY" ]] || die 4 "Must supply readable private ssh key file"

host_vars() {
    host="$1"
    cat <<EOF
---

ansible_host: ${host}
ansible_user: root
ansible_connection: ssh
ansible_ssh_private_key_file: ${SSHKEY}
EOF
}

if ping -q -c 3 $FQDN &> /dev/stderr && ssh $SSHOPTS root@$FQDN /bin/true
then
    host_vars $FQDN
elif ssh $SSHOPTS root@$IPADDR /bin/true
then
    host_vars $IPADDR
else
    die 5 "The system could not be contacted as $IPADDR or $FQDN using $SSHKEY"
fi
