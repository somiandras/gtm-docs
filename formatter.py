import re
from markdown import markdown

class MDFormatter:
    '''
    Markdown formatter for the GTMDocs class to create markdown document
    from list of elements (tags, triggers and variables).

    Only the doc() method is intended for called publicly, like:
        markdown = MDFormatter().doc(elements)
    '''

    def __init__(self):
        pass
    
    def _anchorize(self, name):
        '''Transform from "Element Name" to "element-name" format.
        
        Params:
            name (string): string to transform
        
        Returns: transformed string
        '''

        return re.sub(r'\s+', '-', name.lower().replace('-', ''))

    def _camel_to_title(self, string):
        '''
        Transform string from "camelCase" to "Title Case" without breaking
        all-caps words (eg. HTML or URL).

        Params:
            string (string): string to transform
        
        Returns: transformed string
        '''

        if string.istitle():
            return string
        else:
            words = re.sub(r'([^\s])([A-Z][^A-Z]+)',
                           r'\1 \2', string).strip().split(' ')
            return ' '.join([word[0].upper() + word[1:] for word in words])

    def _md_headline(self, name):
        '''
        Create markdown section for element headline.
        
        Params:
            name (string): name of the element
            url (string): GTM url of the element

        Returns: markdown string for headline with anchor included
        '''

        return '''###<a name="{0}"/>{1}'''.format(self._anchorize(name), name)

    def _md_notes(self, notes, url):
        if len(notes) == 0:
            return '''*No description* <small>
                [view on GTM]({})</small>'''.format(url)
        else:
            return '''{} <small>[view on GTM]({})</small>'''.format(notes, url)

    def _md_key_value(self, key, value):
        '''
        Create markdown section with a key-value pair in a single line.
        
        Params:
            key, value (string): elements of the key-value pair
        
        Returns: markdown string in "**key**: value" format
        '''

        return '**{}:** {}'.format(key, value)

    def _md_list(self, items, title=None, indent=0):
        '''
        Create markdown representation of unordered list. The function 
        takes a list of item dicts, which should contain 'key', 'value'
        and 'anchor' properties (all optional, but items without 'value'
        will be ignored).

        Params:
            items (list): list of dicts with key, value and anchor
            title (string): the title of the list (optional)
            indent (int): number of tabs before bullets (default: 0)

        Returns: markdown formatted string of the list
        '''

        if title:
            headline = '**{}**\n'.format(title)
            parts = [headline]
        else:
            parts = ['']

        for item in items:
            # Start the line with necessary indent and a '-' for bullets
            bullet = ' ' * 4 * indent + '- '
            line = [bullet]

            if 'key' in item:
                item['key'] = self._camel_to_title(item['key'])

            if 'key' in item and 'kanchor' in item:
                # Put link on the key
                line.append('[{}](#{})'.format(item['key'], item['kanchor']))
            elif 'key' in item:
                # No link on the key
                line.append(item['key'])

            if 'key' in item and 'relation' in item:
                # This is comparing something, eg. in a filter
                line.append(' *{}* '.format(item['relation']))
            elif 'key' in item:
                # No comparison just colon
                line.append(': ')

            if 'value' in item and 'vanchor' in item:
                # Add link to the value text
                line.append('[{}](#{})'.format(item['value'], item['vanchor']))
            elif 'value' in item:
                # Simple value without link, add string in quotes
                line.append('"{}"'.format(item['value']))
            
            if 'list' in item:
                # Some kind of list in list, add it with indentation
                line.append(self._md_list(item['list'], indent=1))

            parts.append(''.join(line))

        if len(parts) == 1:
            # No items added besides the title and/or new line
            return '\n'
        else:
            return '\n'.join(parts)

    def _md_section(self, element):
        '''
        Create a markdown section for an element dict with headline and
        content like notes, parameter or filter list, etc.

        Params:
            element (dict): the element to create markdown from
        
        Returns: markdown string
        '''

        sections = []
        sections.append(self._md_headline(element['name']))

        sections.append(self._md_notes(
            element['notes'], element['tagManagerUrl']))

        element['type'] = self._camel_to_title(element['type']) 
        sections.append(self._md_key_value('Type', element['type']))
        
        if 'parameter' in element:
            stripped = self._strip_variables(element['parameter'])
            sorted_list = sorted(stripped, key=lambda x: x['key'])
            sections.append(self._md_list(sorted_list, 'Parameters'))
        
        if element['category'] == 'tag':
            if 'triggers' in element:
                anchorized_list = []
                for trigger in element['triggers']:
                    trigger['vanchor'] = self._anchorize(trigger['value'])
                    anchorized_list.append(trigger)
                sections.append(self._md_list(anchorized_list, 'Triggers'))

        if element['category'] == 'trigger':
            if 'filter' in element:
                stripped = self._strip_variables(element['filter'])
                sections.append(self._md_list(stripped, 'Filters'))

        return '\n\n'.join(sections)

    def doc(self, elements):
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
            md_doc.append(self._md_section(tag))

        md_doc.append('## Triggers')
        for trigger in triggers:
            md_doc.append(self._md_section(trigger))

        md_doc.append('## Variables')
        for variable in variables:
            md_doc.append(self._md_section(variable))

        md = '\n\n'.join(md_doc)

        return md

    def _strip_variables(self, items):
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
            if 'key' in item:
                match = re.match('^{{(.*)}}$', item['key'])
                if match:
                    item['key'] = match.group(1)
                    item['kanchor'] = self._anchorize(item['key'])
            if 'value' in item:
                match = re.match('^{{(.*)}}$', item['value'])
                if match:
                    item['value'] = match.group(1)
                    item['vanchor'] = self._anchorize(item['value'])
            updated.append(item)
        return updated

class HTMLFormatter(MDFormatter):
    def doc(self, elements):
        md = super().doc(elements)
        return markdown(md)
