=====================================================
Autotest-Docker Enabled Product Testing (A.D.E.P.T.)
=====================================================

TODO: Write me!

Basic sequence looks like this:

::

    # or wherever you like
    mkdir /tmp/workspace

    # Set your openstack (for now) credentials
    $EDITOR files/variables.yml

    # Run the ADEPT-four-step (finger-dance I made up)
    ./adept.py slave /tmp/workspace files/slave_container.yml
    ./adept.py setup /tmp/workspace files/slave_container.yml
    ./adept.py run /tmp/workspace files/slave_container.yml
    ./adept.py cleanup /tmp/workspace files/slave_container.yml

.. The quickstart section begins next
