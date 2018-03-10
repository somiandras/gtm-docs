import json
import re

class Process:
    def __init__(self):
        self.load_data()

    def load_data(self):
        self.loaded_elements = []
        for element_type in ['tags', 'triggers', 'variables']:
            filename = '{}.json'.format(element_type)
            with open(filename, 'r') as file:
                self.loaded_elements.extend(json.load(file)[element_type[:-1]])
        self.elements = [self.process_element(elem) for elem 
            in self.loaded_elements]

    def markdown(self, filename=None):
        '''
        Returns or saves compiled markdown for all elements.

        Params: none

        Returns: markdown string or saves it into file if filename is given
        '''
        self.elements = sorted(self.elements, key=lambda x: x['name'])
        tags = [elem for elem in self.elements if elem['category'] == 'tag']
        triggers = [elem for elem in self.elements if elem['category'] == 'trigger']
        variables = [elem for elem in self.elements if elem['category'] == 'variable']

        self.md_list = ['## Tags']
        for tag in tags:
            self.md_list.append(self.create_markdown(tag))

        self.md_list.append('## Triggers')
        for trigger in triggers:
            self.md_list.append(self.create_markdown(trigger))

        self.md_list.append('## Variables')
        for variable in variables:
            self.md_list.append(self.create_markdown(variable))
        
        md = '\n\n'.join(self.md_list)

        if filename:
            with open(filename, 'w') as file:
                file.write(md)
        else:
            return md

    def create_markdown(self, element):
        '''
        Create markdown section from element dict.

        Params:
            element (dict): the element to create markdown for
        
        Returns: markdown string
        '''

        sections = []
        sections.append(self.md_headline(element['name']))
        sections.append(self.md_notes(element['notes'], element['tagManagerUrl']))
        sections.append(self.md_type(element['type']))
        if 'parameter' in element:
            sections.append(self.md_parameters(element['parameter']))
        if element['category'] == 'tag':
            sections.append(self.md_triggers(element['triggers']))

        return '\n\n'.join(sections)

    def anchorize(self, name):
        '''Transform from "Element Name" to "element-name" format.
        
        Params:
            name (string): string to transform
        
        Returns: transformed string
        '''

        return re.sub(r'\s+', '-', name.lower().replace('-', ''))

    def md_headline(self, name):
        '''
        Create markdown section for element headline
        
        Params:
            name (string): name of the element
            url (string): GTM url of the element

        Returns: markdown string for headline
        '''

        return '''###<a name="{0}"/> {1}'''.format(self.anchorize(name), name)

    def md_notes(self, notes, url):
        if len(notes) == 0:
            return '''*No description* <small>
            [view on GTM]({})</small>'''.format(url)
        else:
            return '''{}
            <small>[view on GTM]({})</small>'''.format(notes, url)

    def md_type(self, type):
        '''
        Create markdown section for element type
        
        Params:
            type (string): type of element
        
        Returns: markdown string for type section
        '''

        return '**Type:** {}'.format(type)

    def md_triggers(self, triggers):
        '''
        Create markdown section for trigger list
        
        Params:
            triggers (list): list of trigger names

        Returns: markdown string for trigger section
        '''

        parts = ['**Triggers**\n']
        for trigger in triggers:
            parts.append('- [{}](#{})'
                .format(trigger, self.anchorize(trigger)))
        if len(parts) == 1:
            parts.append('*None*')
        return '\n'.join(parts)

    def md_parameters(self, params):
        md_parts = ['**Parameters**\n']
        for param in params:
            if 'value' in param:
                parsed = self.strip_variable(param['value'])
                if len(parsed) == 1:
                    md_parts.append('- {}: {}'.format(param['key'], param['value']))
                else:
                    md_parts.append('- {}: [{}](#{})'.format(param['key'], parsed[0], parsed[1]))
        if len(md_parts) == 1:
            return '**Parameters:** *None*'
        else:
            return '\n'.join(md_parts)

    def get_trigger_names(self, ids):
        '''
        Collect trigger names for ids of firing triggers
        
        Params:
            ids (list): list of trigger ids

        Returns: list of names for the ids
        '''

        triggers = [elem for elem in self.loaded_elements if 'triggerId' in elem]
        return [trigger['name'] for trigger in triggers
                        if trigger['triggerId'] in ids]

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

    def strip_variable(self, string):
        '''
        Check if a string is in {{ Variable }} format, and return it
        trimmed and also "anchorized" with self.anchorize. Every other 
        string is returned unchanged.

        Params:
            string: the variable value to check

        Returns: tuple, if string is variable template (name, anchor), 
        else (name,)
        '''

        match = re.match('^{{(.*)}}$', string)
        if match:
            name = match.group(1)
            return (name, self.anchorize(name))
        else:
            return (string,)

    def process_element(self, element):
        '''
        Filter and transform element based on its type and existing
        properties.

        Params:
            element: the raw element (tag, trigger or variable) to
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
            element['triggers'] = self.get_trigger_names(
                element['firingTriggerId']
            )
        elif 'triggerId' in element:
            element['category'] = 'trigger'
        elif 'variableId' in element:
            element['category'] = 'variable'
        
        element['notes'] = element.get('notes', '')

        element['parameter'] = self.filter_params(element.get('parameter', []))

        return {key: element[key] for key in fields if key in element}


print(Process().markdown('test.md'))
