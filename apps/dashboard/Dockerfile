# Build stage
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve package
RUN npm install -g serve

# Copy built assets
COPY --from=builder /app/dist ./dist

# Create a start script that uses Railway's PORT variable
RUN echo '#!/bin/sh' > start.sh && \
    echo 'serve -s dist -l ${PORT:-3000}' >> start.sh && \
    chmod +x start.sh

# Expose the port
EXPOSE $PORT

# Start the application
CMD ["./start.sh"]

