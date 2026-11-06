# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is enabled on this template. See [this documentation](https://react.dev/learn/react-compiler) for more information.

Note: This will impact Vite dev & build performances.
You can also try [the experimental native React Compiler support in plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md#rust-react-compiler) by using `compiler: true` in the plugin options instead of using the Babel plugin.

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.

## AI Mode and intent-api
AI Mode asks intent-api (`VITE_INTENT_URL`, default `http://localhost:8006`) first and draws its answer; questions it refuses go to the widget catalog, and when it is down the page says the AI service is not available with a Try again button; when widgets then answer, the reading card keeps "Understood as <domain>" and drops the refusal sentence. To see it, run Laya with the tuned checkpoint and intent-api (see `apps/intent-api/README.md`) with the same `JWT_SECRET`; `docker compose up -d --wait` from the repo root starts the whole stack.

## Company and currency
The company chosen in the picker (`all` for users with several companies) is sent as `company` on every synapse-api read and on intent-api answers; a 403 `COMPANY_NOT_ALLOWED` shows a "No access" message. Widget data is requested with `currency=USD`; a money widget draws the sign of the `currency` the data names, and `₹` when it names none.
