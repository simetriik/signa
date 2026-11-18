# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
from pathlib import Path

import pytest
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext

from signa import styles
from signa.coords import PdfBox
from signa.signer import SigningError, output_path_for, sign_pdf
from conftest import TEST_PASSWORD


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path: Path, p12: Path):
    from pyhanko.sign import signers

    cert = signers.SimpleSigner.load_pkcs12(str(p12), passphrase=TEST_PASSWORD.encode()).signing_cert
    with path.open("rb") as handle:
        reader = PdfFileReader(handle)
        assert len(reader.embedded_signatures) == 1
        sig = reader.embedded_signatures[0]
        vc = ValidationContext(trust_roots=[cert])
        return sig, validate_pdf_signature(sig, vc)


def test_visible_signature_is_valid(work_pdf, p12_file, styles_file):
    original = sha(work_pdf)
    style = styles.load_style(styles_file, "institutional")
    out = sign_pdf(work_pdf, p12_file, TEST_PASSWORD, page=0, box=PdfBox(50, 50, 300, 120), style=style)
    assert out.name == "document-signe.pdf" and out.parent == work_pdf.parent
    assert sha(work_pdf) == original  # l'original est intact
    sig, status = verify(out, p12_file)
    assert status.intact and status.valid and status.trusted
    assert status.coverage.name == "ENTIRE_FILE"
    assert [float(v) for v in sig.sig_field["/Rect"]] == [50, 50, 300, 120]


def test_invisible_signature(work_pdf, p12_file):
    out = sign_pdf(work_pdf, p12_file, TEST_PASSWORD, box=None)
    sig, status = verify(out, p12_file)
    assert status.intact and status.valid
    assert [float(v) for v in sig.sig_field["/Rect"]] == [0, 0, 0, 0]


def test_signature_on_second_page(work_pdf, p12_file, styles_file):
    style = styles.load_style(styles_file, "simple")
    out = sign_pdf(work_pdf, p12_file, TEST_PASSWORD, page=1, box=PdfBox(10, 10, 200, 60), style=style)
    with out.open("rb") as handle:
        reader = PdfFileReader(handle)
        page_ref = reader.embedded_signatures[0].sig_field["/P"].get_object()
        assert page_ref == reader.root["/Pages"]["/Kids"][1].get_object()


def test_wrong_password_leaves_no_file(work_pdf, p12_file):
    with pytest.raises(SigningError, match="Mot de passe"):
        sign_pdf(work_pdf, p12_file, "mauvais", box=None)
    assert not list(work_pdf.parent.glob("*-signe*.pdf"))


def test_never_overwrites(work_pdf, p12_file):
    first = sign_pdf(work_pdf, p12_file, TEST_PASSWORD, box=None)
    second = sign_pdf(work_pdf, p12_file, TEST_PASSWORD, box=None)
    assert first != second and second.name == "document-signe-2.pdf"
    assert first.exists() and second.exists()


def test_output_path_for(tmp_path):
    assert output_path_for(tmp_path / "a.pdf") == tmp_path / "a-signe.pdf"


def test_visible_requires_style(work_pdf, p12_file):
    with pytest.raises(SigningError, match="style"):
        sign_pdf(work_pdf, p12_file, TEST_PASSWORD, box=PdfBox(0, 0, 10, 10), style=None)


def test_missing_certificate(work_pdf, tmp_path):
    with pytest.raises(SigningError, match="introuvable"):
        sign_pdf(work_pdf, tmp_path / "absent.p12", "x", box=None)


def test_already_signed_pdf_gets_second_signature(work_pdf, p12_file):
    first = sign_pdf(work_pdf, p12_file, TEST_PASSWORD, box=None)
    second = sign_pdf(first, p12_file, TEST_PASSWORD, box=None)
    with second.open("rb") as handle:
        names = [sig.field_name for sig in PdfFileReader(handle).embedded_signatures]
    assert names == ["Signature1", "Signature2"]
    assert first.exists()  # la première version signée reste intacte


def test_corrupted_pdf(tmp_path, p12_file):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"%PDF-1.7\nceci est corrompu")
    with pytest.raises(SigningError, match="corrompu"):
        sign_pdf(bad, p12_file, TEST_PASSWORD, box=None)
    assert not list(tmp_path.glob("*-signe*"))


def test_encrypted_pdf(tmp_path, p12_file, work_pdf):
    import pymupdf

    secret = tmp_path / "secret.pdf"
    doc = pymupdf.open(work_pdf)
    doc.save(secret, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="u", owner_pw="o")
    with pytest.raises(SigningError, match="protégé"):
        sign_pdf(secret, p12_file, TEST_PASSWORD, box=None)


def test_invalid_certificate_file(tmp_path, work_pdf):
    fake = tmp_path / "fake.p12"
    fake.write_bytes(b"pas un certificat")
    with pytest.raises(SigningError, match="illisible"):
        sign_pdf(work_pdf, fake, "x", box=None)


def test_page_out_of_range(work_pdf, p12_file, styles_file):
    style = styles.load_style(styles_file, "simple")
    with pytest.raises(SigningError, match="Page"):
        sign_pdf(work_pdf, p12_file, TEST_PASSWORD, page=9, box=PdfBox(0, 0, 10, 10), style=style)
    assert not list(work_pdf.parent.glob("*-signe*"))


def test_password_is_not_written_anywhere(work_pdf, p12_file, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    from signa.settings import Settings

    out = sign_pdf(work_pdf, p12_file, TEST_PASSWORD, box=None)
    Settings(certificate_path=str(p12_file)).save()
    for path in (out, work_pdf, *(tmp_path / "cfg").rglob("*")):
        if path.is_file():
            assert TEST_PASSWORD.encode() not in path.read_bytes()


def test_password_buffer_is_wiped(p12_file, monkeypatch):
    seen = []
    from pyhanko.sign import signers

    real = signers.SimpleSigner.load_pkcs12

    def spy(path, passphrase=None, **kw):
        seen.append(passphrase)
        return real(path, passphrase=passphrase, **kw)

    monkeypatch.setattr(signers.SimpleSigner, "load_pkcs12", spy)
    from signa.signer import load_signer

    load_signer(p12_file, TEST_PASSWORD)
    assert seen and set(seen[0]) == {0}
