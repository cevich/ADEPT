.. _introduction:

Introduction
=============

ADEPT provides the ground-work for managing and executing tests against
systems through multiple Ansible playbooks.  It supports the industry-standard
practice of utilizing a separate triggering/scheduling versus execution host.
Jobs may be defined in-repo or externally, and use the standard Ansible
directory structure.  Jobs may define their own playbooks, roles,
and scripts or re-use any of the content provided.

Systems management, be it local or cloud, is extremely flexible.  Though
an OpenStack setup is the default, any custom host-management tooling
may be used.  Changing and maintaining management tooling is very smooth
since the interface is simple and well defined.  No persistent systems or
data-stores are required, though both may be utilized.

Finally, since initiator-host capabilities are often unknown and fixed,
ADEPT has very low dependency and resource requirements.  The included
``adept.py`` program, along with a simple YAML input file directives,
bootstraps Ansible operations for every job.  While Ansible and it's
dependencies are gathered at runtime, and confined within a python
virtual environment.
