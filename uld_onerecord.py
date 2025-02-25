from dotenv import load_dotenv
load_dotenv()

import os
import requests
import json

class ULD_OneRecord:
    def __init__(self, access_token):
        self.KEYCLOCK_ENDPOINT   = os.getenv("KEYCLOCK_ENDPOINT")
        self.KEYCLOCK_TOKEN      = os.getenv("KEYCLOCK_TOKEN")
        self.ONERECORD_BASE_URL  = os.getenv("ONERECORD_BASE_URL")
        self.ONERECORD_GET_PATH  = os.getenv("ONERECORD_GET_PATH")
        self.GATEKEEPER_ENDPOINT = os.getenv("GATEKEEPER_ENDPOINT")
        if access_token == -1:
            self.access_token = self.get_token()
        else:
            self.access_token = access_token
    
    def get_vp(self):
        # Get the VP from POST GATEKEEPER_ENDPOINT+/issue-vp
        response = requests.post(f"{self.GATEKEEPER_ENDPOINT}/issue-vp")
        result = response.json()
        return result['vp_token']

    def verify_vp(self, vp_token: str):
        # Check the VP from POST GATEKEEPER_ENDPOINT+/verify-vp payload => {"vp_token": vp_token}
        payload = {"vp_token": vp_token}
        response = requests.post(f"{self.GATEKEEPER_ENDPOINT}/verify-vp", json=payload)
        result = response.json()
        return {"verified":result['verified'], "claims":result['claims']}
    
    def get_full_url(self, serial_number: int) -> str:
        return f"{self.ONERECORD_BASE_URL}{self.ONERECORD_GET_PATH}uld-{serial_number}"
    
    def get_token(self):
        url = f'{self.KEYCLOCK_ENDPOINT}/realms/neone/protocol/openid-connect/token'
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'authorization': f'Basic {self.KEYCLOCK_TOKEN}',
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': 'neone-client'
        }
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        return result['access_token']
    
    def get_uld_revision(self, serial_number: int):
        full_get_path = self.get_full_url(serial_number)
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        try:
            response = requests.get(full_get_path, headers=headers)
            current_version = response.headers['Revision']
            return int(current_version)
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def update_uld_revision(self, serial_number: int, revision: int, value_to_add: str):
        full_get_path = self.get_full_url(serial_number)
        value_to_remove = "false" if value_to_add == "true" else "true"
        patch_payload = {
            "@context": {
                "cargo": "https://onerecord.iata.org/ns/cargo#",
                "api": "https://onerecord.iata.org/ns/api#"
            },
            "@type": "api:Change",
            "api:hasLogisticsObject": {
                "@id": full_get_path
            },
            "api:hasDescription": "Change damageFlag",
            "api:hasOperation": [
                {
                    "@type": "api:Operation",
                    "api:op": {
                        "@id": "api:DELETE"
                    },
                    "api:s": full_get_path,
                    "api:p": "https://onerecord.iata.org/ns/cargo#damageFlag",
                    "api:o": [
                        {
                            "@type": "api:OperationObject",
                            "api:hasDatatype": "http://www.w3.org/2001/XMLSchema#boolean",
                            "api:hasValue": value_to_remove
                        }
                    ]
                },
                {
                    "@type": "api:Operation",
                    "api:op": {
                        "@id": "api:ADD"
                    },
                    "api:s": full_get_path,
                    "api:p": "https://onerecord.iata.org/ns/cargo#damageFlag",
                    "api:o": [
                        {
                            "@type": "api:OperationObject",
                            "api:hasDatatype": "http://www.w3.org/2001/XMLSchema#boolean",
                            "api:hasValue": value_to_add
                        }
                    ]
                }
            ],
            "api:hasRevision": {
                "@type": "http://www.w3.org/2001/XMLSchema#positiveInteger",
                "@value": revision
            }
        }
        headers = {
            'Content-Type': 'application/ld+json; version=2.0.0-dev',
            'Accept': 'application/ld+json; version=2.0.0-dev',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        token = uld.get_vp()
        verified = uld.verify_vp(token)
        if not verified['verified']:
            raise Exception("VP not verified.")
        else:
            print("VP verified. Proceeding with patch.")

        response = requests.patch(full_get_path, headers=headers, data=json.dumps(patch_payload))
#        print(response.request.body)
#        print(response.status_code)
#        print(response.headers.get('Location'))
        if response.status_code == 201:
            patch_url = response.headers['Location']
            result = requests.patch(patch_url, headers=headers, params={'status': 'REQUEST_ACCEPTED'})
#            print(result)
    
    def flag_for_damage(self, uld_serial: int, damage: bool):
        damage_value = "true" if damage else "false"
        revision = self.get_uld_revision(uld_serial)
        if revision is not None:
            self.update_uld_revision(uld_serial, revision, damage_value)
        else:
            print("Could not retrieve revision.")

if __name__ == '__main__':
    uld = ULD_OneRecord(-1)
    uld_serial = 12348
    uld.flag_for_damage(uld_serial, damage=False)
