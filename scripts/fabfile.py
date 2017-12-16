# Fabfile to:
#    - Download backups of all odoos

import os
import time

from fabric.context_managers import *
from fabric.contrib.files import exists
from fabric.api import *


env.hosts = ['applejuice.sunflowerweb.nl']
env.user = 'terrence'

def get_password():
    password = sudo("pwgen | awk '{print $1;}'", user='root')
    return password

def setup_unix_user(INSTANCE, PASSWORD):
    sudo(
        "PASSWORD={PASSWORD}; \
        echo $PASSWORD; \
        INSTANCE={INSTANCE}; \
        echo $INSTANCE; \
        USERNAME=odoo-$INSTANCE; \
        echo $USERNAME; \
        adduser $USERNAME --disabled-password --gecos GECOS;\
        echo $USERNAME:$PASSWORD | chpasswd;\
        mkdir -p /home/$USERNAME/.ssh;\
        cp /home/odoo-sunflower/.ssh/authorized_keys /home/$USERNAME/.ssh/authorized_keys;\
        cp /home/odoo-sunflower/.vimrc /home/$USERNAME/.vimrc;\
        chmod 700 /home/$USERNAME/.ssh;\
        chmod 600 /home/$USERNAME/.ssh/authorized_keys;\
        chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh /home/$USERNAME/.vimrc"
        .format(**{
            'INSTANCE': INSTANCE,
            'PASSWORD': PASSWORD,
        }),
        user='root'
    )
    sudo
    print('Unix User Setup Successful...')

def setup_postgres_user(INSTANCE, PASSWORD):
    sudo(
        "createuser {DBUSER}; \
        psql postgres -tAc \"ALTER USER {DBUSER} WITH PASSWORD '{PASSWORD}'\"; \
        psql postgres -tAc \"ALTER USER {DBUSER} CREATEDB\""
        .format(**{
            'DBUSER': 'odoo'+INSTANCE,
            'PASSWORD': PASSWORD,
        }),
        user='postgres'
    )
    print('Postgres User Setup Successful...')

def unix_user_exists(INSTANCE):
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True
    ):
        check_user = sudo(
            "id -u odoo-{INSTANCE}".format(**{
                'INSTANCE': INSTANCE,
            }),
            user='root'
        )
        if "no such user" in check_user: 
            print('Unix User does not exist')
            return False
        else:
            print('Unix User exist')
            return True

def postgres_user_exists(INSTANCE):
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True
    ):
        check_user = sudo(
            "psql postgres -tAc \"SELECT 1 FROM pg_roles WHERE rolname='odoo{INSTANCE}'\"".format(**{
                'INSTANCE': INSTANCE,
            }),
            user='postgres'
        )
        return check_user
           
def add_host_to_ssh_config(USERNAME):
    from os.path import expanduser
    home = expanduser("~")
    config_file = "{}/.ssh/config".format(home)

    # CHECK IF HOST EXISTS IN ./ssh/config
    host_exists = False
    searchfile = open(config_file, "r")
    for line in searchfile:
        if USERNAME in line: 
            host_exists = USERNAME
    searchfile.close()

    #ADD HOST TO ./ssh/config
    if not host_exists:
        with open(config_file, "a") as config:
            config.write("""\nHost {USERNAME}\n\
    ForwardAgent yes\n\
    HostName applejuice.sunflowerweb.nl\n\
    User {USERNAME}\n""".format(**{
                'USERNAME': USERNAME,
            }),)

def ssh_git_clone(USERNAME):
    known_hosts= sudo("find /home/{}/.ssh -name known_hosts".format(USERNAME), user='root')
    buildout = sudo("find /home/{} -type d -name buildout".format(USERNAME), user='root')
    if not known_hosts:
        print "Known Hosts does not exist, adding file known_hosts..."
        os.system("ssh {USERNAME} 'touch /home/{USERNAME}/.ssh/known_hosts'".format(**{
            'USERNAME': USERNAME,
        }))
        os.system("ssh {USERNAME} 'ssh-keygen -F github.com || ssh-keyscan github.com >> /home/{USERNAME}/.ssh/known_hosts'".format(**{
            'USERNAME': USERNAME,
        }))
    if not buildout:
        print "Buildout does not exist, cloning into home dir..."
        os.system("ssh {} 'git clone git@github.com:sunflowerit/custom-installations.git --branch 10.0-custom-standard --single-branch buildout'".format(USERNAME))

def run_buildout(USERNAME, PORT):
    os.system("ssh {} 'python buildout/bootstrap.py -c buildout/local.cfg'".format(USERNAME))
    os.system("ssh {} 'python buildout/bin/buildout -c buildout/local.cfg'".format(USERNAME))
    os.system("ssh {} 'python buildout/bin/buildout -c buildout/local.cfg'".format(USERNAME))


def add_and_start_odoo_service(INSTANCE, USERNAME, PORT):
    service= sudo("find /lib/systemd/system/ -name {0}.service".format(USERNAME), user='root')
    if not service:
        sudo(
            "echo '\
[Unit]\n\
Description=Odoo {INSTANCE}\n\
After=postgresql.service\n\n\
[Service]\n\
Type=simple\n\
User={USERNAME}\n\
ExecStart=/home/{USERNAME}/buildout/bin/start_odoo\n\n\
[Install]\n\
WantedBy=default.target\n' > /lib/systemd/system/{USERNAME}.service".format(**{
                'USERNAME': USERNAME,
                'INSTANCE': INSTANCE,
            }),
            user='root')

    sudo(
        "systemctl daemon-reload && systemctl start {USERNAME};\
        systemctl status {USERNAME} -l;\
        telnet localhost {PORT} -l;\
        systemctl enable {USERNAME} -l".format(**{
            'USERNAME': USERNAME,
            'PORT': PORT,
        }),
        user='root')

def encrypt_https_certificate(URL):
    sudo("service nginx stop;\
        certbot certonly -d {0} -m info@sunflowerweb.nl -n --agree-tos --standalone;\
        service nginx start".format(URL),
        user='root')
      


def create_local_cfg(INSTANCE, PORT, DBUSER, USERNAME, PASSWORD):
    file = sudo("find /home/{}/buildout -name local.cfg".format(USERNAME), user='root')
    if not file:
        print "Local.cfg does not exists, creating file local.cfg ..."
        sudo(
            "echo '\
[buildout]\n\
extends = odoo10-standard.cfg \n\n\
[odoo]\n\
options.admin_passwd = {PASSWORD}\n\
options.db_host = localhost\n\
options.db_name = {DBUSER}\n\
options.db_port = 5432\n\
options.db_user = {DBUSER}\n\
options.db_password = {PASSWORD}\n\
options.xmlrpc_port =   {PORT}\n\
options.longpolling_port = {LONG_PORT}\n\
options.dbfilter = ^{INSTANCE}.*$\n\
options.logfile = /home/{USERNAME}/{USERNAME}.log' >/home/{USERNAME}/buildout/local.cfg".format(**{
                'USERNAME': USERNAME,
                'DBUSER': DBUSER,
                'INSTANCE': INSTANCE,
                'PASSWORD': PASSWORD,
                'PORT': PORT,
                'LONG_PORT': PORT+1,
            }),
        user=USERNAME)

def get_port():
    port_lines = sudo(
        "lsof -P -i -n -sTCP:LISTEN",
        user='root'
    )
    open_ports = []
    for port_details in port_lines.splitlines():
        p = port_details.split(':')
        port = p[-1][:-9]
        if port.isdigit():
            open_ports.append(int(port))

    return max(open_ports) + 2

def configure_nginx(INSTANCE, USERNAME, PORT, URL): 
    NGINXFILE = "odoo_"+INSTANCE
    SERVERNAME= INSTANCE+".1systeem.nl" 
    xmlrpc_port=PORT
    long_port=PORT+1
    semicolon = ';'
    right_par = '}'
    left_par = '{'
    dollar = "$'\'"

    config_file = sudo("find /etc/nginx/sites-available -name {0}".format(NGINXFILE), user='root')
    # if not config_file: #CHANGE
    sudo(
        "echo '\
server {left_par}\n\
  listen 80{semicolon}\n\
  server_name {SERVERNAME}{semicolon}\n\
  location / {left_par}\n\
    return 301 https://\{dollar}host\{dollar}request_uri{semicolon}\n\
  {right_par}\n\
{right_par}\n\n\
server {left_par}\n\
  listen 443{semicolon}\n\
  server_name {SERVERNAME}{semicolon}\n\n\
  ssl on{semicolon}\n\
  ssl_certificate /etc/letsencrypt/live/{SERVERNAME}/cert.pem{semicolon}\n\
  ssl_certificate_key /etc/letsencrypt/live/{SERVERNAME}/privkey.pem{semicolon}\n\
  ssl_dhparam /etc/ssl/certs/dhparam.pem{semicolon}\n\
  add_header Strict-Transport-Security max-age=2592000{semicolon}\n\n\
  # increase file upload size\n\
  client_max_body_size 200M{semicolon}\n\n\
  # increase timeouts to avoid nginx gateway timeout for long requests\n\
  proxy_connect_timeout       6000s{semicolon}\n\
  proxy_send_timeout          6000s{semicolon}\n\
  proxy_read_timeout          6000s{semicolon}\n\
  send_timeout                6000s{semicolon}\n\n\
  # add headers\n\
  proxy_set_header   Host      \{dollar}http_host{semicolon}\n\
  proxy_set_header   X-Real-IP \{dollar}remote_addr{semicolon}\n\
  proxy_set_header   X-Forward-For \{dollar}proxy_add_x_forwarded_for{semicolon}\n\n\
  location / {left_par}\n\
    proxy_pass http://127.0.0.1:{xmlrpc_port}{semicolon}\n\
    proxy_set_header Host \{dollar}host{semicolon}\n\
    proxy_set_header X-Real-IP \{dollar}remote_addr{semicolon}\n\
    proxy_set_header X-Scheme \{dollar}scheme{semicolon}\n\
    proxy_connect_timeout 600{semicolon}\n\
    proxy_send_timeout 600{semicolon}\n\
    proxy_read_timeout 600{semicolon}\n\
  {right_par}\n\n\
  location /longpolling {left_par}\n\
    proxy_pass http://127.0.0.1:{long_port}{semicolon}\n\
  {right_par}\n\
{right_par}' >/etc/nginx/sites-available/{NGINXFILE}".format(**{
                'SERVERNAME': SERVERNAME,
                'NGINXFILE': NGINXFILE,
                'xmlrpc_port': xmlrpc_port,
                'long_port': long_port,
                'left_par': left_par,
                'right_par': right_par,
                'semicolon': semicolon,
                'dollar': dollar,
        }),
    user='root')

    sudo("nginx_ensite {0};\
        systemctl restart nginx;".format(NGINXFILE), 
        user='root')

    os.system("ssh {} 'buildout/bin/upgrade_odoo'".format(USERNAME))
    os.system("ssh {USERNAME} 'service {USERNAME} restart'".format(**{
            'USERNAME': USERNAME,
        })
    )

def after_installation(INSTANCE, DBUSER, USERNAME, PASSWORD):
    #ALTER USER $USERNAME NOCREATEDB;
    sudo(
        "psql postgres -tAc \"ALTER USER {DBUSER} NOCREATEDB\""
        .format(**{
            'DBUSER': 'odoo'+INSTANCE,
            'PASSWORD': PASSWORD,
        }),
        user='postgres'
    )

    #visudo
    sudo(
        "echo '\
{USERNAME} ALL=NOPASSWD: /usr/sbin/service {USERNAME} restart\n\
{USERNAME} ALL=NOPASSWD: /usr/sbin/service {USERNAME} stop\n\
{USERNAME} ALL=NOPASSWD: /usr/sbin/service {USERNAME} start' >/home/{USERNAME}/buildout/local.cfg".format(**{
                'USERNAME': USERNAME,
            }),
        user='root')

    #Add the restart script
    sudo(
        "echo 'sudo /usr/sbin/service {USERNAME} restart > /home/{USERNAME}/buildout/restart';\
        chmod u+x /home/{USERNAME}/buildout/restart".format(**{
            'USERNAME': USERNAME,
        }),
    user='root')

def send_config_to_mail():
    pass
    #TODO

def install_odoo(instance=False, url=False):
    #fab install_odoo:instance=testv2,url=testurl
    if not instance:
        print "You need to add instance name: run 'fab install_odoo:instance=NAME_OF_YOUR_INSTANCE'"
    else:
        URL = url or instance+'.1systeem.nl'
        PASSWORD = get_password()
        PORT = get_port()
        INSTANCE = instance
        USERNAME = "odoo-"+INSTANCE
        DBUSER = "odoo"+INSTANCE
        if not unix_user_exists(INSTANCE):
            print "Setting up Unix User..."
            setup_unix_user(INSTANCE, PASSWORD)

        if not postgres_user_exists(INSTANCE):
            print "Setting up Postgres User..."
            setup_postgres_user(INSTANCE, PASSWORD)

        add_host_to_ssh_config(USERNAME)
        ssh_git_clone(USERNAME)
        create_local_cfg(INSTANCE, PORT, DBUSER, USERNAME, PASSWORD)
        run_buildout(USERNAME, PORT)
        add_and_start_odoo_service(INSTANCE, USERNAME, PORT)
        encrypt_https_certificate(URL)
        configure_nginx(INSTANCE, USERNAME, PORT, URL)
        after_installation(INSTANCE, DBUSER, USERNAME, PASSWORD)
        # send_config_to_mail(email)

        print('Yay, we are done, visit your odoo instance at: \n https://{}'.format(URL))


def backup():
    # can use this to do for each buildout 
    # require('buildouts', provided_by=[irodion])
    
    for host in env.hosts:
        date = time.strftime('%Y%m%d%H%M%S')
        fname = '/tmp/{host}-backup-{date}.xz'.format(**{
            'host': host,
            'date': date,
        })

        output = sudo(
            "psql -P pager -t -A -c 'SELECT datname FROM pg_database'",
            user='postgres'
        )
        for database in output.splitlines():
            fname = '/tmp/{host}-{database}-backup-{date}.xz'.format(**{
                'host': host,
                'database': database,
                'date': date,
            })
            if exists(fname):
                run('rm "{0}"'.format(fname))

            #pg_dump $db |gzip -f > /tmp/pg_$db.sql.gz
            # sudo su - postgres
            sudo('cd; pg_dump {database} | xz > {fname}'.format(**{
                'database': database, 
                'fname': fname,
            }), user='postgres')

        #if exists(fname):
        #    run('rm "{0}"'.format(fname))
        #
        #sudo('cd; pg_dumpall | xz > {0}'.format(fname), user='postgres')
        #
        get(fname, os.path.basename(fname))
        sudo('rm "{0}"'.format(fname), user='postgres')

    # def backup():

    # sudo to backup user
    # catch all the legacy backups
    # copy them here
    # remove them there.
    # mail someone if there is some missing
    # that doesnt have the required date or name

    # sudo to each odoo
    # install oca backup module if its not there yet
    # do the backup from a buildout script
    # download it


