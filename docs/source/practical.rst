Practical Considerations
===========================

Customized Configuration
-------------------------

The intended use of the structured variable ``autotest_docker`` is to
either execute identical testing on all hosts, or differentiated across
different groups and or individual hosts.  Using this feature requires
an understanding of `Ansible's variable scoping rules`_.

The optional list of *templates* or *copies* may produce
special files on test hosts under the ``config_custom`` subdirectory
of Docker Autotest.  Specifically, these filenames are treated specially
by the *autotested* role:

   *  ``control.ini`` :ref:`(docs) <dat:control configuration>` used
      to select specific subtests, sub-subtests, and their order of execution.
      Additionally, it contains options controlling the bugzilla integration
      :ref:`(docs) <dat:bugzilla_intergration>`,
      which can automatically skip tests with open/active bugs.

   *  ``defaults.ini`` :ref:`(docs) <dat:default configuration options>` is
      used at test execution time.  It contains global default options which
      are inherited by all subtests and sub-subtests.  Any option in this
      file may be overridden by them as needed.

   * ``tests.ini`` :ref:`(docs) <dat:subtest modules>`, the default file
     containing all custom subtest and sub-subtest configuration options.
     When not present, one will be automatically generated [#ag]_.

.. _`ansible's variable scoping rules`: http://docs.ansible.com/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable

.. [#ag] All test configurations containing unmodified
   ``__example__`` keys :ref:`(docs) <dat:example values>`
   will be copied into ``tests.ini`` by the role, after inclusion
   of ``templates`` and ``tasks``.

Additional Tests
-----------------

Docker Autotest has the capability of discovering and using additional test
modules if they are present in specific locations
:ref:`(docs) <dat:additional_test_trees>`.  Similar to `Customized Configuration`_,
presence of test module sub-directories within the following directories
is handled specially by Docker Autotest.  Their names are customizable within
``control.ini``, however the default names and functions are:

*  ``<docker autotest directory>/pretests`` modules run once before all other testing.

*  ``<docker autotest directory>/subtests`` contains all the main test modules.
   Many are included by default, but additional tests present in subdirectories
   will be discovered and used if found.  This is intended to support additional
   checkouts from version-control repositories to allow either coexistence or
   overwriting built-in tests.  For example:

   ``git clone https://example.com/private/tests.git subtests/private``

*  ``<docker autotest directory>/intratests`` modules run in-between every module
   from ``subtests``.  By default the *garbage_check* test is included to cleanup
   any leftover images or containers from previously failed tests.

*  ``<docker autotest directory>/posttests`` are the opposite of ``pretests``,
   running after all other modules above.

The most convenient way of placing/replacing custom subtests and/or their configurations
is to use the :ref:`copies and templates variables <copies_templates>`
