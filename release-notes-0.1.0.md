# Signa 0.1.0 — première version publique

Signa est une application de bureau pour **signer des PDF** avec un certificat PKCS#12 (`.p12`), propulsée par pyHanko. Tracez la zone de signature à la souris, choisissez un style de tampon, saisissez le mot de passe : le résultat est enregistré sous `<nom>-signe.pdf`, l'original n'est jamais touché.

## Téléchargements

| Système | Fichier |
|---|---|
| Debian 13 / Linux | `signa_0.1.0-1_amd64.deb` |
| Windows 10/11 | `Signa-0.1.0.msi` |
| macOS 14+ (Apple silicon) | `Signa-0.1.0.dmg` |

## ⚠️ À lire avant d'installer

- **Installateurs non signés** : Windows (SmartScreen : *Informations complémentaires → Exécuter quand même*) et macOS (Gatekeeper : *Réglages Système → Confidentialité et sécurité → Ouvrir quand même*) afficheront un avertissement. Détails dans le [README](README.md#installation).
- **Valeur juridique** : un certificat auto-signé prouve l'intégrité du document, pas l'identité du signataire ; ce n'est pas une signature qualifiée. Pour une valeur juridique, utilisez un certificat d'une autorité reconnue.
- Les versions Windows et macOS n'ont pas été testées par l'auteur avant publication : merci de signaler tout problème.

## Nouveautés

- Ouverture d'un PDF (sélecteur, glisser-déposer, « Ouvrir avec »), navigation par page, tracé de la zone de signature.
- Signature visible (styles YAML pyHanko) ou invisible ; signature d'un PDF déjà signé.
- Mot de passe jamais stocké ni journalisé, effacé de la mémoire après usage (au mieux sous Python).
- Messages d'erreur clairs (mot de passe incorrect, PDF corrompu ou protégé, certificat illisible).
- Linux, Windows et macOS ; interface en français.

Licence GPL-3.0-or-later. Voir le [CHANGELOG](CHANGELOG.md).
