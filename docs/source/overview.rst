Functional Overview
====================

Assuming some familiarity with Ansible_, all major operations are contained within
roles.  Target system state is interrogated prior to executing any task.  If found
already in the desired state, that task will be skipped.  It is perfectly normal
for the vast majority of tasks to be skipped.  Especially when the playbook is
run repeatedly against the same set of hosts.

.. _ansible: http://docs.ansible.com/index.html

Included Playbooks
-------------------

The ``site.yml`` file operates in stages by including three more-specific playbooks.
Any playbook may be run individually at any time w/o consequence to subsequent stages.

The first gathers system information, assigning all test systems into groups based
on their canonical release name.  It then configures each system with roles
specific to their release group.

The second playbook installs and configures both Autotest_ and `Docker Autotest`_.
This includes applying any custom tasks or configuration templates and/or configuring
a reasonable set of discovered test defaults.  Next Autotest is executed and when
finished, the results are gathered and collected onto the host executing the playbook.

The third and final stage performs any required cleanup work on the target hosts.
This may include unsubscribing them if so configured (disabled by default).

.. _autotest: http://autotest.github.io/
.. _`docker autotest`: https://github.com/autotest/autotest-docker


Playbook Details
------------------


``redhat_release``
~~~~~~~~~~~~~~~~~~~

The primary function of this playbook is to uniformly parse the ``/etc/redhat-release``
file on every host.  Dynamic Ansible_ groups are then assigned based on the file's
contents.  This method is used because ** ``ansible_distribution`` ** does not
reliably produce consistent values across all Red Hat releases.

Second, this playbook assigns the ``subscribed`` role for any hosts which require
active subscriptions for package update and install.  The primary input structure
variable consumed by this role is ``rhsm`` from ``group_vars/subscribed``:

.. include:: ../../group_vars/subscribed.sample
   :start-line: 1
   :code: yaml

The, subscription-manager *username* and *password* default to being read read from
the files ``~/rhn_username`` and ``~/rhn_password``.  The ``unsubscribe`` boolean
signals whether or not to unsubscribe and de-register the system during the final
cleanup_ stage (below).

.. _ansible: http://docs.ansible.com/index.html

``autotested``
~~~~~~~~~~~~~~~~

This playbook only operates on hosts assigned to the autotest_docker group (from
the ansible inventory).  This group is not dynamic and must be specified
manually.  Hosts which are not part of the group will have most dependencies installed
short of installing *Autotest* and *Docker Autotest*.

Installation of the Autotest_ framework is controlled by the variable structure
in ``group_vars/autotest_docker``:

.. include:: ../../group_vars/autotest_docker.sample
   :start-line: 2
   :end-before: autotest_docker:
   :code: yaml

Also in this same file is the variable structure ``autotest_docker``.  However,
given the structure size, it will not be represented here.  A portion of the
keys are explained below:

*  ``version``:  This value (when non-empty) will influence the version of the
   Autotest framework.  After cloning, the ``autotest_version`` value
   will be referenced from
   :ref:`Docker Autotest's defaults.ini <dat:default configuration options>`
   and used to reset the Autotest version.  Unless there is a specific reason
   to change this, it is recommended to accept the default (empty) value.

*  The ``test_image`` dictionary specifies values to insert into respective
   keys found in
   :ref:`Docker Autotest's defaults.ini. <dat:default configuration options>`
   If a specific subtest uses a specialized value, that will need to be configured
   via ``templates`` or ``tasks`` (see below).

*  The list of
   :ref:`subtest and sub-subtest names <dat:subtests>`
   to run are specified as
   individual items to the ``include`` key.  By default, only a simple set of
   basic-sanity subtests are run.  If this list is empty, then all available
   subtests will run.

*  ``templates`` is a list of dictionaries containing arguments to the `template
   ansible module`_.  If once rendered on each host, result in the presence of
   any
   :ref:`Docker Autotest Configuration <dat:configuration>`
   files ``config_custom/control.ini``,
   ``config_custom/defaults.ini``, and/or ``config_custom/tests.ini``,
   then the role will not attempt to compose those files from automatically
   discovered values.

.. _`template ansible module`: http://docs.ansible.com/template_module.html#options


``cleanup``
~~~~~~~~~~~~

This role is reserved for any post-testing cleanup operations if needed.  The
final step here is the optional assignment of the *unsubscribed* role.  Disabled
by default by ``rhsm.unsubscribe``, this role does exactly what it's name would
suggest.
