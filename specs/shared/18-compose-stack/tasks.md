# Tasks

- [x] 1. Python image and the first two services: shared uv workspace image, `mock-sap` (butterfly) and `auth-api` with env, data, health checks and the bind-mounted `auth.db`. Done when both are healthy and sign-in works against the container.
- [ ] 2. The other APIs: `synapse-api`, `workspace-api`, `intent-api` wired by service names to mock-sap, intent-classifier and each other, with `depends_on` health order. Done when a sales order, a customer create and an AI question work through the containers.
- [ ] 3. The web apps: Node image, three Vite services on their ports. Done when the three apps load and sign in against the containerised APIs.
- [ ] 4. Watch mode, profiles and retiring `dev.sh`: `develop.watch` rules per service, profiles, `dev.sh` removed, READMEs updated. Done when the watch acceptance cases pass.
