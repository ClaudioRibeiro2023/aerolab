"""
Módulo de Criptografia em Repouso.

Gerencia criptografia de dados sensíveis armazenados.
"""

import os
import base64
import secrets
import hashlib
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


@dataclass
class EncryptedData:
    """Dados criptografados."""
    ciphertext: bytes
    nonce: Optional[bytes] = None
    tag: Optional[bytes] = None
    key_id: Optional[str] = None
    algorithm: str = "fernet"
    created_at: str = ""


class KeyManager:
    """
    Gerenciador de chaves de criptografia.
    
    Features:
    - Geração segura de chaves
    - Rotação de chaves
    - Derivação de chaves (PBKDF2)
    - Armazenamento seguro
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or os.getenv("KEY_STORAGE_PATH", "./data/keys"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._keys: Dict[str, bytes] = {}
        self._active_key_id: Optional[str] = None
        
        self._load_keys()
    
    def _load_keys(self):
        """Carrega chaves do armazenamento."""
        keys_file = self.storage_path / "keys.enc"
        
        if keys_file.exists():
            # Decodificar com master key do ambiente
            master_key = os.getenv("MASTER_ENCRYPTION_KEY")
            if master_key:
                try:
                    fernet = Fernet(master_key.encode())
                    data = fernet.decrypt(keys_file.read_bytes())
                    import json
                    keys_data = json.loads(data)
                    
                    for key_id, key_b64 in keys_data.get("keys", {}).items():
                        self._keys[key_id] = base64.b64decode(key_b64)
                    
                    self._active_key_id = keys_data.get("active")
                except Exception:
                    pass
        
        # Criar chave inicial se não existir
        if not self._keys:
            self._generate_new_key()
    
    def _save_keys(self):
        """Salva chaves criptografadas."""
        master_key = os.getenv("MASTER_ENCRYPTION_KEY")
        if not master_key:
            # Gerar master key e avisar
            master_key = Fernet.generate_key().decode()
            print(f"⚠️ MASTER_ENCRYPTION_KEY não definida. Use: {master_key}")
            os.environ["MASTER_ENCRYPTION_KEY"] = master_key
        
        import json
        data = {
            "keys": {
                key_id: base64.b64encode(key).decode()
                for key_id, key in self._keys.items()
            },
            "active": self._active_key_id
        }
        
        fernet = Fernet(master_key.encode())
        encrypted = fernet.encrypt(json.dumps(data).encode())
        (self.storage_path / "keys.enc").write_bytes(encrypted)
    
    def _generate_new_key(self) -> str:
        """Gera nova chave."""
        key = Fernet.generate_key()
        key_id = f"key_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
        
        self._keys[key_id] = key
        self._active_key_id = key_id
        self._save_keys()
        
        return key_id
    
    def get_active_key(self) -> tuple[str, bytes]:
        """Retorna chave ativa."""
        if not self._active_key_id:
            self._generate_new_key()
        return self._active_key_id, self._keys[self._active_key_id]
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """Obtém chave por ID."""
        return self._keys.get(key_id)
    
    def rotate_key(self) -> str:
        """Rotaciona chave ativa."""
        return self._generate_new_key()
    
    @staticmethod
    def derive_key(
        password: str,
        salt: Optional[bytes] = None,
        iterations: int = 100000
    ) -> tuple[bytes, bytes]:
        """
        Deriva chave de senha usando PBKDF2.
        
        Returns:
            (key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt


class EncryptionService:
    """
    Serviço de criptografia em repouso.
    
    Features:
    - Criptografia AES-256 (via Fernet)
    - Criptografia de campos específicos
    - Suporte a rotação de chaves
    - Hashing seguro de senhas
    
    Configuração:
        MASTER_ENCRYPTION_KEY: Chave mestra para proteger outras chaves
        KEY_STORAGE_PATH: Diretório para armazenamento de chaves
    """
    
    def __init__(self, key_manager: Optional[KeyManager] = None):
        if not HAS_CRYPTOGRAPHY:
            raise ImportError(
                "cryptography não instalado. Instale com: pip install cryptography"
            )
        
        self.key_manager = key_manager or KeyManager()
    
    def encrypt(self, data: Union[str, bytes]) -> EncryptedData:
        """
        Criptografa dados.
        
        Args:
            data: Dados a criptografar (string ou bytes)
        
        Returns:
            Dados criptografados com metadados
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        
        key_id, key = self.key_manager.get_active_key()
        fernet = Fernet(key)
        ciphertext = fernet.encrypt(data)
        
        return EncryptedData(
            ciphertext=ciphertext,
            key_id=key_id,
            algorithm="fernet",
            created_at=datetime.utcnow().isoformat()
        )
    
    def decrypt(self, encrypted: EncryptedData) -> bytes:
        """
        Descriptografa dados.
        
        Args:
            encrypted: Dados criptografados
        
        Returns:
            Dados originais
        """
        key = self.key_manager.get_key(encrypted.key_id)
        if not key:
            raise ValueError(f"Chave {encrypted.key_id} não encontrada")
        
        fernet = Fernet(key)
        return fernet.decrypt(encrypted.ciphertext)
    
    def decrypt_string(self, encrypted: EncryptedData) -> str:
        """Descriptografa e retorna string."""
        return self.decrypt(encrypted).decode("utf-8")
    
    def encrypt_dict(
        self,
        data: Dict[str, Any],
        fields: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Criptografa campos específicos de um dicionário.
        
        Args:
            data: Dicionário com dados
            fields: Campos a criptografar (None = todos os valores string)
        
        Returns:
            Dicionário com campos criptografados
        """
        result = data.copy()
        fields_to_encrypt = fields or [
            k for k, v in data.items() if isinstance(v, str)
        ]
        
        for field in fields_to_encrypt:
            if field in result and result[field]:
                encrypted = self.encrypt(str(result[field]))
                result[field] = {
                    "_encrypted": True,
                    "ciphertext": base64.b64encode(encrypted.ciphertext).decode(),
                    "key_id": encrypted.key_id,
                    "algorithm": encrypted.algorithm
                }
        
        return result
    
    def decrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Descriptografa campos de um dicionário.
        
        Args:
            data: Dicionário com campos criptografados
        
        Returns:
            Dicionário com valores descriptografados
        """
        result = data.copy()
        
        for key, value in data.items():
            if isinstance(value, dict) and value.get("_encrypted"):
                encrypted = EncryptedData(
                    ciphertext=base64.b64decode(value["ciphertext"]),
                    key_id=value["key_id"],
                    algorithm=value.get("algorithm", "fernet")
                )
                result[key] = self.decrypt_string(encrypted)
        
        return result
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Cria hash seguro de senha usando PBKDF2.
        
        Returns:
            Hash no formato: $pbkdf2$iterations$salt$hash
        """
        salt = secrets.token_bytes(16)
        iterations = 100000
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        hash_bytes = kdf.derive(password.encode())
        
        salt_b64 = base64.b64encode(salt).decode()
        hash_b64 = base64.b64encode(hash_bytes).decode()
        
        return f"$pbkdf2${iterations}${salt_b64}${hash_b64}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verifica senha contra hash."""
        try:
            parts = hashed.split("$")
            if parts[1] != "pbkdf2":
                return False
            
            iterations = int(parts[2])
            salt = base64.b64decode(parts[3])
            stored_hash = base64.b64decode(parts[4])
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations,
                backend=default_backend()
            )
            
            kdf.verify(password.encode(), stored_hash)
            return True
            
        except Exception:
            return False
    
    def rotate_and_reencrypt(
        self,
        encrypted_items: list[EncryptedData]
    ) -> list[EncryptedData]:
        """
        Rotaciona chave e re-criptografa itens.
        
        Args:
            encrypted_items: Lista de itens criptografados
        
        Returns:
            Itens re-criptografados com nova chave
        """
        # Descriptografar todos
        decrypted = [self.decrypt(item) for item in encrypted_items]
        
        # Rotacionar chave
        self.key_manager.rotate_key()
        
        # Re-criptografar com nova chave
        return [self.encrypt(data) for data in decrypted]


# Funções de conveniência
def encrypt_field(value: str) -> Dict[str, Any]:
    """Criptografa um campo."""
    service = EncryptionService()
    encrypted = service.encrypt(value)
    return {
        "_encrypted": True,
        "ciphertext": base64.b64encode(encrypted.ciphertext).decode(),
        "key_id": encrypted.key_id
    }


def decrypt_field(encrypted_value: Dict[str, Any]) -> str:
    """Descriptografa um campo."""
    if not encrypted_value.get("_encrypted"):
        return str(encrypted_value)
    
    service = EncryptionService()
    encrypted = EncryptedData(
        ciphertext=base64.b64decode(encrypted_value["ciphertext"]),
        key_id=encrypted_value["key_id"]
    )
    return service.decrypt_string(encrypted)


# Singleton
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Obtém instância singleton do serviço de criptografia."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
