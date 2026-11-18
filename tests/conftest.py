# SPDX-License-Identifier: GPL-3.0-or-later
"""Fixtures : certificat et PDF factices générés à la volée (rien de réel)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pymupdf
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

FIXTURES = Path(__file__).parent / "fixtures"
TEST_PASSWORD = "test-password"


def make_p12(path: Path, password: str = TEST_PASSWORD) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Signataire de test")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(days=1))
        .not_valid_after(now + dt.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=True, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=True,
                crl_sign=False, encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    data = serialization.pkcs12.serialize_key_and_certificates(
        b"test", key, cert, None, serialization.BestAvailableEncryption(password.encode())
    )
    path.write_bytes(data)


def make_pdf(path: Path, *, pages: int = 2, rotation: int = 0, mediabox_origin: bool = False) -> None:
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page factice {i + 1}")
    if rotation:
        doc[0].set_rotation(rotation)
    if mediabox_origin:
        doc[0].set_mediabox(pymupdf.Rect(50, 100, 645, 942))
    doc.save(path)


@pytest.fixture(scope="session")
def p12_file() -> Path:
    FIXTURES.mkdir(exist_ok=True)
    path = FIXTURES / "test.p12"
    if not path.exists():
        make_p12(path)
    return path


@pytest.fixture(scope="session")
def pdf_file() -> Path:
    FIXTURES.mkdir(exist_ok=True)
    path = FIXTURES / "test.pdf"
    if not path.exists():
        make_pdf(path)
    return path


@pytest.fixture
def work_pdf(tmp_path: Path, pdf_file: Path) -> Path:
    target = tmp_path / "document.pdf"
    target.write_bytes(pdf_file.read_bytes())
    return target


@pytest.fixture
def styles_file() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "signa" / "resources" / "pyhanko.example.yml"
