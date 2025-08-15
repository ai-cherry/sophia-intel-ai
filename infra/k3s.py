import pulumi
from pulumi_command import local


class K3sCluster(pulumi.ComponentResource):
    def __init__(self, name, region, control_type, worker_type, ssh_key_id, firewall_id, opts=None):
        super().__init__('sophia:K3sCluster', name, None, opts)
        # ...provision control and worker nodes using LambdaInstance...
        # ...render cloud-init, install K3s, join worker...
        # ...fetch kubeconfig via SSH using pulumi-command...
        # ...set outputs: kubeconfig, control_ip, worker_ip...
        self.kubeconfig = pulumi.Output.secret('kubeconfig-placeholder')
        self.control_ip = pulumi.Output.secret('control-ip-placeholder')
        self.worker_ip = pulumi.Output.secret('worker-ip-placeholder')
