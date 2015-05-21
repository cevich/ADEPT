=====================================================
Autotest-Docker Enabled Product Testing (A.D.E.P.T.)
=====================================================

An Ansible_ Playbook for conducting automated testing with Autotest_
and `Docker Autotest`_ on managed hosts.

.. _ansible: http://docs.ansible.com/index.html
.. _autotest: http://autotest.github.io/
.. _`docker autotest`: https://github.com/autotest/autotest-docker

.. The quickstart section begins next

Prerequisites
==============

*  Red Hat based host (RHEL, CentOS, Fedora, etc), subscribed and fully updated.
*  Ansible 1.9 or later is installed and configured (``/etc/ansible/ansible.conf``)
*  Password-less public-key **ssh** access to the root user on all test systems
*  All hosts have network access to retrieve content from github and/or any alternate
   URLs as specified in configuration variables.

Quickstart
===========

#. ``git clone https://github.com/cevich/autotest-docker-enabled-product-testing.git adept``
#. Copy ``hosts.sample`` to ``hosts`` and edit to list all DNS host names as
   indicated in the file's comments.
#. Copy ``group_vars/autotest_docker.sample`` to ``group_vars/autotest_docker``.
#. Copy ``group_vars/subscribed.sample`` to ``group_vars/subscribed``.  Either provide
   your subscription-manager credentials directly, or (default) in the files
   ``~/rhn_username`` and ``~/rhn_password``.
#. From within the repository directory (``adept``), execute ``ansible-playbook -i hosts site.yml``.

:Note: The most likely Ansible failures are configuration related
       (``/etc/ansible/ansible.conf``).  This can be quickly tested
       by running ``ansible -i hosts all -m ping`` and resolving any problems
       reported.

.. The current documentation section begins next

Latest Documentation
======================

For the latest, most up to date documentation Please visit
http://autotest-docker-enabled-product-testing.readthedocs.org
