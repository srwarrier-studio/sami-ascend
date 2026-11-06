FROM node:24-slim
RUN npm install -g pnpm@11.28.8
USER node
WORKDIR /app
COPY --chown=node package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=node packages/ui/package.json packages/ui/
COPY --chown=node apps/workspace-web/package.json apps/workspace-web/
COPY --chown=node apps/synapse-web/package.json apps/synapse-web/
COPY --chown=node apps/admin-web/package.json apps/admin-web/
RUN pnpm install --frozen-lockfile --ignore-scripts
COPY --chown=node packages/ui packages/ui
COPY --chown=node apps/workspace-web apps/workspace-web
COPY --chown=node apps/synapse-web apps/synapse-web
COPY --chown=node apps/admin-web apps/admin-web
