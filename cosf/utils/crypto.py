import base64
import os
from typing import Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519

class CryptoManager:
    """Handles cryptographic operations for signing and verification."""

    @staticmethod
    def generate_key_pair() -> Tuple[str, str]:
        """Generates an Ed25519 key pair and returns them as base64 strings."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_bytes = private_key.private_bytes_raw()
        public_bytes = public_key.public_bytes_raw()
        
        return (
            base64.b64encode(private_bytes).decode("utf-8"),
            base64.b64encode(public_bytes).decode("utf-8")
        )

    @staticmethod
    def sign_message(private_key_b64: str, message: str) -> str:
        """Signs a message using an Ed25519 private key."""
        private_bytes = base64.b64decode(private_key_b64)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
        
        signature = private_key.sign(message.encode("utf-8"))
        return base64.b64encode(signature).decode("utf-8")

    @staticmethod
    def verify_signature(public_key_b64: str, message: str, signature_b64: str) -> bool:
        """Verifies an Ed25519 signature."""
        try:
            public_bytes = base64.b64decode(public_key_b64)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
            
            signature = base64.b64decode(signature_b64)
            public_key.verify(signature, message.encode("utf-8"))
            return True
        except Exception:
            return False
