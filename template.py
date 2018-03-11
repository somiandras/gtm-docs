import json
import re
from formatter import MDFormatter

class Process():
    def __init__(self, format='markdown'):
        if format == 'markdown':
            self.formatter = MDFormatter()
        self.load_data()

    def load_data(self):
        self.loaded_elements = []
        for element_type in ['tags', 'triggers', 'variables']:
            filename = '{}.json'.format(element_type)
            with open(filename, 'r') as file:
                self.loaded_elements.extend(json.load(file)[element_type[:-1]])
        self.elements = [self.process_element(elem) for elem 
            in self.loaded_elements]

    def save(self, filename):
        '''
        Save the formatted output to a file.

        Params:
            filename (string): the file to save to
        
        Returns: None
        '''
        md = self.formatter.markdown(self.elements)
        with open(filename, 'w') as file:
            file.write(md)

    def get_triggers(self, ids):
        '''
        Collect trigger names for ids of firing triggers

        Params:
            ids (list): list of trigger ids

        Returns: list of names for the ids
        '''

        # Collect all triggers from the loaded elements
        triggers = [elem for elem in self.loaded_elements if 'triggerId' in elem]

        # Return only the names for the given ids
        return [{'value': trigger['name']} for trigger in
            triggers if trigger['triggerId'] in ids]

    def filter_params(self, params):
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
            if param['key'] == 'html':
                param['value'] = '[custom code]'
            filtered.append(param)
        return filtered

    def process_element(self, element):
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
            'type',
        ]

        if 'tagId' in element:
            element['category'] = 'tag'
            element['triggers'] = self.get_triggers(element['firingTriggerId'])
        elif 'triggerId' in element:
            element['category'] = 'trigger'
        elif 'variableId' in element:
            element['category'] = 'variable'
        
        element['notes'] = element.get('notes', '')
        element['parameter'] = self.filter_params(element.get('parameter', []))

        return {key: element[key] for key in fields if key in element}


Process().save('test.md')
