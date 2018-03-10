from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
import json

account_id = '86620968'
container_id = '1761764'
workspace_id = '32'

path_comps = [
    'https://www.googleapis.com/tagmanager/v2',
    'accounts',
    account_id,
    'containers',
    container_id,
    'workspaces',
    workspace_id,
    ]

base_url = '/'.join(path_comps)

scope = ['https://www.googleapis.com/auth/tagmanager.readonly']
credentials = service_account.Credentials.from_service_account_file(
    'credentials/gtm-docs-33fa5f7ff315.json', scopes=scope)

authed_session = AuthorizedSession(credentials)

types = ['tags', 'triggers', 'variables']
for data_type in types:
    r = authed_session.get('{}/{}'.format(base_url, data_type))
    if r.status_code == 200:
        with open('{}.json'.format(data_type), 'w') as file:
            json.dump(r.json(), file, indent=2)
        print('{} saved'.format(data_type))
    else:
        r.raise_for_status()
