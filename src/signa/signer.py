# SPDX-License-Identifier: GPL-3.0-or-later
"""Signature d'un PDF via l'API Python de pyHanko."""

from __future__ import annotations

from pathlib import Path

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import fields, signers
from pyhanko.stamp import BaseStampStyle

from signa.coords import PdfBox

FIELD_PREFIX = "Signature"


class SigningError(Exception):
    """Échec de signature avec un message destiné à l'utilisateur (français)."""


def output_path_for(source: Path) -> Path:
    """Chemin « <nom>-signe.pdf » à côté de l'original, sans jamais écraser.

    Si le fichier existe déjà, on numérote : « -signe-2.pdf », « -signe-3.pdf »…
    """
    candidate = source.with_name(f"{source.stem}-signe.pdf")
    counter = 2
    while candidate.exists():
        candidate = source.with_name(f"{source.stem}-signe-{counter}.pdf")
        counter += 1
    return candidate


def load_signer(p12_path: Path, password: str) -> signers.SimpleSigner:
    """Charge le certificat ; pyHanko renvoie None sans détail en cas d'échec.

    Le mot de passe est copié dans un `bytearray` effacé dès le chargement :
    Python ne permet pas d'effacer une `str` ou un `bytes`, c'est donc un
    effacement au mieux (la copie d'origine dépend du ramasse-miettes).
    """
    if not p12_path.is_file():
        raise SigningError("Certificat introuvable.")
    secret = bytearray(password.encode("utf-8"))
    try:
        signer = signers.SimpleSigner.load_pkcs12(str(p12_path), passphrase=secret)
    except Exception as exc:  # fichier non PKCS#12, tronqué, etc.
        raise SigningError("Certificat illisible : ce n'est pas un fichier .p12 valide.") from exc
    finally:
        for index in range(len(secret)):
            secret[index] = 0
    if signer is None:
        raise SigningError("Mot de passe incorrect ou certificat illisible.")
    return signer


def _free_field_name(reader: PdfFileReader) -> str:
    """Premier nom « SignatureN » libre (le PDF peut déjà être signé)."""
    used = {name for name, _, _ in fields.enumerate_sig_fields(reader)}
    counter = 1
    while f"{FIELD_PREFIX}{counter}" in used:
        counter += 1
    return f"{FIELD_PREFIX}{counter}"


def _open_reader(infile) -> PdfFileReader:
    """Ouvre le PDF source en traduisant les erreurs en messages clairs."""
    try:
        reader = PdfFileReader(infile, strict=False)
        if reader.encrypt_dict is not None:
            raise SigningError("Ce PDF est protégé par mot de passe : il ne peut pas être signé ici.")
        reader.root  # noqa: B018 - force la lecture du catalogue pour détecter un PDF corrompu
    except SigningError:
        raise
    except Exception as exc:
        raise SigningError("Ce fichier n'est pas un PDF valide ou il est corrompu.") from exc
    return reader


def sign_pdf(
    source: Path,
    p12_path: Path,
    password: str,
    *,
    page: int = 0,
    box: PdfBox | None = None,
    style: BaseStampStyle | None = None,
    reason: str | None = None,
) -> Path:
    """Signe `source` et retourne le chemin du nouveau fichier.

    `box=None` produit une signature invisible. L'original n'est jamais modifié ;
    un PDF déjà signé reçoit une signature supplémentaire (révision incrémentale).
    """
    if box is not None and style is None:
        raise SigningError("Aucun style de tampon sélectionné.")
    if not source.is_file():
        raise SigningError("Document introuvable.")
    signer = load_signer(p12_path, password)
    output = output_path_for(source)
    created = False  # on ne supprime que ce fichier de sortie, jamais un fichier préexistant
    try:
        with source.open("rb") as infile:
            reader = _open_reader(infile)
            field_name = _free_field_name(reader)
            if box is None:
                field_spec = fields.SigFieldSpec(field_name)
            else:
                if not 0 <= page < int(reader.root["/Pages"]["/Count"]):
                    raise SigningError("Page inexistante dans ce document.")
                field_spec = fields.SigFieldSpec(field_name, on_page=page, box=box.as_tuple())
            writer = IncrementalPdfFileWriter(infile, strict=False)
            fields.append_signature_field(writer, field_spec)
            meta = signers.PdfSignatureMetadata(field_name=field_name, md_algorithm="sha256", reason=reason)
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=style if box else None)
            with output.open("xb") as outfile:
                created = True
                pdf_signer.sign_pdf(writer, output=outfile)
    except SigningError:
        if created:
            output.unlink(missing_ok=True)
        raise
    except FileExistsError as exc:
        raise SigningError("Le fichier de sortie existe déjà.") from exc
    except PermissionError as exc:
        if created:
            output.unlink(missing_ok=True)
        raise SigningError("Écriture impossible dans ce dossier (droits insuffisants).") from exc
    except Exception as exc:  # pyHanko lève de nombreux types : on les convertit
        if created:
            output.unlink(missing_ok=True)
        raise SigningError(f"Échec de la signature : {exc}") from exc
    return output
