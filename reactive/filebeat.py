import charms.apt
from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import set_state
from charms.reactive import remove_state
from charms.reactive import hook
from charms.reactive.helpers import data_changed
from charms.templating.jinja2 import render

from charmhelpers.core.hookenv import config, status_set
from charmhelpers.core.host import restart_on_change, service_stop
from charmhelpers.core.host import file_hash, service

from elasticbeats import render_without_context
from elasticbeats import enable_beat_on_boot
from elasticbeats import push_beat_index

import base64
import os


LOGSTASH_SSL_CERT = '/etc/ssl/certs/filebeat-logstash.crt'
LOGSTASH_SSL_KEY = '/etc/ssl/private/filebeat-logstash.key'


@when_not('apt.installed.filebeat')
def install_filebeat():
    status_set('maintenance', 'Installing filebeat.')
    charms.apt.queue_install(['filebeat'])


@when('beat.render')
@when('apt.installed.filebeat')
@restart_on_change({
    LOGSTASH_SSL_CERT: ['filebeat'],
    LOGSTASH_SSL_KEY: ['filebeat'],
    })
def render_filebeat_template():
    cfg_path = '/etc/filebeat/filebeat.yml'
    cfg_original_hash = file_hash(cfg_path)
    connections = render_without_context('filebeat.yml', cfg_path)
    cfg_new_hash = file_hash(cfg_path)

    # Ensure ssl files match config each time we render a new template
    manage_filebeat_logstash_ssl()
    remove_state('beat.render')

    if connections:
        if cfg_original_hash != cfg_new_hash:
            service('restart', 'filebeat')
        status_set('active', 'Filebeat ready.')
    else:
        service('stop', 'filebeat')
        status_set('waiting', 'Waiting for connections.')


def manage_filebeat_logstash_ssl():
    """Manage the ssl cert/key that filebeat uses to connect to logstash.

    Create the cert/key files when both logstash_ssl options have been set;
    update when either config option changes; remove if either gets unset.
    """
    logstash_ssl_cert = config().get('logstash_ssl_cert')
    logstash_ssl_key = config().get('logstash_ssl_key')
    if logstash_ssl_cert and logstash_ssl_key:
        cert = base64.b64decode(logstash_ssl_cert).decode('utf8')
        key = base64.b64decode(logstash_ssl_key).decode('utf8')

        if data_changed('logstash_cert', cert):
            render(template='{{ data }}',
                   context={'data': cert},
                   target=LOGSTASH_SSL_CERT, perms=0o444)
        if data_changed('logstash_key', key):
            render(template='{{ data }}',
                   context={'data': key},
                   target=LOGSTASH_SSL_KEY, perms=0o400)
    else:
        if not logstash_ssl_cert and os.path.exists(LOGSTASH_SSL_CERT):
            os.remove(LOGSTASH_SSL_CERT)
        if not logstash_ssl_key and os.path.exists(LOGSTASH_SSL_KEY):
            os.remove(LOGSTASH_SSL_KEY)


@when('apt.installed.filebeat')
@when_not('filebeat.autostarted')
def enlist_filebeat():
    enable_beat_on_boot('filebeat')
    set_state('filebeat.autostarted')


@when('apt.installed.filebeat')
@when('elasticsearch.available')
@when_not('filebeat.index.pushed')
def push_filebeat_index(elasticsearch):
    hosts = elasticsearch.list_unit_data()
    for host in hosts:
        host_string = "{}:{}".format(host['host'], host['port'])
    push_beat_index(host_string, 'filebeat')
    set_state('filebeat.index.pushed')


@hook('stop')
def remove_filebeat():
    service_stop('filebeat')
    try:
        os.remove('/etc/filebeat/filebeat.yml')
    except OSError:
        pass
    charms.apt.purge('filebeat')
