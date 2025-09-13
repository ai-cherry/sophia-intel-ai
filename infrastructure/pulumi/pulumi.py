import pulumi
class SophiaCluster(pulumi.ComponentResource):
    def __init__(self, name, opts=None):
        super().__init__("sophia:cluster", name, None, opts)
        self.cluster = pulumi_lambda_labs.eks.Cluster(
            name,
            role_arn=pulumi.Config().require("eks_role_arn"),
            vpc_config={
                "public_access_cidrs": ["${BIND_IP}/0"],
                "subnet_ids": pulumi.Config().require_object("subnet_ids"),
            },
        )
# Create cluster
sophia_cluster = SophiaCluster("sophia-production")
