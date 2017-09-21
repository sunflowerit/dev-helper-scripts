To install:

    ln -sf $(pwd)/scripts/* $HOME/bin

For the issue script:

    pip install requests
    pip install odoorpc
    pip install pyOpenSSL ndg-httpsclient pyasn1
    touch $HOME/.netrc
    chmod 600 $HOME/.netrc

And place your Sunflower Odoo credentials in your $HOME/.netrc:

    machine odoosunflower login dan@sunflowerweb.nl password danspassword    

For pylint, install:

    pip install --upgrade --pre pylint-odoo

To update the Therp scripts:

    git clone git@gitlab.therp.nl:therp/deployment-scripts.git therp-scripts
    ln -sf $(pwd)/therp-scripts/bin/oe-get-buildout-versions.sh $HOME/bin

