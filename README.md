To install:

    ln -sf $(pwd)/scripts/* $HOME/bin

For scripts like the issue script, that use erppeek:

    pip install --user erppeek pyOpenSSL ndg-httpsclient pyasn1
    cp erppeek.ini.template $HOME/.erppeek.ini  # and edit it

For pylint, install:

    pip install --upgrade --pre pylint-odoo

To update the Therp script:

    git clone git@gitlab.therp.nl:therp/deployment-scripts.git therp-scripts
    cp -f therp-scripts/bin/oe-get-buildout-versions.sh scripts

