"""
Security Manager for Sophia-Artemis Service Mesh
Manages mTLS certificates, RBAC updates, and security policies
"""

import asyncio
import base64
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for services"""

    STRICT = "strict"
    PERMISSIVE = "permissive"
    DISABLED = "disabled"


class AuthorizationMode(Enum):
    """Authorization modes"""

    ALLOW = "ALLOW"
    DENY = "DENY"
    CUSTOM = "CUSTOM"


@dataclass
class Certificate:
    """TLS certificate information"""

    common_name: str
    namespace: str
    cert_pem: str
    key_pem: str
    ca_cert_pem: Optional[str] = None
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: datetime = field(
        default_factory=lambda: datetime.now() + timedelta(days=365)
    )
    serial_number: str = field(default_factory=lambda: secrets.token_hex(16))


@dataclass
class SecurityPolicy:
    """Security policy configuration"""

    name: str
    namespace: str
    mtls_mode: SecurityLevel
    authorization_mode: AuthorizationMode
    allowed_principals: list[str] = field(default_factory=list)
    allowed_namespaces: list[str] = field(default_factory=list)
    allowed_services: list[str] = field(default_factory=list)
    allowed_methods: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    custom_rules: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class RBACPolicy:
    """RBAC policy configuration"""

    name: str
    namespace: str
    role: str
    subjects: list[str] = field(default_factory=list)
    permissions: dict[str, list[str]] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class SecurityManager:
    """
    Manages security aspects of the service mesh
    """

    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        ca_cert_path: Optional[str] = None,
        ca_key_path: Optional[str] = None,
    ):
        """
        Initialize the security manager

        Args:
            kubeconfig_path: Path to kubeconfig file (None for in-cluster)
            ca_cert_path: Path to CA certificate
            ca_key_path: Path to CA private key
        """
        self.ca_cert_path = ca_cert_path
        self.ca_key_path = ca_key_path
        self.certificates: dict[str, Certificate] = {}
        self.policies: dict[str, SecurityPolicy] = {}
        self.rbac_policies: dict[str, RBACPolicy] = {}
        self.running = False

        # Initialize Kubernetes client
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                config.load_incluster_config()

            self.v1 = client.CoreV1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            self.custom_api = client.CustomObjectsApi()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

        # Load CA certificate if provided
        self.ca_cert = None
        self.ca_key = None
        if ca_cert_path and ca_key_path:
            self._load_ca_certificate()

    def _load_ca_certificate(self):
        """Load CA certificate and key"""
        try:
            with open(self.ca_cert_path, "rb") as f:
                self.ca_cert = x509.load_pem_x509_certificate(
                    f.read(), default_backend()
                )

            with open(self.ca_key_path, "rb") as f:
                self.ca_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )

            logger.info("CA certificate loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CA certificate: {e}")
            raise

    async def start(self):
        """Start the security manager"""
        logger.info("Starting security manager")
        self.running = True

        # Start certificate rotation monitor
        asyncio.create_task(self.monitor_certificates())

        # Start policy enforcement monitor
        asyncio.create_task(self.monitor_policies())

        logger.info("Security manager started")

    async def stop(self):
        """Stop the security manager"""
        logger.info("Stopping security manager")
        self.running = False
        logger.info("Security manager stopped")

    async def create_certificate(
        self,
        common_name: str,
        namespace: str,
        san_dns_names: Optional[list[str]] = None,
        san_ip_addresses: Optional[list[str]] = None,
        validity_days: int = 365,
    ) -> Certificate:
        """
        Create a new TLS certificate

        Args:
            common_name: Certificate common name
            namespace: Namespace for the certificate
            san_dns_names: Subject Alternative Names (DNS)
            san_ip_addresses: Subject Alternative Names (IP)
            validity_days: Certificate validity in days

        Returns:
            Certificate object
        """
        logger.info(f"Creating certificate for {common_name} in {namespace}")

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        # Create certificate subject
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Sophia-Artemis"),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, namespace),
            ]
        )

        # Create certificate builder
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)

        # Set issuer (self-signed or CA-signed)
        if self.ca_cert and self.ca_key:
            builder = builder.issuer_name(self.ca_cert.subject)
            signing_key = self.ca_key
        else:
            builder = builder.issuer_name(subject)
            signing_key = private_key

        # Set validity period
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(days=validity_days)
        builder = builder.not_valid_before(valid_from)
        builder = builder.not_valid_after(valid_until)

        # Set serial number
        builder = builder.serial_number(x509.random_serial_number())

        # Set public key
        builder = builder.public_key(private_key.public_key())

        # Add Subject Alternative Names
        san_list = []
        if san_dns_names:
            san_list.extend([x509.DNSName(name) for name in san_dns_names])
        if san_ip_addresses:
            san_list.extend(
                [x509.IPAddress(ipaddress.ip_address(ip)) for ip in san_ip_addresses]
            )

        if san_list:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(san_list), critical=False
            )

        # Add basic constraints
        builder = builder.add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True
        )

        # Add key usage
        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )

        # Sign certificate
        certificate = builder.sign(signing_key, hashes.SHA256(), default_backend())

        # Convert to PEM
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        # Get CA cert PEM if available
        ca_cert_pem = None
        if self.ca_cert:
            ca_cert_pem = self.ca_cert.public_bytes(serialization.Encoding.PEM).decode()

        # Create certificate object
        cert = Certificate(
            common_name=common_name,
            namespace=namespace,
            cert_pem=cert_pem,
            key_pem=key_pem,
            ca_cert_pem=ca_cert_pem,
            valid_from=valid_from,
            valid_until=valid_until,
            serial_number=str(certificate.serial_number),
        )

        # Store certificate
        cert_key = f"{namespace}/{common_name}"
        self.certificates[cert_key] = cert

        # Create Kubernetes secret
        await self._create_tls_secret(cert)

        logger.info(f"Certificate created: {cert_key}")
        return cert

    async def rotate_certificate(self, common_name: str, namespace: str):
        """
        Rotate an existing certificate

        Args:
            common_name: Certificate common name
            namespace: Certificate namespace
        """
        cert_key = f"{namespace}/{common_name}"
        if cert_key not in self.certificates:
            logger.warning(f"Certificate not found for rotation: {cert_key}")
            return

        logger.info(f"Rotating certificate: {cert_key}")

        # Create new certificate with same parameters
        self.certificates[cert_key]
        new_cert = await self.create_certificate(
            common_name=common_name, namespace=namespace, validity_days=365
        )

        # Update Kubernetes secret
        await self._update_tls_secret(new_cert)

        logger.info(f"Certificate rotated: {cert_key}")

    async def enable_mtls(
        self, namespace: str, mode: SecurityLevel = SecurityLevel.STRICT
    ):
        """
        Enable mTLS for a namespace

        Args:
            namespace: Target namespace
            mode: mTLS mode (STRICT, PERMISSIVE, DISABLED)
        """
        logger.info(f"Enabling mTLS in {namespace} with mode {mode.value}")

        try:
            # Create PeerAuthentication resource
            peer_auth = {
                "apiVersion": "security.istio.io/v1beta1",
                "kind": "PeerAuthentication",
                "metadata": {"name": f"{namespace}-mtls", "namespace": namespace},
                "spec": {"mtls": {"mode": mode.value.upper()}},
            }

            # Check if exists
            try:
                existing = self.custom_api.get_namespaced_custom_object(
                    group="security.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="peerauthentications",
                    name=f"{namespace}-mtls",
                )

                # Update existing
                existing["spec"]["mtls"]["mode"] = mode.value.upper()
                self.custom_api.patch_namespaced_custom_object(
                    group="security.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="peerauthentications",
                    name=f"{namespace}-mtls",
                    body=existing,
                )
                logger.info(f"Updated mTLS policy for {namespace}")

            except ApiException as e:
                if e.status == 404:
                    # Create new
                    self.custom_api.create_namespaced_custom_object(
                        group="security.istio.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="peerauthentications",
                        body=peer_auth,
                    )
                    logger.info(f"Created mTLS policy for {namespace}")
                else:
                    raise

        except Exception as e:
            logger.error(f"Failed to enable mTLS: {e}")
            raise

    async def create_authorization_policy(
        self, name: str, namespace: str, policy: SecurityPolicy
    ):
        """
        Create an authorization policy

        Args:
            name: Policy name
            namespace: Policy namespace
            policy: SecurityPolicy object
        """
        logger.info(f"Creating authorization policy {name} in {namespace}")

        try:
            # Build authorization policy
            auth_policy = {
                "apiVersion": "security.istio.io/v1beta1",
                "kind": "AuthorizationPolicy",
                "metadata": {"name": name, "namespace": namespace},
                "spec": {"action": policy.authorization_mode.value, "rules": []},
            }

            # Add rules based on policy
            rules = []

            # Source-based rules
            if policy.allowed_principals or policy.allowed_namespaces:
                rule = {"from": []}

                if policy.allowed_principals:
                    rule["from"].append(
                        {"source": {"principals": policy.allowed_principals}}
                    )

                if policy.allowed_namespaces:
                    rule["from"].append(
                        {"source": {"namespaces": policy.allowed_namespaces}}
                    )

                rules.append(rule)

            # Operation-based rules
            if policy.allowed_methods or policy.allowed_paths:
                rule = {"to": []}

                operation = {}
                if policy.allowed_methods:
                    operation["methods"] = policy.allowed_methods
                if policy.allowed_paths:
                    operation["paths"] = policy.allowed_paths

                if operation:
                    rule["to"].append({"operation": operation})

                rules.append(rule)

            # Add custom rules
            if policy.custom_rules:
                for custom_rule in policy.custom_rules.get("rules", []):
                    rules.append(custom_rule)

            auth_policy["spec"]["rules"] = rules

            # Apply authorization policy
            try:
                existing = self.custom_api.get_namespaced_custom_object(
                    group="security.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="authorizationpolicies",
                    name=name,
                )

                # Update existing
                existing["spec"] = auth_policy["spec"]
                self.custom_api.patch_namespaced_custom_object(
                    group="security.istio.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="authorizationpolicies",
                    name=name,
                    body=existing,
                )
                logger.info(f"Updated authorization policy {name}")

            except ApiException as e:
                if e.status == 404:
                    # Create new
                    self.custom_api.create_namespaced_custom_object(
                        group="security.istio.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="authorizationpolicies",
                        body=auth_policy,
                    )
                    logger.info(f"Created authorization policy {name}")
                else:
                    raise

            # Store policy
            policy_key = f"{namespace}/{name}"
            self.policies[policy_key] = policy

        except Exception as e:
            logger.error(f"Failed to create authorization policy: {e}")
            raise

    async def update_rbac(self, name: str, namespace: str, rbac_policy: RBACPolicy):
        """
        Update RBAC configuration

        Args:
            name: RBAC policy name
            namespace: Target namespace
            rbac_policy: RBACPolicy object
        """
        logger.info(f"Updating RBAC for {name} in {namespace}")

        try:
            # Create or update Role
            role = client.V1Role(
                metadata=client.V1ObjectMeta(name=name, namespace=namespace), rules=[]
            )

            # Add rules based on permissions
            for resource, verbs in rbac_policy.permissions.items():
                rule = client.V1PolicyRule(
                    api_groups=[""], resources=[resource], verbs=verbs
                )
                role.rules.append(rule)

            # Apply Role
            try:
                existing_role = self.rbac_v1.read_namespaced_role(
                    name=name, namespace=namespace
                )

                # Update existing
                existing_role.rules = role.rules
                self.rbac_v1.patch_namespaced_role(
                    name=name, namespace=namespace, body=existing_role
                )
                logger.info(f"Updated Role {name}")

            except ApiException as e:
                if e.status == 404:
                    # Create new
                    self.rbac_v1.create_namespaced_role(namespace=namespace, body=role)
                    logger.info(f"Created Role {name}")
                else:
                    raise

            # Create or update RoleBinding
            role_binding = client.V1RoleBinding(
                metadata=client.V1ObjectMeta(
                    name=f"{name}-binding", namespace=namespace
                ),
                subjects=[],
                role_ref=client.V1RoleRef(
                    api_group="rbac.authorization.k8s.io", kind="Role", name=name
                ),
            )

            # Add subjects
            for subject in rbac_policy.subjects:
                if "/" in subject:
                    # ServiceAccount format: namespace/name
                    ns, sa_name = subject.split("/")
                    role_binding.subjects.append(
                        client.V1Subject(
                            kind="ServiceAccount", name=sa_name, namespace=ns
                        )
                    )
                else:
                    # User format
                    role_binding.subjects.append(
                        client.V1Subject(kind="User", name=subject)
                    )

            # Apply RoleBinding
            try:
                existing_binding = self.rbac_v1.read_namespaced_role_binding(
                    name=f"{name}-binding", namespace=namespace
                )

                # Update existing
                existing_binding.subjects = role_binding.subjects
                self.rbac_v1.patch_namespaced_role_binding(
                    name=f"{name}-binding", namespace=namespace, body=existing_binding
                )
                logger.info(f"Updated RoleBinding {name}-binding")

            except ApiException as e:
                if e.status == 404:
                    # Create new
                    self.rbac_v1.create_namespaced_role_binding(
                        namespace=namespace, body=role_binding
                    )
                    logger.info(f"Created RoleBinding {name}-binding")
                else:
                    raise

            # Store RBAC policy
            policy_key = f"{namespace}/{name}"
            self.rbac_policies[policy_key] = rbac_policy

        except Exception as e:
            logger.error(f"Failed to update RBAC: {e}")
            raise

    async def monitor_certificates(self):
        """Monitor certificates for rotation"""
        while self.running:
            try:
                for cert_key, cert in list(self.certificates.items()):
                    # Check if certificate is expiring soon (30 days)
                    days_until_expiry = (cert.valid_until - datetime.now()).days

                    if days_until_expiry <= 30:
                        logger.warning(
                            f"Certificate {cert_key} expires in {days_until_expiry} days"
                        )

                        # Auto-rotate if less than 7 days
                        if days_until_expiry <= 7:
                            await self.rotate_certificate(
                                cert.common_name, cert.namespace
                            )

            except Exception as e:
                logger.error(f"Error monitoring certificates: {e}")

            # Check every hour
            await asyncio.sleep(3600)

    async def monitor_policies(self):
        """Monitor and enforce security policies"""
        while self.running:
            try:
                # Check for policy violations
                # This would integrate with Istio telemetry
                pass

            except Exception as e:
                logger.error(f"Error monitoring policies: {e}")

            # Check every 5 minutes
            await asyncio.sleep(300)

    async def _create_tls_secret(self, cert: Certificate):
        """Create Kubernetes TLS secret"""
        try:
            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=f"{cert.common_name}-tls", namespace=cert.namespace
                ),
                type="kubernetes.io/tls",
                data={
                    "tls.crt": base64.b64encode(cert.cert_pem.encode()).decode(),
                    "tls.key": base64.b64encode(cert.key_pem.encode()).decode(),
                },
            )

            if cert.ca_cert_pem:
                secret.data["ca.crt"] = base64.b64encode(
                    cert.ca_cert_pem.encode()
                ).decode()

            self.v1.create_namespaced_secret(namespace=cert.namespace, body=secret)

            logger.info(f"Created TLS secret for {cert.common_name}")

        except ApiException as e:
            if e.status != 409:  # Not conflict
                logger.error(f"Failed to create TLS secret: {e}")
                raise

    async def _update_tls_secret(self, cert: Certificate):
        """Update Kubernetes TLS secret"""
        try:
            secret_name = f"{cert.common_name}-tls"

            # Get existing secret
            secret = self.v1.read_namespaced_secret(
                name=secret_name, namespace=cert.namespace
            )

            # Update data
            secret.data = {
                "tls.crt": base64.b64encode(cert.cert_pem.encode()).decode(),
                "tls.key": base64.b64encode(cert.key_pem.encode()).decode(),
            }

            if cert.ca_cert_pem:
                secret.data["ca.crt"] = base64.b64encode(
                    cert.ca_cert_pem.encode()
                ).decode()

            # Apply update
            self.v1.patch_namespaced_secret(
                name=secret_name, namespace=cert.namespace, body=secret
            )

            logger.info(f"Updated TLS secret for {cert.common_name}")

        except ApiException as e:
            logger.error(f"Failed to update TLS secret: {e}")
            raise

    def create_security_policy(
        self, name: str, namespace: str, **kwargs
    ) -> SecurityPolicy:
        """
        Create a security policy

        Args:
            name: Policy name
            namespace: Policy namespace
            **kwargs: Policy parameters

        Returns:
            SecurityPolicy object
        """
        policy = SecurityPolicy(
            name=name,
            namespace=namespace,
            mtls_mode=kwargs.get("mtls_mode", SecurityLevel.STRICT),
            authorization_mode=kwargs.get(
                "authorization_mode", AuthorizationMode.ALLOW
            ),
            allowed_principals=kwargs.get("allowed_principals", []),
            allowed_namespaces=kwargs.get("allowed_namespaces", []),
            allowed_services=kwargs.get("allowed_services", []),
            allowed_methods=kwargs.get("allowed_methods", ["GET", "POST"]),
            allowed_paths=kwargs.get("allowed_paths", ["/*"]),
            custom_rules=kwargs.get("custom_rules", {}),
        )

        policy_key = f"{namespace}/{name}"
        self.policies[policy_key] = policy

        return policy

    def create_rbac_policy(
        self,
        name: str,
        namespace: str,
        role: str,
        subjects: list[str],
        permissions: dict[str, list[str]],
    ) -> RBACPolicy:
        """
        Create an RBAC policy

        Args:
            name: Policy name
            namespace: Policy namespace
            role: Role name
            subjects: List of subjects
            permissions: Resource permissions

        Returns:
            RBACPolicy object
        """
        rbac_policy = RBACPolicy(
            name=name,
            namespace=namespace,
            role=role,
            subjects=subjects,
            permissions=permissions,
        )

        policy_key = f"{namespace}/{name}"
        self.rbac_policies[policy_key] = rbac_policy

        return rbac_policy


# Import for IP address handling
import ipaddress
