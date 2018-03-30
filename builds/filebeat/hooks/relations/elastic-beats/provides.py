from charms.reactive import RelationBase
from charms.reactive import hook


class BeatsProvider(RelationBase):
    ''' Elastic Beats  - Beats can be exchanged between Logstash or
        Elasticsearch. Both services emit a host/port combination for the
        resident beats agent to route traffic to. This interface handles the
        filebeat, packetbeat, and topbeat relations.
    '''

    @hook('{provides:elastic-beats}-relation-{joined,changed}')
    def joined_changed(self):
        ''' Notify the consuming layer we have a request for data'''
        conv = self.conversation()
        conv.set_state('{relation_name}.connected')

    @hook('{provides:elastic-beats}-relation-{departed,broken}')
    def departed_broken(self):
        conv = self.conversation()
        conv.remove_state('{relation_name}.connected')

    def provide_data(self, port):
        ''' Consumers will invoke this method to ship the extant unit the port
            and private address (implicit).
        '''
        for conv in self.conversations():
            self.set_remote(scope=conv.scope, data={'port': port})
