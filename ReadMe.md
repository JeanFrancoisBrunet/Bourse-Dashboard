# Bourse Dashboard

Tableau de bord boursier temps réel pour Raspberry Pi 5 (CAC 40, Mid-Cap, S&P 500, NASDAQ 100, Cryptomonnaies), accompagné d'un **bot Telegram** pour le suivi et les alertes à distance.

Deux composants indépendants, partageant le même univers de valeurs :
- **`bourse_dashboard.py`** — application graphique Tkinter (écran fixe / affichage type dashboard).
- **`telegram_bot_bourse.py`** — bot Telegram pour consulter les cours, gérer une liste de suivi et recevoir des alertes de seuil, où que l'on soit.
- **`Market_dataset.xlsx`** — fichier de référence recensant les valeurs CAC 40 et S&P 500 (tickers, secteurs, dates d'ajout…), utilisé comme base pour maintenir les listes de valeurs codées dans les deux scripts.
- **`config.json`** — sélection courante des valeurs suivies et des graphiques affichés (généré/modifié automatiquement par l'application graphique).

## Bourse Dashboard (`bourse_dashboard.py`)
Application Tkinter plein écran organisée en onglets :
- **📈 Cours en direct** — CAC 40 (sélection personnalisable), Mid-Cap (LISI) et Cryptomonnaies, avec cours, variation et couleur selon la tendance.
- **🇺🇸 Valeurs US** — S&P 500 et NASDAQ 100, avec sélection personnalisable des valeurs affichées.
- **📊 Analyse Graphique** — 4 emplacements de graphiques historiques configurables (valeur + période parmi 1 semaine à 2 ans), tracés avec Matplotlib.

Fonctionnalités :
- Rafraîchissement automatique des cours toutes les 60 secondes.
- Récupération des cours actions via **yfinance** et des cryptomonnaies via l'**API CoinGecko**, en parallèle (`ThreadPoolExecutor`) pour ne pas bloquer l'interface.
- Fenêtres de sélection dédiées pour choisir les valeurs CAC 40 et US à afficher (cases à cocher, recherche visuelle par colonnes).
- Sauvegarde automatique de la sélection et des graphiques dans `config.json`.
- Écran de démarrage (splash screen).

Lancement :
```bash
python3 bourse_dashboard.py
```

Dépendances :
```bash
pip install yfinance requests pillow matplotlib --break-system-packages
```

## Bot Telegram (`telegram_bot_bourse.py`)
Bot Telegram (`@bourse_pi5_bot`) permettant de suivre une sélection de valeurs (CAC 40, S&P 500, NASDAQ 100, Mid-Cap, Cryptos) et de recevoir des alertes de franchissement de seuil, indépendamment du dashboard graphique.

Commandes disponibles :

| Commande                                  | Description                                                  |
|---                                        |---                                                           |
| `/suivi`                                  | Affiche la liste des valeurs suivies avec cours et variation |
| `/cours NOM`                              | Cours actuel d'une valeur + graphique intraday               |
| `/ajouter NOM`                            | Ajoute une valeur à la liste de suivi                        |
| `/retirer NOM`                            | Retire une valeur de la liste de suivi                       |
| `/liste CAC40\SP500\NASDAQ\CRYPTO\MIDCAP` | Liste les valeurs disponibles par catégorie                  |
| `/top`                                    | Meilleures et pires variations du moment                     |
| `/alerte NOM BAS HAUT`                    | Définit un seuil bas/haut pour une valeur                    |
| `/alerte NOM`                             | Consulte l'alerte définie pour une valeur                    |
| `/alerte NOM supprimer`                   | Supprime l'alerte d'une valeur                               |
| `/alertes`                                | Liste toutes les alertes actives                             |
| `/refresh`                                | Force un rafraîchissement immédiat des cours                 |
| `/aide`                                   | Mémo des commandes                                           |

Fonctionnement :
- Boucle de fond (`_background_loop`) qui récupère les cours toutes les 5 minutes et déclenche les notifications d'alerte en cas de franchissement de seuil.
- Message de démarrage automatique envoyé au chat configuré (avec vérification de la synchronisation NTP).
- Bot restreint à un seul `chat_id` autorisé (si configuré) — toute autre conversation est ignorée.
- État persistant (liste de suivi + alertes) sauvegardé dans `bourse_bot_state.json`.
- Journalisation avec rotation automatique (`bourse_bot.log`, 2 Mo max, 1 sauvegarde).

Lancement :
```bash
python3 telegram_bot_bourse.py
```

Dépendances :
```bash
pip install python-telegram-bot yfinance requests matplotlib --break-system-packages
```

### Configuration du bot
Créer le fichier caché `~/.telegram_config` :
```ini
[telegram]
token_bourse = VOTRE_TOKEN
chat_id      = VOTRE_CHAT_ID
```

## Sources de données
- **yfinance** — cours et historiques pour les actions (CAC 40, Mid-Cap, S&P 500, NASDAQ 100) et les cryptomonnaies via les paires `-EUR` (ex. `BTC-EUR`).
- **API CoinGecko** — cours et variation 24h des cryptomonnaies dans le dashboard graphique.

## Structure du dépôt
```
Bourse_Dashboard/
├── bourse_dashboard.py       # Application graphique Tkinter (dashboard)
├── telegram_bot_bourse.py    # Bot Telegram (suivi + alertes)
├── config.json               # Sélection courante (valeurs suivies, graphiques)
├── Market_dataset.xlsx       # Référentiel des valeurs CAC40 / S&P500 (tickers, secteurs...)
└── icons/                    # Images utilisées par l'interface graphique (non incluses ici)
```
> Le fichier `~/.telegram_config` (token et chat_id) ainsi que les fichiers d'état générés à l'exécution (`bourse_bot_state.json`, `bourse_bot.log`) sont propres à chaque installation et ne doivent pas être versionnés.

## Prérequis
- Python 3.11+
- Connexion Internet (accès à Yahoo Finance et à l'API CoinGecko)
- Pour le dashboard : `python3-tk`

## Auteur
Jean-François BRUNET - JFBConseils - Juillet 2026
