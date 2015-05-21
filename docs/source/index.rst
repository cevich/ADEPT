:tocdepth: 2

.. include:: ../../README.rst
   :end-before: The quickstart section begins next

.. sectnum::

.. toctree::
   :hidden:

Introduction
=============

Both Autotest_ and `Docker Autotest`_ represent excellent and comprehensive testing
frameworks. However, they are lacking in modern system configuration and orchestration
capabilities. Especially, those required by Continuous Integration systems such as
Jenkins_.

This project aims to fill in that gap, between when a system is provisioned, and test
results are collected.  It will manage and configure the target systems up to and
through execution of  `Docker Autotest`_.  The supported target platforms are all
Red Hat based, though due to Autotest_'s low dependency count, could be easily extended.

.. _Jenkins: https://jenkins-ci.org/

.. include:: ../../README.rst
   :start-after: The quickstart section begins next

Functional Overview
====================

Assuming some familiarity with Ansible_, all major operations are contained within
roles.  Target system state is interrogated prior to executing any task.  If found
already in the desired state, that task will be skipped.  It is perfectly normal
for the vast majority of tasks to be skipped.  Especially when the playbook is
run repeatedly against the same set of hosts.

Playbook Includes
------------------

The ``site.yml`` file operates in three stages.  The first gathers system information,
assigning all test systems into groups based on their canonical release name
(rhel, rhelah, centos, fedora, etc.).  It then configures each system with roles
specific to their release group.

The second stage installs and configures both Autotest_ and `Docker Autotest`_.
This includes applying any custom tasks or configuration templates and/or configuring
a reasonable set of discovered test defaults.  Next Autotest is executed and when
finished, the results are gathered and collected onto the host executing the playbook.

The third and final stage performs any required cleanup work on the target hosts.
This may include un-subscribing them if so configured (disabled by default).

Stage Details
--------------

**TODO**
