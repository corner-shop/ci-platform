import os
import shutil
import bz2
import requests
import yaml
import tarfile
import zipfile
from jinja2 import FileSystemLoader
from jinja2.environment import Environment
from cStringIO import StringIO
from multiprocessing import Pool
from functools import partial



# TODO: REFACTOR this file

def download_plugin(params):
    (name, version) = params
    if not os.path.exists('target/var/lib/jenkins/'
                          'plugins/%s.jpi' % name):
        print('Downloading plugin %s' % name)
        r = requests.get(
            'http://mirror.xmission.com/jenkins/plugins/'
            '%s/%s/%s.jpi' % (name,
                              version,
                              name)
        )

        # no .jpi available, lets go for a .hpi
        if r.status_code != 200:
            r = requests.get(
                'http://mirror.xmission.com/jenkins/plugins/'
                '%s/%s/%s.hpi' % (name,
                                  version,
                                  name)
            )
        with open('target/var/lib/jenkins/'
                  'plugins/%s.jpi' % name, 'w') as f:
            f.write(r.content)

        # https://wiki.jenkins-ci.org/display/JENKINS/Pinned+Plugins
        with open('target/var/lib/jenkins/'
                  'plugins/%s.jpi.pinned' % name, 'w') as f:
            f.write('')

        path = 'target/var/lib/jenkins/plugins/%s' % name
        if not os.path.exists(path):
            os.makedirs(path)

        with open('target/var/lib/jenkins/plugins'
                  '/%s.jpi' % name, "r") as f:
            zf = zipfile.ZipFile(f)
            zf.extractall(path=path)


def install_plugins(plugins):
    names = []
    versions = []
    for p in plugins:
        names.append(p['name'])
        versions.append(p['version'])

    jobs = [ (p['name'],p['version']) for p in plugins ]

    pool = Pool(processes=16)
    pool.map(download_plugin, jobs)




env = Environment()
env.loader = FileSystemLoader('templates')

# config.yml contains all the configuration settings for our jenkins box
#
with open('config.yml') as f:
    config = yaml.load(f)

# we map the current working directory to /build on the docker instance
# at build time, and create a number of directories and files inside
# /build/target. These files are built/templated from the jinja2 files in the
# templates folder.
dirs = ['target/var/lib/jenkins/plugins',
        'target/var/lib/jenkins/users',
        'target/var/lib/jenkins/slave_config',
        'target/var/lib/jenkins/nodes/node_name',
        'target/var/lib/jenkins/.ssh',
        'target/var/lib/jenkins/log',
        'target/var/lib/jenkins/secrets',
        'target/etc/service/jenkins']

for _dir in dirs:
    if not os.path.exists(_dir):
        os.makedirs(_dir)

# generate XML from our jinja2 files
#
config_pairs = [
    {'j2': 'config.xml.j2',
     'xml': 'target/var/lib/jenkins/config.xml'},

    {'j2': 'org.jenkinsci.plugins.statsd.StatsdConfig.xml.j2',
     'xml': 'target/var/lib/'
            'jenkins/org.jenkinsci.plugins.statsd.StatsdConfig.xml'},

    {'j2': 'org.jenkinsci.plugins.slave_setup.SetupConfig.xml.j2',
     'xml': 'target/var/lib/jenkins/'
            'org.jenkinsci.plugins.slave_setup.SetupConfig.xml'},

    {'j2': 'CommandLineScript.sh.j2',
     'xml': 'target/var/lib/jenkins/slave_config/CommandLineScript.sh'},

    {'j2': 'nodeMonitors.xml.j2',
     'xml': 'target/var/lib/jenkins/nodeMonitors.xml'},

    {'j2': 'credentials.xml.j2',
     'xml': 'target/var/lib/jenkins/credentials.xml'},

    {'j2': 'sauce-ondemand.xml.j2',
     'xml': 'target/var/lib/jenkins/sauce-ondemand.xml'},

    {'j2': 'proxy.xml.j2',
     'xml': 'target/var/lib/jenkins/proxy.xml'},
]

for entry in config_pairs:
    with open(entry['xml'], 'w') as f:
        tmpl = env.get_template(entry['j2'])
        f.write(tmpl.render(config))


# some files are not templated yet, these are copied directly and not
# parsed through jinja2
#
config_pairs = [
    {'src': 'templates/log/hudson.plugins.ec2.ebs.ZPoolMonitor.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.ebs.ZPoolMonitor.xml'},

    {'src': 'templates/log/hudson.plugins.ec2.EC2AbstractSlave.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.EC2AbstractSlave.xml'},

    {'src': 'templates/log/hudson.plugins.ec2.EC2Cloud.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.EC2Cloud.xml'},

    {'src': 'templates/log/hudson.plugins.ec2.EC2ComputerLauncher.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.EC2ComputerLauncher.xml'},

    {'src': 'templates/log/hudson.plugins.ec2.EC2OndemandSlave.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.EC2OndemandSlave.xml'},

    {'src': 'templates/log/hudson.plugins.ec2.EC2RetentionStrategy.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.EC2RetentionStrategy.xml'},

    {'src': 'templates/log/hudson.plugins.ec2.EC2SlaveMonitor.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.EC2SlaveMonitor.xml'},

    {'src': 'templates/log/hudson.plugins.ec2.SlaveTemplate.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.SlaveTemplate.xml'},

    {'src': 'templates/log/hudson.plugins.ec2.ssh.EC2UnixLauncher.xml',
     'dest': 'target/var/lib/jenkins/log/'
             'hudson.plugins.ec2.ssh.EC2UnixLauncher.xml'},

]

for entry in config_pairs:
    shutil.copyfile(entry['src'], entry['dest'])


# all usernames and passwords for jenkins are kept in the config.yaml file
#
for user in config['jenkins']['users']:
    path = 'target/var/lib/jenkins/users/%s' % user['username']

    if not os.path.exists(path):
        os.mkdir(path)

    with open('%s/config.xml' % path, 'w') as f:
        tmpl = env.get_template('do_jenkinsUser.xml.j2')
        f.write(tmpl.render(user))


# Here we configure some static nodes, the configuration for these is kept in
# the config.yaml file.
#
for slave in config['jenkins']['static_slaves']:

    path = 'target/var/lib/jenkins/nodes/%s' % slave['name']
    if not os.path.exists(path):
        os.makedirs(path)

    with open('target/var/lib/jenkins/'
              'nodes/%s/config.xml' % slave['name'], 'w') as f:
        tmpl = env.get_template('static_slave.xml.j2')
        f.write(tmpl.render(slave))


# install plugins
install_plugins(config['jenkins']['plugins'])


for plugin in config['jenkins']['non_published_plugins']:
    if not os.path.exists('target/var/lib/jenkins/'
                          'plugins/%s.jpi' % plugin['name']):
        print('Downloading plugin %s' % plugin['name'])
        r = requests.get(plugin['url'])
        with open('target/var/lib/jenkins/'
                  'plugins/%s.jpi' % plugin['name'], 'w') as f:
            f.write(r.content)

# generate the seed job config
path = 'target/var/lib/jenkins/jobs/seed_job/'
if not os.path.exists(path):
    os.makedirs(path)
tmpl = env.get_template('seed_job.xml.j2')
with open('%s/config.xml' % path, 'w') as f:
    f.write(tmpl.render(config['jenkins']['seed_job']))

path = 'target/var/lib/jenkins/jobs/seed_job/workspace/'
if not os.path.exists(path):
    os.makedirs(path)
tmpl = env.get_template('seed.job.groovy.j2')
with open('%s/seed.job.groovy' % path, 'w') as f:
    f.write(tmpl.render(config['jenkins']['seed_job']))

# update the .ssh keys
with open('target/var/lib/jenkins/.ssh/id_rsa', 'w') as f:
    tmpl = env.get_template('jenkins_private_key.j2')
    f.write(tmpl.render(config))

with open('target/var/lib/jenkins/.ssh/id_rsa.pub', 'w') as f:
    tmpl = env.get_template('jenkins_public_key.j2')
    f.write(tmpl.render(config))

with open('target/var/lib/jenkins/.ssh/authorized_keys', 'w') as f:
    tmpl = env.get_template('authorized_keys.j2')
    f.write(tmpl.render(config))

with open('target/etc/service/jenkins/run', 'w') as f:
    tmpl = env.get_template('etc.service.jenkins.run.j2')
    f.write(tmpl.render(config))

# write the secrets
encoded_tar_bz2_file = config['jenkins']['credentials']['secrets_tar_bz']
tar_bz2_file = encoded_tar_bz2_file.decode('base64')
tar_file = bz2.decompress(tar_bz2_file)
f = StringIO(tar_file)

target_folder = 'target/var/lib/jenkins/'
with tarfile.open(fileobj=f, mode='r:') as tar:
    tar.extractall(target_folder)
