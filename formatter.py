import re

class MDFormatter:
    def __init__(self):
        pass
    
    def anchorize(self, name):
        '''Transform from "Element Name" to "element-name" format.
        
        Params:
            name (string): string to transform
        
        Returns: transformed string
        '''

        return re.sub(r'\s+', '-', name.lower().replace('-', ''))

    def md_headline(self, name):
        '''
        Create markdown section for element headline.
        
        Params:
            name (string): name of the element
            url (string): GTM url of the element

        Returns: markdown string for headline with anchor included
        '''

        return '''###<a name="{0}"/>{1}'''.format(self.anchorize(name), name)

    def md_notes(self, notes, url):
        if len(notes) == 0:
            return '''*No description* <small>
                [view on GTM]({})</small>'''.format(url)
        else:
            return '''{} <small>[view on GTM]({})</small>'''.format(notes, url)

    def md_key_value(self, key, value):
        '''
        Create markdown section with a key-value pair in a single line.
        
        Params:
            key, value (string): elements of the key-value pair
        
        Returns: markdown string in "**key**: value" format
        '''

        return '**{}:** {}'.format(key, value)

    def md_list(self, items, title):
        '''
        Create markdown representation of unordered list. The function 
        takes a list of item dicts, which should contain 'key', 'value'
        and 'anchor' properties (all optional, but items without 'value'
        will be ignored).

        Params:
        items (list): list of dicts with properties of key, value and 
        anchor
        title (string): the title of the list

        Returns: markdown formatted string of the list
        '''

        headline = '**{}**\n'.format(title)
        parts = [headline]
        for item in items:
            line = ['- ']
            if 'key' in item:
                line.append('{}: '.format(item['key']))
            
            if 'value' in item and 'anchor' in item:
                line.append('[{}](#{})'.format(item['value'], item['anchor']))
            elif 'value' in item:
                line.append('{}'.format(item['value']))
            parts.append(''.join(line))

        if len(parts) == 1:
            return '{}: *None*'.format(parts[0].strip())
        else:
            return '\n'.join(parts)

    def md_section(self, element):
        '''
        Create a markdown section for an element dict.

        Params:
            element (dict): the element to create markdown from
        
        Returns: markdown string
        '''

        sections = []
        sections.append(self.md_headline(element['name']))
        sections.append(self.md_notes(
            element['notes'], element['tagManagerUrl']))
        sections.append(self.md_key_value('Type', element['type']))
        if 'parameter' in element:
            stripped = self.strip_variables(element['parameter'])
            sections.append(self.md_list(stripped, 'Parameters'))
        if element['category'] == 'tag':
            stripped = self.strip_variables(element['triggers'])
            sections.append(self.md_list(stripped, 'Triggers'))

        return '\n\n'.join(sections)

    def markdown(self, elements):
        '''
        Chain together markdown formatted strings for elements in the 
        given element list, and return the complete markdown document.

        Params:
            elements (list): list of dicts of elements

        Returns: markdown formatted document string
        '''

        sorted_elements = sorted(elements, key=lambda x: x['name'])
        tags = [elem for elem in sorted_elements if elem['category'] == 'tag']
        triggers = [
            elem for elem in sorted_elements if elem['category'] == 'trigger']
        variables = [
            elem for elem in sorted_elements if elem['category'] == 'variable']

        md_doc = ['## Tags']
        for tag in tags:
            md_doc.append(self.md_section(tag))

        md_doc.append('## Triggers')
        for trigger in triggers:
            md_doc.append(self.md_section(trigger))

        md_doc.append('## Variables')
        for variable in variables:
            md_doc.append(self.md_section(variable))

        md = '\n\n'.join(md_doc)

        return md

    def strip_variables(self, items):
        '''
        Check in a list of items if item values are in {{ Variable }} 
        format, and replace them with the trimmed name and add the
        anchor. Every other string is returned unchanged.

        Params:
            items (list): list of item dicts

        Returns: Updated list
        '''

        updated = []
        for item in items:
            if 'value' in item:
                match = re.match('^{{(.*)}}$', item['value'])
                if match:
                    item['value'] = match.group(1)
                    item['anchor'] = self.anchorize(item['value'])
            updated.append(item)
        return updated
