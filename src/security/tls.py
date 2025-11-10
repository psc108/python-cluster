"""TLS communication security"""
import ssl
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime


class TLSManager:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.cert_dir = f"/tmp/cluster_certs_{node_id}"
        self.private_key = None
        self.certificate = None
        
    def generate_self_signed_cert(self):
        """Generate self-signed certificate for node"""
        # Generate private key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Cluster"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"cluster-node-{self.node_id}"),
        ])
        
        self.certificate = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(f"cluster-node-{self.node_id}"),
                x509.DNSName("localhost"),
            ]),
            critical=False,
        ).sign(self.private_key, hashes.SHA256())
        
    def save_cert_files(self):
        """Save certificate and key to files"""
        os.makedirs(self.cert_dir, exist_ok=True)
        
        # Save private key
        key_path = os.path.join(self.cert_dir, "key.pem")
        with open(key_path, "wb") as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save certificate
        cert_path = os.path.join(self.cert_dir, "cert.pem")
        with open(cert_path, "wb") as f:
            f.write(self.certificate.public_bytes(serialization.Encoding.PEM))
            
        return cert_path, key_path
        
    def create_ssl_context(self, is_server=True):
        """Create SSL context for secure communication"""
        if is_server:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(
                os.path.join(self.cert_dir, "cert.pem"),
                os.path.join(self.cert_dir, "key.pem")
            )
        else:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # For self-signed certs
            
        return context