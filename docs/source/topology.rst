Topology
==========

Systems
--------

    ::

        exekutir --> kommandir --> peon
                               \
                                -> peon
                               \
                                -> peon

**-or-**

    ::

        exekutir/kommandir --> peon
                           \
                            -> peon
                           \
                            -> peon

.. _directory_layout:

Directory Layout
------------------

* ``docs``:  Source for all documentation input and output.

* ``exekutir/``: Standard (recommended) Ansible directory layout, dedicated
  specifically for use by the *exekutir* host.  Some roles are shared by
  the kommandir, but all contents are limited by a reduced set of :ref:`prerequisites`.
  This directory is transferred verbatim to ``{{workspace}}`` (or ``$WORKSPACE``)
  during :ref:`The setup context transition <tsct>`.

* ``kommandir/``: Standard (recommended) Ansible directory layout, dedicated
  specifically for use by the *kommandir* host and *peons* group.  This
  directory is transferred to ``{{kommandir_workspace}}`` on the *exekutir*
  which will ultimately become the ``{{workspace}}`` when the *kommandir*
  playbooks run.  Any/all files in the copy may be overridden by files
  from ``{{job_path}}``.

  The most important of which is ``job.xn``.
  This is the primary entry point for execution on the *kommandir* host
  from the *exekutir's* ``exekutir.xn`` transition file.

* ``{{job_path}}``:  Sparse Ansible directory layout, dedicated
  to one or more jobs.  It's contents will overwrite any files of the same name
  in the ``{{kommandir_workspace}}``, on the *exekutir*.  However,
  copies of all the default playbooks are made with a ``default_`` prefix.
  This allows customized ``setup.yml``, ``run.yml``, and ``cleanup.yml`` to
  re-use the defaults if/where needed.  As above, if there is a
  ``job.xn`` file, it will overwrite the default and act as the primary
  entry point.

* ``jobs``: Default directory for public job definitions, e.g. what ``{{job_path}}``
  cound point to.
