from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

account_id = 86620968
container_id = 1761764

scope = ['https://www.googleapis.com/auth/tagmanager.readonly']
credentials = service_account.Credentials.from_service_account_file(
    'credentials/gtm-docs-33fa5f7ff315.json', scopes=scope)

authed_session = AuthorizedSession(credentials)

r = authed_session.get(
    'https://www.googleapis.com/tagmanager/v2/accounts/86620968/containers')
print(r.json())
