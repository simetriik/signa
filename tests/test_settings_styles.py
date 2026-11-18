# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from signa import styles
from signa.settings import Settings


def test_settings_roundtrip(tmp_path):
    path = tmp_path / "s.json"
    s = Settings(certificate_path="/x.p12", style_name="a", zone_page=1, zone_rect=[1.0, 2.0, 3.0, 4.0])
    s.save(path)
    assert Settings.load(path) == s


def test_settings_never_contains_password(tmp_path):
    path = tmp_path / "s.json"
    Settings(certificate_path="/x.p12").save(path)
    assert "password" not in path.read_text().lower() and "passe" not in path.read_text().lower()


def test_settings_corrupt_file_gives_defaults(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("{pas du json")
    assert Settings.load(path) == Settings()


def test_list_styles(styles_file):
    assert styles.list_styles(styles_file) == ["institutional", "simple"]


def test_unknown_style(styles_file):
    with pytest.raises(styles.StyleError):
        styles.load_style(styles_file, "nope")


def test_invalid_yaml(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("a: [")
    with pytest.raises(styles.StyleError):
        styles.list_styles(bad)


def test_ensure_default_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    target = styles.ensure_default_config()
    assert target.is_file() and styles.list_styles(target)
