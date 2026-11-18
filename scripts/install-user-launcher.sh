#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Installe un lanceur GNOME pour l'utilisateur courant, depuis un clone du dépôt
# (sans paquet .deb). Désinstallation : voir README.
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
icons_dir="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

mkdir -p "$apps_dir" "$icons_dir"
cp "$project_dir/src/signa/resources/signa.svg" "$icons_dir/signa.svg"
sed "s|^Exec=.*|Exec=uv run --project \"$project_dir\" signa %f|" \
  "$project_dir/packaging/signa.desktop" > "$apps_dir/signa.desktop"

command -v update-desktop-database >/dev/null && update-desktop-database "$apps_dir" || true
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t "${icons_dir%/scalable/apps}/.." 2>/dev/null || true
echo "Lanceur installé : $apps_dir/signa.desktop"
