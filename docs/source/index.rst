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
