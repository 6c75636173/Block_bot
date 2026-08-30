# 🤖 Toutes les commandes

> Toutes les commandes ci-dessous ont été extraites **directement du bot en exécution**
> (`bot.tree.get_commands()`), pas recopiées à la main — donc garanties synchrones avec le code.
> 64 commandes top-level (contre 97 avant le grand nettoyage), regroupées en sous-commandes
> là où ça avait du sens. La monnaie du bot s'appelle **pièces**.
>
> Pour l'architecture du code, la configuration technique et l'historique des correctifs,
> voir `DOCUMENTATION.md`.

---

## 📊 Profil & Classements

| Commande | Description |
|---|---|
| `/profil [@membre]` | Profil complet : niveau, XP, pièces, streak, défis, objets |
| `/leaderboard [categorie]` | Classement du serveur — choix : XP, Plus riches, Plus gros joueurs, Plus gros perdants, Business |
| `/balance` | Solde de pièces |
| `/inventaire` | Inventaire complet (objets boutique + items spéciaux) |

**Rangs disponibles :**

| Niveau requis | Rang |
|---|---|
| 1 | Débutant |
| 5 | Membre Actif |
| 10 | Vétéran |
| 15 | Expert |
| 20 | Légende |
| 30 | Maître |

> Chaque message envoyé rapporte **15 XP**. Chaque level up donne **+50 pièces**.

---

## 🛒 Boutique

| Commande | Description |
|---|---|
| `/boutique` | Menu à boutons : 🛍️ Acheter, 🏪 Marché, 🎒 Inventaire |
| `/acheter [item]` | Acheter directement un objet (autocomplétion sur les items disponibles) |

---

## 🛡️ Modération
> *Nécessite des permissions modérateur/admin*

| Commande | Description |
|---|---|
| `/avertir [@membre] [raison]` | Avertir un membre |
| `/avertissements [@membre]` | Voir les avertissements d'un membre |
| `/effacer_avertissements [@membre]` | Effacer tous les avertissements (admin) |
| `/expulser [@membre] [raison]` | Expulser un membre |
| `/bannir [@membre] [raison]` | Bannir un membre |
| `/isoler [@membre] [durée] [raison]` | Isoler un membre (timeout Discord, max 28 jours) |
| `/nettoyer [nombre]` | Supprimer des messages (max 100) |

---

## 🔒 Prison (Admin)

| Commande | Description |
|---|---|
| `/emprisonner [@membre] [raison]` | Emprisonne un membre de façon permanente |
| `/emprisonner_temporaire [@membre] [durée_min] [raison]` | Prison temporaire (1 min → 7 jours) |
| `/liberer [@membre]` | Libère un prisonnier manuellement |

Crée automatiquement le rôle `🔒 Prison` et le salon `#prison` si absents. Anciens rôles
restaurés à la libération. Vérification des libérations automatiques toutes les 60 secondes.

---

## 🎰 Casino

| Commande | Description |
|---|---|
| `/pile_ou_face [mise] [pile/face]` | Pile ou face — 50/50, gain x2 (mise min. 10) |
| `/blackjack [mise]` | Blackjack contre le bot (mise min. 50, x2.5 si blackjack naturel) |
| `/roulette [mise]` | Roulette russe — 1 chance sur 5 de mourir, pot x2 par round (mise max 100) |
| `/roulette_sovietique [mise]` | 5 chances sur 6 de mourir, x2.5 si survie (mise max 1000) |
| `/machine_a_sous [mise]` | Machine à sous avec jackpot progressif (cooldown 10s après la fin du spin) |
| `/info_machine` | Infos sur les symboles de la machine à sous |
| `/des [nombre] [faces]` | Lancer des dés (1-10 dés, 4/6/8/12/20 faces) |
| `/poker [@adversaire] [mise]` | Poker Texas Hold'em 1v1 (buy-in 10-1000) |
| `/course [cheval] [mise]` | Course de chevaux (10-1000 pièces, cooldown 2min) |

**Chevaux disponibles :**

| Cheval | Vitesse | Multiplicateur si victoire |
|---|---|---|
| 🐎 Thunder | 1–3 | x2.5 |
| 🏇 Lightning | 1–4 | x3.0 |
| 🐴 Spirit | 2–3 | x2.0 |
| 🦄 Mystique | 1–5 | x4.0 |
| 🎠 Carousel | 2 fixe | x1.5 |

---

## 🎮 Fun (`/fun ...`)

| Sous-commande | Description |
|---|---|
| `/fun gifler [@membre]` | Gifle quelqu'un (virtuellement) |
| `/fun calin [@membre]` | Câlin |
| `/fun clasher [@membre]` | Insulte gentiment quelqu'un |
| `/fun boule_magique [question]` | Boule magique |
| `/fun pp [@membre]` | Mesure le pp (déterministe par ID) |
| `/fun shipper [@p1] [@p2]` | Compatibilité entre deux personnes |
| `/fun duel [@membre] [mise]` | Duel pierre-papier-ciseaux avec mise (min. 10 pièces) |

**Hors groupe :**

| Commande | Description |
|---|---|
| `/rate [chose]` | Note quelque chose sur 10 |

---

## 💑 Mariage

| Commande | Description |
|---|---|
| `/epouser [@membre]` | Demander quelqu'un en mariage |
| `/divorce` | Divorcer de son partenaire |
| `/partenaire [@membre]` | Voir le partenaire d'un membre |

---

## 👑 Gang (`/gang ...`)

| Sous-commande | Description |
|---|---|
| `/gang creer [nom]` | Créer un gang (coût : 1000 pièces) |
| `/gang inviter [@membre]` | Inviter un membre (leader uniquement) |
| `/gang deposer [montant]` | Déposer dans la banque du gang |
| `/gang retirer [montant]` | Retirer de la banque (leader uniquement) |
| `/gang info` | Infos du gang |
| `/gang quitter` | Quitter son gang (membres uniquement) |
| `/gang dissoudre` | Dissoudre le gang (leader uniquement) — retourne la banque au leader |

---

## 💼 Travail, Crime & Entreprise

| Commande | Description | Cooldown |
|---|---|---|
| `/travailler` | Gagner des pièces | 1 heure |
| `/crime` | Crime risqué (40% de succès) | 30 minutes |
| `/braquage [@complice1] [@complice2]` | Braquage en équipe (30% de succès, gains partagés) | 2 heures |
| `/entreprise` | Boutique + gestion de ton entreprise (boutons Réclamer/Améliorer/Vendre) | — |

**Types d'entreprise (revenus passifs, max 24h en attente) :**

| Entreprise | Prix | Revenu niveau 1 | Niveau max |
|---|---|---|---|
| 🍕 Pizzeria | 5 000 pièces | 50 pièces/h | 10 |
| 🎰 Mini Casino | 15 000 pièces | 150 pièces/h | 10 |
| 🎵 Boîte de Nuit | 25 000 pièces | 250 pièces/h | 10 |
| 💻 Ferme Crypto | 50 000 pièces | 400 pièces/h | 10 |
| 🏰 Empire Commercial | 100 000 pièces | 800 pièces/h | 10 |

> La vente d'une entreprise rembourse 50% de l'investissement total.
> Classement disponible via `/leaderboard business`.

---

## 🎯 Missions

| Commande | Description |
|---|---|
| `/missions` | Missions quotidiennes et hebdomadaires |
| `/recuperer_mission [mission_id] [type]` | Réclamer une récompense de mission complétée (type: daily ou weekly) |

**Types de missions quotidiennes :**
- 💬 Bavard — Envoie 50 messages → 500 pièces
- 🎲 Chanceux — Gagne 3 parties de pile ou face → 300 pièces
- 👷 Travailleur — Travaille 10 fois → 200 pièces
- 💸 Dépensier — Dépense 500 pièces → 600 pièces
- 🎰 Joueur — Joue 5 fois au casino → 400 pièces
- 📈 Progresser — Monte d'un niveau → 1000 pièces

---

## 🎟️ Tickets, Caisses, Objets & Craft

| Commande | Description |
|---|---|
| `/ticket_acheter [type]` | Acheter un ticket à gratter |
| `/tickets` | Voir les types de tickets disponibles et gratter les tiens |
| `/caisse_acheter [type]` | Acheter une caisse |
| `/caisses` | Voir/ouvrir tes caisses |
| `/objet_vendre [item]` | Vendre un objet (80% de sa valeur, autocomplétion) |
| `/objet_utiliser [item]` | Activer le bonus d'un objet (autocomplétion) |
| `/objet_offrir [@membre] [item]` | Offrir un objet (autocomplétion) |
| `/objet_fusionner [item1] [item2]` | Fusionner deux objets (autocomplétion sur les deux) |
| `/bonus` | Voir ses bonus actifs |
| `/fabriquer` | Voir les recettes de craft |

**Types de tickets :**

| Ticket | Prix | Description |
|---|---|---|
| 💎 Triple Match | 10 pièces | Grille 3x3, trouve 3 symboles identiques |
| 🍀 Lucky 7 | 25 pièces | Grille 2x3, trouve des 7 |
| 💰 Jackpot | 50 pièces | Grille 3x3, aligne des montants |
| 👑 Royal Scratch | 100 pièces | Grille 3x3, symboles royaux |

**Recettes de craft :**

| Résultat | Ingrédients | Effet |
|---|---|---|
| 🌈 Épée Diamantée | 💎 Diamant Éternel + ⚔️ Épée Légendaire | +25% tous gains (2h) |
| 🔥 Orbe Enflammé | 🔮 Orbe de Cristal + 🌟 Étoile Filante | x2 gains casino (1h) |
| 🎭👑 Masque Royal | 🎭 Masque Mystérieux + 👑 Couronne Dorée | +35% tous gains (1h30) |

---

## 🏪 Marché entre joueurs

**Commande directe :**

| Commande | Description |
|---|---|
| `/marche` | Voir tous les items en vente sur le marché |

**Sous-commandes du groupe `/marche` :**

| Sous-commande | Description |
|---|---|
| `/marche vendre [item] [prix] [quantite]` | Mettre en vente (prix par unité, autocomplétion, quantité par défaut : 1) |
| `/marche acheter [listing_id] [quantite]` | Acheter (total ou partiel) |
| `/marche offrir [@membre] [item] [prix]` | Offre directe à un joueur |
| `/marche annuler [listing_id]` | Retirer son annonce (rend toute la quantité restante) |

> **Limite :** Une seule annonce par item par vendeur, maximum **3 types d'items différents** en vente simultanément par joueur.
> Accessible aussi via `/boutique` → bouton 🏪, avec des formulaires à remplir.

---

## 🎲 Paris

| Commande | Description |
|---|---|
| `/creer_pari [question] [option1] [option2]` | Créer un pari |
| `/parier [id] [option] [montant]` | Parier sur un résultat |
| `/fermer_pari [id] [gagnant]` | Fermer le pari et distribuer les gains (créateur uniquement) |
| `/paris` | Voir les paris actifs |

---

## 💰 Économie de base

| Commande | Description |
|---|---|
| `/donner [@membre] [montant] [raison]` | Donner des pièces (min. 10, raison optionnelle) |
| `/pret [@membre] [montant] [intérêt%]` | Proposer un prêt (défaut 20%) — rembourse ensuite avec `/donner` |
| `/echanger [@membre] [objet]` | Proposer un échange d'objet |

---

## ⏰ Quotidien & Cycle jour/nuit

| Commande | Description |
|---|---|
| `/quotidien [@membre]` | Réclame la récompense du jour, ou consulte le streak (le tien ou celui d'un membre si déjà réclamé / si @membre précisé) |
| `/periode` | Période actuelle et bonus en cours |

**Récompense quotidienne :** base 100 pièces + bonus streak (+50/jour, max +500) + bonus
semaine tous les 7 jours (+1000 pièces).

| Période | Horaires | Bonus |
|---|---|---|
| 🌅 Aube | 6h–8h | Machine à sous +25%, Tickets -10% |
| ☀️ Jour | 8h–18h | Travail +30% |
| 🌆 Crépuscule | 18h–20h | Machine à sous +50%, Tickets -15% |
| 🌙 Nuit | 20h–6h | Crime +50% |

---

## 🏆 Succès

| Commande | Description |
|---|---|
| `/succes [@membre]` | Voir les succès débloqués (12 au total) |

| Succès | Condition | Récompense |
|---|---|---|
| 🩸 First Blood | Perds tes premiers 100 pièces au casino | 50 pièces |
| 🎰 Gambler | Joue 100 parties au casino | 500 pièces |
| 💎 High Roller | Mise 10 000 pièces en une partie | 1 000 pièces |
| 🍀 Lucky Streak | Gagne 10 parties d'affilée | 2 000 pièces |
| 💸 Broke | Tombe à 0 pièce | 100 pièces |
| 💰 Millionaire | Atteins 10 000 pièces | 500 pièces |
| 💑 Married | Marie-toi avec quelqu'un | 300 pièces |
| 💔 Divorced | Divorce | 100 pièces |
| 👑 Gang Leader | Crée un gang | 500 pièces |
| 👷 Worker | Travaille 50 fois | 1 000 pièces |
| 🔫 Criminal | Commets 20 crimes | 800 pièces |
| 🏦 Heist Master | Réussis 10 braquages | 1 500 pièces |

---

## 🛡️ Vérification anti-raid (`/verification ...`)

| Sous-commande | Description | Permissions |
|---|---|---|
| `/verification configurer` | Configurer le système | Admin |
| `/verification desactiver` | Désactiver | Admin |
| `/verification verifier [code]` | Se vérifier avec le code du captcha | Tous |
| `/verification nouveau_captcha` | Demander un nouveau captcha | Tous |
| `/verification verifier_membre [@membre]` | Vérifier manuellement | Modérateur |
| `/verification info` | Voir la config actuelle | Tous |

Captcha visuel dans le salon configuré, expire après 10 minutes.

> ⚠️ Discord ne permet pas de restreindre finement les permissions par sous-commande via
> l'intégration native — si des membres non-admin accèdent à `configurer`/`desactiver`/
> `verifier_membre`, vérifie manuellement les permissions du groupe dans Paramètres du
> serveur → Intégrations.

---

## 📋 Logs (`/journaux ...`, Admin)

| Sous-commande | Description |
|---|---|
| `/journaux configurer [#salon]` | Choisir le salon de logs |
| `/journaux evenements` | Activer/désactiver les événements loggés (menu à boutons) |
| `/journaux desactiver` | Tout désactiver |
| `/journaux info` | Voir la configuration actuelle |

Un salon de logs configuré reçoit aussi automatiquement les erreurs de commandes inattendues.

---

## 🎂 Anniversaires (`/anniversaire ...`)

| Sous-commande | Description |
|---|---|
| `/anniversaire definir [jour] [mois]` | Enregistrer son anniversaire |
| `/anniversaire supprimer` | Supprimer son anniversaire |
| `/anniversaire voir [@membre]` | Voir l'anniversaire d'un membre |
| `/anniversaire liste` | Prochains anniversaires du serveur |
| `/anniversaire configurer_salon [#salon]` | (Admin) Salon d'annonces |
| `/anniversaire configurer_role [@role]` | (Admin) Rôle temporaire du jour J |

Le jour J : +500 pièces automatiques + annonce dans le salon configuré (une fois par an).

---

## ⚙️ Administration — `/admin` (panneau à boutons)

`/admin` est une **commande unique** (pas un groupe) : tape `/admin`, un panneau interactif
s'ouvre avec 5 boutons. Aucune sous-commande n'apparaît dans le `/` — tout se passe via
menus déroulants Discord et petits formulaires.

| Bouton du panneau | Ce qu'il ouvre |
|---|---|
| 💰 **Pièces** | Sous-menu : Ajouter / Retirer / Définir / Réinitialiser → choix du membre (menu déroulant) puis montant (formulaire) |
| ⭐ **XP** | Choix du membre puis montant d'XP à ajouter |
| 🔍 **Voir un membre** | Choix du membre → affiche solde, XP, niveau, inventaire |
| 📊 **Stats économie** | Vue d'ensemble : total en circulation, moyenne, top 5, détection de soldes anormaux (basée sur la médiane) |
| 🛍️ **Boutique** | Sous-menu : Rôle temporaire / Stock limité / Retirer un item → formulaires dédiés |

**Confirmations** : Retirer des pièces, Définir un solde, Réinitialiser, et Retirer un item
de boutique affichent un message ✅/❌ avant d'agir (30s, seul l'auteur peut confirmer).

**Rôles temporaires** (bouton 🛍️ Boutique → Rôle temporaire) : le bot crée le rôle Discord
automatiquement s'il n'existe pas, l'attribue à l'achat, et le retire après la durée
choisie. Racheter avant expiration **prolonge** le temps restant (additionne, ne reset
pas). Quand plus personne ne l'a, le rôle est supprimé du serveur.

---

*Doc régénérée directement depuis `bot.tree.get_commands()` — plus jamais désynchronisée à la main.*
