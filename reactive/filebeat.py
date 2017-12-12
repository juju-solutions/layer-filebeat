import charms.apt
from charms.reactive import when
from charms.reactive import when_any
from charms.reactive import when_not
from charms.reactive import set_state
from charms.reactive import remove_state
from charms.reactive import hook
from charms.templating.jinja2 import render

from charmhelpers.core.hookenv import config, status_set
from charmhelpers.core.host import restart_on_change, service_stop

from elasticbeats import render_without_context
from elasticbeats import enable_beat_on_boot
from elasticbeats import push_beat_index

import os


LOGSTASH_SSL_CERT = '/etc/ssl/certs/filebeat-logstash.crt'
LOGSTASH_SSL_KEY = '/etc/ssl/private/filebeat-logstash.key'


@when_not('apt.installed.filebeat')
def install_filebeat():
    status_set('maintenance', 'Installing filebeat.')
    charms.apt.queue_install(['filebeat'])


@restart_on_change('/etc/filebeat/filebeat.yml', ['filebeat'])
@when('beat.render')
@when('apt.installed.filebeat')
def render_filebeat_template():
    connections = render_without_context('filebeat.yml', '/etc/filebeat/filebeat.yml')
    remove_state('beat.render')
    if connections:
        status_set('active', 'Filebeat ready.')


@restart_on_change({
    LOGSTASH_SSL_CERT: ['filebeat'],
    LOGSTASH_SSL_KEY: ['filebeat'],
    })
@when('beat.render')
@when('apt.installed.filebeat')
def render_filebeat_logstash_ssl_cert():
    logstash_ssl_cert = config().get('logstash_ssl_cert')
    logstash_ssl_key = config().get('logstash_ssl_key')
    if logstash_ssl_cert and logstash_ssl_key:
        render(template='{{ data }}',
               context={'data': logstash_ssl_cert},
               target=LOGSTASH_SSL_CERT, perms=0o444)
        render(template='{{ data }}',
               context={'data': logstash_ssl_key},
               target=LOGSTASH_SSL_KEY, perms=0o400)
    else:
        if not logstash_ssl_cert and os.path.exists(LOGSTASH_SSL_CERT):
            os.remove(LOGSTASH_SSL_CERT)
        if not logstash_ssl_key and os.path.exists(LOGSTASH_SSL_KEY):
            os.remove(LOGSTASH_SSL_KEY)


@when('apt.installed.filebeat')
@when_not('filebeat.autostarted')
def enlist_packetbeat():
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
