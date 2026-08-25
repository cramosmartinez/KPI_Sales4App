import os
import json
import requests
from msal import ConfidentialClientApplication
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

CLIENT_ID = os.getenv("DYNAMICS_CLIENT_ID")
CLIENT_SECRET = os.getenv("DYNAMICS_CLIENT_SECRET")
TENANT_ID = os.getenv("DYNAMICS_TENANT_ID")
URL_ENV = os.getenv("DYNAMICS_URL_ENV", "https://foragro.operations.dynamics.com")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = [f"{URL_ENV}/.default"]
DYNAMICS_URL = f"{URL_ENV}/api/Services/FAUtils/FASerializationService/SqlStatement2/"

def get_dynamics_token():
    app = ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        raise Exception(f"Error getting token: {result.get('error_description')}")
    return result["access_token"]

def get_sql(sql_statement: str):
    if not sql_statement:
        raise ValueError("SQL statement is required")

    token = get_dynamics_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "contract": {
            "Statement": sql_statement
        }
    }

    response = requests.post(DYNAMICS_URL, headers=headers, json=body, timeout=20000)
    response.raise_for_status()
    return response.json()
