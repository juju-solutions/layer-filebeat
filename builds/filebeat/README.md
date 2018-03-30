# Filebeat

A lightweight, open source shipper for log file data. As the
next-generation Logstash Forwarder, Filebeat tails logs and quickly sends this
information to Logstash for further parsing and enrichment or to Elasticsearch
for centralized storage and analysis.


## Usage

Filebeat can be added to any principal charm thanks to the wonders of being
a subordinate charm. The following usage example will deploy an ubuntu
log source along with the elk stack so we can visualize our log data.

    juju deploy ~elasticsearch-charmers/bundle/elk-stack
    juju deploy xenial/filebeat
    juju deploy xenial/ubuntu
    juju add-relation filebeat:beats-host ubuntu
    juju add-relation filebeat logstash


### Deploying the minimal Beats formation

If you do not need log buffering and alternate transforms on data that is
being shipped to ElasticSearch, you can simply deploy the 'beats-core' bundle
which stands up Elasticsearch, Kibana, and the known working Beats
subordinate applications.

    juju deploy ~containers/bundle/beats-core
    juju deploy xenial/ubuntu
    juju add-relation filebeat:beats-host ubuntu
    juju add-relation topbeat:beats-host ubuntu

### Changing what is shipped

By default, the Filebeat charm is setup to ship everything in:

    /var/log/*/*.log
    /var/log/*.log
<!-- /* -->

If you'd rather target specific log files:

    juju config filebeat logpath /var/log/mylog.log


## Testing the deployment

The applications provide extended status reporting to indicate when they are
ready:

    juju status

This is particularly useful when combined with watch to track the on-going
progress of the deployment:

    watch juju status

The message for each unit will provide information about that unit's state.
Once they all indicate that they are ready, you can navigate to the kibana
url and view the streamed log data from the Ubuntu host.

    juju status kibana --format=yaml | grep public-address

Navigate to http://&lt;kibana-ip&gt;/ in a browser and begin creating your
dashboard visualizations.


## Scale Out Usage

This bundle was designed to scale out. To increase the amount of log storage and
indexers, you can add-units to elasticsearch.

    juju add-unit elasticsearch

You can also increase in multiples, for example: To increase the number of
Logstash parser/buffer/shipping units:

    juju add-unit -n 2 logstash

To monitor additional hosts, simply relate the Filebeat subordinate:

    juju add-relation filebeat:beats-host my-charm


## Contact information

- Charles Butler <Chuck@dasroot.net>
- Matthew Bruzek <mbruzek@ubuntu.com>
- Tim Van Steenburgh <tim.van.steenburgh@canonical.com>
- George Kraft <george.kraft@canonical.com>
- Rye Terrell <rye.terrell@canonical.com>
- Konstantinos Tsakalozos <kos.tsakalozos@canonical.com>


# Need Help?

- [Juju mailing list](https://lists.ubuntu.com/mailman/listinfo/juju)
- [Juju Community](https://jujucharms.com/community)
