# 🤖 Block Bot

> Un bot Discord **complet, modulaire, open source et totalement gratuit**, développé en Python et amélioré progressivement, module après module.

## 📌 À propos du projet

Ce projet a pour objectif de créer un **bot Discord complet et polyvalent**, capable de répondre aux besoins de différents types de serveurs Discord.

Le projet sera développé de manière progressive : plutôt que d'essayer de tout créer dès le départ, le bot sera construit **module par module**.

### 🎯 Les objectifs

* 🧩 Architecture **modulaire**
* 🚀 Ajout régulier de nouvelles fonctionnalités
* 🛠️ Code propre et facilement maintenable
* 🔧 Configuration simple
* 🌐 Destiné à différents types de serveurs Discord

---

## 🧩 Un développement module par module

Le principe du projet est simple : **chaque fonctionnalité importante sera développée sous forme de module indépendant**.

Cela permettra d'ajouter, modifier ou supprimer une fonctionnalité sans devoir modifier l'ensemble du bot.

Par exemple :

```text
Block_Bot
│
├── 🛡️ Modération
├── 🎫 Tickets
├── 👋 Bienvenue
├── 📊 Statistiques
├── 🎮 Fun
├── 🎵 Musique
├── 🔒 Sécurité
├── 🎁 Giveaways
├── 💰 Économie
├── ⭐ Niveaux / XP
├── 📢 Logs
├── ⚙️ Administration
└── ... etc
```

Cette liste n'est pas représentative ni définitive. 

---

## 🛠️ Technologies

Le projet sera principalement basé sur :

* **Python**
* **Discord API**
* **discord.py**
* **SQLite / base de données** selon les besoins
* **Git & GitHub** pour le développement et le suivi du projet

---

## 📂 Architecture prévue

```text
discord-bot/
│
├── cogs/
│   ├── moderation/
│   ├── tickets/
│   ├── welcome/
│   ├── fun/
│   ├── economy/
│   └── ...
│
├── core/
│   ├── bot.py
│   ├── config.py
│   └── database.py
│
├── utils/
│   ├── permissions.py
│   ├── embeds.py
│   └── helpers.py
│
├── data/
│
├── .env.example
├── requirements.txt
├── main.py
└── README.md
```

L'idée est que chaque module puisse être développé et maintenu de manière indépendante.

---

## 📈 Roadmap

Le projet étant développé progressivement, les fonctionnalités seront ajoutées au fur et à mesure.

### 🛡️ Modération

* [ ] Kick
* [ ] Ban
* [ ] Timeout
* [ ] Warn
* [ ] Clear messages
* [ ] Gestion automatique des sanctions
* [ ] Système de logs
* [ ] Système de prison

### 👋 Gestion du serveur

* [ ] Message de bienvenue
* [ ] Message de départ
* [ ] Auto-rôles
* [ ] Configuration personnalisable
* [ ] Commandes d'administration

### 🎫 Tickets

* [ ] Création de tickets
* [ ] Fermeture de tickets
* [ ] Catégories personnalisables
* [ ] Logs des tickets
* [ ] Gestion des permissions

### 🎮 Fun

* [ ] Commandes amusantes
* [ ] Mini-jeux
* [ ] Système de classement
* [ ] Commandes communautaires
* [ ] Système de casino

### 💰 Économie

* [ ] Monnaie virtuelle
* [ ] Récompenses quotidiennes
* [ ] Boutique / marché d'occasion
* [ ] Inventaire
* [ ] Classements / rank

### ⭐ Système XP

* [ ] XP basé sur l'activité
* [ ] Niveaux
* [ ] Récompenses
* [ ] Classement des membres

### 🔒 Sécurité

* [ ] Anti-spam
* [ ] Anti-raid
* [ ] Anti-link
* [ ] Détection d'activités suspectes
* [ ] Protection configurable

> Cette liste est évolutive et non définitive, elle est amenée a évoluer.

---

La roadmap pourra évidemment être modifiée en fonction des besoins et des exigences requises.

---

## 💙 Merci

Merci d'être rester jusqu'ici et d'avoir lu ^^.
