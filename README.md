To install or upgrade:

    pip install --user https://github.com/sunflowerit/dev-helper-scripts/archive/master.zip

Add to your `$HOME/.profile`:

    if [ -d "$HOME/.local/bin" ] ; then
        PATH="$HOME/.local/bin:$PATH"
    fi

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

