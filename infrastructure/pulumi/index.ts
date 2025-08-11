import * as pulumi from "@pulumi/pulumi";
import * as docker from "@pulumi/docker";
import * as random from "@pulumi/random";

// Configuration
const config = new pulumi.Config();

// Lambda Labs Configuration
const lambdaApiKey = config.requireSecret("secrets:LAMBDA_API_KEY");
const lambdaCloudApiKey = config.requireSecret("secrets:LAMBDA_CLOUD_API_KEY");

// Application Configuration
const appName = "sophia-intel";
const environment = config.get("environment") || "dev";

// Create a random suffix for unique naming
const suffix = new random.RandomId("suffix", {
    byteLength: 4,
});

// Docker Network for Sophia Intel services
const sophiaNetwork = new docker.Network("sophia-network", {
    name: pulumi.interpolate`${appName}-network-${suffix.hex}`,
    driver: "bridge",
    ipamConfigs: [{
        subnet: "172.20.0.0/16",
        gateway: "172.20.0.1",
    }],
});

// Redis Cache for session management and caching
const redisContainer = new docker.Container("redis", {
    name: pulumi.interpolate`${appName}-redis-${suffix.hex}`,
    image: "redis:7-alpine",
    restart: "unless-stopped",
    networksAdvanced: [{
        name: sophiaNetwork.name,
        aliases: ["redis"],
    }],
    ports: [{
        internal: 6379,
        external: 6379,
    }],
    command: ["redis-server", "--appendonly", "yes"],
    volumes: [{
        hostPath: "/opt/sophia-intel/redis-data",
        containerPath: "/data",
    }],
    healthcheck: {
        tests: ["CMD", "redis-cli", "ping"],
        interval: "30s",
        timeout: "10s",
        retries: 3,
    },
});

// PostgreSQL Database
const postgresContainer = new docker.Container("postgres", {
    name: pulumi.interpolate`${appName}-postgres-${suffix.hex}`,
    image: "postgres:15-alpine",
    restart: "unless-stopped",
    networksAdvanced: [{
        name: sophiaNetwork.name,
        aliases: ["postgres"],
    }],
    ports: [{
        internal: 5432,
        external: 5432,
    }],
    envs: [
        "POSTGRES_DB=sophia_intel",
        "POSTGRES_USER=sophia",
        "POSTGRES_PASSWORD=sophia_secure_2025",
        "PGDATA=/var/lib/postgresql/data/pgdata",
    ],
    volumes: [{
        hostPath: "/opt/sophia-intel/postgres-data",
        containerPath: "/var/lib/postgresql/data",
    }],
    healthcheck: {
        tests: ["CMD-SHELL", "pg_isready -U sophia -d sophia_intel"],
        interval: "30s",
        timeout: "10s",
        retries: 3,
    },
});

// Qdrant Vector Database
const qdrantContainer = new docker.Container("qdrant", {
    name: pulumi.interpolate`${appName}-qdrant-${suffix.hex}`,
    image: "qdrant/qdrant:latest",
    restart: "unless-stopped",
    networksAdvanced: [{
        name: sophiaNetwork.name,
        aliases: ["qdrant"],
    }],
    ports: [
        {
            internal: 6333,
            external: 6333,
        },
        {
            internal: 6334,
            external: 6334,
        },
    ],
    volumes: [{
        hostPath: "/opt/sophia-intel/qdrant-data",
        containerPath: "/qdrant/storage",
    }],
    healthcheck: {
        tests: ["CMD", "curl", "-f", "http://localhost:6333/health"],
        interval: "30s",
        timeout: "10s",
        retries: 3,
    },
});

// Build Enhanced MCP Server Docker Image
const mcpServerImage = new docker.Image("sophia-mcp-server", {
    imageName: pulumi.interpolate`sophia-intel/mcp-server:${suffix.hex}`,
    build: {
        context: "../../",
        dockerfile: "../../Dockerfile.enhanced-mcp",
        platform: "linux/amd64",
    },
    skipPush: true,
});

// Enhanced MCP Server Container
const mcpServerContainer = new docker.Container("mcp-server", {
    name: pulumi.interpolate`${appName}-mcp-server-${suffix.hex}`,
    image: mcpServerImage.imageName,
    restart: "unless-stopped",
    networksAdvanced: [{
        name: sophiaNetwork.name,
        aliases: ["mcp-server"],
    }],
    ports: [{
        internal: 8001,
        external: 8001,
    }],
    envs: [
        pulumi.interpolate`LAMBDA_API_KEY=${lambdaApiKey}`,
        pulumi.interpolate`LAMBDA_CLOUD_API_KEY=${lambdaCloudApiKey}`,
        "REDIS_URL=redis://redis:6379",
        "DATABASE_URL=postgresql://sophia:sophia_secure_2025@postgres:5432/sophia_intel",
        "QDRANT_URL=http://qdrant:6333",
        "MCP_PORT=8001",
        "ENVIRONMENT=production",
        "LOG_LEVEL=INFO",
    ],
    healthcheck: {
        tests: ["CMD", "curl", "-f", "http://localhost:8001/health"],
        interval: "30s",
        timeout: "10s",
        retries: 3,
        startPeriod: "60s",
    },
});

// Nginx Reverse Proxy for load balancing and SSL termination
const nginxContainer = new docker.Container("nginx", {
    name: pulumi.interpolate`${appName}-nginx-${suffix.hex}`,
    image: "nginx:alpine",
    restart: "unless-stopped",
    networksAdvanced: [{
        name: sophiaNetwork.name,
        aliases: ["nginx"],
    }],
    ports: [
        {
            internal: 80,
            external: 80,
        },
        {
            internal: 443,
            external: 443,
        },
    ],
    volumes: [{
        hostPath: "/opt/sophia-intel/nginx.conf",
        containerPath: "/etc/nginx/nginx.conf",
        readOnly: true,
    }],
});

// Lambda Labs Instance Configuration (for reference)
const lambdaConfig = {
    instanceType: "gpu_1x_h100_pcie",
    region: "us-east-1",
    sshKeyName: "sophia-intel-key",
    name: pulumi.interpolate`sophia-intel-${environment}-${suffix.hex}`,
};

// Create Lambda Labs API test script
const lambdaTestScript = new docker.Container("lambda-test", {
    name: pulumi.interpolate`${appName}-lambda-test-${suffix.hex}`,
    image: "node:18-alpine",
    restart: "no",
    networksAdvanced: [{
        name: sophiaNetwork.name,
    }],
    envs: [
        pulumi.interpolate`LAMBDA_API_KEY=${lambdaApiKey}`,
        pulumi.interpolate`LAMBDA_CLOUD_API_KEY=${lambdaCloudApiKey}`,
    ],
    command: [
        "sh", "-c", 
        `
        apk add --no-cache curl &&
        echo "Testing Lambda Labs API connectivity..." &&
        curl -u $LAMBDA_API_KEY: https://cloud.lambda.ai/api/v1/instances &&
        echo "Lambda Labs API test completed"
        `
    ],
});

// Monitoring and Observability
const prometheusContainer = new docker.Container("prometheus", {
    name: pulumi.interpolate`${appName}-prometheus-${suffix.hex}`,
    image: "prom/prometheus:latest",
    restart: "unless-stopped",
    networksAdvanced: [{
        name: sophiaNetwork.name,
        aliases: ["prometheus"],
    }],
    ports: [{
        internal: 9090,
        external: 9090,
    }],
    volumes: [{
        hostPath: "/opt/sophia-intel/prometheus.yml",
        containerPath: "/etc/prometheus/prometheus.yml",
        readOnly: true,
    }],
});

// Grafana for visualization
const grafanaContainer = new docker.Container("grafana", {
    name: pulumi.interpolate`${appName}-grafana-${suffix.hex}`,
    image: "grafana/grafana:latest",
    restart: "unless-stopped",
    networksAdvanced: [{
        name: sophiaNetwork.name,
        aliases: ["grafana"],
    }],
    ports: [{
        internal: 3000,
        external: 3000,
    }],
    envs: [
        "GF_SECURITY_ADMIN_PASSWORD=sophia_admin_2025",
        "GF_USERS_ALLOW_SIGN_UP=false",
    ],
    volumes: [{
        hostPath: "/opt/sophia-intel/grafana-data",
        containerPath: "/var/lib/grafana",
    }],
});

// Export important values
export const networkId = sophiaNetwork.id;
export const networkName = sophiaNetwork.name;
export const mcpServerUrl = pulumi.interpolate`http://localhost:8001`;
export const redisUrl = pulumi.interpolate`redis://localhost:6379`;
export const postgresUrl = pulumi.interpolate`postgresql://sophia:sophia_secure_2025@localhost:5432/sophia_intel`;
export const qdrantUrl = pulumi.interpolate`http://localhost:6333`;
export const prometheusUrl = pulumi.interpolate`http://localhost:9090`;
export const grafanaUrl = pulumi.interpolate`http://localhost:3000`;
export const lambdaInstanceConfig = lambdaConfig;

// Container health status
export const containerStatus = {
    redis: redisContainer.name,
    postgres: postgresContainer.name,
    qdrant: qdrantContainer.name,
    mcpServer: mcpServerContainer.name,
    nginx: nginxContainer.name,
    prometheus: prometheusContainer.name,
    grafana: grafanaContainer.name,
};

// Lambda Labs API endpoints
export const lambdaEndpoints = {
    instances: "https://cloud.lambda.ai/api/v1/instances",
    instanceTypes: "https://cloud.lambda.ai/api/v1/instance-types",
    sshKeys: "https://cloud.lambda.ai/api/v1/ssh-keys",
};

// Deployment summary
export const deploymentSummary = {
    environment: environment,
    appName: appName,
    version: "2.0.0",
    infrastructure: "Lambda Labs + Docker",
    services: [
        "Enhanced MCP Server",
        "Redis Cache",
        "PostgreSQL Database", 
        "Qdrant Vector DB",
        "Nginx Reverse Proxy",
        "Prometheus Monitoring",
        "Grafana Visualization"
    ],
    ports: {
        mcpServer: 8001,
        redis: 6379,
        postgres: 5432,
        qdrant: 6333,
        nginx: 80,
        prometheus: 9090,
        grafana: 3000,
    },
};

