Examples
==============

This section provides examples covering various usages and scenarios.
They should all be taken as general guidelines, since they easily become
out of date.  Though if you notice a discrepency, please raise an issue
regarding it.


Adding a public job
--------------------

This example shows how to add a new job to the ADEPT repository.
It's possible to store job details elsewhere, but this will be covered
in another example.

#.  The first step for any new job is to decide on it's name,
    and what it's speciality is.  Begin by creating a directory
    to contain it's files, and documentation to describe it's purpose.
    In this example, a job called ``example`` will be created.

    ::

        $ mkdir -p jobs/example

        $ cat << EOF > jobs/example/README
        This job ({{ job_name }}) is intended to demonstrate
        adding a simple job.  If it's found in production,
        somebody has made a terrible, terrible mistake.

        (src: {{ job_path }}/{{ job_docs_template_src }})
        EOF

#.  Now you need to determine which aspects of the stock *kommandir*
    ansible directory you want overwritten.  Start with identifying
    the *peons* you need to run tests against. For this example,
    we'll stick with the default definitions, but limit the selection
    to only a single peon.

    ::

        $ ls kommandir/inventory/host_vars
        ...many...
        fedora-25-docker-latest.yml    # The one we'll use here
        ...others...

        $ mkdir -p jobs/example/inventory

        $ cat << EOF > jobs/example/inventory/peons
        [peons]
        fedora-25-docker-latest
        EOF

#.  In this example, there's an additional Ansible Role we'd like
    to apply after all the default plays.  Since the
    default playbooks are all renamed with a ``default_`` prefix
    (``exekutir/roles/exekutir_workspace_setup`` role),
    we can simply overwrite ``setup.yml`` to include ``default_setup.yml``
    and then apply our special role.

    ::

        $ mkdir -p jobs/example/roles/frobnicated/tasks

        $ cat << EOF > jobs/example/roles/frobnicated/tasks/main.yml
        ---

        - name: Make docker daemon run in debug mode
          lineinfile:
            path: /etc/sysconfig/docker
            regexp: "^OPTIONS=[\\'\\"]?(.*)[\\'\\"]?"
            line: "OPTIONS='\\1 --debug=true --log-level=debug'"

        - name: Docker daemon is restarted to reload changed options
          service:
            name: docker
            state: restarted

        EOF

        $ cat << EOF > jobs/example/setup.yml
        ---

        # First do all the original, default plays.
        - include: default_setup.yml

        # Now apply the new frobnicated role
        - hosts: peons
          vars_files:
            - kommandir_vars.yml
          roles:
            - frobnicated
        EOF

#.  There's no reason to go crazy with debug-mode tests, so
    we'll just re-use whatever the basic job has going for it.

    ::

        $ ln -s ../basic/kommandir_vars.yml ../basic/templates jobs/example/


#.  Finally, the last step is to make sure the new job works using a `local (i.e. ``nocloud``)
    *kommandir*`_.  **Note**: This requires the local system to meet the ``nocloud``
    *kommandir* :ref:`Prerequisites`.

    .. include:: ex_ws_setup.inc

    .. include:: clouds_yml.inc

    A ``$WORKSPACE/exekutir_vars.yml`` instructs the *exekutir* to run the example job.

    ::

        $ cat << EOF > $WORKSPACE/exekutir_vars.yml
        kommandir_groups: ["nocloud"]
        public_peons: True
        job_path: $PWD/jobs/example
        kommandir_name_prefix: "$USER"
        extra_kommandir_setup:
            command: >
                cp "{{ hostvars.exekutir.workspace }}/clouds.yml"
                   "{{ hostvars.exekutir.kommandir_workspace }}/"
        EOF

    Then we kick it off.

    .. include:: adept_setup.inc

    .. include:: adept_run.inc

    .. include:: adept_cleanup.inc

.. _`a local (i.e. ``nocloud``) *kommandir*`: _Local_Kommandir


Adding a private job
----------------------

In certain cases, it's desireable for the details of a particular job to live outside of the
ADEPT repository.  In this case, the steps are exactly the same as `Adding a public job`_
except for one / possibly-two variable values:

    ::

        job_path: /path/to/job/something/else
        job_name: something

    In this example, we also define the ``job_name`` to be ``something``.  Otherwise
    ADEPT takes the base-name of the ``job_path``, so in this case it would have
    named the job ``else``.  Either way is fine, this just gives some extra flexibility
    in naming jobs differently from the directory the reside in.
