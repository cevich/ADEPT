Hacking
===========

Run the unittests
-------------------

This requires that ``python-unittest2`` is installed and/or
the ``unit2`` command is available.  These tests run relatively
quickly, and do a self-sanity check on all major operational areas.

::

    $ unit2
    ...............................s......................
    ----------------------------------------------------------------------
    Ran 54 tests in 9.998s

    OK (skipped=1)


Run the CI test job
--------------------

This is a special ADEPT-job which runs entirely on the local machine,
and verifies the operations of most major Exekutir plays and roles. It's
not perfect, and doesn't test any provisioning or peon-setup aspects.
Optionally, it can be run with ``adept_debug`` and/or ``--verbose`` modes
to retain the temporary workspace for examination.  It requires all the
prerequisites listed for both Kommandir and Exekutir systems.

::

    $ ./test_exekutir_xn.sh
    localhost ######################################
    Parameters:
        optional = '-e some_magic_variable_for_testing='value_for_magic_variable''
        xn = 'exekutir.xn'
        workspace = '/tmp/tmp.wfyfHGypgq.adept.workspace'
        context = 'setup'

    ...cut...

    Examining exit files
    Checking kommandir discovery (before job.xn) cleanup exit file contains 0
    Checking setup exit files
    Verifying exekutir_setup_after_job.exit file contains 0
    Verifying kommandir_setup.exit file contains 0
    Checking contents of test_file_from_setup.txt
    Checking run exit files
    Verifying exekutir_run_after_job.exit file contains 0
    Verifying kommandir_run.exit file contains 0
    Checking contents of test_file_from_run.txt
    Checking cleanup exit files
    Verifying exekutir_cleanup_after_job.exit file contains 0
    Verifying kommandir_cleanup.exit file contains 0
    Checking contents of test_file_from_cleanup.txt
    All checks pass


Local Kommandir
----------------

Having a Kommandir (a.k.a. "Slave") node is useful in production because it offloads
much of the grunt-work onto a dedicated system, with dedicated resources.  It also
decouples the job environment/setup from the execution environment.  Using one
only makes sense in production-environments where the 5-minute setup cost can
be spread over tens or hundreds of jobs.

However, for local testing/development purposes, the extra Kommandir setup time
can be excessive.  If the local system (the Exekutir) meets all the chosen cloud,
Kommandir, and job prerequisites, it's possible to use the Exekutir also as the
Kommandir.  Note however, the Kommandir's ``job.xn`` transition file and playbooks will
still run from a dedicated workspace (created by the Exekutir).

Set the Exekutir's ``kommandir_groups`` (list) variable to include "nocloud"
and enable the flag to create peons with cloud-external IP addresses.
e.g. In ``exekutir_vars.yml``:

::

 kommandir_groups:
     - nocloud
 public_peons: True

Avoid repeating any context transition more than once, against the same
workspace.  The same advice applies to recycling ``uuid`` values.  Both
can be done if needed, but require some careful manipulations of files
in the workspace which isn't straight-forward.  It's safer to apply
the ``cleanup`` context, then start over again with ``setup`` against
a fresh workspace.


Openstack Example
------------------

#. Create a local workspace directory, and populating the
   Exekutir's variables.  In this example, the default (bundled) peon
   definitions are used (from ``kommandir/inventory/host_vars/``).
   All Peon's are members of the ``openstack`` group and use predefined
   image names.  Other options are set to enable subscriptions, use verbose
   output, and retain runtime-workspace files instead of removing them.

    ::
        (from the adept repository root)

        $ export WORKSPACE=/tmp/workspace
        $ rm -rf $WORKSPACE
        $ mkdir -p $WORKSPACE
        $ cat << EOF > $WORKSPACE/exekutir_vars.yml
        ---
        job_path: $PWD/jobs/basic
        kommandir_name_prefix: "$USER"
        kommandir_groups:
            - nocloud
        public_peons: True
        adept_debug: True
        workspace_cleanup_enabled: False
        no_log_synchronize: False
        rhsm:
            username: nobody@example.com
            password: thepassword
        EOF

#. Setup your openstack cloud name (``default`` in this case) and credentials.
   You may either use the standard ``$OS_*`` variables, or the simpler
   ``os-client-config`` file ``clouds.yml`` as show below.  Most of these
   options are specific to the particular openstack setup.  The file
   `format and options are documented here`_.

    ::

        $ cat << EOF > $WORKSPACE/clouds.yml
        ---
        clouds:
            default:
                auth_type: thepassword
                auth:
                    auth_url: http://example.com/v2.0
                    password: foobar
                    tenant_name: baz
                    username: snafu
                regions:
                    - Oz
                verify: False

#. Apply the ADEPT ``setup`` context.  Once this completes, a copy of all runtime
   source material will have been transferred to the workspace.  This includes
   updating initial ``exekutir_vars.yml`` and inventory files.  As noted elsewhere,
   manual changes made to the source, will not be reflected at runtime unless
   they are manually copied into the correct workspace location.

    ::

        $ ./adept.py setup $WORKSPACE exekutir.xn

        localhost ######################################
        Parameters:
            optional = ''
            xn = 'exekutir.xn'
            workspace = '/tmp/workspace'
            context = 'setup'

        ...cut...many...lines...

#. Apply the ADEPT ``run`` context and/or inspect the workspace state.

    ::

        $ ./adept.py run $WORKSPACE exekutir.xn

        localhost ######################################
        Parameters:
            optional = ''
            xn = 'exekutir.xn'
            workspace = '/tmp/workspace'
            context = 'run'

        ...cut...many...lines...

#. Whether or not ``setup`` or ``run`` were successful, always apply ``cleanup``
   to release cloud resources.

    ::

        $ ./adept.py cleanup $WORKSPACE exekutir.xn

        localhost ######################################
        Parameters:
            optional = ''
            xn = 'exekutir.xn'
            workspace = '/tmp/workspace'
            context = 'cleanup'

        ...cut...many...lines...

        $ ls $WORKSPACE

        ansible.cfg             exekutir_ansible.log           roles
        cache                   exekutir_setup_after_job.exit  run_after_job.yml
        callback_plugins        exekutir_vars.yml              run_before_job.yml
        cleanup_after_job.yml   inventory                      setup_after_job.yml
        cleanup_before_job.yml  kommandir_setup.exit           setup_before_job.yml
        clouds.yml              kommandir_workspace            ssh
        dockertest              results

.. _`format and options are documented here`: https://docs.openstack.org/developer/os-client-config/


Helpful References
------------------------

*  split-up host/group variables http://docs.ansible.com/ansible/intro_inventory.html#splitting-out-host-and-group-specific-data
*  magic variables http://docs.ansible.com/ansible/playbooks_variables.html#magic-variables-and-how-to-access-information-about-other-hosts
*  scoping http://docs.ansible.com/ansible/playbooks_variables.html#variable-scopes (esp. need a blurb about silent-read-only)
*  roles http://docs.ansible.com/ansible/playbooks_roles.html#roles
