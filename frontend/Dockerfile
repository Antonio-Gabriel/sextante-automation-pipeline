# Sextante frontend image (deploy ticket 02). Build from the repository root:
#   docker compose build web
# Base images are pinned by digest: a moved tag never changes what is built (SEC-20).

# --- Build: type-check and compile; nothing of this stage reaches the runtime ----------
FROM node:22-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee AS build

WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# Only VITE_SEXTANTE_ variables reach the compiled code, and none is set here: the
# bundle holds no secret (SEC-02). The API types come from the committed openapi.json.
RUN npm run build

# --- Runtime: static files and a reverse proxy, as an unprivileged user ----------------
# The slim variant of the official unprivileged image: nginx only, without curl and the
# extra modules this server does not use, and with the fewest known vulnerabilities.
FROM nginxinc/nginx-unprivileged:mainline-alpine-slim@sha256:a8cb0f33d51fa107c96fd2bd3a71aaf564ec131e9d2bdf8700944f0ed8b170d7

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /build/dist /usr/share/nginx/html

USER 101:101
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]
