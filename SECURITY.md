# Politique de sécurité / Security policy

## Signaler une vulnérabilité / Reporting a vulnerability

Merci de **ne pas** ouvrir d'issue publique pour une faille. Utilisez le
[signalement privé de GitHub](https://github.com/simetriik/signa/security/advisories/new)
(« Report a vulnerability ») ou écrivez à l'auteur : arkryonia@gmail.com.
Please do **not** open a public issue for a vulnerability; use GitHub private reporting or email the author.

Réponse visée sous 7 jours ; correctif et avis publiés une fois la faille corrigée.

## Versions prises en charge

Seule la dernière version publiée reçoit des correctifs de sécurité.

## Garanties de conception

- Le mot de passe du certificat est demandé à chaque signature ; il n'est **jamais écrit sur disque**, ni dans les préférences, ni dans un journal. Il est copié dans un tampon mémoire effacé juste après le chargement du certificat. Python ne permet pas d'effacer les `str`/`bytes` immuables : l'effacement est « au mieux » et ne protège pas contre un attaquant qui lit la mémoire du processus.
- Le document original n'est jamais modifié ni écrasé : le résultat est un nouveau fichier (`<nom>-signe.pdf`, numéroté si besoin), ouvert en création exclusive.
- Les fichiers de styles YAML sont lus avec `yaml.safe_load`.
- Aucune connexion réseau n'est émise par Signa.

## Limites à connaître

- Un certificat **auto-signé** prouve l'intégrité du document, pas l'identité du signataire ni une valeur juridique qualifiée (voir le README).
- Protégez votre fichier `.p12` : toute personne qui le possède avec son mot de passe peut signer à votre place.
- Les installateurs Windows et macOS ne sont pas signés ; vérifiez leur somme de contrôle et téléchargez-les uniquement depuis la page Releases du dépôt.
- Les contrôles automatisés (`bandit`, `pip-audit`) sont lancés avant chaque version.
