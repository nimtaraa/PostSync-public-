import os
import requests
from fastapi import APIRouter, HTTPException, Header


router = APIRouter(prefix="/auth/linkedin", tags=["LinkedIn OAuth"])
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

@router.post("/token")
def get_access_token(data: dict):
    code = data.get("code")
    redirect_uri = data.get("redirect_uri")

    print("redirect uri received:", redirect_uri)

    if not code or not redirect_uri:
        raise HTTPException(status_code=400, detail="Missing code or redirect_uri")

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(token_url, data=payload, headers=headers)

    if res.status_code != 200:
        print("LinkedIn token error:", res.text)
        raise HTTPException(status_code=400, detail=res.json())

    token_data = res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        print("⚠️ No access token received from LinkedIn:", token_data)
        raise HTTPException(status_code=400, detail="No access token received")

    print("🔑 LINKEDIN ACCESS TOKEN:", access_token)
    return token_data


@router.get("/me")
def get_user_info(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    headers = {"Authorization": f"Bearer {token}"}

    # Get profile
    profile_res = requests.get("https://api.linkedin.com/v2/me", headers=headers)
    print("LinkedIn profile response :", profile_res)
    if profile_res.status_code != 200:
        print("LinkedIn profile error:", profile_res.text)
        raise HTTPException(status_code=profile_res.status_code, detail=profile_res.json())
    profile_data = profile_res.json()

    # Get email
    email_res = requests.get(
        "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
        headers=headers,
    )
    if email_res.status_code != 200:
        print("LinkedIn email error:", email_res.text)
        raise HTTPException(status_code=email_res.status_code, detail=email_res.json())
    email_data = email_res.json()

    email_address = email_data.get("elements", [{}])[0].get("handle~", {}).get("emailAddress")

    linkedin_id = profile_data.get("id")
    full_name = f"{profile_data.get('localizedFirstName', '')} {profile_data.get('localizedLastName', '')}".strip()

    # ✅ Generate person URN
    person_urn = f"urn:li:person:{linkedin_id}" if linkedin_id else None

    return {
        "id": linkedin_id,
        "person_urn": person_urn,
        "name": full_name,
        "email": email_address,
    }
