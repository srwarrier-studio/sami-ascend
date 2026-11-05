# workspace-web/10 shell

## Goal
Workspace wears the same floating header and premium look as Synapse: the shared `AppFrame` in its top layout, with the mark and name, the person's role, role-based navigation pills and the user menu.

## Why
The two apps are one product and management will see them side by side. Synapse already uses `AppFrame` (`layout="top"`) and `look="premium"`; Workspace still has a plain Mantine header with a left sidebar. Using the shared frame keeps one pattern, so a later fix to the frame reaches both apps.

## Behavior
- **Frame:** `Shell` renders `AppFrame` with `layout="top"`, `search={false}` and `themeToggle={false}` (as Synapse; Workspace's dark scheme is not reviewed yet). `brand` is `{ name: APP_NAME, subtitle: <role label>, logo: <WorkspaceLogo size={28} /> }`. `user` is `{ name: sap_username, email: '' }` (the session holds no name or e-mail; Synapse does the same). `onSignOut` is the existing logout.
- **Role label:** the person's first role, capitalised (`Purchase`, `Management`, `Sales`, `Stores`, `Accounts`, `Admin`); no roles gives an empty subtitle.
- **Navigation:** one group: `Home` (`/`) then the entries `allowedEntries(roles)` already gives, each with a Phosphor icon exported from `@sami/ui` and rendered as a TanStack `Link`, as Synapse does. The active pill is the entry with the longest path that is the current path or a parent of it, so `/purchase-requisitions/10000012` highlights Purchase requisitions and `/purchase-requisitions/new` highlights New requisition only; `Home` is active only on `/`.
- **Look:** `main.tsx` gives `UiProvider` `look="premium"`; the soft canvas and hairline-bordered surfaces come from `@sami/ui`. No colour, size or font is written in the app.
- **Unchanged:** routes, guards, every page's content, the sign-in page (its own full-screen layout, no frame), the auth session, the tab title and favicon.

## Acceptance cases
- A signed-in purchase user sees the mark, `Sami Workspace`, the subtitle `Purchase`, their SAP user name and pills for Home, Purchase requisitions and New requisition only; a sales user sees Home, Sales orders and New sales order; an admin sees Home only.
- The active pill follows the path by the longest-match rule above (cases for `/`, list, detail, new).
- Choosing Sign out in the user menu signs the user out and lands on the sign-in page.
- The root carries `data-look="premium"`.
- The sign-in page shows no frame.
- All existing workspace-web tests pass after selector updates; `tsc` is clean; nothing changes under `apps/synapse-web`.

## Out of scope
Dark theme toggle, company switcher, search box, notification bell, changing the frame itself, mobile navigation beyond what `AppFrame` already does, the home page content (workspace-web 09).

## Depends on
workspace-web 08 (merged), `AppFrame` and its icon exports in `@sami/ui`. If an icon the nav needs is not exported yet, it is added to `@sami/ui` exports in task 1 (an export line only).
