"""CLE Ao save AES container and CLE game-asset decryption."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass

from ao_save_formats import CLE_PAYLOAD_SIZE

FORMAT_NISA_ZSTD = "nisa_zstd"
FORMAT_CLE_KAI = "cle_kai"
CLE_KEY_SEED = b"5e84w@ypz p@kgpg te"
CLE_IV_SIZE = 16

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7
except ImportError as exc:
    Cipher = algorithms = modes = PKCS7 = None
    CRYPTOGRAPHY_IMPORT_ERROR = exc


def _require_cryptography():
    if Cipher is None:
        raise RuntimeError("缺少 cryptography 依赖，无法读写 CLE Kai 存档。请先安装: pip install cryptography") from CRYPTOGRAPHY_IMPORT_ERROR


def _cle_digest():
    digest = CLE_KEY_SEED
    for _ in range(3):
        digest = hashlib.sha256(digest).digest()
    return digest


def cle_aes_key():
    return _cle_digest()[:16]


def _decrypt(ciphertext, iv):
    _require_cryptography()
    decryptor = Cipher(algorithms.AES(cle_aes_key()), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def decode_cle_asset(raw):
    """Game assets have an explicit IV; save files use a derived fixed IV."""
    if len(raw) < 32 or (len(raw) - 16) % 16:
        raise ValueError("CLE Kai 资源文件长度无效")
    return _decrypt(raw[16:], raw[:16])


@dataclass(frozen=True)
class CleKaiContainer:
    payload: bytes


def looks_like_cle_kai(raw, expected_payload_size=CLE_PAYLOAD_SIZE):
    return len(raw) == ((expected_payload_size + 4) // 16 + 1) * 16


def decode_cle_kai(raw, expected_payload_size=CLE_PAYLOAD_SIZE):
    """Decrypt length + complete Ao payload as one AES-CBC stream."""
    if not looks_like_cle_kai(raw, expected_payload_size):
        raise ValueError("不是受支持的碧 CLE Kai 存档容器")
    plain = _decrypt(raw, _cle_digest()[16:])
    declared, = struct.unpack_from("<I", plain)
    if declared != expected_payload_size or len(plain) != declared + 4:
        raise ValueError("CLE Kai 存档明文长度不匹配")
    return CleKaiContainer(plain[4:])


def encode_cle_kai(payload):
    _require_cryptography()
    if len(payload) != CLE_PAYLOAD_SIZE:
        raise ValueError(f"碧 CLE 明文大小错误: {len(payload):#x}")
    plain = struct.pack("<I", len(payload)) + bytes(payload)
    padder = PKCS7(128).padder()
    padded = padder.update(plain) + padder.finalize()
    encryptor = Cipher(algorithms.AES(cle_aes_key()), modes.CBC(_cle_digest()[16:])).encryptor()
    return encryptor.update(padded) + encryptor.finalize()
