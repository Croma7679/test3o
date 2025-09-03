class SharePointClientBuilder:
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.tenant_id = None
        self.resource_url = None

    def with_client_id(self, client_id):
        self.client_id = client_id
        return self

    def with_client_secret(self, client_secret):
        self.client_secret = client_secret
        return self

    def with_tenant_id(self, tenant_id):
        self.tenant_id = tenant_id
        return self

    def with_resource_url(self, resource_url):
        self.resource_url = resource_url
        return self

    def build(self):
        if not all([self.client_id, self.client_secret, self.tenant_id, self.resource_url]):
            raise ValueError("Incomplete builder configuration. Please provide all required parameters.")
        
        client = SharePointClient(self.tenant_id, self.client_id, self.client_secret, self.resource_url)
        client.authenticate()  # Authenticate immediately upon building
        return client



import requests
import os 
from azure.storage.blob import BlobServiceClient, BlobClient
from helpers import common as cm


class SharePointClient:
    def __init__(self, tenant_id, client_id, client_secret, resource_url):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.resource_url = resource_url
        self.base_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.access_token = None  # Initialize access token to None

    def authenticate(self):
        # Body for the access token request
        body = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.resource_url + '.default'
        }
        response = requests.post(self.base_url, headers=self.headers, data=body)
        self.access_token = response.json().get('access_token')  # Extract access token from the response
       

    def get_site_id(self, site_url):
        # Build URL to request site ID
        full_url = f'https://graph.microsoft.com/v1.0/sites/{site_url}'
        response = requests.get(full_url, headers={'Authorization': f'Bearer {self.access_token}'})
       
        print("DEBUG response:", response.status_code, response.text)
        return response.json().get('id')  # Return the site ID
    
    def get_drive_id(self, site_id):
        # Retrieve drive IDs and names associated with a site
        drives_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives'
        response = requests.get(drives_url, headers={'Authorization': f'Bearer {self.access_token}'})
        drives = response.json().get('value', [])
        return [(drive['id'], drive['name']) for drive in drives]

    def get_folder_id(self, drive_id, folder_path):
        """
        Get the folder ID for a given folder path like 'apply-now'
        """
        folder_url = f'https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_path}'
        response = requests.get(folder_url, headers={'Authorization': f'Bearer {self.access_token}'})
        response.raise_for_status()
        return response.json().get('id')
    
    def get_folder_content(self, site_id, drive_id):
        # Get the contents of a folder
        folder_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children'
        response = requests.get(folder_url, headers={'Authorization': f'Bearer {self.access_token}'})
        items_data = response.json()
        rootdir = []
        if 'value' in items_data:
            for item in items_data['value']:
                rootdir.append((item['id'], item['name']))
        return rootdir
    
    def list_folder_contents(self, site_id, drive_id, folder_id, level=0):
        # Get the contents of a specific folder
        folder_contents_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{folder_id}/children'
        contents_headers = {'Authorization': f'Bearer {self.access_token}'}
        contents_response = requests.get(folder_contents_url, headers=contents_headers)
        folder_contents = contents_response.json()

        items_list = []  # List to store information

        if 'value' in folder_contents:
            for item in folder_contents['value']:
                if 'folder' in item:
                    # Add folder to list
                    items_list.append({'name': item['name'], 'type': 'Folder', 'mimeType': None})
                    # Recursive call for subfolders
                    items_list.extend(self.list_folder_contents(site_id, drive_id, item['id'], level + 1))
                elif 'file' in item:
                    # Add file to the list with its mimeType
                    items_list.append({'name': item['name'], 'type': 'File', 'mimeType': item['file']['mimeType']})

        return items_list




CLIENT_ID = cm.CLIENT_ID #secret_cred.get_secret("CLIENT_ID")
CLIENT_SECRET = cm.CLIENT_SECRET #secret_cred.get_secret("CLIENT_SECRET")
TENANT_ID = cm.TENANT_ID #secret_cred.get_secret("TENANT_ID")
    
builder = SharePointClientBuilder()\
.with_client_id(CLIENT_ID)\
.with_client_secret(CLIENT_SECRET)\
.with_tenant_id(TENANT_ID)\
.with_resource_url('https://graph.microsoft.com/')
    # Example usage
client = builder.build()
site_url = "intertechsystemsllc.sharepoint.com:/sites/ContataWebsite-ApplicationForms"
    
FOLDER_NAME = "abc"
site_id = client.get_site_id(site_url)
print("Site ID:", site_id)

'''
if site_id:
        drive_info = client.get_drive_id(site_id)
        print("Root folder:", drive_info)

        drive_id = drive_info[0][0]  # Assume the first drive ID
        folder_content = client.get_folder_content(site_id, drive_id)
        print("Root Content:", folder_content)

        folder_id = folder_content[0][0]

        contents = client.list_folder_contents(site_id, drive_id, folder_id)
'''

# Get Drive ID
drive_info = client.get_drive_id(site_id)
print("Drives:", drive_info)

drive_id = drive_info[0][0]  # usually "Documents"

# Get Folder ID for apply-now
folder_id = client.get_folder_id(drive_id, "Post/apply-now")
print("apply-now folder ID:", folder_id)

get_folder_content = client.get_folder_content(site_id, drive_id)
print("Folder Content:", get_folder_content)

list_contents = client.list_folder_contents(site_id, drive_id, folder_id)
print("Folder Contents:", list_contents)