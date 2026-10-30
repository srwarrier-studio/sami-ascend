# synapse-web/10 login-page

## Goal
The sign-in page looks like a product, not a form on a blank page, and carries an animation that says "synapse": a network of neurons with an occasional electric pulse.

## Behavior
- `/login` is a full-screen split page (no shell). Wide screens: the brand panel on the left (about 60%), the sign-in form on the right. Narrow screens: the form only, with the animation as a faint background.
- Brand panel: the Synapse mark and name, the line `Your sales, on one board`, and the animated network behind them, on the brand colour with a soft gradient.
- Form side: the existing sign-in (`Work email`, `Password`, `Sign in`, the `Incorrect email or password` error) with a short welcome title, `Sign in to Synapse`, and the same behaviour as today.
- Animation, a fixed hand-placed layout (no random per frame):
  - about 24 nodes joined by thin lines, drifting very slightly;
  - every few seconds a pulse of light runs along a chain of connected lines from one node to another, and each node it reaches flashes briefly (an electric signal passing a synapse);
  - pulses are at different places and times, never all at once; the page is calm between them.
- Pure SVG and CSS, no new dependency, no inline style props (theme-only rule), colours from the theme.
- The animation stops (static network, no pulses) when motion is `minimal` or the user's system asks for reduced motion.
- The splash screen shown while the session loads is unchanged.
- The animation component lives in synapse-web (`src/login/`), the shared `SignInCard` in `@sami/ui` is used as it is or gets one optional prop, other apps unchanged.

## Acceptance cases
- The login page shows the brand name, the tagline and the form; signing in, the wrong-password error and the redirect after sign-in work as before.
- The network is drawn (nodes and lines) and hidden from assistive technology.
- With minimal motion the pulses are not rendered.
- No inline styles and no new dependency (existing theme-only tests pass).

## Out of scope
A canvas or WebGL version, sound, a dark-mode specific design beyond using theme colours, forgot-password and single sign-on buttons, changing the splash screen, the workspace-web login.

## Depends on
synapse-web 09.
