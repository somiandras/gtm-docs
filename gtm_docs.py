import re
import json
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from formatter import MDFormatter, HTMLFormatter
from dictionary import types_dictionary, filtered_parameters

class GTMDocs:
    '''
    Methods to connect to GTM API, download data of a given container
    and export it into a human readable documentation format (currently
    markdown or HTML).

    Methods (chainable):

    - GTMDocs.connect: connect to GTM API with a service account
    - GTMDocs.download: download data for the given container
    - GTMDocs.save: save the docs to the given file
    '''

    def __init__(self):
        pass

    def connect(self, credentials):
        '''
        Create authorized session to GTM API with the downloaded
        credentials for service account. Credentials must be provided 
        as a path to the downloaded json credentials file. The 
        connection is with read-only scope.

        Params:
            credentials (string): path to credentials json

        Returns: self
        '''

        scope = ['https://www.googleapis.com/auth/tagmanager.readonly']
        credentials = service_account.Credentials.from_service_account_file(
            credentials, scopes=scope)

        self.session = AuthorizedSession(credentials)
        return self

    def download(self, account_id, container_id, workspace_id):
        '''
        Download tags, triggers and variables data from the given GTM
        account, container and workspace.

        Params:
            account_id (string or int): account id
            container_id (string or int): container id
            workspace_id (string or int): workspace id

        Returns: self
        '''

        self.loaded_elements = []
        path_comps = [
            'https://www.googleapis.com/tagmanager/v2',
            'accounts',
            str(account_id),
            'containers',
            str(container_id),
            'workspaces',
            str(workspace_id),
        ]
        base_url = '/'.join(path_comps)

        types = ['tags', 'triggers', 'variables']
        for data_type in types:
            r = self.session.get('{}/{}'.format(base_url, data_type))
            if r.status_code == 200:
                data = r.json()
                self.loaded_elements.extend(data[data_type[:-1]])
            else:
                r.raise_for_status()

        self.elements = [self._process_element(elem) 
            for elem in self.loaded_elements]
        
        return self

    def save(self, filename, format='markdown'):
        '''
        Save the formatted output to a file.

        Params:
            filename (string): the file to save to
            format (string): markdown (default) (not other format
            implemented)
        
        Returns: None
        '''

        if format == 'markdown':
            self.formatter = MDFormatter()
        elif format == 'html':
            self.formatter = HTMLFormatter()

        doc = self.formatter.doc(self.elements)
        with open(filename, 'w') as file:
            file.write(doc)

    def _get_triggers(self, ids):
        '''
        Collect trigger names for ids of firing triggers.

        Params:
            ids (list): list of trigger ids

        Returns: list of names for the ids
        '''

        # Collect all triggers from the loaded elements
        triggers = [elem for elem in self.loaded_elements if 'triggerId' in elem]

        # Return only the names for the given ids
        return [{'value': trigger['name']} for trigger in
            triggers if trigger['triggerId'] in ids]

    def _filter_params(self, params):
        '''
        Filter out parameters that are set to false, and mask code in 
        custom HTML tags.

        Params:
            params (list): list of parameters to filter

        Returns: filtered list
        '''

        filtered = []
        for param in params:
            if 'value' in param and param['value'] == 'false':
                continue

            if param['key'] in filtered_parameters:
                continue

            if param['key'] == 'html':
                param['value'] = 'custom code'

            if 'list' in param:
                transformed_list = []
                for item in param['list']:
                    if item['type'] == 'map':
                        new_item = {}
                        new_item['key'] = item['map'][0]['value']
                        new_item['value'] = item['map'][1]['value']
                        transformed_list.append(new_item)
                param['list'] = transformed_list
            filtered.append(param)

        return filtered

    def _process_filters(self, filters):
        '''
        Collapse trigger filters and customEventFilters into one dict
        to use later in formatter.

        Params:
            filters (list): list of filters from trigger
        
        Returns: updated list with single dicts for each filter
        '''

        updated_filters = []
        for trig_filter in filters:
            new_filter = {}
            new_filter['relation'] = trig_filter['type']
            new_filter['key'] = [arg['value'] for arg in trig_filter['parameter']
                                   if arg['key'] == 'arg0'][0]
            new_filter['value'] = [arg['value'] for arg in trig_filter['parameter']
                                   if arg['key'] == 'arg1'][0]
            negated = [arg['value'] for arg in trig_filter['parameter']
                       if arg['key'] == 'negate']
            
            if len(negated) == 1 and negated[0] == 'true':
                new_filter['relation'] = 'not {}'.format(new_filter['relation'])

            updated_filters.append(new_filter)

        return updated_filters

    def _process_element(self, element):
        '''
        Filter and transform element based on its type and existing
        properties.

        Params:
            element (dict): the raw element (tag, trigger or variable) to
            process
        
        Returns: processed and updated element with only the needed keys
        '''
        
        fields = [
            'category',
            'customEventFilter',
            'filter',
            'triggers',
            'name',
            'notes',
            'parameter',
            'tagManagerUrl',
            'type'
        ]

        if 'tagId' in element:
            element['category'] = 'tag'
            element['triggers'] = self._get_triggers(element['firingTriggerId'])
        elif 'triggerId' in element:
            element['category'] = 'trigger'
            if 'filter' in element:
                element['filter'] = self._process_filters(element['filter'])
            elif 'customEventFilter' in element:
                element['filter'] = self._process_filters(
                    element['customEventFilter'])
        elif 'variableId' in element:
            element['category'] = 'variable'
        
        element['type'] = types_dictionary.get(element['type'], element['type'])
        element['notes'] = element.get('notes', '')
        element['parameter'] = self._filter_params(element.get('parameter', []))

        return {key: element[key] for key in fields if key in element}
