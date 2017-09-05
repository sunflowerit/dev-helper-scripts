To install bash scripts:

    ln -sf $(pwd)/scripts/* $HOME/bin

For scripts like the issue script, that use erppeek:

    pip install --user erppeek pyOpenSSL ndg-httpsclient pyasn1
    cp erppeek.ini.template $HOME/.erppeek.ini  # and edit it
