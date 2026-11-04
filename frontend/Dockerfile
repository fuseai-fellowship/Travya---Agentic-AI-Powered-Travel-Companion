# syntax=docker/dockerfile:1
# check=skip=SecretsUsedInArgOrEnv
# (The VITE_FIREBASE_* values are public web-app identifiers that end up in the bundle anyway, not secrets.)
# Travya web. Targets: `dev` (Vite dev server) and `prod` (default; static build on unprivileged nginx).

FROM node:24-alpine@sha256:8a32c8cf649a49915a66e81e7a609223c708d0adabf288ee3f4077d765542f85 AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

# ---------------------------------------------------------------------------
# dev: source is bind-mounted over /app by compose.override.yaml (node_modules stays in the image).
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]

# ---------------------------------------------------------------------------
# build: Vite inlines VITE_* at build time. Never pass secrets here; everything lands in the public bundle.
FROM deps AS build
ARG VITE_API_URL
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_AUTH_DOMAIN
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_AUTH_EMULATOR_URL
COPY . .
RUN npm run build

# ---------------------------------------------------------------------------
# prod: nginx renders nginx.conf through envsubst at start (only *_ORIGIN variables), listens on 8080 as uid 101.
FROM nginxinc/nginx-unprivileged:1.31-alpine@sha256:b5047b9b76845eac124358373c6852377c52e4b05834a47647e955dd91cb8f1e AS prod
ENV API_ORIGIN=http://localhost:8000 \
    AUTH_EMULATOR_ORIGIN="" \
    NGINX_ENVSUBST_FILTER=_ORIGIN\$
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "--spider", "http://127.0.0.1:8080/healthz"]
