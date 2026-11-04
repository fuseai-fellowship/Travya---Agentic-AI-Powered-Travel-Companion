# syntax=docker/dockerfile:1
# Firebase Auth emulator for local development and e2e (project `demo-travya`: no credentials, no network).
FROM node:24-alpine@sha256:8a32c8cf649a49915a66e81e7a609223c708d0adabf288ee3f4077d765542f85
ARG FIREBASE_TOOLS_VERSION=15.34.2
RUN npm install --global --no-audit --no-fund "firebase-tools@${FIREBASE_TOOLS_VERSION}" \
    && npm cache clean --force
WORKDIR /srv/firebase
# firebase-tools writes firebase-debug.log to the working directory
COPY --chown=node:node firebase.json ./
RUN chown node:node /srv/firebase
USER node
EXPOSE 9099
HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=20 \
    CMD ["wget", "-qO-", "http://127.0.0.1:9099/"]
CMD ["firebase", "emulators:start", "--only", "auth", "--project", "demo-travya"]
