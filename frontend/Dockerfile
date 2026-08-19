FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ARG VITE_APP_NAME=Swift
ARG VITE_DEFAULT_THEME=light
ARG VITE_USE_MOCK_API=true
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_DEFAULT_THEME=${VITE_DEFAULT_THEME} \
    VITE_USE_MOCK_API=${VITE_USE_MOCK_API}

RUN npm run build

FROM nginx:1.27-alpine AS runtime

LABEL org.opencontainers.image.title="Swift Frontend" \
      org.opencontainers.image.description="Trilingual financial support ticket frontend" \
      org.opencontainers.image.source="local" \
      org.opencontainers.image.version="1.0.0"

COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html
COPY --chown=nginx:nginx nginx/nginx.conf /etc/nginx/nginx.conf
COPY --chown=nginx:nginx nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --chown=nginx:nginx nginx/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh

RUN chmod 755 /docker-entrypoint.d/40-runtime-config.sh \
    && sed -i 's/\r$//' /docker-entrypoint.d/40-runtime-config.sh \
    && mkdir -p /tmp/nginx-conf \
    && chown -R nginx:nginx /tmp/nginx-conf

ENV API_BASE_URL=http://backend:8000/api/v1 \
    NGINX_ENVSUBST_OUTPUT_DIR=/tmp/nginx-conf

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
