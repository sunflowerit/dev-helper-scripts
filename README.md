To install or upgrade as user (note: on Ubuntu-like systems this will fail because python-cryptography egg wont install as non-root):

    pip install --upgrade --user https://github.com/sunflowerit/dev-helper-scripts/archive/master.zip

Add to your `$HOME/.profile`:

    if [ -d "$HOME/.local/bin" ] ; then
        PATH="$HOME/.local/bin:$PATH"
    fi

To install or upgrade as root:

    sudo pip install --upgrade https://github.com/sunflowerit/dev-helper-scripts/archive/master.zip

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

    touch $HOME/.netrc
    chmod 600 $HOME/.netrc

Place your Sunflower Odoo credentials in your $HOME/.netrc:

    machine odoosunflower login dan@sunflowerweb.nl password danspassword    

To update the Therp scripts:

    git clone git@gitlab.therp.nl:therp/deployment-scripts.git therp-scripts
    ln -sf $(pwd)/therp-scripts/bin/oe-get-buildout-versions.sh $HOME/bin

