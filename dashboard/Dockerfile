# =============================================================================
# Xcapit FHE-ML Platform — Dashboard Dockerfile
# =============================================================================
#
# Multi-stage build for the React dashboard.
#
# Usage:
#   docker build -t xcapit-dashboard .
#   docker run -p 3000:80 xcapit-dashboard
#
# Build args:
#   VITE_API_BASE_URL   → Backend API URL (default: http://localhost:8000)
#   VITE_DEFAULT_LANG   → Default language: es | en (default: es)
#
# =============================================================================

# --------------- Stage 1: Build ---------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_DEFAULT_LANG=es
ARG VITE_ENABLE_BLOCKCHAIN=true
ARG VITE_ENABLE_FHE=true

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_DEFAULT_LANG=${VITE_DEFAULT_LANG}
ENV VITE_ENABLE_BLOCKCHAIN=${VITE_ENABLE_BLOCKCHAIN}
ENV VITE_ENABLE_FHE=${VITE_ENABLE_FHE}

RUN npm run build

# --------------- Stage 2: Serve ---------------
FROM nginx:1.27-alpine AS production

# Security: non-root user
RUN addgroup -g 1001 -S app && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G app app

# Nginx configuration for SPA
COPY --from=builder /app/dist /usr/share/nginx/html

RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 256;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml text/javascript image/svg+xml;

    # Cache static assets (1 year)
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA: all routes → index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Health check
    location /health {
        access_log off;
        return 200 '{"status":"ok"}';
        add_header Content-Type application/json;
    }
}
EOF

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --spider -q http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
