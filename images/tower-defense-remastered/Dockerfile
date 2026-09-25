# syntax=docker/dockerfile:1
# Tower Defense Remastered: static Vite build served by an unprivileged nginx.
# Context: the tower-defense-remastered repository. The nginx configuration comes from this folder through the
# named build context "config" (docker buildx build --build-context config=images/tower-defense-remastered ...).

FROM node:25-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.30-alpine
# "config" is a named build context, not a stage
# hadolint ignore=DL3022
COPY --from=config nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD ["wget", "-qO", "/dev/null", "http://127.0.0.1:8080/"]
