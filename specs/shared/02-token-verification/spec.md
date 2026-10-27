# shared/02 token-verification

## Goal
One small Python package that every API uses to verify the login cookie and read the user's id, SAP username and roles, so no API copies the JWT code from auth-api.

## Behavior
- Package `token-verification` in `packages/token-verification` (import `token_verification`), added to the uv workspace.
- `TokenVerifier(secret)` with `verify(token) -> TokenClaims`; raises `InvalidToken` for a bad signature, expired, malformed or missing-claim token. HS256 only.
- `TokenClaims` (`userid`, `sap_username`, `roles`) and `Role` move here; the claims shape is unchanged.
- FastAPI helpers: `current_claims` reads the `access_token` cookie and returns claims or responds 401; `require_roles(*roles)` responds 403 if the user has none of them.
- auth-api imports the verifier from the package. Issuing tokens stays in auth-api.
- Each API gets the secret from its own settings (`JWT_SECRET`), the same value as auth-api.

## Acceptance cases
- Valid token returns the same claims auth-api issued.
- Wrong secret, expired, garbage, and a token missing `roles` each raise `InvalidToken`.
- A token signed with `alg: none` or another algorithm is rejected.
- No cookie gives 401; bad cookie gives 401; valid cookie with the wrong role gives 403; right role passes.
- Existing auth-api tests still pass.

## Out of scope
Issuing tokens, refresh, revocation, key rotation, RS256/JWKS, service-to-service tokens, wiring into synapse-api and workspace-api (their own phases).

## Depends on
Nothing.
