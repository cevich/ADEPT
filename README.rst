===========
A.D.E.P.T.
===========

An Ansible_ Playbook for conducting automated testing with Autotest_
and `Docker Autotest`_ on managed hosts.

.. _ansible: http://docs.ansible.com/index.html
.. _autotest: http://autotest.github.io/
.. _`docker autotest`: https://github.com/autotest/autotest-docker

Quickstart
===========

#. ``git clone https://github.com/cevich/autotest-docker-enabled-product-testing.git adept``
#. Copy sample and edit ``hosts`` to list all DNS host names to test (public-key ssh access to root assumed)
#. Copy sample and edit ``group_vars/autotest_docker`` as needed (file is commented).
#. Copy sample and edit ``group_vars/subscribed`` for any RHEL or RHELAH systems that need a subscription
   (default loads ``~/rhn_username`` and ``~/rhn_password``).
#. Execute ``ansible-playbook -u root -s -i hosts --forks 10 site.yml``.  Though you may need
   to adjust parameters depending on your particular environment/setup.

Documentation
==============

Please visit http://autotest-docker-enabled-product-testing.readthedocs.org
