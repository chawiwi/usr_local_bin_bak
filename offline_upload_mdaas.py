# Copyright (C) Microsoft Corporation. All rights reserved.

import argparse
import ntpath

from azure.identity import CertificateCredential
import requests
import credential

TENANT_ID = "microsoft.onmicrosoft.com"

# Application Client ID
CLIENT_ID = credential.client

# Application Certificate
CERTIFICATE_PATH = credential.path
CERTIFICATE_SCOPE_URL = "https://mdaas-prod.azure-api.net"

API_URL = "https://mdaas.microsoft.com"
BLOB_CONTAINER = "offline"


def get_token():

    credential = CertificateCredential(tenant_id=TENANT_ID,
                                       client_id=CLIENT_ID,
                                       certificate_path=CERTIFICATE_PATH,
                                       send_certificate_chain=True)

    scope = CERTIFICATE_SCOPE_URL + "/.default"
    token = credential.get_token(scope)
    return token.token


def upload_files(file_list):
    status_results = []
    token = get_token()

    headers = {'Authorization': f'Bearer {token}'}
    try:
        for f in file_list:
            with open(f, 'rb') as fp:
                payload = fp.read()

            blob = ntpath.basename(f)
            url = f"{API_URL}/blob/{BLOB_CONTAINER}/{blob}"
            r = requests.put(url, headers=headers, data=payload)
            
            if r.status_code != 201:
                print(r.json())
                status_results.append('FAIL')
            else:
                print(f"{f} upload successfully")
                status_results.append('SUCCESS')
    except Exception as e:
        print (e)
        status_results.append('FAIL')
    return status_results


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('zip_file', type=str, nargs='*',
                        help='ZIP files to be uploaded')

    args = parser.parse_args()

    upload_files(args.zip_file)
