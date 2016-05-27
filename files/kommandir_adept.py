---

- command:
    filepath: /usr/bin/bash
    arguments: |
        -c 'set -e;
            cd $WORKSPACE;

            # TODO: This really belongs in variables.yml
            # These were updated in playbook above but may not be in env.

            . properties;

            for thing in "${KMNDRIP}" "${KMNDRWS}";
            do
                [ -n "$thing" ] || exit 1;
            done;

            if [ -z "${UNIQUE_JOB_ID}" ];
            then
                export UNIQUE_JOB_ID=$(/usr/bin/uuidgen);
                echo "UNIQUE_JOB_ID=${UNIQUE_JOB_ID}" >> properties;
            fi;

            ssh -tt -i ssh_private_key root@$KMNDRIP \
                "UNIQUE_JOB_ID=${UNIQUE_JOB_ID} ${KMNDRWS}/adept/adept.py \
                    $ADEPT_CONTEXT \
                    ${KMNDRWS} \
                    ${KMNDRWS}/adept/files/slave_container.yml \
                    $ADEPT_OPTIONAL";
            exit $?;'
