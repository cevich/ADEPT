Operational Overview
=====================

This is a general, high-level outline of key steps performed during the three
standard transitions (*setup*, *run* and *cleanup*).  It omits many
small details, but the overall sequence should more/less match reality.

The names in parenthesis following each bullet's text denote the ``adept.py``
transition file (``*.xn``), or the source Ansible role or script.

.. _tsct:

The *setup* context transition
-------------------------------

#. Fundamental setup of *exekutir's* ssh keys, and `workspace`_ directory.
   (``exekutir.xn``)

    * Copy repository's ``exekutir/*`` to the `workspace`_.

    * Copy ``$ANSIBLE_PRIVATE_KEY_FILE`` (and ``.pub``) or
      generate new ``{{workspace}}/ssh/exekutir_key``.

#. Intermediate *exekutir* setup, prepare the initial `kommandir_workspace`_
   directory for future remote synchronization.
   (``exekutir/roles/exekutir_workspace_setup`` role)

    * Copy ``kommandir/*`` (from repo.) to local ``{{kommandir_workspace}}``

    * Backup default playbooks to allow selective re-use.
      i.e. ``{{kommandir_workspace}}/*.yml --> {{kommandir_workspace}}/default_*.yml``

    * Copy contents of `job_path`_ to `kommandir_workspace`_, overwriting any
      existing files to allow customization.

    * Generate unique ssh key for *kommandir* to use for this job,
      in ``{{workspace}}/kommandir_workspace/ssh/kommandir_key``

.. _kommandir_discovered:

#. Create or discover the remote *kommandir* VM if configured.
   (``exekutir/roles/kommandir_discovered`` role)

    * The *exekutir* has set the *kommandir's* Ansible group membership from contents
      of the `kommandir_groups`_ list.  (``exekutir/roles/common`` role)

    * Membership in `the ``nocloud`` Ansible group <local_kommandir>`_ will
      always cause the *kommandir* to be the same host as the *exekutir*
      (i.e., ``ansible_host: localhost``).

    * Otherwise, the `cloud_provisioning_command`_ is executed,
      with its ``stdout`` parsed as a YAML dictionary, updating
      ``{{workspace}}/inventory/host_vars/kommandir.yml`` inventory variables.

#. Complete *kommandir* VM setup (if needed), install packages,
   setup storage, etc. (``exekutir/roles/installed`` and ``kommandir_setup`` roles)

#. Finalize the workspace for a remote *kommandir* VM (if used).
   (``exekutir/roles/kommandir_workspace_update`` role)

    * A remote *kommandir* has a `user named ``{{uuid}}`` created <uuid>`_.

    * Remote *kommandir's* ``/home/{{uuid}}`` (its `workspace`_)
      synchronized from the local ``{{kommandir_workspace}}`` copy.

.. _jobxn_on_kommandir:

#. Run ``job.xn`` on *kommandir* (local or remote).  This file may be
   overridden by a copy from `job_path`_ to customize testing operations.
   The default simply executes the ``setup.yml`` playbook to create and
   configure *peons* for testing purposes. (``exekutir.xn``)

#. For a remote *kommandir*, ``/home/{{uuid}}`` is synchronized
   back down to the *exekutir's* local ``{{kommandir_workspace}}``
   directory.  This prevents state from being bound to a remote system.
   (``exekutir/roles/kommandir_to_exekutir_sync`` role)

.. _trct:

The *run* context transition
-----------------------------

#. Create or discover the *kommandir* VM. If needed, set it up,
   install packages, etc. exactly as in *setup*.  This prevents
   the need to maintain a persistent slave-host.

#. Synchronize the local ``{{kommandir_workspace}}`` to a remote
   *kommandir* (if used).  (``exekutir/roles/kommandir_workspace_update``)

#. Run ``job.xn`` on *kommandir* (local or remote).  Same as in
   *setup*, this may have been overridden by a copy from `job_path`_.  The
   default simply executes the ``run.yml`` playbook.  (``exekutir.xn``)

#. For a remote *kommandir*, ``/home/{{uuid}}`` is synchronized
   back down to the *exekutir's* local ``{{kommandir_workspace}}``
   directory.  This prevents state from being bound to a remote system.
   (``exekutir/roles/kommandir_to_exekutir_sync`` role)

.. _tcct:

The *cleanup* context transition.
----------------------------------

**N/B:** This should always run, whether or not any other contexts were
successful.  It may not exit successfully, but it must never orphan
a remote *kommandir* or any *peons*.

#. Create or discover the *kommandir* VM. If needed, set it up,
   install packages, etc.  This may fail again if it also failed
   during *setup* or *run* - this is normal.

#. If possible, synchronize the local ``{{kommandir_workspace}}`` to a remote
   *kommandir* (if used).  (``exekutir/roles/kommandir_workspace_update``)

#. If accessible, run ``job.xn`` on *kommandir* (local or remote).
   The default copy simply executes the ``cleanup.yml`` playbook
   to handle deallocation of *peons* and other resources.
   (``exekutir.xn``)

#. For a remote *kommandir*, ``/home/{{uuid}}`` is synchronized
   back down to the *exekutir's* local ``{{kommandir_workspace}}``
   directory.  This prevents state from being bound to a remote system.
   (``exekutir/roles/kommandir_to_exekutir_sync`` role)

#. Examine the state of the remote *kommandir*.  If configured
   for automatic destruction (after some number of days), it
   will be destroyed.  It will also be removed if the `stonith`_
   flag is ``True``,  to support testing of the *kommandir* setup itself.
   (``exekutir/roles/kommandir_destroyed/`` role)
