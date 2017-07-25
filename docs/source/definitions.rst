Definitions
==============

``context``:
             The label given to the end-state / completion of a transition.
             Analogous to a "phase", or collection of related steps. The context
             label (string) is assumed to pass unmodified, through all
             facilities (adept.py files, playbooks, scripts, etc.) and through
             all layers (original calling host, through slave, and into testing
             hosts). No facility or layer will alter the context label from
             the one originally passed into the first, lowest-level call of
             ``adept.py``.

``transition``:
                The collection of steps necessary to realize a context.
                Analogous to the act of performing all described tasks
                within a "phase" to reach some end-state.

``setup``, ``run``, and ``cleanup``:
                                     The three context labels currently
                                     used in ADEPT.  Operationally,
                                     the *run* context is dependent (to some degree)
                                     on a successful *setup* transition.  However,
                                     the *cleanup* context transition does not
                                     depend on success or failure of either
                                     *setup* or *run*.

``job``:
         A single, top-level invocation through all context transitions,
         concluding in a resource-clean, final end-state.  Independent
         of the existence of any results or useful data.  Logically represented
         by a set of files within the path pointed to by the ``job_path`` variable.

``exekutir``:
              The initial, starting host that executes one or more jobs.
              In practice this is just a fancy name for ``localhost``,
              in concept it's a more distinguished/specif name relevant
              to the cloud-nature of ADEPT.

``kommandir``:
               The name of the "slave" VM as referenced from within playbooks,
               adept files, and configurations.  Currently based on CentOs,
               it's utilized by one or more concurrent jobs to offloads work
               from the *exekutir*.

``peon``:
          The lowest-level VM used for testing (running playbooks).
          Assumed to be controlled by a one-way connection from the *kommandir*.
          Cannot and must not be able to access the *kommandir* or *exekutir*.
