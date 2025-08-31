# Agent UI - Next.js Frontend for Sophia Intel AI
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
COPY pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

# Copy source code (excluding node_modules to avoid conflicts)
COPY src ./src
COPY public ./public
COPY next.config.ts ./
COPY tailwind.config.ts ./
COPY postcss.config.mjs ./
COPY tsconfig.json ./
COPY package.json ./
COPY package-lock.json ./
COPY components.json ./

# Set environment variables for build
ARG NEXT_PUBLIC_API_URL=http://localhost:8003
ARG NEXT_PUBLIC_DEFAULT_ENDPOINT=http://localhost:8003
ARG NEXT_PUBLIC_PLAYGROUND_URL=http://localhost:8003
ARG NEXT_PUBLIC_BRIDGE_URL=http://localhost:7777
ARG NEXT_PUBLIC_USE_BRIDGE=false

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_DEFAULT_ENDPOINT=$NEXT_PUBLIC_DEFAULT_ENDPOINT
ENV NEXT_PUBLIC_PLAYGROUND_URL=$NEXT_PUBLIC_PLAYGROUND_URL
ENV NEXT_PUBLIC_BRIDGE_URL=$NEXT_PUBLIC_BRIDGE_URL
ENV NEXT_PUBLIC_USE_BRIDGE=$NEXT_PUBLIC_USE_BRIDGE
ENV NODE_ENV=production

# Build the application
RUN pnpm build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["pnpm", "start"]