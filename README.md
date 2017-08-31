To install bash scripts:

    ln -sf $(pwd)/scripts/* $HOME/bin

To install erppeek:

    pip install --user erppeek pyOpenSSL ndg-httpsclient pyasn1
    cp erppeek.ini.template erppeek.ini  # and edit erppeek.ini
