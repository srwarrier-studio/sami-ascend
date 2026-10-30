# synapse-web/10 login-page

## Goal
The sign-in page looks like a product, not a form on a blank page: a centred card over a full-screen animation that says "synapse": a network of neurons with an occasional electric pulse.

## Behavior
- `/login` is a full-screen page (no shell) on a deep navy gradient with the animated network filling the whole background. The sign-in card sits in the centre, with the Synapse mark, name and `Your sales, on one board` above it in white. The same on narrow screens.
- Form: the existing sign-in (`Work email`, `Password`, `Sign in`, the `Incorrect email or password` error) with the title `Sign in to Synapse`, and the same behaviour as today.
- Animation, a fixed hand-placed layout (no random per frame):
  - about 24 nodes joined by thin, dim blue lines;
  - every few seconds a pulse of light runs along a chain of connected lines from one node to another, and each node it reaches flashes briefly (an electric signal passing a synapse);
  - pulses are at different places and times, never all at once; the page is calm between them.
- Pure SVG and CSS, no new dependency, no inline style props (theme-only rule). The navy and the blue-white pulse are fixed brand colours, the same in light and dark mode.
- The animation stops (static network, no pulses) when motion is `minimal` or the user's system asks for reduced motion.
- The splash screen shown while the session loads is unchanged.
- The animation is used on the login page only. The component lives in synapse-web (`src/login/`), the shared `SignInCard` in `@sami/ui` is used as it is or gets one optional prop, other apps unchanged.

## Acceptance cases
- The login page shows the brand name, the tagline and the form; signing in, the wrong-password error and the redirect after sign-in work as before.
- The network is drawn (nodes and lines) and hidden from assistive technology.
- With minimal motion the pulses are not rendered.
- No inline styles and no new dependency (existing theme-only tests pass).

## Out of scope
A canvas or WebGL version, sound, a dark-mode specific design beyond using theme colours, forgot-password and single sign-on buttons, changing the splash screen, the workspace-web login.

## Depends on
synapse-web 09.
