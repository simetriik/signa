# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; versionnage [SemVer](https://semver.org/lang/fr/).

## [0.1.0] - 2026-11-18

### Ajouté
- Installateurs : paquet Debian, MSI Windows et DMG macOS (Briefcase), construits par GitHub Actions à chaque tag.
- Fonctionne sous Linux, Windows et macOS : dossier de configuration propre à chaque système (platformdirs), ressources embarquées dans le paquet.
- Intégration « Ouvrir avec » pour les PDF (Linux, Windows, macOS).
- Signature d'un PDF déjà signé (champ « SignatureN » libre) ; messages clairs pour un mot de passe incorrect, un PDF corrompu ou protégé, un certificat illisible.
- Mot de passe copié dans un tampon mémoire effacé après usage.
- Ouverture d'un PDF (sélecteur, glisser-déposer, argument de ligne de commande) et affichage page par page.
- Tracé de la zone de signature à la souris, conversion en coordonnées PDF entières (origine en bas à gauche, rotation et MediaBox décalée gérées).
- Signature via pyHanko (tampon visible ou signature invisible), styles lus depuis un fichier YAML.
- Sortie `<nom>-signe.pdf` sans écrasement (numérotation si le fichier existe).
- Mémorisation du dernier certificat, du style et de la zone ; mot de passe jamais stocké.
- Lanceur GNOME, icône, page de manuel.
