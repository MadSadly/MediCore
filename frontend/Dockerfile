# ── Stage 1: 빌드 ──────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

# 의존성 캐시 레이어
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: Nginx 서빙 ────────────────────────────────────────────
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
