# SOPHIA Dashboard Dockerfile for Northflank
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY apps/dashboard/package.json apps/dashboard/pnpm-lock.yaml ./

# Install dependencies
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile

# Copy source code
COPY apps/dashboard/ .

# Build the application
RUN pnpm run build

# Production stage with Nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY northflank/docker/nginx.conf /etc/nginx/nginx.conf

# Create non-root user
RUN addgroup -g 1001 -S sophia && \
    adduser -S sophia -u 1001 -G sophia

# Set permissions
RUN chown -R sophia:sophia /usr/share/nginx/html
RUN chown -R sophia:sophia /var/cache/nginx
RUN chown -R sophia:sophia /var/log/nginx
RUN chown -R sophia:sophia /etc/nginx/conf.d
RUN touch /var/run/nginx.pid
RUN chown -R sophia:sophia /var/run/nginx.pid

# Switch to non-root user
USER sophia

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]

