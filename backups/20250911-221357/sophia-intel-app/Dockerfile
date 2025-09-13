# Agent UI - Next.js Frontend for Sophia Intel AI
# Multi-stage build with proper node permissions to fix BuildKit cache corruption

# Dependencies stage
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat curl

# Create app directory with proper ownership
RUN mkdir -p /app && chown node:node /app
WORKDIR /app
USER node

# Install dependencies with cache mount
COPY --chown=node:node package*.json pnpm-lock.yaml* ./
RUN --mount=type=cache,target=/home/node/.pnpm-store,uid=1000,gid=1000 \
    npm install -g pnpm && pnpm install --frozen-lockfile

# Builder stage
FROM node:20-alpine AS builder
RUN mkdir -p /app && chown node:node /app
WORKDIR /app
USER node

# Copy dependencies
COPY --from=deps --chown=node:node /app/node_modules ./node_modules

# Copy source code with proper ownership
COPY --chown=node:node src ./src
COPY --chown=node:node public ./public
COPY --chown=node:node next.config.ts ./
COPY --chown=node:node tailwind.config.ts ./
COPY --chown=node:node postcss.config.mjs ./
COPY --chown=node:node tsconfig.json ./
COPY --chown=node:node package.json ./
COPY --chown=node:node package-lock.json ./
COPY --chown=node:node components.json ./

# Set environment variables for build
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_DEFAULT_ENDPOINT=http://localhost:8000
ARG NEXT_PUBLIC_PLAYGROUND_URL=http://localhost:8000
ARG NEXT_PUBLIC_BRIDGE_URL=http://localhost:7777
ARG NEXT_PUBLIC_USE_BRIDGE=false

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_DEFAULT_ENDPOINT=$NEXT_PUBLIC_DEFAULT_ENDPOINT
ENV NEXT_PUBLIC_PLAYGROUND_URL=$NEXT_PUBLIC_PLAYGROUND_URL
ENV NEXT_PUBLIC_BRIDGE_URL=$NEXT_PUBLIC_BRIDGE_URL
ENV NEXT_PUBLIC_USE_BRIDGE=$NEXT_PUBLIC_USE_BRIDGE
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build with standalone output
RUN npx pnpm build

# Production stage
FROM node:20-alpine AS runner
RUN apk add --no-cache curl

# Create app directory with proper ownership
RUN mkdir -p /app && chown node:node /app
WORKDIR /app
USER node

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy standalone build output
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/public ./public

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["node", "server.js"]
