# synapse-web/01 mock-shell

## Goal
The synapse-web app runs with the soft shell, a mock login and session, a "not allowed" page and route guards, with no API calls.

## Behavior
- `SessionClient` (`me`, `login`, `logout`) is an interface; `MockSessionClient` holds three users: `manager@mock-sami.com` (`management`), `admin@mock-sami.com` (`admin`), `sales@mock-sami.com` (`sales`), password `mock`. In memory only; a reload signs out.
- Loading shows `SplashScreen`; signed out shows `SignInCard` on `/login`; bad credentials show an error.
- Signed in with `management` or `admin` uses `AppFrame` (top layout, brand Synapse) with one nav item, "My boards" (`/`), a placeholder until synapse-web 03.
- Signed in without those roles goes to `/not-allowed`; signed out goes to `/login`; signed in on `/login` goes to `/`; unknown paths show Page not found.
- Sign out returns to `/login`.
- Palette `synapsePalette`, motion full.

## Acceptance cases
Loading splash; signed out redirect; bad credentials error; manager and admin reach `/`; sales lands on not-allowed; sign out; not found; shell shows user name; app code has no `@mantine/*` import or inline style.

## Out of scope
Widgets, boards, real API, Entra.

## Depends on
shared 08, 09, 10.
