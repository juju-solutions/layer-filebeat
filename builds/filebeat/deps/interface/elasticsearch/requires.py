# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=c0111,c0103,c0301

from charms.reactive import RelationBase
from charms.reactive import hook
from charms.reactive import scopes


class ElasticSearchClient(RelationBase):
    # Existing elasticsearch client interface listed here:
    # https://api.jujucharms.com/charmstore/v5/trusty/elasticsearch-13/archive/playbook.yaml
    scope = scopes.UNIT
    auto_accessors = ['host', 'port']

    @hook('{requires:elasticsearch}-relation-{joined,changed}')
    def changed(self):
        self.set_state('{relation_name}.connected')
        conv = self.conversation()
        # assume we have all the data if we have the port
        if conv.get_remote('port'):
            conv.set_state('{relation_name}.available')

    @hook('{requires:elasticsearch}-relation-{departed,broken}')
    def departed(self):
        conv = self.conversation()
        conv.remove_state('{relation_name}.connected')
        conv.remove_state('{relation_name}.available')
        conv.set_state('{relation_name}.broken')

    def list_unit_data(self):
        ''' Iterate through all ElasticSearch conversations and return the data
        for each cached conversation. This allows us to build a cluster string
        directly from the relation data. eg:

        for unit in elasticsearch.list_data():
            print(unit['cluster_name'])
        '''
        for conv in self.conversations():
            yield {'cluster_name': conv.get_remote('cluster_name'),
                   'host': conv.get_remote('private-address'),
                   'port': conv.get_remote('port')}
