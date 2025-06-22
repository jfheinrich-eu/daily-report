#!/bin/bash

(sudo apt update && sudo apt install keychain -y)

(gh auth status || gh auth login) && gh extension install https://github.com/nektos/gh-act

(python -m pip install --user pip) && \
(pip install --upgrade pip) && \
(python -m pip install --user poetry) && \
(if [ -f pyproject.toml ]; then poetry install --no-root --with dev; fi)

/usr/bin/keychain \
--dir ~/.ssh/.keychain \
--gpg2 --agents gpg,ssh \
$(find ~/.ssh -name '*ed25519*' ! -iname '*.pub')

source ~/.ssh/.keychain/$HOSTNAME-sh
source ~/.ssh/.keychain/$HOSTNAME-sh-gpg

# Set GPG environment.
export GPG_TTY=$(tty)
