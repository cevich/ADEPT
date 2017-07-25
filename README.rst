=====================================================
Autotest-Docker Enabled Product Testing (A.D.E.P.T.)
=====================================================

ADEPT includes a python program, a collection of ansible playbooks, and
related configurations.  Together, they help orchestrate a complete
run of Docker Autotest over one or more local or cloud-based systems.

.. _prerequisites:

Prerequisites
==============

*  Red Hat based host (RHEL_, CentOS_, Fedora_, etc), subscribed and fully updated.
*  Python 2.7
*  PyYAML 3.10 or later
*  libselinux-python 2.0 or later
*  rsync 2.5 or later
*  Ansible_ 2.1 or later
*  Ansible_ 2.3 or later is required if a
   slave (a.k.a. *kommandir*) is not used (i.e. ``kommandir_groups: ["nocloud"]``)
*  Root access **not** required

Testing/Development
--------------------

*  python-unittest2 1.0 or later
*  python2-mock 1.8 or later
*  pylint 1.4 or later
*  python-virtualenv or python2-virtualenv
*  Optional (for building documentation), ``make``, ``python-sphinx``,
   and ``docutils`` or equivalent for your platform.

Openstack support:
-------------------

*  redhat-rpm-config (rpm)
*  gcc
*  python-virtualenv or python2-virtualenv (EPEL rpm)
*  openssl-devel
*  `Openstack client config credentials`_

.. _Ansible: http://docs.ansible.com/index.html
.. _RHEL: http://www.redhat.com/rhel
.. _CentOS: http://www.centos.org
.. _Fedora: http://www.fedoraproject.org
.. _`Openstack client config credentials`: https://docs.openstack.org/developer/os-client-config/

Quickstart
===========

This demonstration doesn't do anything extraordinarily useful, however it does
demonstrate ADEPT's essential purpose:

    *Setup an initial state, execute nested playbooks, maintain the state,
    and reqire only a very small number of dependencies*

In this case, the nested playbooks reside under ``jobs/quickstart``.  One
playbook is executed for each transition (``setup``, ``run``, ``cleanup``),
however in this case they're all the same.

::

    # Optional: set $ANSIBLE_PRIVATE_KEY_FILE
    # if unset, a new temporary key will be generated in workspace
    $ export ANSIBLE_PRIVATE_KEY_FILE="$HOME/.ssh/id_rsa"

    # Create a place for runtime details and results to be stored
    $ export WORKSPACE="$(mktemp -d --suffix=.workspace)"

    # Run the ADEPT-three-step (keyboard finger-dance)
    $ ./adept.py setup $WORKSPACE exekutir.xn
    $ ./adept.py run $WORKSPACE exekutir.xn
    $ ./adept.py cleanup $WORKSPACE exekutir.xn

**Notes:**

#. Useful output files should be recorded under ``$WORKSPACE/results/``.

#. Nearly everything runs from a copy of the source in ``$WORKSPACE``
   created during ``setup``.

#. To see select debugging output (select variable values and infos),
   append ``-e adept_debug=true`` onto any of the ``adept.py`` lines above.

#. Setting ``-e adept_debug=true`` will prevent roles in the cleanup context
   from removing any leftover files in the workspaces.

#. To see massive amounts of ugly details, append one or more ``--verbose``,
   options onto any of the ``adept.py`` lines above.

.. _latest_documentation:

Latest Documentation
======================

For the latest, most up to date documentation please visit
http://autotest-docker-enabled-product-testing.readthedocs.io

The latest `Docker Autotest`_ documentation is located at:
http://docker-autotest.readthedocs.io

.. _Docker Autotest: https://github.com/autotest/autotest-docker
