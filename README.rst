=====================================================
Autotest-Docker Enabled Product Testing (A.D.E.P.T.)
=====================================================

An Ansible_ Playbook for conducting automated testing with Autotest_
and `Docker Autotest`_ on managed hosts.

.. _Ansible: http://docs.ansible.com/index.html
.. _autotest: http://autotest.github.io/
.. _`docker autotest`: https://github.com/autotest/autotest-docker

.. contents::

.. The quickstart section begins next

Prerequisites
==============

*  Red Hat based host (RHEL_, Atomic_, CentOS_, Fedora_, etc), subscribed and fully updated.
*  Ansible_ 1.9 or later is installed and configured (``/etc/ansible/ansible.conf``)
*  Password-less public-key **ssh** access to the root user on all test systems
*  All hosts have network access to retrieve content from github_ and/or any alternate
   URLs as specified in configuration variables.

.. _Ansible: http://docs.ansible.com/index.html
.. _github: https://github.com
.. _RHEL: http://www.redhat.com/rhel
.. _Atomic: http://www.redhat.com/en/resources/red-hat-enterprise-linux-atomic-host
.. _CentOS: http://www.centos.org
.. _Fedora: http://www.fedoraproject.org

Quickstart
===========

#. ``git clone https://github.com/cevich/autotest-docker-enabled-product-testing.git adept``
#. Copy ``hosts.sample`` to ``hosts`` and edit to list all DNS host names as
   indicated in the file's comments.
#. Copy ``group_vars/autotested.sample`` to ``group_vars/autotested``.
#. Copy ``group_vars/subscribed.sample`` to ``group_vars/subscribed``.  Either provide
   your subscription-manager credentials directly, or (default) in the files
   ``~/rhn_username`` and ``~/rhn_password``.
#. From within the repository directory (``adept``), execute ``ansible-playbook -i hosts site.yml``.

.. Note:: The most likely Ansible failures are configuration related
   (``/etc/ansible/ansible.conf``).  This can be quickly tested
   by running ``ansible -i hosts all -m ping`` and resolving any problems
   reported.

.. The current documentation section begins next

Latest Documentation
======================

For the latest, most up to date documentation please visit
http://autotest-docker-enabled-product-testing.readthedocs.org

The latest `Docker Autotest`_ documentation is located at:
http://docker-autotest.readthedocs.org
