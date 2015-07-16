"""
Deployment script for Wiki Labels setup on Wikimedia Labs

Fabric script for doing multiple operations on Wiki Labels servers,
both production and staging.

## Setting up a new server ##

This assumes that the puppet role has been applied, and then you
can initialize it with:

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

    fab deploy_web

This updates all the web workers of wikilabels to the new code and restarts them.
"""
from fabric.api import cd, env, put, roles, shell_env, sudo

env.roledefs = {
    'web': ['labels-web.eqiad.wmflabs'],
    'staging': ['labels-staging.eqiad.wmflabs'],
    'database': ['labels-database.eqiad.wmflabs'],
}
env.use_ssh_config = True

src_dir = '/srv/wikilabels/src'
venv_dir = '/srv/wikilabels/venv'

def sr(*cmd):
    with shell_env(HOME='/srv/wikilabels'):
        return sudo(' '.join(cmd), user='www-data', group='www-data')


@roles('web')
def deploy_web():
    """
    Deploys updated code to the web server
    """
    update_config()
    upgrade_requirements()
    upload_oauth_creds()
    restart_uwsgi()

@roles('staging')
def stage():
    """
    Deployes updated code to the staging server
    """
    update_config('staging')
    upgrade_requirements()
    upload_oauth_creds()
    restart_uwsgi()

@roles('database')
def setup_db():
    """
    Initializes the database node
    """

    # Install requirements
    upgrade_requirements()

    # Create psql user & db
    sudo('createuser', 'wikilabels', '--createdb')

    # Load schema (will not overwrite data if exists)
    sr('wikilabels', 'load_schema', 'config/ores.wmflabs.org.yaml')

@roles('web')
def setup_web():
    """
    Initializes a web server node
    """

    # Install requirements
    upgrade_requirements()

    # Restart uWSGI
    restart_uwsgi()

def install_wikilabels():
    """
    Setup an initial deployment on a fresh host.
    """

    # Updates current version of wikilabels-wikimedia-config
    update_config()

    # Sets up a virtualenv directory
    sr('mkdir', '-p', venv_dir)
    sr('virtualenv', '--python', 'python3', '--system-site-packages', venv_dir)

    # Updates the virtualenv with new wikilabels code
    update_requirements()

@roles('web')
def update_config(branch='deploy'):
    """
    Updates the service configuration
    """
    with cd(src_dir):
        sr('git', 'fetch', 'origin')
        sr('git', 'reset', '--hard', 'origin/%s' % branch)


@roles('web')
def restart_uwsgi():
    """
    Restarts the uWSGI server
    """
    sudo('uwsgictl restart')


@roles('web')
def upgrade_requirements():
    """
    Installs upgraded versions of requirements (if applicable)
    """
    sr(venv_dir + '/bin/pip', 'install', '--upgrade',
       '-r', src_dir + '/requirements.txt')

@roles('web')
def upload_oauth_creds():
    put("oauth-wikimedia.yaml", '/srv/wikilabels/src/', use_sudo=True)
    sudo('chown', 'www-data:www-data',
         '/srv/wikilabels/src/oauth-wikimedia.yaml')

def run_puppet():
    sudo('puppet agent -tv')
