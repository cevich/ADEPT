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

#. Fundamental setup of *exekutir's* ssh keys, and copying ``exekutir`` dir.
   into ``$WORKSPACE``.  (``exekutir.xn``)

    * Copy local ``exekutir/*`` (form repo.) to ``$WORKSPACE``.

    * Drop default ``$WORKSPACE/exekutir_vars.yml`` if not present

    * Copy ``$ANSIBLE_PRIVATE_KEY_FILE`` (and ``.pub``) or
      generate new ``$WORKSPACE/ssh/exekutir_key``.

#. Intermediate *exekutir* setup, check Ansible version, setup
   separate *kommandir* workspace source directory.
   (``exekutir/roles/exekutir_workspace_setup`` role)

    * Copy ``kommandir/*`` (form repo.) to local ``{{workspace}}/kommandir_workspace``

    * Duplicate all default playbooks so they may be both overriden, and re-used if needed.
      i.e. `{{workspace}}/kommandir_workspace/*.yml --> {{workspace}}/kommandir_workspace/default_*.yml``

    * Copy contents of dir pointed to by ``job_path`` to ``{{workspace}}/kommandir_workspace``
      overwriting any files already there (i.e. from the ``kommandir/*`` source).

    * Check/Modify/Lock-down ``{{workspace}}/exekutir_vars.yml`` and
      ``{{workspace}}/kommandir_workspace/kommandir_vars.yml``.

    * Generate unique ssh key for *kommandir* to use for accessing *peons*
      in ``{{workspace}}/kommandir_workspace/ssh/kommandir_key``

#. Create or discover the *kommandir*.
   (``exekutir/roles/kommandir_discovered`` role)

    * The *exekutir* has set the *kommandir's* Ansible group membership from contents
      of the ``{{kommandir_groups}}`` list variable.  (``exekutir/roles/common`` role)

    * The command pointed to by ``{{cloud_provisioning_command}}`` is executed,
      and it's ``stdout`` is parsed as a YAML dictionary, updating
      ``{{workspace}}/inventory/host_vars/kommandir.yml``

    * Membership in the ``nocloud`` Ansible group will always cause the *kommandir*
      to be the same host as the *exekutir* (i.e. ``ansible_host: localhost``).

#. Complete *kommandir* VM setup (if needed), install packages,
   setup storage, etc. (``exekutir/roles/installed`` and ``kommandir_setup`` roles)

#. Finalize the local or remote workspace for the *kommandir*.
   (``exekutir/roles/kommandir_workspace_update`` role)

    * A remote *kommandir* has a user named ``{{uuid}}`` created.  The
      user's ssh ``authorized_keys`` is updated with the contents from
      ``$WORKSPACE/ssh/exekutir_key.pub``

    * Remote *kommandir's* ``/home/{{uuid}}`` (it's workspace) destructively
      synchronized from ``{{workspace}}/kommandir_workspace``.

#. Run ``job.xn`` on *kommandir* (local or remote).
   (``exekutir.xn``)

    * This transition file may have been overridden by a copy from ``{{job_path}}``.

    * The default executes the ``setup.yml`` playbook, which creates and
      configures any *peons* that are members of the "*peons*" Ansible group

    * For a remote *kommandir*, the ``{{uuid}}`` user is used for execution.
      This user is not expected to have or need sudo access.

#. For a remote *kommandir*, synchronize ``/home/{{uuid}}`` (it's workspace)
   back down to the local ``{{workspace}}/kommandir_workspace`` directory.
   (``exekutir/roles/kommandir_to_exekutir_sync`` role)

.. _trct:

The *run* context transition
-----------------------------

#. Create or discover the *kommandir* VM and
   if needed, set it up, install packages, etc. just as in
   *setup* context (above).

#. Run ``job.xn`` on *kommandir* (local or remote).  Note: This transition
   file may have been overridden by a copy from ``{{job_path}}``.
   The default copy simply executes the ``run.yml`` playbook.
   Runs as user ``{{uuid}}`` for a remote *kommandir*.
   (``exekutir.xn``)

#. For a remote *kommandir*, synchronize ``/home/{{uuid}}`` (it's workspace)
   back down to the local ``{{workspace}}/kommandir_workspace`` directory.
   (``exekutir/roles/kommandir_to_exekutir_sync`` role)

.. _tcct:

The *cleanup* context transition.
----------------------------------

**N/B:** This should always run, whether or not any other contexts were
successful.  It may not exit successfully, but it must never orphan
a remote *kommandir* or any *peons*.

#. Create or discover the *kommandir* VM and
   if needed, set it up, install packages, etc. just as in
   *setup* context (above).

#. Run ``job.xn`` on *kommandir* (local or remote).  Note: This transition
   file may have been overridden by a copy from ``{{job_path}}``.
   The default copy simply executes the ``cleanup.yml`` playbook.
   Runs as user ``{{uuid}}`` for a remote *kommandir*.
   (``exekutir.xn``)

#. For a remote *kommandirs*, synchronize ``/home/{{uuid}}`` (it's workspace)
   back down to the local ``{{workspace}}/kommandir_workspace`` directory.
   (``exekutir/roles/kommandir_to_exekutir_sync`` role)

#. Examine the state of the remote *kommandir*.  If it was installed/setup more than a
   few days ago (or the ``{{stonith}}`` variable is ``True``) then
   destroy it by executing ``{{cloud_destruction_command}}``.
   (``exekutir/roles/kommandir_destroyed/`` role)

#. If the *kommandir* was remote, prune the workspace of any unnecessary
   or files with sensitive contents (usernames/passwords).
   (``exekutir/roles/workspace_cleanup`` role)
