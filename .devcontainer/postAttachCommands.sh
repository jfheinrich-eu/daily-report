#!/bin/bash

(sudo apt update && sudo apt install keychain shellcheck -y)

(gh auth status || gh auth login) && gh extension install https://github.com/nektos/gh-act

(python -m pip install --user pip) && \
(pip install --upgrade pip) && \
(python -m pip install --user poetry) && \
(if [ -f pyproject.toml ]; then poetry self add 'poethepoet[poetry_plugin]' && poetry install --no-root --with dev; fi)

/usr/bin/keychain \
--dir ~/.ssh/.keychain \
--gpg2 --agents gpg,ssh \
"$(find ~/.ssh -name '*ed25519*' ! -iname '*.pub')"

# shellcheck source=/home/vscode/.ssh/.keychain/daily-report-devcontainer-sh
source "$HOME/.ssh/.keychain/$HOSTNAME-sh"
# shellcheck source=/home/vscode/.ssh/.keychain/daily-report-devcontainer-sh-gpg
source "$HOME/.ssh/.keychain/$HOSTNAME-sh-gpg"

# Set GPG environment.
GPG_TTY_VALUE=$(tty)
export GPG_TTY="$GPG_TTY_VALUE"
