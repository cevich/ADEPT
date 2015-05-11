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
#. ``cd adept``
#. Edit Ansible inventory (``hosts``), list all dns host names and host names to test
#. For any RHEL or RHELAH systems, provide subscription info in ``group_vars/subscribed``.
   Alternatively, place credentials into ``~/rhn_username`` and ``~/rhn_password``.
#. ``ansible-playbook -u root -s -i hosts --forks 10 site.yml``.  Though you may need
   to adjust parameters depending on your particular environment/setup.
