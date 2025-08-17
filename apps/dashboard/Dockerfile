# Build stage
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# Production stage - use a simple static server
FROM node:18-alpine

WORKDIR /app

# Install serve package for static file serving
RUN npm install -g serve

# Copy built assets from builder stage
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Serve static files
CMD ["serve", "-s", "dist", "-l", "3000"]

