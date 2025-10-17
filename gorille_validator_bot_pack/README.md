# Gorille Validator Bot (Discord)

Bot de validation semi-automatique des rôles de guildes :
- Les joueurs réagissent dans `#rôles de guilde`
- Le bot crée une demande dans `#validation role guilde`
- Un **Gorille** réagit ✅ pour **approuver** (rôle attribué) ou ❌ pour **refuser**
- (Optionnel) Le rôle **En attente de validation** est ajouté/retiré automatiquement

## Déploiement rapide sur Railway (24/7)
1. Crée un compte sur https://railway.app et un **Nouveau Projet → Empty Service**.
2. Upload ces fichiers (ou connecte un dépôt Git).
3. Dans **Variables**, ajoute `DISCORD_TOKEN` avec le token de ton bot (Discord Developer Portal → Bot → Reset Token).
4. Dans **Deploy → Start Command**, mets : `python bot.py` (ou garde le `Procfile` : `worker: python bot.py`).
5. Clique **Deploy**. Le bot doit afficher `Connecté comme ...` dans les logs.

## Déploiement local (PC)
```
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
# Windows PowerShell (temporaire):
$env:DISCORD_TOKEN="TON_TOKEN_ICI"
# macOS/Linux:
export DISCORD_TOKEN="TON_TOKEN_ICI"

python bot.py
```

## À vérifier côté Discord
- Activer **Server Members Intent** dans le Developer Portal (onglet Bot)
- Inviter le bot avec permissions: Manage Roles, View Channels, Send Messages, Add Reactions, Embed Links, Read Message History
- Placer le **rôle du bot au-dessus** des rôles de guilde + "En attente de validation"
- Adapter si besoin les emojis et les IDs dans `EMOJI_TO_GUILD_ROLE`

Bonne jungle 🦍🍃
