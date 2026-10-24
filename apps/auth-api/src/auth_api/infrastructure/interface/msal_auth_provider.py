import time
from auth_api.domain.interface.auth_provider import AuthProvider
from msal import ConfidentialClientApplication
from auth_api.core.config import settings


class MSALAuthProvider(AuthProvider):
    def __init__(self):
        self.app = ConfidentialClientApplication(
            client_id=settings.ENTRA_CLIENT_ID,
            client_credential=settings.ENTRA_SECRET,
            authority=settings.ENTRA_AUTHORITY,
        )

    def initiate_flow(self) -> dict:
        return self.app.initiate_auth_code_flow(
            scopes=["User.Read"], 
            redirect_uri=settings.ENTRA_REDIRECT_URL
        )

    def authenticate(self, flow: dict, auth_response: dict) -> dict:
        result = self.app.acquire_token_by_auth_code_flow(flow, auth_response)
        if "error" in result:
            return {
                "error": result.get("error"),
                "description": result.get("error_description")
            }
        claims = result.get("id_token_claims", {})
        expires_in = result.get("expires_in", 3600)
        return {
            "message": "Successfully authenticated!",
            "user": {
                "oid": claims.get("oid") or claims.get("sub"),
                "tenant_id": claims.get("tid"),
                "email": claims.get("preferred_username") or claims.get("email"),
                "name": claims.get("name"),
            },
            "tokens": {
                "access_token": result.get("access_token"),
                "token_type": result.get("token_type", "Bearer"),
                "scopes": result.get("scope", []),
                "expires_at": int(time.time()) + expires_in
            }
        }