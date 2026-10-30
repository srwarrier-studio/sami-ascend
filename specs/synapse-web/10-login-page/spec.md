# synapse-web/10 login-page

## Goal
The sign-in page looks like a product, not a form on a blank page: a centred card over a full-screen animation that says "synapse": a network of neurons with an occasional electric pulse.

## Behavior
- `/login` is a full-screen page (no shell) on a deep navy gradient with the animated network filling the whole background. The sign-in card sits in the centre, with the Synapse mark, name and `Sense. Connect. Lead.` above it in white. The same on narrow screens.
- Form: the existing sign-in (`Work email`, `Password`, `Sign in`, the `Incorrect email or password` error) with the title `Sign in to Synapse`, and the same behaviour as today.
- Animation, drawn as neurons on a canvas (cell bodies, branching dendrites, long axons) with a fixed hand-placed layout:
  - seven neurons, each drifting a few pixels on its own slow loop, like floating in fluid;
  - every few seconds an electric pulse (blue-white) runs along an axon to the next neuron, flashing the synapse where it arrives and the next cell body, so a signal passes across the network; the page is calm between signals;
  - drawn at 30 frames per second, paused while the tab is hidden, nothing drawn per frame that is not needed.
- No new dependency, no inline style props (theme-only rule). The navy and the blue-white pulse are fixed brand colours, the same in light and dark mode.
- The app is named `Sami Synapse` (one `APP_NAME`), and the card has a `Sign in with Microsoft` button that only says it is coming soon; wiring it to Entra is a later phase.
- The animation stops (static network, no pulses) when motion is `minimal` or the user's system asks for reduced motion.
- The splash screen shown while the session loads is unchanged.
- The animation is used on the login page only. The component lives in synapse-web (`src/login/`), the shared `SignInCard` in `@sami/ui` is used as it is or gets one optional prop, other apps unchanged.

## Acceptance cases
- The login page shows the brand name, the tagline and the form; signing in, the wrong-password error and the redirect after sign-in work as before.
- The network is a canvas hidden from assistive technology; the timeline (pulse travel, flash, drift) is tested.
- With minimal motion nothing is animated.
- No inline styles and no new dependency (existing theme-only tests pass).

## Out of scope
WebGL, sound, a looping video background, a dark-mode specific design beyond using theme colours, forgot-password and single sign-on buttons, changing the splash screen, the workspace-web login.

## Depends on
synapse-web 09.
