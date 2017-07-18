ADEPT Variables Reference
==========================

From the perspective of a task in a playbook, the `lookup order is defined
by Ansible's documentation`_.  This reference is just an overview of some
of the common variables used throughout ADEPT's plays and tasks.

.. _`lookup order is defined by Ansible's documentation`: http://docs.ansible.com/ansible/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable

High-level Variables
---------------------

Use of variable-overrides on the Ansible command-line is highly-discouraged.
It has a very hard, non-obvious side-effect which can make debugging very
difficult:  It forces those variables to be read-only, and silently
fails to change they're contents.  Instead, there are two high-level
YAML-dictionary variable files guaranteed to exist in ``$WORKSPACE``.

*  ``exekutir_vars.yml``:  This may originally have arrived in ``$WORKSPACE``
   by external means (i.e. it was copied there), or it was produced by
   the ``exekutir.xn`` transition file.  This file's variables are included
   in every play that runs on the exekutir.  Whatever it's original source,
   the *exekutir's* ``exekutir_workspace_setup`` role does manipulate it's contents
   during *setup*, to ensure consistency of critical variables like ``uuid``.

* ``kommandir_vars.yml``: This only resides within the *kommandir's* workspace,
  but may have arrived from the specific job (i.e. from inside ``job_path``)
  or externally via ``extra_exekutir_setup`` or ``extra_kommandir_setup``.  It
  is included in every default play that runs on
  the *kommandir*.  In all cases, the *exekutir's* ``exekutir_workspace_setup``
  role will always produces/manipulate it's contents during *setup* along
  with hard-coding critical values, like ``uuid``.

Low-level Variables
--------------------

This includes variables defined by tasks, playbooks, ``host_vars`` and ``group_vars``
files.  General guidance is to define a variable in one spot, which is as close
to it's usage-context as possible.

For example, if a variable is specific to a...

*  ...play, it should wind up in global ``vars_files``, in ADEPT's case that means
   ``exekutir_vars.yml`` or ``kommandir_vars.yml``
*  ...role, stick it in that role's defaults.
*  ...set of hosts, make them part of a group and define it under it's ``group_vars``.
*  ...specific host, define it under that hosts ``host_vars``.

Descriptions of specific, widely used or very important variables are defined below.

* ``adept_debug``: Boolean, defaults to ``False``.
  *Exekutir's* value copied to *kommandir*.
  Enables many ansible ``debug``
  statements across many roles to display relevant variable values.  Also disables actually
  removing files from the ``workspace_cleanup`` role.

* ``cleanup``: Boolean, defaults to ``True``
  *Exekutir's* value copied to *kommandir*.
  Enables/Disables removal of all *peons* by the *kommandir*, in the *cleanup* context.
  See also, ``stonith`` (below)

* ``cleanup_globs``: List, defaults to ``[]``.
  Not shared between *exekutir* and *kommandir*
  A list of strings, each interpreted as a relative shell-like file glob relative to ``workspace``.
  Intended to mark certain sensitive files/directories for removal in the *cleanup* context.

* ``cloud_environment``: Dictionary, defaults to ``{}``.
  Not shared between *exekutir* and *kommandir*.
  Defines the environment variable names, and values which should be set when executing ``cloud_provisioning_command`` and ``cloud_destruction_command`` (below).  Supports jinja2 template resolution.

* ``cloud_asserts``: List, defaults to ``[]``.
  Not shared between *exekutir* and *kommandir*.
  List of Ansible conditionals (with jinja2 template resolution) which must all evaluate true prior to executing ``cloud_provisioning_command`` and ``cloud_destruction_command`` (below).

* ``cloud_provisioning_command``: Dictionary, defaults to ``Null``.
  Not shared between *exekutir* and *kommandir*.
  Same keys/values used for the Ansible ``shell`` module, excluding ``cloud_environment`` which is
  brought into the task separately.  Upon success, it is expected that ``stdout`` is a valid
  YAML dictionary document.  Any keys/values in that document will be written into the file
  pointed to by the ``hostvarsfile`` variable.  Normally,
  ``{{invendory_dir}}/{{inventory_hostname}}.yml``.

* ``cloud_destruction_command``:  Same as ``cloud_provisioning_command`` but defines the command
  for removing the host.

* ``extra_exekutir_setup``: Dictionary, defaults to ``Null``.
  Not shared between *exekutir* and *kommandir*.
  Same keys/values used for the Ansible ``shell`` module.  Represents a command to execute
  on the *exekutir* during the ``exekutir_workspace_setup``
  role.  It's purpose is to allow additional files to be copied into the workspace, such as
  those containing cloud or access credentials.  **N/B:** It would be wise make sure any copied in
  files, are also listed in ``cleanup_globs`` so they don't persist after *cleanup*.

* ``empty``:  Defines the set of values which are to be considered "not set" or "blank".  This
  is used as a convenience value for quickly testing whether or not a variable contains something
  useful.

* ``extra_kommandir_setup``: Dictionary, defaults to ``Null``.
  Not shared between *exekutir* and *kommandir*.
  Same as ``extra_exekutir_setup``, with one additional possible key, ``delegate`` which
  should contain the inventory hostname upon which to act.  This happens every time the
  ``kommandir_workspace_update`` role is applied.

* ``job_name``: String, defaults to the basename of ``job_path``.
  *Exekutir's* value copied to *kommandir*.
  The value of this variable is primarily used to identify job-specific resources.
  For example, it is appended to the end of all *peons* when they are created in an
  *openstack* cloud.

* ``job_path``: String, defaults to ``jobs/full``.
  *Exekutir's* value copied to *kommandir*.
  This is the absolute path containing all files which should overwrite or support
  contents from the directory referenced by ``kommandir_workspace``.  This is the
  primary method for a job to specialize it's activities.  Typically, this is where
  you will find the job's ``kommandir_vars.yml`` file.

* ``kommandir_groups``:  List, defaults to contents of ``default_kommandir_groups`` variable.
  Not shared between *exekutir* and *kommandir*.
  Any Ansible groups the *kommandir* should be made a member of on the *exekutir*.  The
  listed groups indicate which ``inventory/group_vars`` files should be used on that host.

* ``kommandir_workspace``: String, defaults to ``{{ workspace }}/kommandir_workspace``
  Present, but not shared between *exekutir* and *kommandir*.
  This is only used in the ``exekutir/`` playbooks.  From the *exekutir's* perspective,
  it represents the local path which contains/will contain the authoritative copy of
  the *kommandir's* workspace.  From the *kommandir's* perspective, it represents
  the destination.  When the *kommandir* is a member of the ``nocloud`` group, both
  values will be the same (and no synchronization is done).

* ``kommandir_name_prefix``: String, defaults to ``empty``
  Not shared between *exekutir* and *kommandir*.
  When non-empty, this is used as a prefix when discovering or creating a *kommandir*.
  It's mainly used to control which jobs share which *kommandirs*.  e.g. CI jobs
  testing ADEPT changes, should never clash with a production *kommandir*.

* ``needs_reboot``: Boolean, defaults to ``False``.
  Only used by *peons*.
  If any role sets this ``True``, subsequent application of the ``rebooted`` role will
  result in that host being rebooted, and then confirmed accessible.  Afterwards
  the value is always reset back to ``False``.

* ``no_log_synchronize``: Boolean, defaults to ``True``
  *Exekutir's* value copied to *kommandir*.
  When ``False`` and ``adept_debug`` (above) is ``True`` or ``--verbose`` was used,
  the Ansible ``synchronize`` module will output the full contents of its operation.
  Depending on the context, this can be a HUGE number (many hundreds) of output lines.
  Even when debugging, it's recommended to keep this ``True`` unless the details are
  really needed.

* ``public_peons``:  Boolean, defaults to ``False``
  Only used by *peons*.
  When ``True``, whatever ``cloud_provisioning_command`` is in use, it should
  make every effort to allow unrestricted network access to any created *peons*.
  Otherwise, when ``False``, unrestricted access is optional, and access by
  only the *kommandir* is preferred.

* ``stonith``: Boolean, defaults to ``False``
  Only used  by *kommandir* from the ``exekutir/roles/kommandir_destroyed`` role.
  When ``True`` during the *cleanup* context, it forces removal of the *kommandir*.
  Related to ``kommandir_name_prefix``, this is used during CI jobs for ADEPT itself
  to ensure that particular *kommandir* is job-specific and temporary.

* ``uuid``: DNS & Username compatible string, defaults to a random number.
  *Exekutir's* value copied to *kommandir*.
  This is a critical value which must never change throughout the duration of
  all context transitions and for the lifetime of any *kommandir*.  It's primary
  purpose is to prevent resource contention (hostnames, usernames, and directory names).
  For all ``cloud_provisioning_command`` values, it is recommended this value is
  incorporated to help fulfil it's purpose.
