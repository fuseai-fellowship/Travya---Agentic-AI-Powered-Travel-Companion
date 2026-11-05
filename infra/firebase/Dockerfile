# syntax=docker/dockerfile:1
# Firebase Auth emulator for local development and e2e (project `demo-travya`: no credentials, no network).
# firebase-tools comes from package-lock.json (npm ci), so every dependency is pinned by integrity hash.
FROM node:26-alpine@sha256:c6ad9e9c1d80f6eb607c26b4b0a132ff7a2344fad1c78ea3baa2a7d4c8de6d94
WORKDIR /srv/firebase
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund && npm cache clean --force
ENV PATH="/srv/firebase/node_modules/.bin:${PATH}"
# firebase-tools writes firebase-debug.log to the working directory
COPY --chown=node:node firebase.json ./
RUN chown node:node /srv/firebase
USER node
EXPOSE 9099
HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=20 \
    CMD ["wget", "-qO-", "http://127.0.0.1:9099/"]
CMD ["firebase", "emulators:start", "--only", "auth", "--project", "demo-travya"]
