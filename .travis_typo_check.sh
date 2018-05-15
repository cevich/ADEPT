#!/bin/bash

set -e

# Common typos, and other patterns to watch for. Dashes break up words so we
# don't trigger on ourself; spaces are for readability. Both will be removed.
TYPOS="e-c-o-h | r-o-e-l | FIX-ME | p-d-b-.set_trace | fix-up! | s-qua-sh!"
TYPOS=$(echo "$TYPOS" | tr -d ' -')

# Try to determine where we diverged from master, and use that as our
# base for diffs.
echo "Checking against master for conflict and whitespace problems:"
git diff --check $( echo $TRAVIS_COMMIT_RANGE | cut -d . -f 1) # Silent unless problem detected

git log -p $TRAVIS_COMMIT_RANGE -- . &> /tmp/commits_with_diffs
LINES=$(wc -l </tmp/commits_with_diffs)
if (( $LINES == 0 ))
then
    echo "FATAL: no changes found since ${ANCESTOR}"
    exit 3
fi

# The TYPOS value was formerly specified in .travis.yml
# TODO: Remove this workaround in another/later PR
sed -i -r -e '/^-        - TYPOS=/d' /tmp/commits_with_diffs

echo "Examining $LINES change lines for typos:"
egrep -a -i -2 --color=always "$TYPOS" /tmp/commits_with_diffs && exit 3

exit 0
