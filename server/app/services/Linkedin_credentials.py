# This will store token and person URN globally in backend memory
linkedin_credentials = {
    "access_token": None,
    "person_urn": None
}

def set_credentials(access_token: str, person_urn: str):
    linkedin_credentials["access_token"] = access_token
    linkedin_credentials["person_urn"] = person_urn

def get_credentials():
    print("access_token:", linkedin_credentials["access_token"])
    print("person_urn:", linkedin_credentials["person_urn"])
    return linkedin_credentials["access_token"], linkedin_credentials["person_urn"]
