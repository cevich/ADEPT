Operational Overview
=====================

This is a rough, high-level outline of key steps performed during the three
standard transitions (``setup``, ``run`` and ``cleanup``).

* The 'setup' context transition

    * Fundimental setup of exekutir's ssh keys, and copying ``exekutir`` dir.
      into ``$WORKSPACE``.  (``exekutir.xn``)

    * Intermediate exekutir setup, check ansible version, setup
      separate kommandir workspace source directory.

    * Create or discover the kommandir VM by running a script.  YAML
      output from script updates kommandir's host_vars in workspace inventory.

    * Complete kommandir VM setup (if needed), install packages,
      setup storage, etc.

    * Create a workspace for the kommandir, under the exekutir's workspace.
      Recursively copy contents of path pointed to by ``job_path``, into
      kommandir's workspace.

    * Fill kommandir workspace cache directory with files that will be
      required on each peon (test system).

    * Use rsync to send the kommandir's workspace to the remote
      kommandir (if there is one).

    * Run ``job.xn`` on kommandir (local or remote).  This transition
      file may be overriden on a job-by-job basis.  The default
      simply executes the ``setup.yml`` playbook.

    * Use rsync to retrieve the kommandir's (changed) workspace back to
      the local (exekutir) workspace.

* The 'run' context transition

    * Create or discover the kommandir VM by running a script.
      If needed, re-setup kommandir VM, install packages,
      setup storage, etc.

    * Use rsync to send the kommandir's workspace to the remote
      kommandir (if there is one).

    * Run ``job.xn`` on kommandir (local or remote). The default
      simply executes the ``run.yml`` playbook.

    * Use rsync to retrieve the kommandir's (changed) workspace back to
      the local (exekutir) workspace.

* The 'cleanup' context transition.  This should always run, whether or
   not any other contexts were successful.

    * Create or discover the kommandir VM by running a script.
      If needed, re-setup kommandir VM, install packages,
      setup storage, etc.

    * Use rsync to send the kommandir's workspace to the remote
      kommandir (if there is one).

    * Run ``job.xn`` on kommandir (local or remote). The default
      simply executes the ``cleanup.yml`` playbook.

    * Use rsync to retrieve the kommandir's (changed) workspace back to
      the local (exekutir) workspace.

    * Examine the state of the kommandir.  Destroy the kommandir
      by calling a script, if it was installed/setup more than a
      few days ago, or the ``stonith`` variable is ``True``.

    * Prune the workspace of any unnecessary or files with sensitive
      contents (usernames/passwords).
