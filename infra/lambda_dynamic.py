import pulumi
from pulumi.dynamic import Resource, ResourceProvider, CreateResult, UpdateResult, DiffResult, CheckResult, ReadResult
import httpx
import os

API_KEY = os.environ.get("LAMBDA_CLOUD_API_KEY")
API_URL = "https://cloud.lambda.ai/api/v1"


class LambdaSSHKeyProvider(ResourceProvider):
    def create(self, props):
        # ...create SSH key via Lambda Cloud API...
        # Return CreateResult(id, outs)
        pass

    def delete(self, id, props):
        # ...delete SSH key...
        pass
    # ...other methods...


class LambdaInstanceProvider(ResourceProvider):
    def create(self, props):
        # ...create instance via Lambda Cloud API...
        pass

    def delete(self, id, props):
        # ...delete instance...
        pass
    # ...other methods...


class LambdaFirewallProvider(ResourceProvider):
    def create(self, props):
        # ...create firewall via Lambda Cloud API...
        pass

    def delete(self, id, props):
        # ...delete firewall...
        pass
    # ...other methods...


class LambdaSSHKey(Resource):
    def __init__(self, name, public_key, opts=None):
        super().__init__(LambdaSSHKeyProvider(),
                         name, {"public_key": public_key}, opts)


class LambdaInstance(Resource):
    def __init__(self, name, type, region, ssh_key_id, firewall_id, user_data, opts=None):
        super().__init__(LambdaInstanceProvider(), name, {
            "type": type,
            "region": region,
            "ssh_key_id": ssh_key_id,
            "firewall_id": firewall_id,
            "user_data": user_data
        }, opts)


class LambdaFirewall(Resource):
    def __init__(self, name, allowed_ssh_cidrs, allow_http, allow_https, ssh_key_id, opts=None):
        super().__init__(LambdaFirewallProvider(), name, {
            "allowed_ssh_cidrs": allowed_ssh_cidrs,
            "allow_http": allow_http,
            "allow_https": allow_https,
            "ssh_key_id": ssh_key_id
        }, opts)
