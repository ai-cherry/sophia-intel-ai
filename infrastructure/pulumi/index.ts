import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as docker from "@pulumi/docker";
import * as random from "@pulumi/random";

// Configuration
const config = new pulumi.Config();
const environment = config.get("environment") || "dev";
const lambdaRegion = config.get("lambda:region") || "us-west-1";
const awsRegion = config.get("aws:region") || "us-west-2";

// Tags for all resources
const commonTags = {
    Project: "sophia-intel",
    Environment: environment,
    ManagedBy: "pulumi",
    Owner: "sophia-team"
};

// Secret Management with Pulumi ESC Integration
const secretConfig = new pulumi.Config("secrets");

// Core secrets from environment
const secrets = {
    // AI Providers
    openaiApiKey: secretConfig.requireSecret("OPENAI_API_KEY"),
    anthropicApiKey: secretConfig.requireSecret("ANTHROPIC_API_KEY"),
    geminiApiKey: secretConfig.requireSecret("GEMINI_API_KEY"),
    grokApiKey: secretConfig.requireSecret("GROK_API_KEY"),
    groqApiKey: secretConfig.requireSecret("GROQ_API_KEY"),
    deepseekApiKey: secretConfig.requireSecret("DEEPSEEK_API_KEY"),
    openrouterApiKey: secretConfig.requireSecret("OPENROUTER_API_KEY"),
    
    // Infrastructure
    lambdaApiKey: secretConfig.requireSecret("LAMBDA_API_KEY"),
    lambdaCloudApiKey: secretConfig.requireSecret("LAMBDA_CLOUD_API_KEY"),
    pulumiAccessToken: secretConfig.requireSecret("PULUMI_ACCESS_TOKEN"),
    dockerPat: secretConfig.requireSecret("DOCKER_PAT"),
    
    // Databases
    neonApiToken: secretConfig.requireSecret("NEON_API_TOKEN"),
    weaviateApiKey: secretConfig.requireSecret("WEAVIATE_ADMIN_API_KEY"),
    qdrantApiKey: secretConfig.requireSecret("QDRANT_API_KEY"),
    neo4jClientId: secretConfig.requireSecret("NEO4J_CLIENT_ID"),
    neo4jClientSecret: secretConfig.requireSecret("NEO4J_CLIENT_SECRET"),
    redisApiKey: secretConfig.requireSecret("REDIS_USER_API_KEY"),
    
    // Business Tools
    gongAccessKey: secretConfig.requireSecret("GONG_ACCESS_KEY"),
    gongClientSecret: secretConfig.requireSecret("GONG_CLIENT_SECRET"),
    hubspotApiToken: secretConfig.requireSecret("HUBSPOT_API_TOKEN"),
    salesforceAccessToken: secretConfig.requireSecret("SALESFORCE_ACCESS_TOKEN"),
    
    // Communication
    telegramApiKey: secretConfig.requireSecret("TELEGRAM_API_KEY"),
    slackAppToken: secretConfig.requireSecret("SLACK_APP_TOKEN"),
    
    // Monitoring
    sentryApiToken: secretConfig.requireSecret("SENTRY_API_TOKEN"),
};

// VPC and Networking
const vpc = new aws.ec2.Vpc("sophia-vpc", {
    cidrBlock: "10.0.0.0/16",
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: { ...commonTags, Name: "sophia-vpc" }
});

const publicSubnet = new aws.ec2.Subnet("sophia-public-subnet", {
    vpcId: vpc.id,
    cidrBlock: "10.0.1.0/24",
    availabilityZone: "us-west-2a",
    mapPublicIpOnLaunch: true,
    tags: { ...commonTags, Name: "sophia-public-subnet" }
});

const privateSubnet = new aws.ec2.Subnet("sophia-private-subnet", {
    vpcId: vpc.id,
    cidrBlock: "10.0.2.0/24",
    availabilityZone: "us-west-2b",
    tags: { ...commonTags, Name: "sophia-private-subnet" }
});

const internetGateway = new aws.ec2.InternetGateway("sophia-igw", {
    vpcId: vpc.id,
    tags: { ...commonTags, Name: "sophia-igw" }
});

const routeTable = new aws.ec2.RouteTable("sophia-rt", {
    vpcId: vpc.id,
    routes: [{
        cidrBlock: "0.0.0.0/0",
        gatewayId: internetGateway.id
    }],
    tags: { ...commonTags, Name: "sophia-rt" }
});

const routeTableAssociation = new aws.ec2.RouteTableAssociation("sophia-rta", {
    subnetId: publicSubnet.id,
    routeTableId: routeTable.id
});

// Security Groups
const mcpServerSg = new aws.ec2.SecurityGroup("sophia-mcp-sg", {
    name: "sophia-mcp-security-group",
    description: "Security group for Sophia MCP servers",
    vpcId: vpc.id,
    ingress: [
        {
            protocol: "tcp",
            fromPort: 8000,
            toPort: 8010,
            cidrBlocks: ["0.0.0.0/0"],
            description: "MCP server ports"
        },
        {
            protocol: "tcp",
            fromPort: 22,
            toPort: 22,
            cidrBlocks: ["0.0.0.0/0"],
            description: "SSH access"
        },
        {
            protocol: "tcp",
            fromPort: 443,
            toPort: 443,
            cidrBlocks: ["0.0.0.0/0"],
            description: "HTTPS"
        }
    ],
    egress: [{
        protocol: "-1",
        fromPort: 0,
        toPort: 0,
        cidrBlocks: ["0.0.0.0/0"]
    }],
    tags: { ...commonTags, Name: "sophia-mcp-sg" }
});

// Application Load Balancer
const alb = new aws.lb.LoadBalancer("sophia-alb", {
    name: "sophia-alb",
    loadBalancerType: "application",
    subnets: [publicSubnet.id, privateSubnet.id],
    securityGroups: [mcpServerSg.id],
    tags: commonTags
});

// Target Groups for MCP Services
const mcpTargetGroup = new aws.lb.TargetGroup("sophia-mcp-tg", {
    name: "sophia-mcp-tg",
    port: 8001,
    protocol: "HTTP",
    vpcId: vpc.id,
    healthCheck: {
        enabled: true,
        healthyThreshold: 2,
        interval: 30,
        matcher: "200",
        path: "/health",
        port: "traffic-port",
        protocol: "HTTP",
        timeout: 5,
        unhealthyThreshold: 2
    },
    tags: commonTags
});

// ALB Listener
const albListener = new aws.lb.Listener("sophia-alb-listener", {
    loadBalancerArn: alb.arn,
    port: 443,
    protocol: "HTTPS",
    sslPolicy: "ELBSecurityPolicy-TLS-1-2-2017-01",
    certificateArn: "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012", // Replace with actual cert
    defaultActions: [{
        type: "forward",
        targetGroupArn: mcpTargetGroup.arn
    }]
});

// ECS Cluster for MCP Services
const cluster = new aws.ecs.Cluster("sophia-cluster", {
    name: "sophia-cluster",
    tags: commonTags
});

// IAM Role for ECS Tasks
const taskRole = new aws.iam.Role("sophia-task-role", {
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Effect: "Allow",
            Principal: {
                Service: "ecs-tasks.amazonaws.com"
            }
        }]
    }),
    tags: commonTags
});

const taskRolePolicy = new aws.iam.RolePolicy("sophia-task-role-policy", {
    role: taskRole.id,
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "secretsmanager:GetSecretValue",
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath"
                ],
                Resource: "*"
            }
        ]
    })
});

// ECS Task Definition for MCP Server
const mcpTaskDefinition = new aws.ecs.TaskDefinition("sophia-mcp-task", {
    family: "sophia-mcp",
    networkMode: "awsvpc",
    requiresCompatibilities: ["FARGATE"],
    cpu: "1024",
    memory: "2048",
    executionRoleArn: taskRole.arn,
    taskRoleArn: taskRole.arn,
    containerDefinitions: JSON.stringify([{
        name: "sophia-mcp-server",
        image: "sophia-intel/mcp-server:latest",
        portMappings: [{
            containerPort: 8001,
            protocol: "tcp"
        }],
        environment: [
            { name: "ENVIRONMENT", value: environment },
            { name: "AWS_REGION", value: awsRegion },
            { name: "LAMBDA_REGION", value: lambdaRegion }
        ],
        secrets: [
            { name: "OPENAI_API_KEY", valueFrom: secrets.openaiApiKey },
            { name: "ANTHROPIC_API_KEY", valueFrom: secrets.anthropicApiKey },
            { name: "LAMBDA_API_KEY", valueFrom: secrets.lambdaApiKey },
            { name: "WEAVIATE_API_KEY", valueFrom: secrets.weaviateApiKey },
            { name: "QDRANT_API_KEY", valueFrom: secrets.qdrantApiKey }
        ],
        logConfiguration: {
            logDriver: "awslogs",
            options: {
                "awslogs-group": "/ecs/sophia-mcp",
                "awslogs-region": awsRegion,
                "awslogs-stream-prefix": "ecs"
            }
        },
        healthCheck: {
            command: ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"],
            interval: 30,
            timeout: 5,
            retries: 3,
            startPeriod: 60
        }
    }]),
    tags: commonTags
});

// CloudWatch Log Group
const logGroup = new aws.cloudwatch.LogGroup("sophia-mcp-logs", {
    name: "/ecs/sophia-mcp",
    retentionInDays: 30,
    tags: commonTags
});

// ECS Service
const mcpService = new aws.ecs.Service("sophia-mcp-service", {
    name: "sophia-mcp-service",
    cluster: cluster.id,
    taskDefinition: mcpTaskDefinition.arn,
    desiredCount: 2,
    launchType: "FARGATE",
    networkConfiguration: {
        subnets: [privateSubnet.id],
        securityGroups: [mcpServerSg.id],
        assignPublicIp: false
    },
    loadBalancers: [{
        targetGroupArn: mcpTargetGroup.arn,
        containerName: "sophia-mcp-server",
        containerPort: 8001
    }],
    tags: commonTags
}, { dependsOn: [albListener] });

// Lambda Labs Integration (Custom Resource)
const lambdaLabsInstance = new aws.lambda.Function("sophia-lambda-labs", {
    name: "sophia-lambda-labs-manager",
    runtime: "python3.9",
    handler: "index.handler",
    role: taskRole.arn,
    code: new pulumi.asset.AssetArchive({
        "index.py": new pulumi.asset.StringAsset(`
import json
import boto3
import requests
import os

def handler(event, context):
    """Manage Lambda Labs instances"""
    
    lambda_api_key = os.environ['LAMBDA_API_KEY']
    action = event.get('action', 'status')
    
    headers = {
        'Authorization': f'Bearer {lambda_api_key}',
        'Content-Type': 'application/json'
    }
    
    base_url = 'https://cloud.lambda.ai/api/v1'
    
    if action == 'create':
        # Create GPU instance for MCP workloads
        payload = {
            'region_name': 'us-west-1',
            'instance_type_name': 'gpu_1x_h100',
            'ssh_key_names': ['sophia-ssh-key'],
            'file_system_names': [],
            'quantity': 1,
            'name': 'sophia-mcp-gpu'
        }
        
        response = requests.post(
            f'{base_url}/instance-operations/launch',
            headers=headers,
            json=payload
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(response.json())
        }
    
    elif action == 'status':
        response = requests.get(
            f'{base_url}/instances',
            headers=headers
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(response.json())
        }
    
    return {
        'statusCode': 400,
        'body': json.dumps({'error': 'Invalid action'})
    }
`)
    }),
    environment: {
        variables: {
            LAMBDA_API_KEY: secrets.lambdaApiKey
        }
    },
    tags: commonTags
});

// Route 53 DNS Configuration
const hostedZone = new aws.route53.Zone("sophia-zone", {
    name: "sophia-intel.ai",
    tags: commonTags
});

const mcpRecord = new aws.route53.Record("sophia-mcp-record", {
    zoneId: hostedZone.zoneId,
    name: "mcp.sophia-intel.ai",
    type: "A",
    aliases: [{
        name: alb.dnsName,
        zoneId: alb.zoneId,
        evaluateTargetHealth: true
    }]
});

// Outputs
export const vpcId = vpc.id;
export const albDnsName = alb.dnsName;
export const mcpEndpoint = pulumi.interpolate`https://${mcpRecord.name}`;
export const clusterName = cluster.name;
export const lambdaLabsFunctionName = lambdaLabsInstance.name;
export const hostedZoneId = hostedZone.zoneId;

// Export configuration for other stacks
export const config_outputs = {
    vpc_id: vpc.id,
    public_subnet_id: publicSubnet.id,
    private_subnet_id: privateSubnet.id,
    security_group_id: mcpServerSg.id,
    alb_dns_name: alb.dnsName,
    cluster_name: cluster.name,
    environment: environment
};

