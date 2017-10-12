To install:

    ln -sf $(pwd)/scripts/* $HOME/bin

To add pylint-odoo to PyCharm:

* Go to File - Settings - Tools - External Tools
* Add a tool, call it PyLint Odoo, with description Sunflower IT Pylint Odoo
* Under 'Options', tick 'Open Console' and leave others unchecked
* Under 'Show in', you can enable all four checkboxes
* Under 'Tool Settings', set Program to `pylint-odoo`
* Under 'Tool Settings', set Working directory to `$FileDir$`
* Under 'Output Filters', add a new output filter of any name containing `$FILE_PATH$\:$LINE$\:.*`
* To use, open a file and right-click External Tools - Pylint Odoo

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

