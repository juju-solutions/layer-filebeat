from charms.reactive import RelationBase
from charms.reactive import hook


class BeatsClient(RelationBase):

    @hook('{requires:elastic-beats}-relation-{joined,changed}')
    def joined_changed(self):
        ''' During the joined /changed cycle - poll for the port
        to determine eligibility to participate '''
        conv = self.conversation()
        if conv.get_remote('port'):
            conv.set_state('{relation_name}.available')

    @hook('{requires:elastic-beats}-relation-{departed,broken}')
    def departed_broken(self):
        conv = self.conversation()
        conv.remove_state('{relation_name}.available')

    def list_unit_data(self):
        ''' Iterate through all Beats conversations and return the data
        for each cached conversation. This allows us to build a cluster string
        directly from the relation data. eg:

        for unit in beats.list_data():
            print(unit['port'])
        '''
        for conv in self.conversations():
            yield {'private_address': conv.get_remote('private-address'),
                   'port': conv.get_remote('port')}
