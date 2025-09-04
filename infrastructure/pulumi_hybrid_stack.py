"""
Pulumi Infrastructure as Code for Unified Hybrid Intelligence Platform
=====================================================================

Dynamic infrastructure provisioning for Sophia (Business) + Artemis (Technical)
agent factories with auto-scaling, multi-region deployment, and GPU integration.
"""

import json
from typing import Dict, List, Any

import pulumi
import pulumi_aws as aws
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s
from pulumi import Config, export, Output
from pulumi_aws import ec2, ecs, iam, rds, elasticache, s3

# Configuration
config = Config()
environment = config.get("environment") or "production"
region = config.get("region") or "us-east-1"
project_name = "sophia-artemis-unified"

# Resource tags
default_tags = {
    "Project": project_name,
    "Environment": environment,
    "ManagedBy": "pulumi",
    "Platform": "hybrid-intelligence"
}


class HybridIntelligencePlatform:
    """
    Complete infrastructure stack for unified hybrid intelligence platform
    """
    
    def __init__(self):
        self.vpc = None
        self.subnets = {}
        self.security_groups = {}
        self.databases = {}
        self.cache_clusters = {}
        self.compute_resources = {}
        self.storage = {}
        self.load_balancers = {}
        self.auto_scaling = {}
        
    def create_infrastructure(self):
        """Create complete infrastructure stack"""
        
        # 1. Network Infrastructure
        self._create_network_infrastructure()
        
        # 2. Data Layer
        self._create_data_layer()
        
        # 3. Compute Infrastructure
        self._create_compute_infrastructure()
        
        # 4. Auto-scaling and Load Balancing
        self._create_auto_scaling()
        
        # 5. GPU Clusters for Learning
        self._create_gpu_infrastructure()
        
        # 6. Monitoring and Observability
        self._create_monitoring_stack()
        
        # 7. Security and IAM
        self._create_security_infrastructure()
        
        # Export key outputs
        self._export_outputs()
        
        return self
    
    def _create_network_infrastructure(self):
        """Create VPC, subnets, and networking components"""
        
        # VPC
        self.vpc = ec2.Vpc(
            f"{project_name}-vpc",
            cidr_block="10.0.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={**default_tags, "Name": f"{project_name}-vpc"}
        )
        
        # Internet Gateway
        igw = ec2.InternetGateway(
            f"{project_name}-igw",
            vpc_id=self.vpc.id,
            tags={**default_tags, "Name": f"{project_name}-igw"}
        )
        
        # Public Subnets (for load balancers)
        availability_zones = ["a", "b", "c"]
        for i, az in enumerate(availability_zones):
            self.subnets[f"public-{az}"] = ec2.Subnet(
                f"{project_name}-public-subnet-{az}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i+1}.0/24",
                availability_zone=f"{region}{az}",
                map_public_ip_on_launch=True,
                tags={**default_tags, "Name": f"{project_name}-public-{az}"}
            )
            
            # Private Subnets (for application servers)
            self.subnets[f"private-{az}"] = ec2.Subnet(
                f"{project_name}-private-subnet-{az}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i+10}.0/24",
                availability_zone=f"{region}{az}",
                tags={**default_tags, "Name": f"{project_name}-private-{az}"}
            )
            
            # Database Subnets
            self.subnets[f"db-{az}"] = ec2.Subnet(
                f"{project_name}-db-subnet-{az}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i+20}.0/24",
                availability_zone=f"{region}{az}",
                tags={**default_tags, "Name": f"{project_name}-db-{az}"}
            )
        
        # Route Tables
        public_route_table = ec2.RouteTable(
            f"{project_name}-public-rt",
            vpc_id=self.vpc.id,
            routes=[
                ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    gateway_id=igw.id
                )
            ],
            tags={**default_tags, "Name": f"{project_name}-public-rt"}
        )
        
        # Associate public subnets with public route table
        for az in availability_zones:
            ec2.RouteTableAssociation(
                f"{project_name}-public-rta-{az}",
                subnet_id=self.subnets[f"public-{az}"].id,
                route_table_id=public_route_table.id
            )
        
        # NAT Gateways for private subnets
        for i, az in enumerate(availability_zones):
            nat_eip = ec2.Eip(
                f"{project_name}-nat-eip-{az}",
                vpc=True,
                tags={**default_tags, "Name": f"{project_name}-nat-eip-{az}"}
            )
            
            nat_gateway = ec2.NatGateway(
                f"{project_name}-nat-{az}",
                allocation_id=nat_eip.id,
                subnet_id=self.subnets[f"public-{az}"].id,
                tags={**default_tags, "Name": f"{project_name}-nat-{az}"}
            )
            
            private_route_table = ec2.RouteTable(
                f"{project_name}-private-rt-{az}",
                vpc_id=self.vpc.id,
                routes=[
                    ec2.RouteTableRouteArgs(
                        cidr_block="0.0.0.0/0",
                        nat_gateway_id=nat_gateway.id
                    )
                ],
                tags={**default_tags, "Name": f"{project_name}-private-rt-{az}"}
            )
            
            ec2.RouteTableAssociation(
                f"{project_name}-private-rta-{az}",
                subnet_id=self.subnets[f"private-{az}"].id,
                route_table_id=private_route_table.id
            )
    
    def _create_data_layer(self):
        """Create databases, cache clusters, and storage"""
        
        # Database Subnet Group
        db_subnet_group = rds.SubnetGroup(
            f"{project_name}-db-subnet-group",
            subnet_ids=[
                self.subnets["db-a"].id,
                self.subnets["db-b"].id,
                self.subnets["db-c"].id
            ],
            tags={**default_tags, "Name": f"{project_name}-db-subnet-group"}
        )
        
        # PostgreSQL for structured data (Neon-compatible)
        self.databases["postgresql"] = rds.Instance(
            f"{project_name}-postgresql",
            identifier=f"{project_name}-postgresql",
            engine="postgres",
            engine_version="15.4",
            instance_class="db.r6g.xlarge",  # 4 vCPU, 32 GB RAM
            allocated_storage=500,
            max_allocated_storage=2000,
            storage_type="gp3",
            storage_encrypted=True,
            
            # Database configuration
            db_name="sophia_artemis",
            username="sophia_admin",
            password=config.require_secret("db_password"),
            
            # Network and security
            vpc_security_group_ids=[self._create_database_security_group().id],
            db_subnet_group_name=db_subnet_group.name,
            publicly_accessible=False,
            
            # Backup and maintenance
            backup_retention_period=7,
            backup_window="03:00-04:00",
            maintenance_window="Sun:04:00-Sun:05:00",
            
            # Performance insights
            performance_insights_enabled=True,
            performance_insights_retention_period=7,
            
            tags={**default_tags, "Component": "database"}
        )
        
        # Redis for caching and real-time operations
        cache_subnet_group = elasticache.SubnetGroup(
            f"{project_name}-cache-subnet-group",
            subnet_ids=[
                self.subnets["private-a"].id,
                self.subnets["private-b"].id,
                self.subnets["private-c"].id
            ]
        )
        
        self.cache_clusters["redis"] = elasticache.ReplicationGroup(
            f"{project_name}-redis",
            description="Redis cluster for hybrid intelligence platform",
            replication_group_id=f"{project_name}-redis",
            
            # Configuration
            node_type="cache.r6g.xlarge",  # 4 vCPU, 26.32 GB RAM
            port=6379,
            parameter_group_name="default.redis7",
            
            # High availability
            num_cache_clusters=3,
            automatic_failover_enabled=True,
            multi_az_enabled=True,
            
            # Network and security
            subnet_group_name=cache_subnet_group.name,
            security_group_ids=[self._create_cache_security_group().id],
            
            # Backup
            snapshot_retention_limit=5,
            snapshot_window="02:00-03:00",
            
            tags={**default_tags, "Component": "cache"}
        )
        
        # S3 Buckets for data storage
        self.storage["data_lake"] = s3.Bucket(
            f"{project_name}-data-lake",
            bucket=f"{project_name}-data-lake-{pulumi.get_stack()}",
            versioning=s3.BucketVersioningArgs(enabled=True),
            server_side_encryption_configuration=s3.BucketServerSideEncryptionConfigurationArgs(
                rule=s3.BucketServerSideEncryptionConfigurationRuleArgs(
                    apply_server_side_encryption_by_default=s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                        sse_algorithm="AES256"
                    )
                )
            ),
            lifecycle_configuration=s3.BucketLifecycleConfigurationArgs(
                rules=[
                    s3.BucketLifecycleConfigurationRuleArgs(
                        id="transition_to_ia",
                        status="Enabled",
                        transitions=[
                            s3.BucketLifecycleConfigurationRuleTransitionArgs(
                                days=30,
                                storage_class="STANDARD_IA"
                            ),
                            s3.BucketLifecycleConfigurationRuleTransitionArgs(
                                days=90,
                                storage_class="GLACIER"
                            )
                        ]
                    )
                ]
            ),
            tags={**default_tags, "Component": "storage"}
        )
        
        # Vector database storage (for Weaviate)
        self.storage["vector_db"] = s3.Bucket(
            f"{project_name}-vector-db",
            bucket=f"{project_name}-vector-db-{pulumi.get_stack()}",
            versioning=s3.BucketVersioningArgs(enabled=True),
            server_side_encryption_configuration=s3.BucketServerSideEncryptionConfigurationArgs(
                rule=s3.BucketServerSideEncryptionConfigurationRuleArgs(
                    apply_server_side_encryption_by_default=s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                        sse_algorithm="AES256"
                    )
                )
            ),
            tags={**default_tags, "Component": "vector-storage"}
        )
    
    def _create_compute_infrastructure(self):
        """Create ECS clusters and compute resources"""
        
        # ECS Cluster for Sophia Business Intelligence
        sophia_cluster = ecs.Cluster(
            f"{project_name}-sophia-cluster",
            name=f"{project_name}-sophia-cluster",
            capacity_providers=["FARGATE", "FARGATE_SPOT"],
            default_capacity_provider_strategies=[
                ecs.ClusterDefaultCapacityProviderStrategyArgs(
                    capacity_provider="FARGATE",
                    weight=1,
                    base=2
                ),
                ecs.ClusterDefaultCapacityProviderStrategyArgs(
                    capacity_provider="FARGATE_SPOT",
                    weight=4
                )
            ],
            tags={**default_tags, "Component": "sophia-compute"}
        )
        
        # ECS Cluster for Artemis Technical Intelligence
        artemis_cluster = ecs.Cluster(
            f"{project_name}-artemis-cluster", 
            name=f"{project_name}-artemis-cluster",
            capacity_providers=["FARGATE", "FARGATE_SPOT"],
            default_capacity_provider_strategies=[
                ecs.ClusterDefaultCapacityProviderStrategyArgs(
                    capacity_provider="FARGATE",
                    weight=1,
                    base=2
                ),
                ecs.ClusterDefaultCapacityProviderStrategyArgs(
                    capacity_provider="FARGATE_SPOT",
                    weight=4
                )
            ],
            tags={**default_tags, "Component": "artemis-compute"}
        )
        
        # ECS Cluster for Unified Coordination
        unified_cluster = ecs.Cluster(
            f"{project_name}-unified-cluster",
            name=f"{project_name}-unified-cluster",
            capacity_providers=["FARGATE"],
            default_capacity_provider_strategies=[
                ecs.ClusterDefaultCapacityProviderStrategyArgs(
                    capacity_provider="FARGATE",
                    weight=1,
                    base=1
                )
            ],
            tags={**default_tags, "Component": "unified-compute"}
        )
        
        self.compute_resources = {
            "sophia_cluster": sophia_cluster,
            "artemis_cluster": artemis_cluster,
            "unified_cluster": unified_cluster
        }
        
        # Task Definitions
        self._create_task_definitions()
    
    def _create_task_definitions(self):
        """Create ECS task definitions for each service"""
        
        # Sophia Business Intelligence Task Definition
        sophia_task_role = self._create_task_role("sophia")
        sophia_execution_role = self._create_execution_role("sophia")
        
        sophia_task_def = ecs.TaskDefinition(
            f"{project_name}-sophia-task",
            family=f"{project_name}-sophia",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            cpu="2048",  # 2 vCPU
            memory="4096",  # 4 GB
            task_role_arn=sophia_task_role.arn,
            execution_role_arn=sophia_execution_role.arn,
            container_definitions=pulumi.Output.json_dumps([{
                "name": "sophia-business",
                "image": f"{project_name}:sophia-latest",
                "memory": 3584,  # Leave some memory for system
                "essential": True,
                "portMappings": [{
                    "containerPort": 8000,
                    "protocol": "tcp"
                }],
                "environment": [
                    {"name": "SERVICE_TYPE", "value": "business_intelligence"},
                    {"name": "ENVIRONMENT", "value": environment},
                    {"name": "AWS_REGION", "value": region}
                ],
                "secrets": [
                    {"name": "DB_PASSWORD", "valueFrom": config.require_secret("db_password")},
                    {"name": "REDIS_PASSWORD", "valueFrom": config.get("redis_password")},
                    {"name": "PORTKEY_API_KEY", "valueFrom": config.require_secret("portkey_api_key")}
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": f"/ecs/{project_name}-sophia",
                        "awslogs-region": region,
                        "awslogs-stream-prefix": "ecs"
                    }
                },
                "healthCheck": {
                    "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3,
                    "startPeriod": 60
                }
            }]),
            tags={**default_tags, "Component": "sophia-task"}
        )
        
        # Artemis Technical Intelligence Task Definition  
        artemis_task_role = self._create_task_role("artemis")
        artemis_execution_role = self._create_execution_role("artemis")
        
        artemis_task_def = ecs.TaskDefinition(
            f"{project_name}-artemis-task",
            family=f"{project_name}-artemis",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            cpu="4096",  # 4 vCPU
            memory="8192",  # 8 GB
            task_role_arn=artemis_task_role.arn,
            execution_role_arn=artemis_execution_role.arn,
            container_definitions=pulumi.Output.json_dumps([{
                "name": "artemis-technical",
                "image": f"{project_name}:artemis-latest",
                "memory": 7168,  # Leave some memory for system
                "essential": True,
                "portMappings": [{
                    "containerPort": 8001,
                    "protocol": "tcp"
                }],
                "environment": [
                    {"name": "SERVICE_TYPE", "value": "technical_intelligence"},
                    {"name": "ENVIRONMENT", "value": environment},
                    {"name": "AWS_REGION", "value": region}
                ],
                "secrets": [
                    {"name": "DB_PASSWORD", "valueFrom": config.require_secret("db_password")},
                    {"name": "REDIS_PASSWORD", "valueFrom": config.get("redis_password")},
                    {"name": "PORTKEY_API_KEY", "valueFrom": config.require_secret("portkey_api_key")}
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": f"/ecs/{project_name}-artemis",
                        "awslogs-region": region,
                        "awslogs-stream-prefix": "ecs"
                    }
                },
                "healthCheck": {
                    "command": ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"],
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3,
                    "startPeriod": 60
                }
            }]),
            tags={**default_tags, "Component": "artemis-task"}
        )
        
        # Unified Coordinator Task Definition
        unified_task_role = self._create_task_role("unified")
        unified_execution_role = self._create_execution_role("unified")
        
        unified_task_def = ecs.TaskDefinition(
            f"{project_name}-unified-task",
            family=f"{project_name}-unified",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            cpu="1024",  # 1 vCPU
            memory="2048",  # 2 GB
            task_role_arn=unified_task_role.arn,
            execution_role_arn=unified_execution_role.arn,
            container_definitions=pulumi.Output.json_dumps([{
                "name": "unified-coordinator",
                "image": f"{project_name}:unified-latest",
                "memory": 1536,  # Leave some memory for system
                "essential": True,
                "portMappings": [{
                    "containerPort": 8002,
                    "protocol": "tcp"
                }],
                "environment": [
                    {"name": "SERVICE_TYPE", "value": "hybrid_coordinator"},
                    {"name": "ENVIRONMENT", "value": environment},
                    {"name": "AWS_REGION", "value": region}
                ],
                "secrets": [
                    {"name": "DB_PASSWORD", "valueFrom": config.require_secret("db_password")},
                    {"name": "REDIS_PASSWORD", "valueFrom": config.get("redis_password")},
                    {"name": "PORTKEY_API_KEY", "valueFrom": config.require_secret("portkey_api_key")}
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": f"/ecs/{project_name}-unified",
                        "awslogs-region": region,
                        "awslogs-stream-prefix": "ecs"
                    }
                }
            }]),
            tags={**default_tags, "Component": "unified-task"}
        )
        
        self.compute_resources["task_definitions"] = {
            "sophia": sophia_task_def,
            "artemis": artemis_task_def,
            "unified": unified_task_def
        }
    
    def _create_auto_scaling(self):
        """Create auto-scaling groups and load balancers"""
        
        # Application Load Balancer
        alb_security_group = self._create_alb_security_group()
        
        alb = aws.lb.LoadBalancer(
            f"{project_name}-alb",
            name=f"{project_name}-alb",
            load_balancer_type="application",
            scheme="internet-facing",
            security_groups=[alb_security_group.id],
            subnets=[
                self.subnets["public-a"].id,
                self.subnets["public-b"].id,
                self.subnets["public-c"].id
            ],
            enable_deletion_protection=environment == "production",
            tags={**default_tags, "Component": "load-balancer"}
        )
        
        # Target Groups
        sophia_target_group = aws.lb.TargetGroup(
            f"{project_name}-sophia-tg",
            name=f"{project_name}-sophia-tg",
            port=8000,
            protocol="HTTP",
            vpc_id=self.vpc.id,
            target_type="ip",
            health_check=aws.lb.TargetGroupHealthCheckArgs(
                enabled=True,
                healthy_threshold=2,
                interval=30,
                matcher="200",
                path="/health",
                port="traffic-port",
                protocol="HTTP",
                timeout=5,
                unhealthy_threshold=3
            ),
            tags={**default_tags, "Component": "sophia-target-group"}
        )
        
        artemis_target_group = aws.lb.TargetGroup(
            f"{project_name}-artemis-tg",
            name=f"{project_name}-artemis-tg",
            port=8001,
            protocol="HTTP",
            vpc_id=self.vpc.id,
            target_type="ip",
            health_check=aws.lb.TargetGroupHealthCheckArgs(
                enabled=True,
                healthy_threshold=2,
                interval=30,
                matcher="200",
                path="/health",
                port="traffic-port",
                protocol="HTTP",
                timeout=5,
                unhealthy_threshold=3
            ),
            tags={**default_tags, "Component": "artemis-target-group"}
        )
        
        unified_target_group = aws.lb.TargetGroup(
            f"{project_name}-unified-tg",
            name=f"{project_name}-unified-tg",
            port=8002,
            protocol="HTTP",
            vpc_id=self.vpc.id,
            target_type="ip",
            health_check=aws.lb.TargetGroupHealthCheckArgs(
                enabled=True,
                healthy_threshold=2,
                interval=30,
                matcher="200",
                path="/health",
                port="traffic-port",
                protocol="HTTP",
                timeout=5,
                unhealthy_threshold=3
            ),
            tags={**default_tags, "Component": "unified-target-group"}
        )
        
        # ALB Listeners
        alb_listener = aws.lb.Listener(
            f"{project_name}-alb-listener",
            load_balancer_arn=alb.arn,
            port="80",
            protocol="HTTP",
            default_actions=[
                aws.lb.ListenerDefaultActionArgs(
                    type="fixed-response",
                    fixed_response=aws.lb.ListenerDefaultActionFixedResponseArgs(
                        content_type="text/plain",
                        message_body="Sophia-Artemis Unified Intelligence Platform",
                        status_code="200"
                    )
                )
            ]
        )
        
        # Listener Rules for path-based routing
        aws.lb.ListenerRule(
            f"{project_name}-sophia-rule",
            listener_arn=alb_listener.arn,
            priority=100,
            actions=[
                aws.lb.ListenerRuleActionArgs(
                    type="forward",
                    target_group_arn=sophia_target_group.arn
                )
            ],
            conditions=[
                aws.lb.ListenerRuleConditionArgs(
                    path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                        values=["/api/sophia/*"]
                    )
                )
            ]
        )
        
        aws.lb.ListenerRule(
            f"{project_name}-artemis-rule",
            listener_arn=alb_listener.arn,
            priority=200,
            actions=[
                aws.lb.ListenerRuleActionArgs(
                    type="forward",
                    target_group_arn=artemis_target_group.arn
                )
            ],
            conditions=[
                aws.lb.ListenerRuleConditionArgs(
                    path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                        values=["/api/artemis/*"]
                    )
                )
            ]
        )
        
        aws.lb.ListenerRule(
            f"{project_name}-unified-rule",
            listener_arn=alb_listener.arn,
            priority=300,
            actions=[
                aws.lb.ListenerRuleActionArgs(
                    type="forward",
                    target_group_arn=unified_target_group.arn
                )
            ],
            conditions=[
                aws.lb.ListenerRuleConditionArgs(
                    path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                        values=["/api/unified/*", "/api/hybrid/*"]
                    )
                )
            ]
        )
        
        self.load_balancers = {
            "alb": alb,
            "target_groups": {
                "sophia": sophia_target_group,
                "artemis": artemis_target_group,
                "unified": unified_target_group
            }
        }
        
        # ECS Services with Auto Scaling
        self._create_ecs_services_with_autoscaling()
    
    def _create_ecs_services_with_autoscaling(self):
        """Create ECS services with auto scaling"""
        
        app_security_group = self._create_app_security_group()
        
        # Sophia Business Intelligence Service
        sophia_service = ecs.Service(
            f"{project_name}-sophia-service",
            name=f"{project_name}-sophia-service",
            cluster=self.compute_resources["sophia_cluster"].id,
            task_definition=self.compute_resources["task_definitions"]["sophia"].arn,
            desired_count=3,
            launch_type="FARGATE",
            platform_version="1.4.0",
            
            network_configuration=ecs.ServiceNetworkConfigurationArgs(
                subnets=[
                    self.subnets["private-a"].id,
                    self.subnets["private-b"].id,
                    self.subnets["private-c"].id
                ],
                security_groups=[app_security_group.id],
                assign_public_ip=False
            ),
            
            load_balancers=[
                ecs.ServiceLoadBalancerArgs(
                    target_group_arn=self.load_balancers["target_groups"]["sophia"].arn,
                    container_name="sophia-business",
                    container_port=8000
                )
            ],
            
            deployment_configuration=ecs.ServiceDeploymentConfigurationArgs(
                maximum_percent=200,
                minimum_healthy_percent=50
            ),
            
            tags={**default_tags, "Component": "sophia-service"}
        )
        
        # Artemis Technical Intelligence Service  
        artemis_service = ecs.Service(
            f"{project_name}-artemis-service",
            name=f"{project_name}-artemis-service",
            cluster=self.compute_resources["artemis_cluster"].id,
            task_definition=self.compute_resources["task_definitions"]["artemis"].arn,
            desired_count=3,
            launch_type="FARGATE",
            platform_version="1.4.0",
            
            network_configuration=ecs.ServiceNetworkConfigurationArgs(
                subnets=[
                    self.subnets["private-a"].id,
                    self.subnets["private-b"].id,
                    self.subnets["private-c"].id
                ],
                security_groups=[app_security_group.id],
                assign_public_ip=False
            ),
            
            load_balancers=[
                ecs.ServiceLoadBalancerArgs(
                    target_group_arn=self.load_balancers["target_groups"]["artemis"].arn,
                    container_name="artemis-technical",
                    container_port=8001
                )
            ],
            
            deployment_configuration=ecs.ServiceDeploymentConfigurationArgs(
                maximum_percent=200,
                minimum_healthy_percent=50
            ),
            
            tags={**default_tags, "Component": "artemis-service"}
        )
        
        # Unified Coordinator Service
        unified_service = ecs.Service(
            f"{project_name}-unified-service",
            name=f"{project_name}-unified-service",
            cluster=self.compute_resources["unified_cluster"].id,
            task_definition=self.compute_resources["task_definitions"]["unified"].arn,
            desired_count=2,
            launch_type="FARGATE",
            platform_version="1.4.0",
            
            network_configuration=ecs.ServiceNetworkConfigurationArgs(
                subnets=[
                    self.subnets["private-a"].id,
                    self.subnets["private-b"].id,
                    self.subnets["private-c"].id
                ],
                security_groups=[app_security_group.id],
                assign_public_ip=False
            ),
            
            load_balancers=[
                ecs.ServiceLoadBalancerArgs(
                    target_group_arn=self.load_balancers["target_groups"]["unified"].arn,
                    container_name="unified-coordinator",
                    container_port=8002
                )
            ],
            
            deployment_configuration=ecs.ServiceDeploymentConfigurationArgs(
                maximum_percent=200,
                minimum_healthy_percent=50
            ),
            
            tags={**default_tags, "Component": "unified-service"}
        )
        
        self.auto_scaling["services"] = {
            "sophia": sophia_service,
            "artemis": artemis_service,
            "unified": unified_service
        }
        
        # Auto Scaling Targets and Policies
        self._create_autoscaling_policies()
    
    def _create_autoscaling_policies(self):
        """Create auto scaling policies for ECS services"""
        
        services = ["sophia", "artemis", "unified"]
        
        for service_name in services:
            service = self.auto_scaling["services"][service_name]
            
            # Auto Scaling Target
            scaling_target = aws.appautoscaling.Target(
                f"{project_name}-{service_name}-scaling-target",
                max_capacity=20 if service_name != "unified" else 10,
                min_capacity=2 if service_name != "unified" else 1,
                resource_id=pulumi.Output.concat("service/", 
                                               self.compute_resources[f"{service_name}_cluster"].name,
                                               "/", service.name),
                scalable_dimension="ecs:service:DesiredCount",
                service_namespace="ecs"
            )
            
            # CPU-based scaling policy
            aws.appautoscaling.Policy(
                f"{project_name}-{service_name}-cpu-scaling",
                name=f"{project_name}-{service_name}-cpu-scaling",
                policy_type="TargetTrackingScaling",
                resource_id=scaling_target.resource_id,
                scalable_dimension=scaling_target.scalable_dimension,
                service_namespace=scaling_target.service_namespace,
                
                target_tracking_scaling_policy_configuration=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
                    target_value=70.0,
                    predefined_metric_specification=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
                        predefined_metric_type="ECSServiceAverageCPUUtilization"
                    ),
                    scale_out_cooldown=300,
                    scale_in_cooldown=300
                )
            )
            
            # Memory-based scaling policy
            aws.appautoscaling.Policy(
                f"{project_name}-{service_name}-memory-scaling",
                name=f"{project_name}-{service_name}-memory-scaling",
                policy_type="TargetTrackingScaling",
                resource_id=scaling_target.resource_id,
                scalable_dimension=scaling_target.scalable_dimension,
                service_namespace=scaling_target.service_namespace,
                
                target_tracking_scaling_policy_configuration=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
                    target_value=80.0,
                    predefined_metric_specification=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
                        predefined_metric_type="ECSServiceAverageMemoryUtilization"
                    ),
                    scale_out_cooldown=300,
                    scale_in_cooldown=300
                )
            )
    
    def _create_gpu_infrastructure(self):
        """Create GPU infrastructure for intensive learning operations"""
        
        # Note: This is a placeholder for Lambda Labs integration
        # In practice, this would integrate with Lambda Labs API for GPU provisioning
        
        # EC2 GPU instances for fallback learning operations
        gpu_launch_template = ec2.LaunchTemplate(
            f"{project_name}-gpu-template",
            name=f"{project_name}-gpu-template",
            image_id="ami-0c02fb55956c7d316",  # Deep Learning AMI
            instance_type="p3.2xlarge",  # 1 V100 GPU, 8 vCPUs, 61 GB RAM
            
            vpc_security_group_ids=[self._create_gpu_security_group().id],
            
            iam_instance_profile=aws.ec2.LaunchTemplateIamInstanceProfileArgs(
                name=self._create_gpu_instance_profile().name
            ),
            
            user_data=pulumi.Output.from_input("""#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install nvidia-docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | \
sudo tee /etc/yum.repos.d/nvidia-docker.repo

yum install -y nvidia-docker2
systemctl restart docker

# Pull learning containers
docker pull tensorflow/tensorflow:latest-gpu
docker pull pytorch/pytorch:latest

# Setup CloudWatch agent
yum install -y amazon-cloudwatch-agent
""").apply(lambda data: data.encode("utf-8").hex()),
            
            tags={**default_tags, "Component": "gpu-template"}
        )
        
        # Auto Scaling Group for GPU instances (for burst learning)
        gpu_asg = aws.autoscaling.Group(
            f"{project_name}-gpu-asg",
            name=f"{project_name}-gpu-asg",
            vpc_zone_identifiers=[
                self.subnets["private-a"].id,
                self.subnets["private-b"].id
            ],
            
            launch_template=aws.autoscaling.GroupLaunchTemplateArgs(
                id=gpu_launch_template.id,
                version="$Latest"
            ),
            
            min_size=0,
            max_size=5,
            desired_capacity=0,  # Start with 0, scale up when needed
            
            health_check_type="EC2",
            health_check_grace_period=300,
            
            tags=[
                aws.autoscaling.GroupTagArgs(
                    key="Name",
                    value=f"{project_name}-gpu-instance",
                    propagate_at_launch=True
                ),
                aws.autoscaling.GroupTagArgs(
                    key="Component",
                    value="gpu-learning",
                    propagate_at_launch=True
                )
            ]
        )
        
        self.compute_resources["gpu_infrastructure"] = {
            "launch_template": gpu_launch_template,
            "auto_scaling_group": gpu_asg
        }
    
    def _create_monitoring_stack(self):
        """Create comprehensive monitoring and observability"""
        
        # CloudWatch Log Groups
        log_groups = {}
        for service in ["sophia", "artemis", "unified"]:
            log_groups[service] = aws.cloudwatch.LogGroup(
                f"{project_name}-{service}-logs",
                name=f"/ecs/{project_name}-{service}",
                retention_in_days=14 if environment == "development" else 30,
                tags={**default_tags, "Component": f"{service}-logs"}
            )
        
        # CloudWatch Dashboard
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/ECS", "CPUUtilization", "ServiceName", f"{project_name}-sophia-service"],
                            [".", "MemoryUtilization", ".", "."],
                            ["AWS/ECS", "CPUUtilization", "ServiceName", f"{project_name}-artemis-service"],
                            [".", "MemoryUtilization", ".", "."],
                            ["AWS/ECS", "CPUUtilization", "ServiceName", f"{project_name}-unified-service"],
                            [".", "MemoryUtilization", ".", "."]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": region,
                        "title": "ECS Service Resource Utilization"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", 
                             pulumi.Output.concat(self.load_balancers["alb"].arn_suffix)],
                            [".", "TargetResponseTime", ".", "."],
                            [".", "HTTPCode_Target_2XX_Count", ".", "."],
                            [".", "HTTPCode_Target_5XX_Count", ".", "."]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": region,
                        "title": "Application Load Balancer Metrics"
                    }
                }
            ]
        }
        
        aws.cloudwatch.Dashboard(
            f"{project_name}-dashboard",
            dashboard_name=f"{project_name}-hybrid-intelligence",
            dashboard_body=pulumi.Output.json_dumps(dashboard_body)
        )
        
        # CloudWatch Alarms
        self._create_cloudwatch_alarms()
    
    def _create_cloudwatch_alarms(self):
        """Create CloudWatch alarms for monitoring"""
        
        services = ["sophia", "artemis", "unified"]
        
        for service_name in services:
            # High CPU alarm
            aws.cloudwatch.MetricAlarm(
                f"{project_name}-{service_name}-high-cpu",
                alarm_name=f"{project_name}-{service_name}-high-cpu",
                comparison_operator="GreaterThanThreshold",
                evaluation_periods=2,
                metric_name="CPUUtilization",
                namespace="AWS/ECS",
                period=300,
                statistic="Average",
                threshold=80.0,
                alarm_description=f"High CPU utilization for {service_name} service",
                dimensions={
                    "ServiceName": f"{project_name}-{service_name}-service",
                    "ClusterName": f"{project_name}-{service_name}-cluster"
                },
                alarm_actions=[],  # Add SNS topic ARN for notifications
                tags={**default_tags, "Component": f"{service_name}-alarm"}
            )
            
            # High memory alarm
            aws.cloudwatch.MetricAlarm(
                f"{project_name}-{service_name}-high-memory",
                alarm_name=f"{project_name}-{service_name}-high-memory",
                comparison_operator="GreaterThanThreshold",
                evaluation_periods=2,
                metric_name="MemoryUtilization",
                namespace="AWS/ECS",
                period=300,
                statistic="Average",
                threshold=85.0,
                alarm_description=f"High memory utilization for {service_name} service",
                dimensions={
                    "ServiceName": f"{project_name}-{service_name}-service",
                    "ClusterName": f"{project_name}-{service_name}-cluster"
                },
                alarm_actions=[],  # Add SNS topic ARN for notifications
                tags={**default_tags, "Component": f"{service_name}-alarm"}
            )
    
    def _create_security_infrastructure(self):
        """Create security groups and IAM roles"""
        
        # This method calls other security-related methods
        pass  # Security groups and roles are created in helper methods
    
    # Security Group Helper Methods
    def _create_database_security_group(self):
        """Create security group for database"""
        return ec2.SecurityGroup(
            f"{project_name}-db-sg",
            name=f"{project_name}-db-sg",
            description="Security group for database access",
            vpc_id=self.vpc.id,
            
            ingress=[
                ec2.SecurityGroupIngressArgs(
                    description="PostgreSQL from app",
                    from_port=5432,
                    to_port=5432,
                    protocol="tcp",
                    cidr_blocks=["10.0.0.0/16"]
                )
            ],
            
            egress=[
                ec2.SecurityGroupEgressArgs(
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                    cidr_blocks=["0.0.0.0/0"]
                )
            ],
            
            tags={**default_tags, "Component": "database-security"}
        )
    
    def _create_cache_security_group(self):
        """Create security group for cache"""
        return ec2.SecurityGroup(
            f"{project_name}-cache-sg",
            name=f"{project_name}-cache-sg",
            description="Security group for cache access",
            vpc_id=self.vpc.id,
            
            ingress=[
                ec2.SecurityGroupIngressArgs(
                    description="Redis from app",
                    from_port=6379,
                    to_port=6379,
                    protocol="tcp",
                    cidr_blocks=["10.0.0.0/16"]
                )
            ],
            
            egress=[
                ec2.SecurityGroupEgressArgs(
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                    cidr_blocks=["0.0.0.0/0"]
                )
            ],
            
            tags={**default_tags, "Component": "cache-security"}
        )
    
    def _create_alb_security_group(self):
        """Create security group for ALB"""
        return ec2.SecurityGroup(
            f"{project_name}-alb-sg",
            name=f"{project_name}-alb-sg",
            description="Security group for Application Load Balancer",
            vpc_id=self.vpc.id,
            
            ingress=[
                ec2.SecurityGroupIngressArgs(
                    description="HTTP from internet",
                    from_port=80,
                    to_port=80,
                    protocol="tcp",
                    cidr_blocks=["0.0.0.0/0"]
                ),
                ec2.SecurityGroupIngressArgs(
                    description="HTTPS from internet",
                    from_port=443,
                    to_port=443,
                    protocol="tcp",
                    cidr_blocks=["0.0.0.0/0"]
                )
            ],
            
            egress=[
                ec2.SecurityGroupEgressArgs(
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                    cidr_blocks=["0.0.0.0/0"]
                )
            ],
            
            tags={**default_tags, "Component": "alb-security"}
        )
    
    def _create_app_security_group(self):
        """Create security group for application servers"""
        alb_sg = self._create_alb_security_group()
        
        return ec2.SecurityGroup(
            f"{project_name}-app-sg",
            name=f"{project_name}-app-sg",
            description="Security group for application servers",
            vpc_id=self.vpc.id,
            
            ingress=[
                ec2.SecurityGroupIngressArgs(
                    description="HTTP from ALB",
                    from_port=8000,
                    to_port=8002,
                    protocol="tcp",
                    security_groups=[alb_sg.id]
                )
            ],
            
            egress=[
                ec2.SecurityGroupEgressArgs(
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                    cidr_blocks=["0.0.0.0/0"]
                )
            ],
            
            tags={**default_tags, "Component": "app-security"}
        )
    
    def _create_gpu_security_group(self):
        """Create security group for GPU instances"""
        return ec2.SecurityGroup(
            f"{project_name}-gpu-sg",
            name=f"{project_name}-gpu-sg",
            description="Security group for GPU instances",
            vpc_id=self.vpc.id,
            
            ingress=[
                ec2.SecurityGroupIngressArgs(
                    description="SSH from app servers",
                    from_port=22,
                    to_port=22,
                    protocol="tcp",
                    cidr_blocks=["10.0.0.0/16"]
                )
            ],
            
            egress=[
                ec2.SecurityGroupEgressArgs(
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                    cidr_blocks=["0.0.0.0/0"]
                )
            ],
            
            tags={**default_tags, "Component": "gpu-security"}
        )
    
    # IAM Role Helper Methods
    def _create_task_role(self, service_name: str):
        """Create IAM task role for ECS tasks"""
        
        task_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        task_role = iam.Role(
            f"{project_name}-{service_name}-task-role",
            name=f"{project_name}-{service_name}-task-role",
            assume_role_policy=json.dumps(task_role_policy),
            tags={**default_tags, "Component": f"{service_name}-task-role"}
        )
        
        # Attach policies for S3, CloudWatch, etc.
        iam.RolePolicyAttachment(
            f"{project_name}-{service_name}-task-s3-policy",
            role=task_role.name,
            policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
        )
        
        iam.RolePolicyAttachment(
            f"{project_name}-{service_name}-task-logs-policy", 
            role=task_role.name,
            policy_arn="arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
        )
        
        return task_role
    
    def _create_execution_role(self, service_name: str):
        """Create IAM execution role for ECS tasks"""
        
        execution_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        execution_role = iam.Role(
            f"{project_name}-{service_name}-execution-role",
            name=f"{project_name}-{service_name}-execution-role",
            assume_role_policy=json.dumps(execution_role_policy),
            tags={**default_tags, "Component": f"{service_name}-execution-role"}
        )
        
        iam.RolePolicyAttachment(
            f"{project_name}-{service_name}-execution-policy",
            role=execution_role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
        )
        
        return execution_role
    
    def _create_gpu_instance_profile(self):
        """Create instance profile for GPU instances"""
        
        gpu_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        gpu_role = iam.Role(
            f"{project_name}-gpu-role",
            name=f"{project_name}-gpu-role",
            assume_role_policy=json.dumps(gpu_role_policy),
            tags={**default_tags, "Component": "gpu-role"}
        )
        
        # Attach necessary policies
        iam.RolePolicyAttachment(
            f"{project_name}-gpu-s3-policy",
            role=gpu_role.name,
            policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
        )
        
        iam.RolePolicyAttachment(
            f"{project_name}-gpu-cloudwatch-policy",
            role=gpu_role.name,
            policy_arn="arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
        )
        
        gpu_instance_profile = iam.InstanceProfile(
            f"{project_name}-gpu-instance-profile",
            name=f"{project_name}-gpu-instance-profile",
            role=gpu_role.name,
            tags={**default_tags, "Component": "gpu-instance-profile"}
        )
        
        return gpu_instance_profile
    
    def _export_outputs(self):
        """Export key infrastructure outputs"""
        
        export("vpc_id", self.vpc.id)
        export("alb_dns_name", self.load_balancers["alb"].dns_name)
        export("alb_zone_id", self.load_balancers["alb"].zone_id)
        
        export("database_endpoint", self.databases["postgresql"].endpoint)
        export("redis_endpoint", self.cache_clusters["redis"].configuration_endpoint)
        
        export("sophia_cluster_arn", self.compute_resources["sophia_cluster"].arn)
        export("artemis_cluster_arn", self.compute_resources["artemis_cluster"].arn)
        export("unified_cluster_arn", self.compute_resources["unified_cluster"].arn)
        
        export("s3_data_lake_bucket", self.storage["data_lake"].bucket)
        export("s3_vector_db_bucket", self.storage["vector_db"].bucket)
        
        # Service endpoints
        export("sophia_endpoint", pulumi.Output.concat("http://", 
                                                     self.load_balancers["alb"].dns_name, 
                                                     "/api/sophia/"))
        export("artemis_endpoint", pulumi.Output.concat("http://", 
                                                      self.load_balancers["alb"].dns_name, 
                                                      "/api/artemis/"))
        export("unified_endpoint", pulumi.Output.concat("http://", 
                                                      self.load_balancers["alb"].dns_name, 
                                                      "/api/unified/"))


# Create and deploy the infrastructure
def main():
    """Main function to create infrastructure"""
    platform = HybridIntelligencePlatform()
    infrastructure = platform.create_infrastructure()
    
    # Output summary
    pulumi.log.info("🚀 Hybrid Intelligence Platform infrastructure created successfully!")
    pulumi.log.info("📊 Sophia Business Intelligence cluster ready")
    pulumi.log.info("🔧 Artemis Technical Intelligence cluster ready") 
    pulumi.log.info("🎯 Unified Hybrid Coordinator ready")
    pulumi.log.info("💾 Data layer with PostgreSQL, Redis, and S3 provisioned")
    pulumi.log.info("📈 Auto-scaling and monitoring configured")
    pulumi.log.info("🔐 Security groups and IAM roles established")
    
    return infrastructure


if __name__ == "__main__":
    main()