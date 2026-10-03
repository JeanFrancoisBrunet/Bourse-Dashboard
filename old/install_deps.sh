#!/bin/bash
# Installation des dépendances pour le tableau de bord financier
# Jean-François - JFBConseils

echo "=== Installation des dépendances ==="
echo ""

# Mise à jour pip
python3 -m pip install --upgrade pip --break-system-packages

# Bibliothèques nécessaires
echo "→ Installation de yfinance (données CAC40)..."
pip3 install yfinance --break-system-packages

echo "→ Installation de requests (API CoinGecko)..."
pip3 install requests --break-system-packages

echo ""
echo "=== Dépendances installées ! ==="
echo ""
echo "Lancer le tableau de bord avec :"
echo "  python3 bourse_dashboard.py"
echo ""
echo "Pour lancer au démarrage, ajouter dans ~/.bashrc ou /etc/rc.local :"
echo "  DISPLAY=:0 python3 /home/jfbrunet/Projects/Bourse/bourse_dashboard.py &"
