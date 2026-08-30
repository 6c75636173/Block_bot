# 📖 Documentation technique — Bot Ulysse

> Pour la liste de toutes les commandes, voir `COMMANDES.md`. Ce fichier couvre
> l'architecture du code, la configuration, le fonctionnement interne, et l'historique
> des correctifs.

---

## 🚀 Démarrage

1. Copie `.env.example` en `.env` et colle ton token Discord :
   ```
   DISCORD_TOKEN=ton_token_ici
   ```
2. `pip install -r requirements.txt`
3. `python main/Ulysse.py`

Le bot refuse de démarrer si `DISCORD_TOKEN` est absent du `.env`.

---

## 🏗️ Architecture du code

Depuis la réorganisation du 20/08/2026, le code est en arborescence par dossiers façon
`cogs/` : `main/Ulysse.py` ne contient plus aucune commande — c'est un pur bootstrap qui
ajoute chaque sous-dossier de `cogs/` au chemin Python, crée le bot, connecte `core/`,
charge tous les cogs, et lance.

```
viez_bot/
├── bot_data/                   ← Toutes les données JSON (exclu de git, voir .gitignore)
│   ├── users.json              ← Profils joueurs (XP, pièces, niveau, inventaire)
│   ├── daily.json              ← Streaks quotidiens par utilisateur
│   ├── challenges.json         ← Défis quotidiens et progression
│   ├── missions_data.json      ← Missions quotidiennes et hebdomadaires
│   ├── achievements.json       ← Succès débloqués par joueur
│   ├── game_stats.json         ← Stats casino (gains, pertes, total misé)
│   ├── gangs.json              ← Gangs et membres
│   ├── marriages.json          ← Liens de mariage entre joueurs
│   ├── shop.json                ← Objets disponibles en boutique
│   ├── items_inventory.json    ← Inventaire d'objets spéciaux
│   ├── boxes_data.json         ← Pity system des caisses + jackpot
│   ├── scratch_data.json       ← Streaks tickets à gratter
│   ├── slots_data.json         ← Jackpot de la machine à sous
│   ├── business_data.json      ← Entreprises par joueur
│   ├── jail_data.json          ← Prisonniers actuels
│   ├── logs_config.json        ← Configuration des logs par serveur
│   ├── verification.json       ← Config vérification par serveur
│   ├── birthday_data.json      ← Anniversaires + config par serveur
│   ├── market_data.json        ← Marché joueur-à-joueur
│   ├── buffs_data.json         ← Bonus actifs par joueur
│   ├── cooldowns.json          ← Cooldowns persistants
│   ├── temp_roles.json         ← Rôles temporaires achetés en boutique et leur expiration
│   └── warnings.json           ← Avertissements de modération
├── main/
│   ├── Ulysse.py                ← Bootstrap : ajoute cogs/*/ au path, crée le bot, charge tout, lance
│   │
│   ├── core/                    ← État partagé, utilisé par tous les cogs
│   │   ├── __init__.py           ← Ré-exporte config+database+bot (import core fonctionne comme avant)
│   │   ├── config.py             ← Chemins des fichiers, RANKS, DAILY_CHALLENGES
│   │   ├── database.py           ← Chargement des données JSON + migration coins→pieces
│   │   └── bot.py                ← Instance bot, get_user_data, get_rank_name, get_display_user, add_xp, défis
│   │
│   ├── utils/                   ← Fonctions génériques réutilisables partout
│   │   ├── __init__.py           ← Ré-exporte helpers+permissions+embeds (from utils import X fonctionne comme avant)
│   │   ├── helpers.py            ← load/save JSON, SPECIAL_ITEMS, cooldowns persistants
│   │   ├── permissions.py        ← is_admin, ConfirmDangerView, ask_confirmation
│   │   └── embeds.py             ← Réservé aux futurs helpers d'embeds génériques (actuellement peu utilisé)
│   │
│   └── cogs/                    ← Un dossier par domaine
│       ├── profil/profil.py           ← /profil, /leaderboard
│       ├── economy/
│       │   ├── boutique.py             ← /boutique, /acheter, /balance, /inventaire
│       │   ├── economie.py             ← /donner, /pret
│       │   ├── quotidien.py            ← /quotidien, /defi
│       │   ├── business_system.py      ← /entreprise
│       │   ├── items_system.py         ← /objet_*, groupe /marche
│       │   ├── addictive_systems.py    ← tickets, caisses, missions
│       │   ├── temp_roles_system.py    ← rôles temporaires (achetés via /admin → Boutique)
│       │   └── economy_extensions.py   ← mariage, gang, succès, travailler/crime/braquage, duel
│       ├── casino/
│       │   ├── casino.py               ← /pile_ou_face, /des, /roulette, /roulette_sovietique, /blackjack
│       │   ├── slots_and_time.py       ← /machine_a_sous, /info_machine, /jackpot, /periode
│       │   ├── poker_system.py         ← /poker
│       │   └── horse_race.py           ← /course
│       ├── fun/fun.py                 ← groupe /fun + /rate
│       ├── paris/paris.py             ← /creer_pari, /parier, /fermer_pari, /paris
│       ├── admin/admin.py             ← /admin (panneau à boutons complet)
│       ├── moderation/
│       │   ├── moderation.py           ← /avertir, /expulser, /bannir, /isoler, /nettoyer...
│       │   └── jail_system.py          ← /emprisonner, /emprisonner_temporaire, /liberer
│       ├── verification/verification_system.py  ← groupe /verification
│       ├── logs/logs_system.py        ← groupe /journaux + événements de logs
│       ├── birthday/birthday_system.py ← groupe /anniversaire
│       └── events/events.py           ← on_ready, on_member_join, on_message, gestion d'erreur globale
│
├── .env                        ← Contient DISCORD_TOKEN (jamais commité)
├── COMMANDES.md                ← Liste complète de toutes les commandes
└── DOCUMENTATION.md            ← Ce fichier
```

### Comment les imports fonctionnent entre dossiers

Les fichiers dans `cogs/*/` s'importent entre eux de façon "plate" (`import core`,
`import items_system`, `from utils import ...`) exactement comme avant la mise en
dossiers — **aucun import interne n'a eu besoin d'être réécrit**. `Ulysse.py` ajoute
chaque sous-dossier de `cogs/` au chemin de recherche Python (`sys.path`) au tout début,
avant d'importer quoi que ce soit ; Python trouve donc chaque fichier peu importe dans
quel sous-dossier il se trouve. C'est un choix volontairement simple plutôt que des
imports relatifs de package (`from cogs.economy import items_system`), qui aurait demandé
de modifier chaque fichier déplacé.

### Le pattern `setup_xxx(bot, ...)`

Chaque cog expose une fonction `async def setup_xxx(bot, ...)` appelée depuis
`Ulysse.py::setup_hook()`. Cette fonction attache ses commandes à `bot.tree` directement
— pas de système de Cogs discord.py (classes `commands.Cog`) : un choix volontaire pour
rester simple et cohérent avec le style déjà en place, plutôt qu'une réécriture complète
en classes.

### `core/` — état partagé

`core/` centralise tout ce qui est utilisé par plusieurs domaines à la fois : les données
utilisateur (`core.users_data`), la boutique (`core.shop_items`), les fonctions
`get_user_data`, `get_rank_name`, `get_display_user`, `add_xp`, et la gestion des défis
quotidiens — réparti en 3 fichiers (`config.py`, `database.py`, `bot.py`) mais ré-exporté
intégralement par `core/__init__.py`, donc `import core` puis `core.xxx` fonctionne
exactement comme avec l'ancien `core.py` monolithique (avant la mise en dossiers). `core.bot` est rempli une seule
fois par `Ulysse.py` via `core.init_bot(bot)` au démarrage.

Les modules préexistants (`business_system.py`, `economy_extensions.py`, etc.) reçoivent
`core.users_data` en paramètre plutôt que de l'importer directement — c'est le même
dictionnaire (Python passe les objets mutables par référence), donc pas de risque de
désynchronisation entre `core/` et ces modules.

### `utils/` — fonctions génériques

Même principe que `core/` : `utils/` est réparti en `helpers.py` (JSON, items spéciaux,
cooldowns), `permissions.py` (vérification admin, confirmations d'actions destructives —
extrait de `cogs/admin/admin.py` où ça vivait avant, généralisé pour être réutilisable
ailleurs) et `embeds.py` (encore peu rempli — voir sa docstring). `utils/__init__.py`
ré-exporte tout, donc `from utils import load_data, SPECIAL_ITEMS, is_admin, ...`
fonctionne sans changement ailleurs dans le code.

---

## 🗣️ Renommage complet en français

Toutes les commandes ont été renommées en français, et la monnaie du bot s'appelle
**pièces** (au lieu de "coins") — aussi bien dans le code (clé `user_data["pieces"]`) que
dans tout le texte affiché. Une migration automatique s'exécute au premier démarrage du
bot pour convertir les anciens fichiers `users.json` (clé `coins` → `pieces`) sans perte
de données — un message `🔄 Migration : N profil(s) converti(s)` s'affiche dans la console
si c'est le cas.

Le nombre de commandes top-level est passé de **97 à 64** en regroupant les familles de
commandes liées sous un même préfixe (`/admin`, `/verification`, `/gang`, `/marche`,
`/journaux`, `/fun`) et en fusionnant les doublons (`/profil` = ex-`/rank`+`/stats`,
`/quotidien` = ex-`/daily`+`/streak`). Modération, Prison, Paris et Casino ont été
**renommés mais pas regroupés** (décision volontaire : commandes tapées très souvent, en
réflexe — un sous-menu ajouterait de la friction).

### `/admin` : panneau à boutons plutôt que groupe

Les groupes Discord (`app_commands.Group`, utilisés par `/verification`, `/gang`,
`/marche`, `/journaux`, `/fun`) affichent quand même **toutes leurs sous-commandes**
individuellement dans le menu `/` — Discord les déplie automatiquement pour la recherche.
Ça ne réduit donc pas le nombre de lignes visibles, juste leur organisation.

`/admin` a été converti en **commande unique** avec panneau interactif (boutons → menus
déroulants Discord → petits formulaires) pour qu'une seule ligne apparaisse dans le `/`.
Toute la logique métier (ajout/retrait de pièces, XP, stats, boutique) a été extraite en
fonctions réutilisables (`do_argent_ajouter`, `do_xp_ajouter`, etc. dans
`cogs/admin/admin.py`) appelées depuis les boutons.

---

## ⚙️ Paramètres techniques

### Cooldowns
| Commande | Cooldown | Stockage |
|---|---|---|
| `/travailler` | 1 heure | `cooldowns.json` ✅ persisté |
| `/crime` | 30 minutes | `cooldowns.json` ✅ persisté |
| `/braquage` | 2 heures | `cooldowns.json` ✅ persisté |
| `/course` | 2 minutes | `cooldowns.json` ✅ persisté |
| `/machine_a_sous` | 5 secondes | `cooldowns.json` ✅ — démarre à la fin du spin, pas à l'appel |
| `/quotidien` | 24h (reset minuit) | `daily.json` ✅ |

Persistés via `main/utils/helpers.py` (`check_cooldown`/`set_cooldown`) : survivent aux redémarrages.

### Probabilités des jeux
| Jeu | Chance de gagner | Notes |
|---|---|---|
| Pile ou face | 50% | Gain x2 |
| Blackjack | Variable | x2.5 si Blackjack naturel |
| Roulette russe | 80% survie | Pot x2 par round, max 5 rounds |
| Roulette soviétique | 16.7% | x2.5 si survie |
| Crime | 40% | Multiplicateur selon période |
| Braquage | 30% | Gains partagés entre l'équipe |
| Machine à sous | Variable | Selon symboles et poids |

### Système de pity des caisses
`boxes_data.json` : après un certain nombre d'ouvertures sans item rare, la probabilité
augmente automatiquement.

### Détection des soldes anormaux
`/admin` → 📊 Stats économie calcule la **médiane** des soldes (pas la moyenne, qui serait
elle-même faussée par un très gros solde isolé) et signale tout solde supérieur à 20x la
médiane.

### Rôles temporaires
`/admin` → 🛍️ Boutique → Rôle temporaire : le bot crée le rôle Discord automatiquement
s'il n'existe pas, l'attribue à l'achat, le retire après la durée choisie. Racheter avant
expiration **prolonge** le temps restant (additionne, ne reset pas). Le rôle est supprimé
du serveur quand plus personne ne l'a. Vérification toutes les 5 minutes
(`temp_roles.json`). Le bot doit avoir la permission "Gérer les rôles", avec son propre
rôle au-dessus du rôle temporaire dans la hiérarchie — sinon l'achat est remboursé.

### Permissions par sous-commande — limitation Discord
L'API Discord ne permet de régler les permissions par défaut qu'au niveau du **groupe
entier** (ex : `/verification`), pas sous-commande par sous-commande. Le code déclare
quand même chaque sous-commande avec son niveau de permission voulu, mais si des membres
non-admin accèdent à une sous-commande censée être restreinte, ajuste manuellement dans
**Paramètres du serveur → Intégrations**.

### Gestion d'erreur globale
Toute commande qui plante affiche un message clair adapté au type d'erreur (permissions
manquantes, cooldown, erreur inattendue...) au lieu du générique "L'application n'a pas
répondu". Les erreurs inattendues sont affichées en console avec la trace complète, et
envoyées automatiquement dans le salon configuré via `/journaux configurer`, si un serveur
en a un. Voir `cogs/events/events.py`.

### Redémarrage et synchronisation des commandes
Après un redémarrage, les commandes slash peuvent prendre jusqu'à **1 heure** pour se
synchroniser globalement sur Discord (souvent bien plus rapide en pratique). `Ulysse.py`
appelle `bot.tree.sync()` à chaque `on_ready()`, ce qui remplace intégralement la liste de
commandes globales par celle du code actuel — donc les anciens noms disparaissent
automatiquement avec le temps, sans action supplémentaire.

**Si d'anciennes commandes restent visibles après un renommage important :**
1. Redémarre complètement le client Discord (pas juste `Ctrl+R` — ferme et rouvre
   l'app), le client garde un cache local des commandes.
2. Si le bot a un jour été synchronisé sur un serveur spécifique (`bot.tree.sync(guild=...)`,
   pour des tests rapides), ces commandes propres au serveur ne sont **pas** effacées par
   un sync global. Utilise `clear_commands.py` (à la racine de `main/`) une seule fois :
   il vide les commandes globales ET celles de chaque serveur où le bot est présent, puis
   il faut relancer `Ulysse.py` normalement pour resynchroniser proprement. Supprime le
   script après usage.

Les données persistantes sont toutes dans `bot_data/` et survivent aux redémarrages,
cooldowns compris.

---

## 🐛 Historique des correctifs

### Passe de nettoyage initiale
| Problème | Solution appliquée |
|---|---|
| Token hardcodé dans `Ulysse.py` | Lu depuis `DISCORD_TOKEN` (`.env`). Le bot refuse de démarrer si absent. |
| `items_system` importé deux fois | Doublon supprimé. |
| Cooldowns perdus au redémarrage | Persistés dans `cooldowns.json`. |
| `SPECIAL_ITEMS` dupliqué dans 2 fichiers | Centralisé dans `utils/helpers.py`. |
| `business_system.py`, `horse_race.py`, `poker_system.py`, `jail_system.py` jamais branchés | Fichiers présents mais jamais importés/appelés — `/entreprise`, `/course`, `/poker`, `/emprisonner` n'existaient pas en pratique. Corrigé. |
| `/give` et `/pay` doublons stricts | Fusionnés dans `/donner` (paramètre `raison` optionnel). |
| 6 commandes de classement séparées | Fusionnées en `/leaderboard [categorie]`. |
| Docs désynchronisées (plusieurs fichiers redondants/obsolètes) | Fusionnées et régénérées depuis le code réel. |
| `/gang_disband` mentionné dans un message d'erreur alors qu'il n'a jamais existé | Message corrigé. |
| `/market_cancel` ne rendait qu'1 seul exemplaire au vendeur même si l'annonce en contenait plusieurs | Corrigé. |
| `/leaderboard` et consorts faisaient jusqu'à 10 appels API séquentiels (`bot.fetch_user`) | Nouvelle fonction `get_display_user()` : cache d'abord, API en dernier recours. |
| Détection d'anomalie économique basée sur la moyenne | Un seul très gros solde fausse la moyenne elle-même — recalculé sur la **médiane**, testé sur cas extrême et cas normal. |
| Aucune gestion d'erreur globale | Ajout de `on_app_command_error`. |
| Pas d'autocomplétion sur les noms d'items | Ajoutée sur 6 commandes. |
| Item inventaire décrit en dur une 3ᵉ fois dans `/inventaire` | Source unique désormais (`utils.SPECIAL_ITEMS` + `items_system.items_inventory`). |

### Regroupement, panneau admin & renommage FR
- **97 → 64 commandes**, tout en français ; groupes `/admin`, `/verification`, `/gang`,
  `/marche`, `/journaux`, `/fun` ; fusions `/profil`, `/quotidien` ; `coins` → `pieces`
  partout avec migration automatique.
- `/admin` converti d'un groupe à sous-commandes en **panneau à boutons** (une seule
  ligne dans le `/`, tout le reste en interface) après retour utilisateur montrant que
  les groupes Discord exposent quand même toutes leurs sous-commandes dans la liste.
- Nouvelles fonctionnalités : autocomplétion sur 6 commandes, `/admin` → Stats économie,
  confirmations par bouton sur les actions destructives, optimisation réseau du
  leaderboard.

### Tentative de système multilingue (annulée)
Un système `/config` + package `i18n/` (français/anglais, un domaine traduit comme preuve
de concept) a été construit puis retiré à la demande explicite : retour à un bot
uniquement en français. Le correctif de bug trouvé au passage (le footer de `/pret`
référençait encore l'ancien nom `/give` au lieu de `/donner`) a été conservé.

### Réorganisation en dossiers `cogs/`
- Passage d'une arborescence à plat (26 fichiers `.py` directement dans `main/`) à des
  dossiers par domaine (`cogs/economy/`, `cogs/casino/`, `cogs/moderation/`, etc.), plus
  `core/` et `utils/` éclatés en packages (`config.py`/`database.py`/`bot.py` et
  `helpers.py`/`permissions.py`/`embeds.py` respectivement).
- Compatibilité totale préservée : `core/__init__.py` et `utils/__init__.py`
  ré-exportent tout leur contenu, donc `import core` / `core.xxx` et
  `from utils import xxx` continuent de fonctionner sans qu'aucun fichier existant
  n'ait eu besoin d'être modifié pour ça.
- `Ulysse.py` ajoute chaque sous-dossier de `cogs/` au chemin Python (`sys.path`) au
  démarrage, donc les imports "plats" internes à chaque fichier (`import core`,
  `import items_system`...) fonctionnent sans réécriture — seuls les noms de fichiers
  déplacés (ex: `addon_admin.py` → `cogs/admin/admin.py`) et leur import dans
  `Ulysse.py` ont changé.
- `is_admin()`, `ConfirmDangerView` et `ask_confirmation()` (auparavant définis dans
  `addon_admin.py`) ont été généralisés et déplacés dans `utils/permissions.py`,
  réutilisables par n'importe quel autre cog à l'avenir.

### Refonte architecturale — addons par domaine
- `Ulysse.py` réduit de **2588 à 97 lignes** : ne contient plus que le bootstrap (création
  du bot, chargement des addons, lancement).
- Tout le reste réparti en cogs par domaine sous `cogs/` plus `core/` pour l'état
  partagé (voir la section Architecture plus haut pour le détail complet).
- `/verification` était coupé en deux (une partie dans `Ulysse.py`, une partie dans
  `verification_system.py`) — entièrement consolidé dans `verification_system.py`.
- Nettoyage des commentaires superflus dans tous les fichiers (ceux qui ne faisaient que
  répéter ce que la ligne suivante fait déjà) — gardés uniquement ceux expliquant une
  raison, un cas limite, ou un choix d'architecture non-évident.
- Toute la documentation `.md` fusionnée en 2 fichiers : `COMMANDES.md` (liste complète
  des commandes) et ce fichier (`DOCUMENTATION.md`).
- Un incident d'extraction (perte accidentelle d'un bloc de code lors d'un remplacement
  trop large) a été détecté immédiatement grâce aux tests systématiques après chaque
  étape, et corrigé par récupération depuis une sauvegarde intermédiaire — depuis, chaque
  extraction est suivie d'un test complet et d'un checkpoint avant de continuer.

**Encore ouvert (décision produit, pas du nettoyage) :**

| Sujet | Pourquoi ce n'est pas fait |
|---|---|

### Améliorations v8 — Rééquilibrage et stabilité

| Problème | Solution appliquée |
|---|---|
| Défis quotidiens impossibles à completer | Type "commands" jamais incrémenté — changé en "work_count" pour "Travailleur" (tracké dans `/travailler`). |
| Cooldown slots de 5s insuffisant | Augmenté à 10s pour réduire le spam. |
| Leaders de gang bloqués | Ajout de `/gang dissoudre` qui retourne la banque au leader et efface le gang. |
| Marché trop profond | `/marche parcourir` inaccessible directement — `/marche` ajouté comme commande directe. |
| Spam d'items en vente | Limite: max 3 types d'items différents simultanément par vendeur (quantités illimitées pour chacun). |
| Messages `/gang quitter` dépassés | Mis à jour pour pointer vers `/gang dissoudre`. |

**Encore ouvert (décision produit, pas du nettoyage) :**

| Sujet | Pourquoi ce n'est pas fait |
|---|---|
| `/defi` et `/missions` sont deux systèmes de défis/objectifs parallèles | Les fusionner change les récompenses et l'expérience joueur — décision côté produit. |
| Architecture JSON vs SQLite | Le bot self-hosté reste en JSON, choix assumé pour la simplicité de déploiement. Une architecture SQLite + API + dashboard web a été envisagée à un moment mais n'a jamais été branchée sur ce déploiement — si des traces de cette idée existent encore quelque part, elles sont obsolètes. |
| Fusion tickets/caisses | Deux mécaniques "pièces → item random" proches, mais gardées séparées à la demande explicite. |
