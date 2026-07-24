# P1 — Angular application. Build context: frontend/ (this directory).
# environment.ts's apiBaseUrl (http://localhost:8080) is baked in at build
# time and still correct in Docker: the browser runs on the host, not inside
# the compose network, so it reaches Spring Boot via its published port —
# no reverse proxy needed, same as CorsConfig's existing localhost:4200 allow-list.
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration production

FROM nginx:alpine
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
