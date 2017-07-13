#!/usr/bin/env python2

"""
ADEPT VM provisioning / cleanup script for the openstack ansible group.

Assumed to be running under an exclusive lock to prevent TOCTOU race
and/or clashes with existing named VMs.

Requires:
*  RHEL/CentOS host w/ RPMs:
    * Python 2.7+
    * redhat-rpm-config (base repo)
    * gcc
    * glibc-devel
    * python-virtualenv or python2-virtualenv (EPEL repo)
* Openstack credentials as per:
    https://docs.openstack.org/developer/os-client-config/
"""

import sys
import os
import os.path
import logging
import time
import argparse
import subprocess
from base64 import b64encode
import shutil
import virtualenv
from flock import Flock

# Operation is discovered by symlink name used to execute script
ONLY_CREATE_NAME = 'openstack_exclusive_create.py'
DISCOVER_CREATE_NAME = 'openstack_discover_create.py'
DESTROY_NAME = 'openstack_destroy.py'
ALLOWED_NAMES = (DISCOVER_CREATE_NAME, DESTROY_NAME, ONLY_CREATE_NAME)

DESCRIPTION = ('Low dependency script called by ADEPT playbooks'
               ' to manage OpenStack VMs.')

EPILOG = ('Required:  The WORKSPACE environment variable must exist and point to a'
          ' writeable directory.  The script must be invoked by link (or symlink)'
          ' named "%s" or "%s". Alternatively, if named "%s", VM creation will'
          ' fail, should another with the same name already exist.'
          % ALLOWED_NAMES)

# Needed for unitesting so argparse doesn't call system.exit()
ENABLE_HELP = True

# Placeholder, will be set by unittests or under if __name__ == '__main__'
os_client_config = ValueError  # pylint: disable=C0103

# Lock-down versions of os-client-config and all dependencies for stability
PIP_REQUIREMENTS = [
    "appdirs==1.4.3",
    "Babel==2.4.0",
    "cliff==2.5.0",
    "cmd2==0.7.0",
    "debtcollector==1.13.0",
    "deprecation==1.0",
    "funcsigs==1.0.2",
    "functools32==3.2.3.post2",
    "iso8601==0.1.11",
    "jsonpatch==1.15",
    "jsonpointer==1.10",
    "jsonschema==2.6.0",
    "keystoneauth1==2.19.0",
    "monotonic==1.3",
    "msgpack-python==0.4.7",
    "netaddr==0.7.19",
    "netifaces==0.10.5",
    "openstacksdk==0.9.14",
    "os-client-config==1.26.0",
    "osc-lib==1.3.0",
    "oslo.config==3.24.0",
    "oslo.i18n==3.15.0",
    "oslo.serialization==2.18.0",
    "oslo.utils==3.25.0",
    "packaging==16.8",
    "pbr==2.0.0",
    "positional==1.1.1",
    "prettytable==0.7.2",
    "pyparsing==2.2.0",
    "python-cinderclient==2.0.1",
    "python-glanceclient==2.6.0",
    "python-keystoneclient==3.10.0",
    "python-novaclient==7.1.0",
    "python-openstackclient==3.9.0",
    "pytz==2017.2",
    "PyYAML==3.12",
    "requests==2.13.0",
    "requestsexceptions==1.2.0",
    "rfc3986==0.4.1",
    "simplejson==3.10.0",
    "six==1.10.0",
    "stevedore==1.21.0",
    "unicodecsv==0.14.1",
    "warlock==1.3.0",
    "wrapt==1.10.10"]

# No C/C++ compiler is available in this virtualenv
PIP_ONLY_BINARY = [':all:']
# These must be compiled, but don't require C/C++
PIP_NO_BINARY = ['wrapt', 'PyYAML', 'positional', 'warlock',
                 'PrettyTable', 'cmd2', 'unicodecsv', 'simplejson',
                 'netifaces', 'deprecation', 'functools32']

# Exit code to return when --help output is displayed (for unitesting)
HELP_EXIT_CODE = 127

DEFAULT_TIMEOUT = 300

# Must use format dictionary w/ keys: name, ip_addr, and uuid
OUTPUT_FORMAT = """---
ansible_host: {ip_addr}
ansible_ssh_host: {ip_addr}
host_uuid: {uuid}
host_name: {name}
ansible_user: root
ansible_ssh_user: root
ansible_become: False
ansible_connection: ssh
"""

WORKSPACE_LOCKFILE_PREFIX = '.adept_workspace'
GLOBAL_LOCKFILE_PREFIX = '.adept_global'

class Singleton(object):
    """
    Base class for singletons, every instantiated class is the same object

    :param args: Positional arguments to pass to subclass ``__new__`` and ``__init__``
    :param drgs: Keyword arguments to pass to subclass ``__new__`` and ``__init__``
    """

    # Singleton instance is stored here
    _singleton = None

    def __new__(cls, *args, **dargs):
        if cls._singleton is None:
            cls._singleton = super(Singleton, cls).__new__(cls, *args, **dargs)
            cls._singleton.__new__init__(*args, **dargs)
        return cls._singleton  # instance's ``__ini__()`` runs next

    def __new__init__(self, *args, **dargs):
        """
        Creation-time abstraction for singleton, only happens once, ever.

        :param args: Positional arguments to pass to subclass ``__new__`` and ``__init__``
        :param drgs: Keyword arguments to pass to subclass ``__new__`` and ``__init__``
        """
        raise NotImplementedError

    @classmethod
    def __clobber__(cls):
        """
        Provides a way to un-singleton the class, mostly just useful for unittesting.
        """
        cls._singleton = None


class OpenstackLock(Singleton, Flock):
    """
    Singleton security around critical (otherwise) non-atomic Openstack operations
    """

    # Only initialize singleton once
    # pylint: disable=W0231
    def __init__(self, lockfilepath=None):
        del lockfilepath

    def __new__init__(self, lockfilepath=None):
        super(OpenstackLock, self).__init__(lockfilepath)


class OpenstackREST(Singleton):
    """
    State-full centralized cache of Openstack REST API interactions.

    :docs: https://developer.openstack.org/#api
    :param service_sessions: Map of service names to service instances
                             (from os-client-config cloud instance)
    """

    # Cache of current and previous response instances and json() return.
    response_json = None
    response_obj = None
    response_code = None
    # Useful for debugging purposes
    previous_responses = None

    # Current session object
    service_sessions = None

    def __new__init__(self, service_sessions=None):
        if service_sessions is None and self.service_sessions is None:
            raise ValueError("service_sessions must be passed on first instantiation")
        self.service_sessions = service_sessions

    def __init__(self, service_sessions=None):
        del service_sessions  # consumed by __new__
        logging.debug('New %s created, wiping any previous REST API history.',
                      self.__class__.__name__)
        self.previous_responses = []

    def raise_if(self, true_condition, xception, msg):
        """
        If true_condition, throw xception with additional msg.
        """
        if not true_condition:
            return None

        if self.previous_responses:
            responses = self.previous_responses + [self.response_obj]
        elif self.response_obj:
            responses = [self.response_obj]
        else:
            responses = []

        logging.debug("Response History:")
        for response in responses:
            logging.debug('  (%s) %s:', response.request.method, response.request.url)
            try:
                logging.debug('    %s', response.json())
            except ValueError:
                pass
            logging.debug('')

        if callable(xception):  # Exception not previously raised
            xcept_class = xception
            xcept_value = xception(msg)
            xcept_traceback = None   # A stack trace would be nice here
            raise xcept_class, xcept_value, xcept_traceback
        else:  # Exception previously raised, re-raise it.
            raise

    def service_request(self, service, uri, unwrap=None, method='get', post_json=None):
        """
        Make a REST API call to uri, return optionally unwrapped json instance.

        :param service: Name of service to request uri from
        :param uri: service URI for get, post, delete operation
        :param unwrap: Optional, unwrap object name from response
        :param method: Optional, http method to use, 'get', 'post', 'delete'.
        :param post_json: Optional, json instance to send with post method
        :raise ValueError: If request was unsuccessful
        :raise KeyError: If unwrap key does not exist in response_json
        :returns: json instance
        """
        session = self.service_sessions[service]
        if self.response_obj is not None:
            self.previous_responses.append(self.response_obj)
        if method == 'get':
            self.response_obj = session.get(uri)
        elif method == 'post':
            self.response_obj = session.post(uri, json=post_json)
        elif method == 'delete':
            self.response_obj = session.delete(uri)
        else:
            self.raise_if(True,
                          ValueError,
                          "Unknown method %s" % method)

        self.response_code = int(self.response_obj.status_code)
        self.raise_if(self.response_code not in [200, 201, 202, 204],
                      ValueError, "Failed: %s request to %s: %s" % (method, uri,
                                                                    self.response_code))

        try:
            self.response_json = self.response_obj.json()
        except ValueError:  # Not every request has a JSON response
            self.response_json = None

        # All responses encode the object under it's name.
        if unwrap:
            self.raise_if(unwrap not in self.response_json,
                          KeyError, "No %s in json: %s"
                          % (unwrap, self.response_json))
            self.response_json = self.response_json[unwrap]
            return self.response_json
        else:  # return it as-is
            return self.response_json

    def compute_request(self, uri, unwrap=None, method='get', post_json=None):
        """
        Short-hand for ``service_request('compute', uri, unwrap, method, post_json)``
        """
        return self.service_request('compute', uri, unwrap, method, post_json)

    def volume_request(self, uri, unwrap=None, method='get', post_json=None):
        """
        Short-hand for ``service_request('volume', uri, unwrap, method, post_json)``
        """
        return self.service_request('volume', uri, unwrap, method, post_json)

    def child_search(self, key, value=None, alt_list=None):
        """
        Search cached, or alt_list for object with key, or key set to value.

        :param key: String, the key to search for, return list of values.
        :param value: Optional, required value for key, first matching item.
        :param alt_list: Optional, search this instance instead of cache
        :raises TypeError: If self.response_json or alt_json are None
        :raises ValueError: If self.response_json or alt_json are empty
        :raises IndexError: If no item has key with value
        """
        if alt_list is not None:
            search_list = alt_list
        else:
            search_list = self.response_json

        self.raise_if(search_list is None,
                      TypeError, "No requests have been made/cached")

        if value:
            found = [child for child in search_list
                     if child.get(key) == value]
            self.raise_if(not found,
                          IndexError,
                          'Could not find key %s with value %s in %s'
                          % (key, value, search_list))
            return found[0]
        else:
            found = [child[key] for child in search_list
                     if key in child]
            return found

    def server_list(self, key='name'):
        """
        Cache list of servers and return list of values for key

        :param key: key to list values for (e.g. 'id')
        :returns: List of values for key
        """
        self.compute_request('/servers', 'servers')
        try:
            return self.child_search(key)
        except IndexError:
            return []

    def server(self, name=None, uuid=None):
        """
        Cache and return details about server name or uuid

        :param name: Optional, exclusive of uuid, name of server
        :param uuid: Optional, exclusive of name, ID of server
        :returns: dictionary of server details
        """
        self.raise_if(not name and not uuid,
                      ValueError,
                      "Must provide either name or uuid")
        if name:
            self.compute_request('/servers', 'servers')
            server_details = self.child_search(key='name', value=name)
            uri = '/servers/%s' % server_details['id']
        elif uuid:
            uri = '/servers/%s' % uuid
        return self.compute_request(uri, unwrap='server')

    def server_ip(self, name=None, uuid=None, net_name=None, net_type='floating'):
        """
        Cache details about server, return ip address of server

        :param name: Optional, exclusive of uuid, name of server
        :param uuid: Optional, exclusive of name, ID of server
        :param net_name: Optional, name of network or None for first-found
        :param net_type: Type of interface to return (e.g. 'fixed')
        :returns: IPv4 address for server or None if none are assigned
        :raises RuntimeError: Server does not exist
        """
        try:
            server_details = self.server(name=name, uuid=uuid)
        except (ValueError, IndexError, KeyError), xcept:  # Very bad, should never happen
            # Assume caller is not catching RuntimeError, so this gets noticed
            self.raise_if(True, RuntimeError,
                          "Server %s/%s disappeared while checking for assigned IP: %s"
                          % (name, uuid, xcept))
        if net_name is None:  # first-found
            net_names = server_details['addresses'].keys()
            net_name = net_names[0]
        iface = self.child_search('OS-EXT-IPS:type', net_type,
                                  server_details['addresses'][net_name])
        return iface['addr']

    def server_delete(self, uuid):
        """
        Cache list of servers, try to delete server by uuid.

        :param uuid: Unique ID of server to delete
        :returns: Listing of server IDs (may include uuid)
        """
        try:
            self.compute_request('/servers/%s' % uuid, method='delete')
        # This can fail for any number of reasons, let caller deal with them
        except Exception, xcept:
            logging.warning("server_delete(%s) raised %s", uuid, xcept)
        return self.server_list(key='id')

    def floating_ip(self):
        """
        Cache list of floating IPs, return first un-assigned or None

        :returns: IP address string or None
        """
        self.service_request('network', '/v2.0/floatingips', 'floatingips')
        try:
            return self.child_search('status', value='DOWN')["floating_ip_address"]
        except (KeyError, IndexError):
            return None

    def attachments(self, name=None, uuid=None):
        """
        Cache details about server, return list of attached volume IDs

        :param name: Optional, exclusive of uuid, name of server
        :param uuid: Optional, exclusive of name, ID of server
        :returns: List of volume IDs currently attached
        """
        long_key = 'os-extended-volumes:volumes_attached'
        return self.child_search('id', alt_list=self.server(name, uuid)[long_key])

    def volume_list(self):
        """
        Cache list of volumes, return list of volume ID's
        """
        self.volume_request('/volumes', 'volumes')
        return self.child_search('id')

    def volume(self, uuid):
        """
        Cache and return details about specific volume uuid

        :param uuid: ID of volume to retrieve details about
        """
        return self.volume_request('/volumes/%s' % uuid, 'volume')


class TimeoutAction(object):
    """
    ABC callable, raises an exception on timeout, or returns non-None value of done()
    """

    sleep = 1  # Sleep time per iteration, avoids busy-waiting.
    # N/B: timeout value referenced outside of class (I know I'm lazy)
    timeout = DEFAULT_TIMEOUT  # (seconds)
    time_out_at = None  # absolute
    timeout_exception = RuntimeError

    def __init__(self, *args, **dargs):
        """
        Initialize instance, perform initial actions, timeout checking on call.

        :param *args: (Optional) list of positional arguments to pass to am_done()
        :param **dargs: (Optional) dictionary of keyword arguments to pass to am_done()
        """
        self._args = args
        self._dargs = dargs

    def __str__(self):
        return ("%s(*%s, **%s) after %0.2f"
                % (self.__class__.__name__, self._args, self._dargs, self.timeout))

    def __call__(self):
        """
        Repeatedly call ``am_done()`` until timeout or non-None return
        """
        result = None
        start = time.time()
        if self.time_out_at is None:
            self.time_out_at = start + self.timeout
        while result is None:
            if time.time() >= self.time_out_at:
                raise self.timeout_exception(str(self))
            time.sleep(self.sleep)
            result = self.am_done(*self._args, **self._dargs)
        return result

    def am_done(self, *args, **dargs):
        """
        Abstract method, must return non-None to stop iterating
        """
        raise NotImplementedError


class TimeoutDelete(TimeoutAction):
    """
    Helper class to ensure server is deleted within timeout window

    :param server_id: uuid of server to delete
    :raises ValueError: If more than one server with name is found
    """

    sleep = 2  # Deleting takes a while

    def __init__(self, server_id):
        self.os_rest = OpenstackREST()
        self.os_rest.server_delete(uuid=server_id)
        super(TimeoutDelete, self).__init__(server_id)

    def am_done(self, server_id):
        """Return remaining ids when server_id not found, None if still present."""
        server_ids = self.os_rest.server_list(key='id')
        if server_id in server_ids:
            logging.info("    Deleting %s", server_id)
            return None
        else:
            logging.info("Confirmed VM %s does not exist", server_id)
            return server_ids


class TimeoutCreate(TimeoutAction):
    """Helper class to ensure server creation and state within timeout window"""

    sleep = 2  # Creating takes a while

    POWERSTATES = {
        0: 'NOSTATE',
        1: 'RUNNING',
        3: 'PAUSED',
        4: 'SHUTDOWN',
        6: 'CRASHED',
        7: 'SUSPENDED'}

    def __init__(self, name, auth_key_lines, image, flavor, userdata_filepath=None):
        """
        Callable instance to create VM or timeout by raising RuntimeError exception

        :param name: VM Name to create (may already exist - not checked)
        :param auth_key_lines: public key file contents for authorized_keys
        :param image: Name of te image to use for VM
        :param flavor: Name of the flavor to use for VM
        :param userdata_filepath: Optional, path to file containing alternate cloud-config
                                  userdata.  The token '{auth_key_lines}' will be
                                  substituted with the ``auth_key_lines`` JSON list.
        """
        self.os_rest = OpenstackREST()

        self.os_rest.compute_request('/flavors', 'flavors')
        flavor_details = self.os_rest.child_search('name', flavor)
        logging.debug("Flavor %s is id %s", flavor, flavor_details['id'])

        # Faster for the server to search for this
        image_details = self.os_rest.service_request('image',
                                                     '/v2/images?name=%s&status=active'
                                                     % image, 'images')
        self.os_rest.raise_if(len(image_details) != 1,
                              RuntimeError,
                              "Found more than one image named %s" % image)
        image_details = image_details[0]
        logging.debug("Image %s is id %s", image, image_details['id'])

        if userdata_filepath:
            with open(userdata_filepath, "rb") as userdata_file:
                # Will throw exception if token is not found
                userdata = userdata_file.read().format(auth_key_lines=str(auth_key_lines))
        else:
            userdata = ("#cloud-config\n"
                        # Because I'm self-centered
                        "timezone: US/Eastern\n"
                        # We will configure our own filesystems/partitioning
                        "growpart:\n"
                        "    mode: off\n"
                        # Don't add silly 'please login as' to .ssh/authorized_keys
                        "disable_root: false\n"
                        # Allow password auth in case it's needed
                        "ssh_pwauth: True\n"
                        # Import all ssh_authorized_keys (below) into these users
                        "ssh_import_id: [root]\n"
                        # public keys to import to users (above)
                        "ssh_authorized_keys: %s\n"
                        # Prevent creating the default, generic user
                        "users:\n"
                        "   - name: root\n"
                        "     primary-group: root\n"
                        "     homedir: /root\n"
                        "     system: true\n" % str(auth_key_lines))
        logging.debug("\nUserdata: %s", userdata)

        server_json = dict(
            name=name,
            flavorRef=flavor_details['id'],
            imageRef=image_details['id'],
            user_data=b64encode(userdata)
        )

        # Immediatly bail out if somehow another server exists with name
        if self.os_rest.server_list().count(name) > 1:
            raise RuntimeError("More than one server %s found during creation", name)

        logging.info("Submitting creation request for %s", name)
        self.os_rest.compute_request('/servers', 'server',
                                     'post', post_json=dict(server=server_json))
        server_id = self.os_rest.response_json['id']
        super(TimeoutCreate, self).__init__(name, server_id)

    def am_done(self, name, server_id):
        """Return server_id if active and powered up, None otherwise"""
        # Immediatly bail out if somehow another server exists with name
        if self.os_rest.server_list().count(name) > 1:
            raise RuntimeError("More than one server %s found during creation", name)
        try:
            server_details = self.os_rest.server(uuid=server_id)
        except ValueError:   # Doesn't exist yet
            return None
        vm_state = server_details['OS-EXT-STS:vm_state']
        power_state = self.POWERSTATES.get(server_details['OS-EXT-STS:power_state'],
                                           'UNKNOWN')
        logging.info("     id: %s: %s, power %s", server_id, vm_state, power_state)
        self.os_rest.raise_if(power_state == 'UNKNOWN',
                              RuntimeError,
                              "Got unknown power-state '%s' from response JSON"
                              % server_details['OS-EXT-STS:power_state'])
        if power_state == 'RUNNING' and vm_state == 'active':
            return server_details['id']
        else:
            return None


class TimeoutAssignFloatingIP(TimeoutAction):
    """Helper class to ensure floating IP assigned to server within timeout window"""

    timeout = 30

    def __init__(self, server_id, router_name=None):
        self.os_rest = OpenstackREST()
        self.os_rest.service_request('network', '/v2.0/routers', "routers")
        if router_name:
            router_details = self.os_rest.child_search('name', router_name)
        else:
            router_details = self.os_rest.response_json[0]
        net_name = router_details['name']
        gw_info = router_details['external_gateway_info']
        net_id = gw_info['network_id']
        logging.info("Router %s maps to network id %s", net_name, net_id)
        super(TimeoutAssignFloatingIP, self).__init__(server_id, net_name, net_id)

    def am_done(self, server_id, net_name, net_id):
        """Return assigned floating IP for server or None if unassigned"""
        try:
            ip_addr = self.os_rest.server_ip(uuid=server_id, net_name=net_name)
            logging.info("    IP %s assigned", ip_addr)
            return ip_addr
        except (ValueError, IndexError, KeyError):
            floating_ip = self.os_rest.floating_ip()  # Get dis-used IP
            if not floating_ip:
                logging.info("    creating new floating IP to %s", net_name)
                floatingip = dict(floating_network_id=net_id)

                self.os_rest.service_request('network', '/v2.0/floatingips',
                                             "floatingip", method='post',
                                             post_json=dict(floatingip=floatingip))
                floating_ip = self.os_rest.response_json['floating_ip_address']

            logging.info("    Assigning %s to server id %s",
                         floating_ip, server_id)

            addfloatingip = dict(address=floating_ip)
            try:
                self.os_rest.compute_request('/servers/%s/action' % server_id,
                                             unwrap=None, method='post',
                                             post_json=dict(addFloatingIp=addfloatingip))
            except ValueError:
                logging.info("    Assignment failed")

            return None  # Assignment may have failed, another server snagged it.


class TimeoutAttachVolume(TimeoutAction):
    """
    Helper class to create and attach a volume to a server

    :param server_name: Used only for volume's description
    :param server_id: Name of new volume and host proximity hint
    :param size: Size in gigabytes for new volume
    """

    timeout = 120
    attach_requested = False

    def __init__(self, server_name, server_id, size):
        self.os_rest = OpenstackREST()
        volume = dict(size=size, name=server_id, multiattach=False,
                      description='Created for %s (%s)' % (server_name, server_id))
        # Try to allocate storage on same host as server
        scheduler_hints = dict(same_host=[server_id])
        logging.info("Creating %sGB volume for VM %s", size, server_name)
        post_json = {'volume': volume,
                     'OS-SCH-HNT:scheduler_hints': scheduler_hints}
        self.os_rest.volume_request('/volumes', 'volume',
                                    method='post', post_json=post_json)
        volume_id = self.os_rest.response_json['id']
        super(TimeoutAttachVolume, self).__init__(server_id, volume_id)


    def am_done(self, server_id, volume_id):
        """
        Return volume_id if attachment complete or None if not
        """
        attachments = self.os_rest.attachments(uuid=server_id)
        attached_to_server = volume_id in attachments
        logging.info("     %s: attached to %s: %s)",
                     volume_id, server_id, attached_to_server)
        if not attached_to_server and not self.attach_requested:
            volumeattachment = dict(volumeId=volume_id)
            self.os_rest.compute_request('/servers/%s/os-volume_attachments' % server_id,
                                         'volumeAttachment', method='post',
                                         post_json=dict(volumeAttachment=volumeattachment))
            self.attach_requested = True
            return None
        elif attached_to_server:
            return volume_id
        else:
            return None


class TimeoutDeleteVolume(TimeoutAction):
    """Helper class to detach and delete a volume"""

    detach_requests = None
    vanish_fmt = 'Volume %s vanished while deleting, raised %s'

    def __init__(self, volume_id):
        self.os_rest = OpenstackREST()
        self.detach_requests = set()
        self._sentinel = self
        super(TimeoutDeleteVolume, self).__init__(volume_id)

    def detach_all(self, volume_id, server_ids):
        """
        Submit detach requests for all id's in server_ids for volume_id
        """
        for server_id in set(server_ids) - self.detach_requests:
            try:
                self.os_rest.compute_request('/servers/%s/os-volume_attachments/%s'
                                             % (server_id, volume_id),
                                             unwrap=None, method='delete')
            # Server may have "gone away" before request could be submitted
            except Exception, xcept:
                logging.warning("detach server %s from volume %s raised %s",
                                server_id, volume_id, xcept)
            self.detach_requests |= set([server_id])

    def _safe_query(self, volume_id):
        try:  # Prevent TOCTOU: id in list, then vanishes before query
            return self.os_rest.volume(volume_id)
        except Exception, xcept:
            volume_ids = self.os_rest.volume_list()
            if volume_id not in volume_ids:
                # Gone now, whew! this is okay
                logging.debug(self.vanish_fmt, volume_id, xcept)
                # Stub volume_details to satisfy original caller and identify race
                return dict(id=volume_id, attachments=[], sentinel=self._sentinel)
            else:
                raise

    def am_done(self, volume_id):
        """
        Return former volume details (or equivalent) if deleted, or None if not
        """
        volume_details = self._safe_query(volume_id)
        if volume_details.get('sentinel', None) == self._sentinel:
            return volume_details  # removal was the goal
        attachments = self.os_rest.child_search('id',
                                                alt_list=volume_details['attachments'])
        if attachments:  # delete request will fail!
            logging.warning("    Detaching unexpected VMs: %s", attachments)
            self.detach_all(volume_id, attachments)
            return None  # try again
        else:
            logging.info("     Deleting volume %s: status %s",
                         volume_id, volume_details['status'])
            try:  # Prevent TOCTOU: id vanishes before query
                self.os_rest.volume_request('/volumes/%s' % volume_id,
                                            unwrap=None, method='delete')
            except Exception, xcept:
                logging.debug(self.vanish_fmt, volume_id, xcept)
                return volume_details
            return None  # try again


def discover(name=None, uuid=None, router_name=None, private=False, **dargs):
    """
    Write ansible host_vars to stdout if a VM name exists with a floating IP.

    :param name: Name of the VM to search for
    :param uuid: Optional, search by uuid instead of name
    :param router_name: Name of router for address lookup (if more than one)
    :param dargs: Completely ignored
    :raise RuntimeError: Severe conditions which must result in script exit
    :raise IndexError: No server found with name
    """
    del dargs
    os_rest = OpenstackREST()

    # Prefer to operate on ID's because they can never race/clash
    if uuid:
        thing = uuid
    elif name:
        thing = name
    else:
        raise RuntimeError("Must pass name and/or uuid to discover()")

    logging.info("Trying to discover server %s", thing)

    nr_found = os_rest.server_list().count(name)
    if nr_found == 1:
        if private:
            net_type = 'fixed'
        else:
            net_type = 'floating'

        # Throws exception if neither name or uuid are set
        ip_addr = os_rest.server_ip(name=name, uuid=uuid,
                                    net_name=router_name, net_type=net_type)
        if name is None:
            name = os_rest.response_json['name']  # Cached by server_ip()
        if uuid is None:
            uuid = os_rest.response_json['id']
        sys.stdout.write(OUTPUT_FORMAT.format(name=name, uuid=uuid, ip_addr=ip_addr))
    elif nr_found > 1:
        raise RuntimeError("More than one server %s found", name)
    else:
        raise IndexError("No server %s found", thing)


def destroy(name=None, uuid=None, **dargs):
    """
    Destroy VM name (or uuid) and any volumes currently attached to it

    :param name: Name of the VM to destroy
    :param uuid: Optional, search by uuid instead of name
    :param dargs: Ignored
    """
    del dargs
    os_rest = OpenstackREST()

    # Prefer to operate on ID's because they can never race/clash
    if uuid:
        thing = uuid
    elif name:
        thing = name
        if os_rest.server_list().count(name) > 1:
            raise RuntimeError("More than one server %s found", name)
    else:
        raise ValueError("Must pass name and/or uuid to destroy()")

    logging.info("Deleting VM %s", thing)

    server_id = None
    volume_ids = []
    try:
        volume_ids = os_rest.attachments(name, uuid)  # Caches server details
        server_id = os_rest.response_json.get('id')  # None if not found
    except IndexError:  # Attachments and server not found
        pass

    if server_id:
        TimeoutDelete(server_id)()

    for volume_id in volume_ids:
        logging.info("Deleting leftover volumes: %s", volume_id)
        TimeoutDeleteVolume(volume_id)()


# Arguments come from argparse, listing them all for clarity of intent
def create(name, pub_key_files, image, flavor,  # pylint: disable=R0913
           private=False, router_name=None, size=None,
           userdata_filepath=None, **dargs):
    """
    Create a new VM with name and authorized_keys containing pub_key_files.

    :param name: Name of the VM to create
    :param pub_key_files: List of ssh public key files to read
    :param image: Name of the openstack image to use
    :param flavor: Name of the openstack VM flavor to use
    :param private: When False, assign a floating IP to VM.
    :param router_name: When private==False, router name to use, or None for first-found.
    :param size: Optional size (gigabytes) volume to attach to VM
    :param userdata_filepath: Optional full path to YAML file containing userdata and,
                              optional ``{auth_key_lines}`` token (JSON).
    :param dargs: Additional parsed arguments, possibly not relevant.
    """
    del dargs  # not used
    pubkeys = []
    for pub_key_file in pub_key_files:
        logging.info("Loading public key file: %s", pub_key_file)
        with open(pub_key_file, 'rb') as key_file:
            pubkeys.append(key_file.read().strip())
            if 'PRIVATE KEY' in pubkeys[-1]:
                raise ValueError("File %s appears to be a private, not a public, key"
                                 % pub_key_file)

    # Needed in case of exception
    server_id = None
    try:
        server_id = TimeoutCreate(name, pubkeys, image, flavor, userdata_filepath)()
        logging.info("Creation successful, VM %s id %s", name, server_id)

        if size:
            logging.info("Attempting to create and attach %sGB size volume", size)
            # name is added to volume description
            TimeoutAttachVolume(name, server_id, int(size))()

        if not private:
            # This can steal a floating IP out from another server
            # if addFloatingIp POST happens concurrently.  It is
            # only partly mitigated by locking between processes of this job.
            with OpenstackLock().timeout_acquire_write(TimeoutAction.timeout) as oslock:
                if oslock is None:
                    raise ValueError("Timeout acquiring lock")
                logging.info("Attempting to assign floating ip on network %s", router_name)
                TimeoutAssignFloatingIP(server_id, router_name)()

        discover(name=name, uuid=server_id, router_name=router_name, private=private)

    # Must not leak servers or volumes, original exception will be re-raised
    except Exception, xcept:
        logging.error("Create threw %s, attempting to destroy VM.", xcept)
        try:
            destroy(name, server_id)
        finally:
            raise

def parse_args(argv, operation='help'):
    """
    Examine command line arguments, show usage info if inappropriate for operation

    :param argv: List of command-line arguments
    :param operation: String of 'discover', 'create', 'destroy' or 'help'
    :returns: Dictionary of parsed command-line options
    """
    # Operate on a copy
    argv = list(argv)
    parser = argparse.ArgumentParser(prog=argv.pop(0),
                                     description=DESCRIPTION,
                                     epilog=EPILOG,
                                     add_help=ENABLE_HELP)

    if operation != 'destroy':
        parser.add_argument('--image', '-i', default='CentOS-Cloud-7',
                            help=('If creating a VM, use this (existing) image instead'
                                  ' of "CentOS-Cloud-7" (Optional).'))

        parser.add_argument('--flavor', '-f', default='m1.medium',
                            help=('If creating a VM, use this (existing) flavor'
                                  ' instead of "m1.medium" (Optional).'))

        parser.add_argument('--router', '-r', default=None, dest='router_name',
                            help=('If creating a VM, assign a floating IP routed'
                                  ' through gateway assigned to (existing) ROUTER,'
                                  ' instead of first-found (Optional).'))

        parser.add_argument('--private', '-p', default=False,
                            action='store_true',
                            help='If creating a VM, do not assign a floating IP (Optional).')

        parser.add_argument('--size', '-s', default=None, type=int,
                            help=('If creating a VM, also create and attach'
                                  ' a volume with the same name, of SIZE'
                                  ' gigabytes (Optional).'))

        parser.add_argument('--userdata', '-u', default=None, dest='userdata_filepath',
                            help=('Path to filename containing cloud-config userdata'
                                  ' YAML to use instead of default (Optional).'))

        parser.add_argument('--lockdir', '-l', default='', type=str,
                            help=('Absolute path to directory where global lock file'
                                  ' should be created/used.'))

    # All operations get these
    parser.add_argument('--verbose', '-v', default=False,
                        action='store_true',
                        help='Increate logging verbosity to maximum.')

    parser.add_argument('--timeout', '-t', default=DEFAULT_TIMEOUT, type=int,
                        help=('Major operations timeout (default %s) in seconds'
                              ' (Optional).' % DEFAULT_TIMEOUT))

    parser.add_argument('name',
                        help='The VM name to search for, create, or destroy (required)')

    # Consumer of remaining arguments must come last
    if operation != 'destroy':
        # "pubkey" will be a list, using "pubkeys" causes --help to be wrong
        # (workaround below)
        parser.add_argument('pubkey', nargs='+',
                            help=('One or more paths to ssh public key files'
                                  ' (not required for "%s")' % DESTROY_NAME))

    if operation == 'help':
        parser.print_help()
        parser.exit()
        return {}  # for unittests

    args = parser.parse_args(argv)
    logging.debug("Parsed arguments: %s", args)

    # Encode as dictionary, makes parameter passing easier to unitest
    dargs = dict([(n, getattr(args, n))
                  for n in args.__dict__.keys()  # no better way to do ths
                  if n[0] != '_'])

    # Workaround: name should be plural
    if 'pubkey' in dargs:
        dargs['pub_key_files'] = dargs['pubkey']  # Can't use dest (above)
        del dargs['pubkey']

    # Add operation for reference
    dargs['operation'] = operation

    logging.info("Processed arguments: %s", dargs)

    return dargs


def main(argv, dargs, service_sessions):
    """
    Contains all primary calls for script for easier unit-testing

    :param argv: List of command-line arguments, e.g. sys.argv
    :param service_sessions: Mapping of service names
                             to request-like session instances
    :returns: Exit code integer
    """
    if dargs['operation'] in ('discover', 'create', 'exclusive'):
        logging.info('Attempting to find VM %s.', dargs['name'])
        # The general exception is re-raised on secondary exception
        try:
            OpenstackREST(service_sessions)
            discover(**dargs)
            if dargs['operation'] == 'exclusive':  # no exception == found VM
                logging.error("Found existing vm %s, refusing to re-create!"
                              "  Exiting non-zero.", dargs['name'])
                sys.exit(1)
        except IndexError, xcept:
            # Different requirements from discover (yes, this is a bad design)
            dargs = parse_args(argv, 'create')
            # Not an error (yet), will try creating VM next
            logging.warning("Failed to find existing VM: %s.", dargs['name'])
            logging.debug("%s: %s", xcept.__class__.__name__, str(xcept))
            try:
                OpenstackREST(service_sessions)
                logging.info('Attempting to create new VM %s.', dargs['name'])
                create(**dargs)
            except:
                logging.error("Original discovery-exception,"
                              " creation exception follows:")
                logging.error(xcept)
                logging.error("Creation exception:")
                raise
    elif dargs['operation'] == 'destroy':
        OpenstackREST(service_sessions)
        logging.info("Destroying VM %s", dargs['name'])
        destroy(**dargs)


def api_debug_dump():
    """Dump out all API request responses into a file in virtualenv dir"""
    lines = []
    os_rest = OpenstackREST()
    seq_num = 0
    for response in os_rest.previous_responses + [os_rest.response_obj]:
        try:
            lines.append({response.request.method: response.request.url})
            lines[-1]['response'] = response.json()
            lines[-1]['status_code'] = response.status_code
            # These are useful for creating unitest data + debugging unittests
            lines[-1]['sequence_number'] = seq_num
            seq_num += 10
        except (ValueError, AttributeError):
            pass
    _basename = os.path.basename(sys.argv[0])
    prefix = _basename.split('.', 1)[0]
    filepath = os.path.join(workspace, '.virtualenv',
                            '%s_api_responses.json' % prefix)
    # Don't fail main operations b/c missing module
    import json as simplejson
    with open(filepath, 'wb') as debugf:
        simplejson.dump(lines, debugf, indent=2, sort_keys=True)
    logging.info("Recorded all response JSONs into: %s", filepath)


def _pip_upgrade_install(venvdir, requirements, onlybin, nobin):
    bindir = os.path.join(venvdir, 'bin')
    environment = os.environ.copy()
    # Fool pip into only touching files under this
    environment['VIRTUAL_ENV'] = venvdir
    # Pip doesn't work well when imported as a module in this use-case.
    # Executing it under a shell also allows hiding it's stdout/stderr
    # unless there's a problem.
    shell = lambda cmd: subprocess.check_call(os.path.join(bindir, cmd),
                                              close_fds=True, shell=True,
                                              env=environment,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT)
    # Sometimes there are glitches, retry this a few times
    for tries in (1, 2, 3):
        try:
            logging.info("Upgrading pip (try %d).", tries)
            shell('pip install --upgrade pip')
            logging.info("Installing packages.")
            pargs = ['pip', 'install']
            pargs += ['--only-binary', ','.join(onlybin)]
            pargs += ['--no-binary', ','.join(nobin)]
            pargs += requirements
            shell(' '.join(pargs))
        # last exception will be raised after 3 tries
        except:  # pylint: disable=W0702
            continue
        else:
            return
    raise


def activate_and_setup(namespace, venvdir, requirements, onlybin, nobin):
    """
    Create, activate, and install isolated python virtual environment

    :param namespace: Variable namespace to use, e.g. ``globals()``
    :param venvdir: Directory path to contain virtual environment and packages
    :param requirements: List of pip packages and optionally, version requirements.
    :param onlybin: List of pip packages to only install pre-built binaries or
                    magic item ':all:' wildcard (overriden by ``nobin``)
    :param nobin: List of pip packages to build and install (overrides onlybin)
    """

    logging.info("Setting up python virtual environment under %s", venvdir)
    # Only one concurrent process should do _pip_upgrade_install()
    lockfile = Flock()  # No need to use global lock, a local one is fine
    with lockfile.timeout_acquire_write(TimeoutAction.timeout) as vlock:
        if vlock is None:
            raise ValueError("Timeout acquiring lock")
        try:
            if os.path.isdir(venvdir):
                logging.info("Found existing virtual environment")
            else:
                logging.info("Creating new virtual environment")
                virtualenv.create_environment(venvdir, site_packages=False)
                _pip_upgrade_install(venvdir, requirements, onlybin, nobin)
        except:
            shutil.rmtree(venvdir, ignore_errors=True)
            raise

    logging.debug("Activating python virtual environment from %s", venvdir)
    old_file = namespace['__file__']  # activate_this checks __file__
    try:
        namespace['__file__'] = os.path.join(venvdir, 'bin', 'activate_this.py')
        execfile(__file__, namespace, namespace)
    finally:
        namespace['__file__'] = old_file


if __name__ == '__main__':
    # Parse arguments
    basename = os.path.basename(sys.argv[0])
    if basename == DISCOVER_CREATE_NAME:
        _dargs = parse_args(sys.argv, 'discover')
    elif basename == ONLY_CREATE_NAME:
        _dargs = parse_args(sys.argv, 'exclusive')
    elif basename == DESTROY_NAME:
        _dargs = parse_args(sys.argv, 'destroy')
    else:
        logging.error("Script was not called as %s, %s, or %s", *ALLOWED_NAMES)
        parse_args(sys.argv, 'help')  # exits
    workspace = os.environ.get('WORKSPACE')
    if workspace is None:
        logging.error(EPILOG)
        sys.exit(2)
    TimeoutAction.timeout = _dargs['timeout']
    Flock.def_path = workspace
    Flock.def_prefix = WORKSPACE_LOCKFILE_PREFIX
    # initialize singleton
    if 'lockdir' in _dargs:
        OpenstackLock(os.path.join(_dargs['lockdir'],
                                   '%s.lock' % WORKSPACE_LOCKFILE_PREFIX))
    else:
        OpenstackLock(os.path.join(workspace,
                                   '%s.lock' % GLOBAL_LOCKFILE_PREFIX))
    # pip and os-client-config behavior depends on these
    os.environ['HOME'] = workspace
    os.chdir(workspace)
    # Allow early debugging/verbose mode
    logger = logging.getLogger()
    if _dargs['verbose']:
        logger.setLevel(logging.DEBUG)
    else:
        # Lower to INFO level and higher for general details
        logger.setLevel(logging.INFO)
    del logger # keep global namespace clean

    # N/B: Any/All names used here are in the global scope
    # pylint: disable=C0103
    activate_and_setup(globals(),
                       os.path.join(workspace, '.virtualenv'),
                       PIP_REQUIREMENTS,
                       PIP_ONLY_BINARY,
                       PIP_NO_BINARY)

    logging.info("Loading openstack client config module")
    os_client_config = __import__('os_client_config')

    # Shut down the most noisy loggers
    for noisy_logger in ('stevedore.extension',
                         'keystoneauth.session',
                         'requests.packages.urllib3.connectionpool'):
        shut_me_up = logging.getLogger(noisy_logger)
        shut_me_up.setLevel(logging.WARNING)

    # OpenStackConfig() obliterates os.environ for security reasons
    original_environ = os.environ.copy()
    osc = os_client_config.OpenStackConfig()
    clouds = osc.get_cloud_names()
    os_cloud_name = original_environ.get('OS_CLOUD_NAME', osc.get_cloud_names()[0])

    logging.info("Using cloud '%s' from %s", os_cloud_name, osc.config_filename)
    cloud = osc.get_one_cloud(os_cloud_name)
    del os_cloud_name  # keep global namespace clean
    service_names = cloud.get_services()
    logging.debug("Initializing openstack services: %s", service_names)
    sessions = dict([(svc, cloud.get_session_client(svc))
                     for svc in service_names])
    del cloud  # keep global namespace clean
    try:
        main(sys.argv, _dargs, sessions)
    finally:
        if _dargs['verbose']:
            api_debug_dump()
