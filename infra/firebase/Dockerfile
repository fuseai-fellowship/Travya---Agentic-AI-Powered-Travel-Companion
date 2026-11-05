# syntax=docker/dockerfile:1
# Firebase Auth emulator for local development and e2e (project `demo-travya`: no credentials, no network).
# firebase-tools comes from package-lock.json (npm ci), so every dependency is pinned by integrity hash.
FROM node:24-alpine@sha256:8a32c8cf649a49915a66e81e7a609223c708d0adabf288ee3f4077d765542f85
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
