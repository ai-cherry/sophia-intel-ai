FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY apps/interface/package*.json ./
RUN npm ci

# Copy source
COPY apps/interface/ .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
