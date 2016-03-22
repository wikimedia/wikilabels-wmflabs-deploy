"""
Deployment script for Wiki Labels setup on Wikimedia Labs

Fabric script for doing multiple operations on Wiki Labels servers,
both production and staging.

## Setting up a new server ##

This assumes that the puppet role has been applied, and then you
can initialize it with:

For staging:

    fab initialize_staging_server:hosts="<fqdn1>;<fqdn2>"

For production:

    fab initialize_server:hosts="<fqdn1>;<fqdn2>"

This:
    1. Sets up the virtualenv appropriately
    2. Sets up latest models
    3. Does a deploy / restarts uwsgi

For first time use, just doing this step should provide a working server!

## Deploying a code update to staging ##

This pushes the 'staging' branch to the staging server. Make sure to push
the changes you want to test / stage to the 'staging' branch before running
this! You can run this with:

    fab stage

This updates the staging server (labels-staging.wmflabs.org) with code from
the staging branch, and restarts uwsgi so the changes take effect.

## Deploying a code update to 'production' ##

This pushes the 'deploy' branch to the production servers. Make sure to push
the changes you want deployed to the 'deploy' branch before running this!
This can be simply run by:

    fab deploy

This updates all the web workers of wikilabels to the new code and restarts them.
"""
from fabric.api import cd, env, put, roles, shell_env, sudo
import os

env.roledefs = {
    'web': ['wikilabels-01.wikilabels.eqiad.wmflabs'],
    'staging': ['wikilabels-staging-01.wikilabels.eqiad.wmflabs'],
}
env.use_ssh_config = True
env.shell = '/bin/bash -c'

config_dir = '/srv/wikilabels/config'
venv_dir = '/srv/wikilabels/venv'
main_config_file = 'labels.wmflabs.org.yaml'
db_config_file = 'wikilabels-db-config.yaml'
oauth_creds_file = 'oauth-wikimedia.yaml'


def sr(*cmd):
    with shell_env(HOME='/srv/wikilabels'):
        return sudo(' '.join(cmd), user='www-data')


@roles('web')
def deploy():
    """
    Deploys updated code to the web server
    """
    update_config()
    upgrade_requirements()
    restart_uwsgi()


@roles('staging')
def stage(branch='master'):
    """
    Deployes updated code to the staging server
    """
    update_config(branch)
    upgrade_requirements()
    restart_uwsgi()


def setup_db():
    """
    Loads the db schema (will not overwrite data if exists)
    """
    sr(venv_dir + '/bin/wikilabels', 'load_schema',
        os.path.join(config_dir, main_config_file))


def initialize_staging_server():
    initialize_server('master')


def initialize_server(branch='deploy'):
    """
    Setup an initial deployment on a fresh host.
    """
    # Sets up a virtualenv directory
    sr('mkdir', '-p', venv_dir)
    sr('virtualenv', '--python', 'python3', venv_dir)

    # Updates current version of wikilabels-wikimedia-config
    update_config(branch)

    # Updates the virtualenv with new wikilabels code
    upgrade_requirements()

    # Uploads the db and oauth creds to the server
    upload_creds(branch)

    # Initialize DB
    setup_db()


def update_config(branch='deploy'):
    """
    Updates the service configuration
    """
    with cd(config_dir):
        sr('git', 'fetch', 'origin')
        sr('git', 'reset', '--hard', 'origin/%s' % branch)
        sr('git', 'submodule', 'update', '--init', '--recursive')


def restart_uwsgi():
    """
    Restarts the uWSGI server
    """
    sudo('service uwsgi-wikilabels-web restart')


def upgrade_requirements():
    """
    Installs upgraded versions of requirements (if applicable)
    """
    with cd(venv_dir):
        sr(venv_dir + '/bin/pip', 'install', '--upgrade', '-r',
            os.path.join(config_dir, 'requirements.txt'))


def upload_creds(branch='deploy'):
    """
    Uploads config files to server
    """
    # Upload oauth creds
    put(oauth_creds_file, config_dir, use_sudo=True)
    sudo("chown www-data:www-data " + os.path.join(config_dir, oauth_creds_file))

    # Upload postgres db config
    put(branch + "-db-config.yaml", os.path.join(config_dir, db_config_file),
        use_sudo=True)
    sudo("chown www-data:www-data " + os.path.join(config_dir, db_config_file))


def run_puppet():
    sudo('puppet agent -tv')
