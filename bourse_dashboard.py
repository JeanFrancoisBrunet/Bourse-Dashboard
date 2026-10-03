#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  Tableau de bord Boursier — CAC 40 · Mid-Cap · Cryptomonnaies · Graphiques
#  Raspberry Pi 5 (16 Go RAM, SSD NVMe 256 Go, OS Bookworm)
#  Utilise : yfinance (CAC40 & Mid-Cap) + CoinGecko API (Crypto)
#
#  Dépendances : pip install yfinance requests pillow matplotlib
#
#  Auteur : Jean-François BRUNET – JFBConseils – Juin 2026
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import yfinance as yf
from datetime import datetime
import time
import os
import json

import warnings
import matplotlib
matplotlib.use("TkAgg")
# Supprime le warning Axes3D causé par la double installation matplotlib
# (paquet système + pip) sur Raspberry Pi OS Bookworm
warnings.filterwarnings(
    "ignore",
    message="Unable to import Axes3D",
    category=UserWarning,
    module="matplotlib",
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

# ─── CONFIGURATION ───

REFRESH_INTERVAL          = 60
SPLASH_DURATION_MS        = 3000
YF_TIMEOUT                = 15
YF_HISTORY_TIMEOUT        = 20
COINGECKO_TIMEOUT         = 10
COINGECKO_RATELIMIT_RETRY = 2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPLASH_IMG  = os.path.join(SCRIPT_DIR, "icons", "bourse.png")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

# Périodes disponibles pour les graphiques historiques
CHART_PERIODS = {
    "1 sem":  "5d",
    "1 mois": "1mo",
    "3 mois": "3mo",
    "6 mois": "6mo",
    "1 an":   "1y",
    "2 ans":  "2y",
}

# ─── DONNÉES ───

CAC40_ALL = {
    "Accor":                 "AC.PA",
    "Air Liquide":           "AI.PA",
    "Airbus":                "AIR.PA",
    "Atos":                  "ATO.PA",
    "AXA":                   "CS.PA",
    "BNP Paribas":           "BNP.PA",
    "Bouygues":              "EN.PA",
    "Bureau Veritas":        "BVI.PA",
    "Capgemini":             "CAP.PA",
    "Carrefour":             "CA.PA",
    "Crédit Agricole":       "ACA.PA",
    "Danone":                "BN.PA",
    "Dassault Systèmes":     "DSY.PA",
    "Eiffage":               "FGR.PA",
    "Engie":                 "ENGI.PA",
    "EssilorLuxottica":      "EL.PA",
    "Eurofins Scientific":   "ERF.PA",
    "Euronext":              "ENX.PA",
    "Hermès":                "RMS.PA",
    "Kering":                "KER.PA",
    "L'Oréal":               "OR.PA",
    "LVMH":                  "MC.PA",
    "Legrand":               "LR.PA",
    "Michelin":              "ML.PA",
    "Orange":                "ORA.PA",
    "Pernod Ricard":         "RI.PA",
    "Publicis":              "PUB.PA",
    "Renault":               "RNO.PA",
    "Safran":                "SAF.PA",
    "Saint-Gobain":          "SGO.PA",
    "Sanofi":                "SAN.PA",
    "Schneider Electric":    "SU.PA",
    "Société Générale":      "GLE.PA",
    "Teleperformance":       "TEP.PA",
    "Thales":                "HO.PA",
    "TotalEnergies":         "TTE.PA",
    "Unibail-Rodamco":       "URW.PA",
    "Veolia":                "VIE.PA",
    "Vinci":                 "DG.PA",
    "Worldline":             "WLN.PA",
}
#   "STMicroelectronics":    "STM.PA",
#   "Arcelor Mittal":        "MT.PA",

CAC40_DEFAULT_SELECTION = {
    "LVMH", "TotalEnergies", "Sanofi", "BNP Paribas", "Airbus",
    "L'Oréal", "Hermès", "Schneider Electric", "Vinci", "Société Générale",
    "AXA", "Safran", "Air Liquide", "Danone", "Renault",
}

MIDCAP_SYMBOLS = {"LISI": "FII.PA"}

# ─── S&P 500 ───
SP500_SYMBOLS = {
    "3M":                        "MMM",
    "Abbott Laboratories":       "ABT",
    "AbbVie":                    "ABBV",
    "Accenture":                 "ACN",
    "Adobe":                     "ADBE",
    "Airbnb":                    "ABNB",
    "Alphabet":                  "GOOGL",
    "Altria":                    "MO",
    "Amazon":                    "AMZN",
    "Amcor":                     "AMCR",
    "AMD":                       "AMD",
    "American Express":          "AXP",
    "Amgen":                     "AMGN",
    "Apple":                     "AAPL",
    "AT&T":                      "T",
    "Autodesk":                  "ADSK",
    "Baker Hughes":              "BKR",
    "Bank of America":           "BAC",
    "Baxter International":      "BAX",
    "Berkshire Hathaway":        "BRK-B",
    "BlackRock":                 "BLK",
    "Blackstone":                "BX",
    "Boeing":                    "BA",
    "Boston Scientific":         "BSX",
    "Bristol Myers Squibb":      "BMY",
    "Broadcom":                  "AVGO",
    "Carrier Global":            "CARR",
    "Caterpillar":               "CAT",
    "Charles River Labo.":       "CRL",
    "Charles Schwab":            "SCHW",
    "Chevron":                   "CVX",
    "Cisco":                     "CSCO",
    "Citigroup":                 "C",
    "Coca-Cola":                 "KO",
    "Danaher":                   "DHR",
    "Deere":                     "DE",
    "Dell Technologies":         "DELL",
    "Delta Air Lines":           "DAL",
    "DuPont":                    "DD",
    "eBay":                      "EBAY",
    "Ecolab":                    "ECL",
    "ExxonMobil":                "XOM",
    "FedEx":                     "FDX",
    "Ford Motor":                "F",
    "Fox Corp.":                 "FOXA",
    "Garmin":                    "GRMN",
    "GE HealthCare":             "GEHC",
    "General Electric":          "GE",
    "General Motors":            "GM",
    "Goldman Sachs":             "GS",
    "Hasbro":                    "HAS",
    "Hewlett Packard":           "HPE",
    "Hilton Worldwide":          "HLT",
    "Home Depot":                "HD",
    "Honeywell":                 "HON",
    "Howmet Aerospace":          "HWM",
    "HP Inc.":                   "HPQ",
    "IBM":                       "IBM",
    "Ingersoll Rand":            "IR",
    "Intel":                     "INTC",
    "Johnson & Johnson":         "JNJ",
    "Johnson Controls":          "JCI",
    "JPMorgan Chase":            "JPM",
    "Lilly (Eli)":               "LLY",
    "Linde":                     "LIN",
    "Lockheed Martin":           "LMT",
    "Lowe's":                    "LOW",
    "M&T Bank":                  "MTB",
    "Marriott International":    "MAR",
    "Mastercard":                "MA",
    "McDonald's":                "MCD",
    "Medtronic":                 "MDT",
    "Merck & Co.":               "MRK",
    "Meta Platforms":            "META",
    "MGM Resorts":               "MGM",
    "Microsoft":                 "MSFT",
    "Moody's":                   "MCO",
    "Morgan Stanley":            "MS",
    "Motorola Solutions":        "MSI",
    "Nasdaq Inc.":               "NDAQ",
    "Netflix":                   "NFLX",
    "NextEra Energy":            "NEE",
    "Nike":                      "NKE",
    "NVIDIA":                    "NVDA",
    "NXP Semiconductors":        "NXPI",
    "Oracle":                    "ORCL",
    "Palo Alto Networks":        "PANW",
    "Paramount Skydance":        "PSKY",
    "PayPal":                    "PYPL",
    "PepsiCo":                   "PEP",
    "Pfizer":                    "PFE",
    "Philip Morris":             "PM",
    "Procter & Gamble":          "PG",
    "Prologis":                  "PLD",
    "PTC Inc.":                  "PTC",
    "Qualcomm":                  "QCOM",
    "Ralph Lauren":              "RL",
    "Rockwell Automation":       "ROK",
    "RTX":                       "RTX",
    "S&P Global":                "SPGI",
    "Salesforce":                "CRM",
    "Sandisk":                   "SNDK",
    "Stanley Black & Decker":    "SWK",
    "Starbucks":                 "SBUX",
    "Stryker":                   "SYK",
    "Sysco":                     "SYY",
    "TE Connectivity":           "TEL",
    "Tesla":                     "TSLA",
    "Texas Instruments":         "TXN",
    "Textron":                   "TXT",
    "Thermo Fisher":             "TMO",
    "T-Mobile US":               "TMUS",
    "Travelers Companies":       "TRV",
    "Uber":                      "UBER",
    "UnitedHealth":              "UNH",
    "UPS":                       "UPS",
    "Verizon":                   "VZ",
    "Visa":                      "V",
    "Walmart":                   "WMT",
    "Walt Disney":               "DIS",
    "Warner Bros. Discovery":    "WBD",
    "Western Digital":           "WDC",
    "Zimmer Biomet":             "ZBH",
}

# ─── NASDAQ 100 (hors S&P500 déjà listé) ───
NASDAQ100_SYMBOLS = {
    "ADP":                       "ADP",
    "Booking Holdings":          "BKNG",
    "CSX":                       "CSX",
    "Gilead Sciences":           "GILD",
    "Intuit":                    "INTU",
    "Intuitive Surgical":        "ISRG",
    "Keurig Dr Pepper":          "KDP",
    "Mondelez":                  "MDLZ",
    "Regeneron":                 "REGN",
    "SpaceX":                    "SPCX",  # ajout 12 Juin 2026
    "Vertex Pharma":             "VRTX",
}

CRYPTO_IDS = {
    "Bitcoin":  "bitcoin",
    "Ethereum": "ethereum",
    "BNB":      "binancecoin",
    "Solana":   "solana",
    "XRP":      "ripple",
    "Cardano":  "cardano",
}

# Univers graphable : CAC40 + Mid-Cap (toutes valeurs avec symbole yfinance)
# Symboles yfinance pour les cryptomonnaies (paires EUR)
CRYPTO_YF_SYMBOLS = {
    "Bitcoin":  "BTC-EUR",
    "Ethereum": "ETH-EUR",
    "BNB":      "BNB-EUR",
    "Solana":   "SOL-EUR",
    "XRP":      "XRP-EUR",
    "Cardano":  "ADA-EUR",
}

# Sélection par défaut pour le panneau US
US_ALL_SYMBOLS: dict[str, str] = {}
US_ALL_SYMBOLS.update(SP500_SYMBOLS)
US_ALL_SYMBOLS.update(NASDAQ100_SYMBOLS)

US_DEFAULT_SELECTION = {
    "Apple", "Microsoft", "NVIDIA", "Amazon", "Alphabet",
    "Meta Platforms", "Tesla", "SpaceX", "JPMorgan Chase", "Visa", "Mastercard",
    "Broadcom", "Netflix",
}

# Dict actif pour les requêtes cours US — protégé par lock
US_SYMBOLS_ACTIVE = {k: v for k, v in US_ALL_SYMBOLS.items() if k in US_DEFAULT_SELECTION}
_us_symbols_lock  = threading.Lock()

# Univers graphable : CAC40 + Mid-Cap + S&P500 + NASDAQ100 + Cryptomonnaies
ALL_CHARTABLE = dict(CAC40_ALL)
ALL_CHARTABLE.update(MIDCAP_SYMBOLS)
ALL_CHARTABLE.update(SP500_SYMBOLS)
ALL_CHARTABLE.update(NASDAQ100_SYMBOLS)
ALL_CHARTABLE.update(CRYPTO_YF_SYMBOLS)

# Dict actif pour les requêtes cours — protégé par lock
CAC40_SYMBOLS     = {k: v for k, v in CAC40_ALL.items() if k in CAC40_DEFAULT_SELECTION}
_cac_symbols_lock = threading.Lock()

# Sélection par défaut pour les 4 panneaux graphiques
CHART_DEFAULT_SLOTS = [
    {"name": "LVMH",          "period": "3 mois"},
    {"name": "Airbus",        "period": "3 mois"},
    {"name": "TotalEnergies", "period": "3 mois"},
    {"name": "Bitcoin",       "period": "1 mois"},
]

# ─── COULEURS & STYLE ───

BG_MAIN      = "#0d0f14"
BG_PANEL     = "#13161e"
BG_HEADER    = "#1a1e2a"
BG_ROW_ODD   = "#161922"
BG_ROW_EVEN  = "#13161e"

COLOR_GOLD   = "#f0c040"
COLOR_BLUE   = "#4fc3f7"
COLOR_GREEN  = "#4ade80"
COLOR_RED    = "#f87171"
COLOR_WHITE  = "#e8eaf0"
COLOR_GRAY   = "#6b7280"
COLOR_ORANGE = "#fb923c"
COLOR_TEAL   = "#2dd4bf"
COLOR_PURPLE = "#a78bfa"

CHART_ACCENTS = [COLOR_GOLD, COLOR_BLUE, COLOR_TEAL, COLOR_PURPLE]

FONT_TITLE  = ("Courier New", 13, "bold")
FONT_HEADER = ("Courier New",  9, "bold")
FONT_DATA   = ("Courier New", 10)
FONT_DATA_B = ("Courier New", 10, "bold")
FONT_SMALL  = ("Courier New",  8)
FONT_STATUS = ("Courier New",  8)

# ─── CONFIG PERSISTANTE ───

def load_config() -> dict:
    defaults = {
        "cac40_selection": sorted(CAC40_DEFAULT_SELECTION),
        "us_selection":    sorted(US_DEFAULT_SELECTION),
        "chart_slots":     CHART_DEFAULT_SLOTS,
    }
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        sel   = set(data.get("cac40_selection", []))
        valid = sel & set(CAC40_ALL.keys())
        data["cac40_selection"] = sorted(valid) if valid else sorted(CAC40_DEFAULT_SELECTION)
        raw   = data.get("chart_slots", CHART_DEFAULT_SLOTS)
        slots = []
        for s in raw[:4]:
            n, p = s.get("name",""), s.get("period","3 mois")
            if n in ALL_CHARTABLE and p in CHART_PERIODS:
                slots.append({"name": n, "period": p})
        while len(slots) < 4:
            slots.append(CHART_DEFAULT_SLOTS[len(slots)])
        data["chart_slots"] = slots
        return data
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return defaults

def save_config(cac_selection: set, chart_slots: list) -> str | None:
    """Sauvegarde la config (CAC40 + graphiques + US). Retourne None si OK, sinon l'erreur."""
    try:
        existing = {}
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
        with _us_symbols_lock:
            us_sel = sorted(US_SYMBOLS_ACTIVE.keys())
        existing.update({
            "cac40_selection": sorted(cac_selection),
            "chart_slots":     chart_slots,
            "us_selection":    us_sel,
        })
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return None
    except OSError as e:
        msg = f"Impossible d'écrire {CONFIG_FILE} :\n{e}"
        print(f"[config] {msg}")
        return msg

# ─── SPLASH SCREEN ───

class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=BG_HEADER)
        self.attributes("-topmost", True)
        self._img_ref = None
        try:
            from PIL import Image, ImageTk
            img = Image.open(SPLASH_IMG)
            img.thumbnail((600, 400), Image.LANCZOS)
            self._img_ref = ImageTk.PhotoImage(img)
            tk.Label(self, image=self._img_ref, bg=BG_HEADER).pack()
        except Exception:
            tk.Label(self, text="◈  Marchés Financiers  ◈",
                     font=("Courier New", 28, "bold"),
                     fg=COLOR_GOLD, bg=BG_HEADER, pady=30, padx=60).pack()
        tk.Label(self, text="Tableau de Bord Boursier",
                 font=("Courier New", 13, "bold"),
                 fg=COLOR_BLUE, bg=BG_HEADER).pack(pady=(4, 2))
        tk.Label(self, text="CAC 40  ·  Mid-Cap  ·  Cryptomonnaies  ·  Analyse Graphique",
                 font=FONT_SMALL, fg=COLOR_GRAY, bg=BG_HEADER).pack(pady=(0, 8))
        tk.Label(self, text="Chargement en cours…",
                 font=FONT_SMALL, fg=COLOR_GRAY, bg=BG_HEADER).pack(pady=(0, 12))
        self._center()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

# ─── FETCH RESULT ───

class FetchResult:
    def __init__(self, data=None, error=None):
        self.data  = data
        self.error = error
    def ok(self):       return self.data is not None
    def __bool__(self): return self.ok()

# ─── FONCTIONS DE DONNÉES — COURS ───

def _fetch_yf_one(name: str, symbol: str) -> FetchResult:
    result, exc = [None], [None]
    def _inner():
        try:
            info      = yf.Ticker(symbol).fast_info
            result[0] = (info.last_price, info.previous_close)
        except Exception as e:
            exc[0] = e
    t = threading.Thread(target=_inner, daemon=True)
    t.start(); t.join(timeout=YF_TIMEOUT)
    if t.is_alive():
        return FetchResult(error=f"{name} ({symbol}) : délai dépassé ({YF_TIMEOUT}s)")
    if exc[0]:
        return FetchResult(error=f"{name} ({symbol}) : {type(exc[0]).__name__} — {exc[0]}")
    price, prev = result[0]
    if price and prev and prev > 0:
        return FetchResult(data={"price": price,
                                  "change_pct": (price-prev)/prev*100,
                                  "currency": "EUR"})
    return FetchResult(error=f"{name} ({symbol}) : données incomplètes (price={price}, prev={prev})")

def _fetch_yf_symbols(symbols: dict, max_workers: int = 8) -> tuple:
    """Récupère les cours en parallèle (max_workers workers simultanés)."""
    results: dict = {name: None for name in symbols}
    errors:  list = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_map = {ex.submit(_fetch_yf_one, name, sym): name
                      for name, sym in symbols.items()}
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                fr = future.result()
            except Exception as e:
                fr = FetchResult(error=f"{name} : {type(e).__name__} — {e}")
            if fr.ok():
                results[name] = fr.data
            else:
                errors.append(fr.error)
    return results, errors

def fetch_cac40() -> tuple:
    with _cac_symbols_lock: symbols = dict(CAC40_SYMBOLS)
    return _fetch_yf_symbols(symbols)

def fetch_midcap() -> tuple:
    results, errors = _fetch_yf_symbols(MIDCAP_SYMBOLS)
    for name, symbol in MIDCAP_SYMBOLS.items():
        if not results.get(name): continue
        extra, exc = [None], [None]
        def _inner(s=symbol):
            try: extra[0] = yf.Ticker(s).info
            except Exception as e: exc[0] = e
        t = threading.Thread(target=_inner, daemon=True)
        t.start(); t.join(timeout=YF_TIMEOUT)
        if t.is_alive():
            errors.append(f"{name} : timeout enrichissement ({YF_TIMEOUT}s)"); continue
        if exc[0]:
            errors.append(f"{name} enrichissement : {exc[0]}"); continue
        info = extra[0] or {}
        results[name]["volume"]    = info.get("volume")
        results[name]["market_cap"]= info.get("marketCap")
        results[name]["pe_ratio"]  = info.get("trailingPE")
        results[name]["52w_high"]  = info.get("fiftyTwoWeekHigh")
        results[name]["52w_low"]   = info.get("fiftyTwoWeekLow")
        results[name]["long_name"] = info.get("longName", name)
    return results, errors

def fetch_us() -> tuple:
    """Récupère les cours des valeurs US sélectionnées (S&P500 + NASDAQ100)."""
    with _us_symbols_lock: symbols = dict(US_SYMBOLS_ACTIVE)
    return _fetch_yf_symbols(symbols, max_workers=10)

def fetch_crypto(stop_event: threading.Event | None = None) -> tuple:
    """Récupère les données crypto via CoinGecko.
    stop_event : si fourni et activé, interrompt le sleep() du retry 429."""
    ids = ",".join(CRYPTO_IDS.values())
    url = ("https://api.coingecko.com/api/v3/simple/price"
           f"?ids={ids}&vs_currencies=eur&include_24hr_change=true&include_market_cap=true")
    errors = []

    def _interruptible_sleep(seconds: float) -> bool:
        """Dort par tranches de 0.2 s. Retourne False si stop_event déclenché."""
        elapsed = 0.0
        while elapsed < seconds:
            if stop_event and stop_event.is_set():
                return False
            time.sleep(min(0.2, seconds - elapsed))
            elapsed += 0.2
        return True

    try:
        resp = requests.get(url, timeout=COINGECKO_TIMEOUT)
        if resp.status_code == 429:
            retry = int(resp.headers.get("Retry-After", COINGECKO_RATELIMIT_RETRY))
            errors.append(f"CoinGecko : quota API dépassé (429) — réessai dans {retry}s.")
            if not _interruptible_sleep(retry):
                errors.append("CoinGecko : réessai 429 annulé par l'utilisateur.")
                return {name: None for name in CRYPTO_IDS}, errors
            resp = requests.get(url, timeout=COINGECKO_TIMEOUT)
        resp.raise_for_status()
        data, results = resp.json(), {}
        for name, cg_id in CRYPTO_IDS.items():
            d = data.get(cg_id, {})
            if not d:
                errors.append(f"CoinGecko : données manquantes pour {name} ({cg_id})")
                results[name] = None
            else:
                results[name] = {"price": d.get("eur"), "change_pct": d.get("eur_24h_change"),
                                  "market_cap": d.get("eur_market_cap")}
        return results, errors
    except requests.exceptions.ConnectionError:
        errors.append("CoinGecko : pas de connexion réseau")
    except requests.exceptions.Timeout:
        errors.append(f"CoinGecko : timeout ({COINGECKO_TIMEOUT}s dépassé)")
    except requests.exceptions.HTTPError as e:
        errors.append(f"CoinGecko : erreur HTTP {e.response.status_code} — {e}")
    except Exception as e:
        errors.append(f"CoinGecko : {type(e).__name__} — {e}")
    return {name: None for name in CRYPTO_IDS}, errors

# ─── FONCTIONS DE DONNÉES — HISTORIQUE GRAPHIQUE ───

def fetch_history(name: str, symbol: str, period_label: str) -> FetchResult:
    yf_period   = CHART_PERIODS.get(period_label, "3mo")
    result, exc = [None], [None]
    def _inner():
        try:
            df = yf.Ticker(symbol).history(period=yf_period, auto_adjust=True)
            result[0] = df
        except Exception as e:
            exc[0] = e
    t = threading.Thread(target=_inner, daemon=True)
    t.start(); t.join(timeout=YF_HISTORY_TIMEOUT)
    if t.is_alive():
        return FetchResult(error=f"{name} : timeout historique ({YF_HISTORY_TIMEOUT}s)")
    if exc[0]:
        return FetchResult(error=f"{name} : {type(exc[0]).__name__} — {exc[0]}")
    df = result[0]
    if df is None or df.empty:
        return FetchResult(error=f"{name} : historique vide pour '{period_label}'")
    return FetchResult(data=df)

# ─── UTILITAIRES D'AFFICHAGE ───

def format_price(value, currency="€", crypto=False):
    if value is None:            return "  ---"
    if crypto and value >= 1000: return f"{value:>12,.0f} {currency}"
    if crypto and value >= 1:    return f"{value:>12,.2f} {currency}"
    if crypto:                   return f"{value:>12,.4f} {currency}"
    return f"{value:>10,.2f} {currency}"

def format_marketcap(value):
    if value is None: return "       ---"
    if value >= 1e12: return f"{value/1e12:>7.2f} T€"
    if value >= 1e9:  return f"{value/1e9:>7.2f} Md€"
    if value >= 1e6:  return f"{value/1e6:>7.1f} M€"
    return f"{value:>10.0f} €"

def format_volume(value):
    if value is None: return "---"
    if value >= 1e6:  return f"{value/1e6:.2f}M"
    if value >= 1e3:  return f"{value/1e3:.1f}k"
    return str(value)

def arrow_and_color(pct):
    if pct is None: return "  ", COLOR_GRAY
    if pct > 0:     return "▲", COLOR_GREEN
    if pct < 0:     return "▼", COLOR_RED
    return "─", COLOR_GRAY

# ─── PANNEAU GRAPHIQUE INDIVIDUEL ───

class ChartPanel(tk.Frame):
    """Un des 4 panneaux de l'onglet Analyse Graphique.
    Barre de contrôle (combo valeur + combo période + bouton) + zone matplotlib."""

    def __init__(self, parent, slot_index: int, initial_name: str,
                 initial_period: str, accent_color: str, on_config_changed):
        super().__init__(parent, bg=BG_PANEL, bd=1, relief="flat")
        self._slot    = slot_index
        self._accent  = accent_color
        self._on_cfg  = on_config_changed
        self._loading = False
        self._fig     = None
        self._canvas  = None

        self._build_controls(initial_name, initial_period)
        self._build_placeholder()

    # ── Construction ──

    def _build_controls(self, initial_name, initial_period):
        bar = tk.Frame(self, bg=BG_HEADER, pady=3)
        bar.pack(fill="x")

        tk.Label(bar, text=f" [{self._slot+1}]",
                 font=("Courier New", 8, "bold"),
                 fg=self._accent, bg=BG_HEADER).pack(side="left", padx=(4, 0))

        self._name_var = tk.StringVar(value=initial_name)
        cb_name = ttk.Combobox(bar, textvariable=self._name_var,
                               values=sorted(ALL_CHARTABLE.keys()),
                               state="readonly", width=22,
                               font=("Courier New", 8))
        cb_name.pack(side="left", padx=4)
        cb_name.bind("<<ComboboxSelected>>", self._on_changed)

        self._period_var = tk.StringVar(value=initial_period)
        cb_period = ttk.Combobox(bar, textvariable=self._period_var,
                                 values=list(CHART_PERIODS.keys()),
                                 state="readonly", width=7,
                                 font=("Courier New", 8))
        cb_period.pack(side="left", padx=2)
        cb_period.bind("<<ComboboxSelected>>", self._on_changed)

        self._btn = tk.Button(
            bar, text="⟳", font=("Courier New", 9, "bold"),
            fg=self._accent, bg=BG_HEADER,
            activeforeground=COLOR_WHITE, activebackground="#353a50",
            relief="flat", bd=0, padx=6, pady=1, cursor="hand2",
            command=self.load_chart,
        )
        self._btn.pack(side="left", padx=2)

        self._status_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self._status_var,
                 font=FONT_SMALL, fg=COLOR_GRAY, bg=BG_HEADER).pack(side="left", padx=6)

        self._pct_var = tk.StringVar(value="")
        self._lbl_pct = tk.Label(bar, textvariable=self._pct_var,
                                 font=("Courier New", 8, "bold"),
                                 fg=COLOR_GRAY, bg=BG_HEADER)
        self._lbl_pct.pack(side="right", padx=8)

    def _build_placeholder(self):
        self._chart_area = tk.Frame(self, bg=BG_PANEL)
        self._chart_area.pack(fill="both", expand=True)
        tk.Label(self._chart_area,
                 text="Sélectionnez une valeur et cliquez  ⟳",
                 font=FONT_SMALL, fg=COLOR_GRAY, bg=BG_PANEL).pack(expand=True)

    # ── Événements ──

    def _on_changed(self, event=None):
        self._on_cfg()
        self.load_chart()

    def get_config(self) -> dict:
        return {"name": self._name_var.get(), "period": self._period_var.get()}

    # ── Chargement asynchrone ──

    def load_chart(self):
        if self._loading: return
        name   = self._name_var.get()
        period = self._period_var.get()
        if not name or name not in ALL_CHARTABLE: return

        self._loading = True
        self._btn.config(state="disabled")
        self._status_var.set("⏳ chargement…")
        self._pct_var.set(""); self._lbl_pct.config(fg=COLOR_GRAY)

        symbol = ALL_CHARTABLE[name]
        def worker():
            fr = fetch_history(name, symbol, period)
            self.after(0, lambda: self._on_data_ready(name, period, fr))
        threading.Thread(target=worker, daemon=True).start()

    def _on_data_ready(self, name, period, fr):
        self._loading = False
        self._btn.config(state="normal")
        if not fr.ok():
            self._status_var.set(f"⚠ {fr.error[:60]}")
            return
        self._status_var.set("")
        self._draw(name, period, fr.data)

    # ── Tracé matplotlib ──

    def _draw(self, name: str, period: str, df):
        # Nettoyage
        for w in self._chart_area.winfo_children(): w.destroy()
        if self._fig is not None:
            try:
                import matplotlib.pyplot as _plt; _plt.close(self._fig)
            except Exception as _e:
                print(f"[chart] Avertissement nettoyage figure matplotlib : {_e}")
            self._fig = None

        closes      = df["Close"].values
        first, last = float(closes[0]), float(closes[-1])
        total_pct   = (last - first) / first * 100 if first != 0 else 0.0
        arrow, _    = arrow_and_color(total_pct)
        pct_color   = COLOR_GREEN if total_pct >= 0 else COLOR_RED
        self._pct_var.set(f"{arrow} {total_pct:+.2f}%  sur {period}")
        self._lbl_pct.config(fg=pct_color)

        line_col = "#4ade80" if total_pct >= 0 else "#f87171"
        fill_col = "#0d2a14" if total_pct >= 0 else "#2a0d0d"

        BG_FIG = "#0d0f14"; BG_AX = "#13161e"
        TXT    = "#9ca3af"; GRID  = "#1f2535"

        fig = Figure(figsize=(4, 2.6), dpi=90)
        fig.patch.set_facecolor(BG_FIG)
        # 2 axes : prix (haut, 68%) et volume (bas, 20%)
        ax_p = fig.add_axes([0.08, 0.30, 0.88, 0.62], facecolor=BG_AX)
        ax_v = fig.add_axes([0.08, 0.05, 0.88, 0.20], facecolor=BG_AX, sharex=ax_p)

        dates = df.index.to_pydatetime()

        # Courbe prix + remplissage
        ax_p.plot(dates, closes, color=line_col, linewidth=1.4, zorder=3)
        ax_p.fill_between(dates, closes, closes.min() * 0.998,
                          color=fill_col, alpha=0.6, zorder=2)

        # Annotations max / min
        i_max = int(closes.argmax()); i_min = int(closes.argmin())
        ax_p.annotate(f"{closes[i_max]:,.2f}",
                      xy=(dates[i_max], closes[i_max]),
                      xytext=(0, 5), textcoords="offset points",
                      color=COLOR_GREEN, fontsize=6, ha="center", va="bottom")
        ax_p.annotate(f"{closes[i_min]:,.2f}",
                      xy=(dates[i_min], closes[i_min]),
                      xytext=(0, -10), textcoords="offset points",
                      color=COLOR_RED, fontsize=6, ha="center", va="top")

        ax_p.set_title(f"{name}  ·  {period}",
                       color=self._accent, fontsize=8, fontweight="bold", pad=4)
        ax_p.tick_params(colors=TXT, labelsize=6, labelbottom=False)
        ax_p.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
        ax_p.yaxis.tick_right()
        ax_p.grid(True, color=GRID, linewidth=0.5, linestyle="--", zorder=1)
        for sp in ax_p.spines.values(): sp.set_edgecolor(GRID)

        # Histogramme volume
        if "Volume" in df.columns and df["Volume"].sum() > 0:
            vol_col = ["#4ade80" if float(c) >= float(o) else "#f87171"
                       for c, o in zip(df["Close"], df["Open"])]
            ax_v.bar(dates, df["Volume"].values,
                     color=vol_col, alpha=0.75, width=0.8, zorder=2)
        ax_v.set_ylabel("Vol", color=TXT, fontsize=5, labelpad=2)
        ax_v.tick_params(colors=TXT, labelsize=5)
        ax_v.yaxis.tick_right()
        ax_v.yaxis.set_major_formatter(
            mticker.FuncFormatter(
                lambda x, _: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.0f}k"))
        ax_v.grid(True, color=GRID, linewidth=0.4, linestyle="--", zorder=1)
        for sp in ax_v.spines.values(): sp.set_edgecolor(GRID)

        # Format axe X selon l'amplitude temporelle
        n_days = max((df.index[-1] - df.index[0]).days, 1)
        if n_days <= 10:
            ax_v.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
            ax_v.xaxis.set_major_locator(mdates.DayLocator())
        elif n_days <= 40:
            ax_v.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
            ax_v.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))
        elif n_days <= 200:
            ax_v.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
            ax_v.xaxis.set_major_locator(mdates.MonthLocator())
        else:
            ax_v.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
            ax_v.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax_v.tick_params(axis="x", labelsize=5, colors=TXT, rotation=30)

        canvas = FigureCanvasTkAgg(fig, master=self._chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._fig = fig; self._canvas = canvas

# ─── ONGLET ANALYSE GRAPHIQUE (grille 2×2) ───

class AnalyseTab(tk.Frame):
    def __init__(self, parent, initial_slots: list, on_config_changed):
        super().__init__(parent, bg=BG_MAIN)
        self._on_cfg = on_config_changed
        self._panels = []
        self._build(initial_slots)

    def _build(self, slots):
        for i in range(2):
            self.columnconfigure(i, weight=1, uniform="col")
            self.rowconfigure(i,    weight=1, uniform="row")
        self.rowconfigure(2, weight=0)

        for i, slot in enumerate(slots):
            row, col = divmod(i, 2)
            panel = ChartPanel(
                self, slot_index=i,
                initial_name=slot["name"], initial_period=slot["period"],
                accent_color=CHART_ACCENTS[i],
                on_config_changed=self._on_cfg,
            )
            panel.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
            self._panels.append(panel)

        bar = tk.Frame(self, bg=BG_MAIN)
        bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))

        tk.Button(bar, text="⟳  Actualiser tous les graphiques",
                  font=FONT_SMALL, fg=COLOR_GOLD, bg="#252a38",
                  activeforeground=COLOR_WHITE, activebackground="#353a50",
                  relief="flat", bd=0, padx=12, pady=4, cursor="hand2",
                  command=self.load_all).pack(side="left")

        tk.Label(bar,
                 text="Données : Yahoo Finance · yfinance  |  Cours de clôture ajustés",
                 font=FONT_SMALL, fg=COLOR_GRAY, bg=BG_MAIN).pack(side="right", padx=8)

    def load_all(self):
        for p in self._panels: p.load_chart()

    def get_slots_config(self) -> list:
        return [p.get_config() for p in self._panels]

# ─── DASHBOARD PRINCIPAL ───

class Dashboard(tk.Tk):
    def __init__(self, config: dict):
        super().__init__()
        self.withdraw()
        self.title("Marchés Financiers")
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)

        self._config       = config
        self._cac_data     = {}
        self._midcap_data  = {}
        self._us_data      = {}
        self._crypto_data  = {}
        self._lock         = threading.Lock()
        self._refreshing   = False
        self._stop_refresh = False
        self._stop_event   = threading.Event()   # interrompt le sleep() du retry 429
        self._countdown_id = None
        self._last_errors: list = []

        self._build_ui()

        splash = SplashScreen(self)
        self.after(SPLASH_DURATION_MS, lambda: self._after_splash(splash))

    # ── Cycle de vie ──

    def _after_splash(self, splash):
        splash.destroy()
        self.deiconify()
        self._center_window()
        self._start_refresh()
        self.after(2000, self._analyse_tab.load_all)

    def _center_window(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w,  h  = self.winfo_reqwidth(),   self.winfo_reqheight()
        self.geometry(f"+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}")

    # ── Tooltip helper ──

    def _add_tooltip(self, widget, text: str):
        tip = {"win": None}
        def _enter(event):
            if tip["win"]: return
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 4
            win = tk.Toplevel(widget)
            win.overrideredirect(True); win.attributes("-topmost", True)
            win.geometry(f"+{x}+{y}")
            tk.Label(win, text=text, justify="left",
                     font=("Courier New", 8), fg=COLOR_WHITE,
                     bg="#2a2f40", relief="flat", padx=6, pady=4,
                     wraplength=320).pack()
            tip["win"] = win
        def _leave(event):
            if tip["win"]: tip["win"].destroy(); tip["win"] = None
        widget.bind("<Enter>", _enter); widget.bind("<Leave>", _leave)

    # ── Construction UI ──

    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_HEADER, pady=4)
        hdr.pack(fill="x")

        # ── Ligne 1 : Titre centré ──
        tk.Label(hdr, text="◈  TABLEAU DE BORD BOURSIER  ◈",
                 font=("Courier New", 15, "bold"),
                 fg=COLOR_GOLD, bg=BG_HEADER).pack()
        tk.Label(hdr, text="CAC 40  ·  Mid-Cap (LISI)  ·  Cryptomonnaies  ·  Analyse Graphique",
                 font=FONT_SMALL, fg=COLOR_GRAY, bg=BG_HEADER).pack()

        # ── Ligne 2 : frame dédiée aux boutons ──
        btn_bar = tk.Frame(hdr, bg=BG_HEADER)
        btn_bar.pack(fill="x", pady=(2, 4))

        # Lecture gauche→droite : [⚙ Valeurs CAC40]  [⟳ Actualiser]
        # Avec side="right" : le 1er packagé est le plus à droite.
        self._btn_refresh = tk.Button(btn_bar, text="⟳ Actualiser", font=FONT_SMALL,
                                      fg=COLOR_BLUE, bg="#252a38",
                                      activeforeground=COLOR_WHITE, activebackground="#353a50",
                                      relief="flat", bd=0, padx=10, pady=3, cursor="hand2",
                                      command=self._manual_refresh)
        self._btn_refresh.pack(side="right", padx=(0, 12))

        btn_sel = tk.Button(btn_bar, text="⚙ Valeurs CAC40", font=FONT_SMALL,
                            fg=COLOR_GOLD, bg="#252a38",
                            activeforeground=COLOR_WHITE, activebackground="#353a50",
                            relief="flat", bd=0, padx=10, pady=3, cursor="hand2",
                            command=self._open_selection)
        btn_sel.pack(side="right", padx=(0, 4))

        btn_sel_us = tk.Button(btn_bar, text="⚙ Valeurs US", font=FONT_SMALL,
                               fg=COLOR_BLUE, bg="#252a38",
                               activeforeground=COLOR_WHITE, activebackground="#353a50",
                               relief="flat", bd=0, padx=10, pady=3, cursor="hand2",
                               command=self._open_selection_us)
        btn_sel_us.pack(side="right", padx=(0, 4))

        self._btn_stop = tk.Button(btn_bar, text="⏹ Arrêter MàJ", font=FONT_SMALL,
                                   fg=COLOR_RED, bg="#252a38",
                                   activeforeground=COLOR_WHITE, activebackground="#353a50",
                                   relief="flat", bd=0, padx=10, pady=3, cursor="hand2",
                                   command=self._request_stop)

        # Notebook
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",
                         background=BG_MAIN, borderwidth=0, tabmargins=[2, 2, 0, 0])
        style.configure("TNotebook.Tab",
                         background=BG_HEADER, foreground=COLOR_GRAY,
                         font=("Courier New", 9, "bold"),
                         padding=[14, 5], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", BG_PANEL)],
                  foreground=[("selected", COLOR_GOLD)])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        tab_live = tk.Frame(nb, bg=BG_MAIN)
        nb.add(tab_live, text="  📈  Cours en direct  ")
        self._build_live_tab(tab_live)

        tab_us = tk.Frame(nb, bg=BG_MAIN)
        nb.add(tab_us, text="  🇺🇸  Valeurs US  ")
        self._build_us_tab(tab_us)

        self._analyse_tab = AnalyseTab(
            nb,
            initial_slots=self._config.get("chart_slots", CHART_DEFAULT_SLOTS),
            on_config_changed=self._save_config_now,
        )
        nb.add(self._analyse_tab, text="  📊  Analyse Graphique  ")

        # Barre de statut
        status_bar = tk.Frame(self, bg=BG_HEADER, pady=4)
        status_bar.pack(fill="x", side="bottom")

        self._status_var = tk.StringVar(value="⏳ Chargement initial…")
        tk.Label(status_bar, textvariable=self._status_var,
                 font=FONT_STATUS, fg=COLOR_GRAY, bg=BG_HEADER).pack(side="left", padx=12)

        self._error_var = tk.StringVar(value="")
        self._lbl_error = tk.Label(status_bar, textvariable=self._error_var,
                                   font=FONT_STATUS, fg=COLOR_ORANGE, bg=BG_HEADER,
                                   cursor="hand2")
        self._lbl_error.pack(side="left", padx=6)
        self._lbl_error.bind("<Button-1>", lambda e: self._show_errors_popup())
        self._add_tooltip(self._lbl_error,
            "Cliquez pour voir le détail des erreurs du dernier rafraîchissement.")

        self._next_var = tk.StringVar(value="")
        tk.Label(status_bar, textvariable=self._next_var,
                 font=FONT_STATUS, fg=COLOR_BLUE, bg=BG_HEADER).pack(side="right", padx=12)

    def _build_live_tab(self, parent):
        body = tk.Frame(parent, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=10, pady=6)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=2)
        body.rowconfigure(0, weight=1)

        # ── Panneau CAC40 : _make_panel crée le titre + séparateur,
        #    puis on ajoute un Canvas scrollable dans ce panel (enfant [2+]).
        #    _frame_cac reste le Frame interne (contenu des lignes).
        cac_panel = self._make_panel(body, "📈  CAC 40", COLOR_GOLD)
        cac_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        cac_panel.rowconfigure(0, weight=1)
        cac_panel.columnconfigure(0, weight=1)

        _cac_canvas = tk.Canvas(cac_panel, bg=BG_PANEL, highlightthickness=0)
        _cac_sb     = ttk.Scrollbar(cac_panel, orient="vertical", command=_cac_canvas.yview)
        _cac_canvas.configure(yscrollcommand=_cac_sb.set)
        _cac_sb.pack(side="right", fill="y")
        _cac_canvas.pack(side="left", fill="both", expand=True)

        self._frame_cac = tk.Frame(_cac_canvas, bg=BG_PANEL)
        _cac_win = _cac_canvas.create_window((0, 0), window=self._frame_cac, anchor="nw")
        def _cac_resize(event): _cac_canvas.itemconfig(_cac_win, width=event.width)
        _cac_canvas.bind("<Configure>", _cac_resize)
        self._frame_cac.bind("<Configure>", lambda e: _cac_canvas.configure(
            scrollregion=_cac_canvas.bbox("all")))
        # Molette : bind local au canvas (pas bind_all pour éviter les conflits)
        def _cac_scroll(event):
            _cac_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        _cac_canvas.bind("<MouseWheel>", _cac_scroll)
        _cac_canvas.bind("<Button-4>", lambda e: _cac_canvas.yview_scroll(-1, "units"))
        _cac_canvas.bind("<Button-5>", lambda e: _cac_canvas.yview_scroll( 1, "units"))
        # Propagation molette depuis les lignes enfants vers le canvas
        self._frame_cac.bind("<MouseWheel>", _cac_scroll)
        self._frame_cac.bind("<Button-4>", lambda e: _cac_canvas.yview_scroll(-1, "units"))
        self._frame_cac.bind("<Button-5>", lambda e: _cac_canvas.yview_scroll( 1, "units"))
        self._cac_canvas = _cac_canvas   # référence pour propagation dynamique

        self._frame_mid    = self._make_panel(body, "🏭  MID-CAP",        COLOR_TEAL)
        self._frame_crypto = self._make_panel(body, "₿  CRYPTOMONNAIES", COLOR_ORANGE)
        self._frame_mid.grid(   row=0, column=1, sticky="nsew", padx=(0, 5))
        self._frame_crypto.grid(row=0, column=2, sticky="nsew")

    def _make_panel(self, parent, title, accent):
        outer = tk.Frame(parent, bg=BG_PANEL, bd=1, relief="flat")
        tk.Label(outer, text=title, font=FONT_TITLE,
                 fg=accent, bg=BG_PANEL, pady=6).pack(fill="x", padx=10)
        tk.Frame(outer, bg=accent, height=1).pack(fill="x", padx=6, pady=(0, 4))
        return outer

    # ── Rendus cours ──

    @staticmethod
    def _update_label(lbl: tk.Label, **kwargs):
        """Met à jour un label existant uniquement si les valeurs changent."""
        for key, val in kwargs.items():
            if str(lbl.cget(key)) != str(val):
                lbl.config(**{key: val})

    def _build_us_tab(self, parent):
        """Onglet S&P500 / NASDAQ100 : 3 colonnes côte à côte, chacune scrollable."""
        parent.columnconfigure(0, weight=1, uniform="uscol")
        parent.columnconfigure(1, weight=1, uniform="uscol")
        parent.columnconfigure(2, weight=1, uniform="uscol")
        parent.rowconfigure(0, weight=1)

        self._us_col_frames   = []
        self._us_col_canvases = []

        for col in range(3):
            outer = tk.Frame(parent, bg=BG_PANEL, bd=1, relief="flat")
            outer.grid(row=0, column=col, sticky="nsew", padx=3, pady=6)
            outer.rowconfigure(2, weight=1)
            outer.columnconfigure(0, weight=1)

            tk.Label(outer, text=f"\U0001f1fa\U0001f1f8  S&P 500 · NASDAQ 100  [{col+1}/3]",
                     font=FONT_TITLE, fg=COLOR_BLUE, bg=BG_PANEL, pady=6).grid(
                     row=0, column=0, columnspan=2, sticky="ew", padx=10)
            tk.Frame(outer, bg=COLOR_BLUE, height=1).grid(
                     row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))

            canvas = tk.Canvas(outer, bg=BG_PANEL, highlightthickness=0)
            sb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=sb.set)
            sb.grid(row=2, column=1, sticky="ns")
            canvas.grid(row=2, column=0, sticky="nsew")

            inner = tk.Frame(canvas, bg=BG_PANEL)
            win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
            def _on_resize(event, c=canvas, w=win_id):
                c.itemconfig(w, width=event.width)
            canvas.bind("<Configure>", _on_resize)
            inner.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            def _scroll(event, c=canvas):
                c.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind("<MouseWheel>", _scroll)
            canvas.bind("<Button-4>",   lambda e, c=canvas: c.yview_scroll(-1, "units"))
            canvas.bind("<Button-5>",   lambda e, c=canvas: c.yview_scroll( 1, "units"))
            inner.bind("<MouseWheel>",  _scroll)
            inner.bind("<Button-4>",    lambda e, c=canvas: c.yview_scroll(-1, "units"))
            inner.bind("<Button-5>",    lambda e, c=canvas: c.yview_scroll( 1, "units"))

            self._us_col_frames.append(inner)
            self._us_col_canvases.append(canvas)

        self._frame_us = self._us_col_frames[0]
    def _open_selection_us(self):
        for w in self.winfo_children():
            if isinstance(w, USSelectionWindow): w.lift(); return
        USSelectionWindow(self)

    def _render_cac(self, data, index_data=None):
        """Reconstruit les lignes CAC dans _frame_cac (frame interne du canvas scrollable).
        Ce frame ne contient PAS le titre ni le séparateur — ceux-ci sont dans cac_panel.
        Stratégie anti-scintillement : mise à jour des labels existants si N identique."""
        existing = self._frame_cac.winfo_children()   # [0:] — pas de titre ici
        expected_data_children = 1 + len(data) + 1 + 1  # header + N valeurs + séparateur + index
        if len(existing) != expected_data_children:
            for w in existing: w.destroy()
            hdr = tk.Frame(self._frame_cac, bg=BG_HEADER)
            hdr.pack(fill="x", padx=6, pady=(0, 2))
            for txt in [f"{'VALEUR':<18}", f"{'COURS':>12}", f"{'VAR%':>8}"]:
                tk.Label(hdr, text=txt, font=FONT_HEADER,
                         fg=COLOR_GOLD, bg=BG_HEADER).pack(side="left", padx=4)
            for i, (name, d) in enumerate(data.items()):
                bg = BG_ROW_ODD if i % 2 == 0 else BG_ROW_EVEN
                row = tk.Frame(self._frame_cac, bg=bg)
                row.pack(fill="x", padx=6, pady=1)
                if d:
                    arrow, color = arrow_and_color(d["change_pct"])
                    pct = f"{d['change_pct']:+.2f}%" if d["change_pct"] is not None else "  ---"
                    tk.Label(row, text=f"{name:<18}", font=FONT_DATA,
                             fg=COLOR_WHITE, bg=bg).pack(side="left", padx=4)
                    tk.Label(row, text=format_price(d["price"], "€"), font=FONT_DATA_B,
                             fg=COLOR_WHITE, bg=bg).pack(side="left", padx=4)
                    tk.Label(row, text=f"{arrow} {pct:>8}", font=FONT_DATA_B,
                             fg=color, bg=bg).pack(side="left", padx=4)
                else:
                    tk.Label(row, text=f"{name:<18} — indisponible",
                             font=FONT_DATA, fg=COLOR_GRAY, bg=bg).pack(side="left", padx=4)
            tk.Frame(self._frame_cac, bg=COLOR_GOLD, height=1).pack(fill="x", padx=6, pady=(4, 2))
            self._render_cac_index(index_data)
        else:
            row_frames = existing[1 : 1 + len(data)]
            for row_frame, (name, d) in zip(row_frames, data.items()):
                labels = row_frame.winfo_children()
                if d:
                    arrow, color = arrow_and_color(d["change_pct"])
                    pct = f"{d['change_pct']:+.2f}%" if d["change_pct"] is not None else "  ---"
                    if len(labels) == 3:
                        self._update_label(labels[1], text=format_price(d["price"], "€"))
                        self._update_label(labels[2], text=f"{arrow} {pct:>8}", fg=color)
                    elif len(labels) == 1:
                        for w in labels: w.destroy()
                        bg = row_frame.cget("bg")
                        tk.Label(row_frame, text=f"{name:<18}", font=FONT_DATA,
                                 fg=COLOR_WHITE, bg=bg).pack(side="left", padx=4)
                        tk.Label(row_frame, text=format_price(d["price"], "€"), font=FONT_DATA_B,
                                 fg=COLOR_WHITE, bg=bg).pack(side="left", padx=4)
                        tk.Label(row_frame, text=f"{arrow} {pct:>8}", font=FONT_DATA_B,
                                 fg=color, bg=bg).pack(side="left", padx=4)
                else:
                    if len(labels) == 1:
                        self._update_label(labels[0], text=f"{name:<18} — indisponible")
                    else:
                        for w in labels: w.destroy()
                        bg = row_frame.cget("bg")
                        tk.Label(row_frame, text=f"{name:<18} — indisponible",
                                 font=FONT_DATA, fg=COLOR_GRAY, bg=bg).pack(side="left", padx=4)
            self._render_cac_index(index_data)

    def _render_us(self, data):
        """Distribue les valeurs US sur 3 colonnes côte à côte."""
        items   = list(data.items())
        n       = len(items)
        n_cols  = 3
        # Répartition équitable : col 0 prend le surplus si n % 3 != 0
        sizes   = [(n + n_cols - 1 - c) // n_cols for c in range(n_cols)]
        splits  = []
        idx = 0
        for s in sizes:
            splits.append(items[idx:idx+s]); idx += s

        for col, (frame, chunk) in enumerate(zip(self._us_col_frames, splits)):
            for w in frame.winfo_children(): w.destroy()
            hdr = tk.Frame(frame, bg=BG_HEADER)
            hdr.pack(fill="x", padx=4, pady=(0, 2))
            for txt in [f"{'VALEUR':<22}", f"{'COURS':>12}", f"{'VAR%':>8}"]:
                tk.Label(hdr, text=txt, font=FONT_HEADER,
                         fg=COLOR_BLUE, bg=BG_HEADER).pack(side="left", padx=2)
            for i, (name, d) in enumerate(chunk):
                bg  = BG_ROW_ODD if i % 2 == 0 else BG_ROW_EVEN
                row = tk.Frame(frame, bg=bg)
                row.pack(fill="x", padx=4, pady=1)
                if d:
                    arrow, color = arrow_and_color(d["change_pct"])
                    pct = f"{d['change_pct']:+.2f}%" if d["change_pct"] is not None else "  ---"
                    tk.Label(row, text=f"{name:<22}", font=FONT_DATA,
                             fg=COLOR_WHITE, bg=bg).pack(side="left", padx=2)
                    tk.Label(row, text=format_price(d["price"], "$"), font=FONT_DATA_B,
                             fg=COLOR_WHITE, bg=bg).pack(side="left", padx=2)
                    tk.Label(row, text=f"{arrow} {pct:>8}", font=FONT_DATA_B,
                             fg=color, bg=bg).pack(side="left", padx=2)
                else:
                    tk.Label(row, text=f"{name:<22} — indisponible",
                             font=FONT_DATA, fg=COLOR_GRAY, bg=bg).pack(side="left", padx=2)
            tk.Frame(frame, bg=COLOR_BLUE, height=1).pack(fill="x", padx=4, pady=(4, 2))
    def _render_cac_index(self, index_data=None):
        if index_data:
            price, change = index_data.get("price"), index_data.get("change_pct")
            arrow, color  = arrow_and_color(change)
            txt = (f"CAC 40 INDEX :  {price:,.2f}  {arrow} {change:+.2f}%"
                   if price and change is not None
                   else "CAC 40 INDEX : données incomplètes")
            if not (price and change is not None): color = COLOR_GRAY
        else:
            txt, color = "CAC 40 INDEX : non disponible", COLOR_GRAY
        row = tk.Frame(self._frame_cac, bg=BG_HEADER)
        row.pack(fill="x", padx=6, pady=(2, 6))
        tk.Label(row, text=txt, font=FONT_DATA_B,
                 fg=color, bg=BG_HEADER).pack(padx=8, pady=2)

    def _render_midcap(self, data):
        for w in self._frame_mid.winfo_children()[2:]: w.destroy()
        for i, (name, d) in enumerate(data.items()):
            bg = BG_ROW_ODD if i % 2 == 0 else BG_ROW_EVEN
            if not d:
                row = tk.Frame(self._frame_mid, bg=bg)
                row.pack(fill="x", padx=6, pady=1)
                tk.Label(row, text=f"{name} — indisponible",
                         font=FONT_DATA, fg=COLOR_GRAY, bg=bg).pack(side="left", padx=4)
                continue
            arrow, color = arrow_and_color(d["change_pct"])
            long_name    = d.get("long_name", name)
            th = tk.Frame(self._frame_mid, bg=BG_HEADER)
            th.pack(fill="x", padx=6, pady=(6, 0))
            tk.Label(th, text=f"  {long_name}", font=FONT_DATA_B,
                     fg=COLOR_TEAL, bg=BG_HEADER).pack(side="left")
            tk.Label(th, text=f"({name})", font=FONT_SMALL,
                     fg=COLOR_GRAY, bg=BG_HEADER).pack(side="left", padx=4)
            pct_str = f"{d['change_pct']:+.2f}%" if d["change_pct"] is not None else "  ---"
            for label, val, fnt in [
                ("Cours :",   f"{format_price(d['price'],'€')}  {arrow} {pct_str}", FONT_DATA_B),
                ("Volume :",  format_volume(d.get("volume")),                        FONT_SMALL),
                ("Mkt Cap :", format_marketcap(d.get("market_cap")),                 FONT_SMALL),
                ("P/E :",     f"{d['pe_ratio']:.1f}" if d.get("pe_ratio") else "---", FONT_SMALL),
                ("52w :",     (f"{d.get('52w_low'):.2f} / {d.get('52w_high'):.2f} €"
                               if d.get("52w_low") and d.get("52w_high") else "---"), FONT_SMALL),
            ]:
                row = tk.Frame(self._frame_mid, bg=bg)
                row.pack(fill="x", padx=6, pady=1)
                tk.Label(row, text=label, font=FONT_SMALL,
                         fg=COLOR_GRAY, bg=bg).pack(side="left", padx=4)
                tk.Label(row, text=val, font=fnt,
                         fg=color if label == "Cours :" else COLOR_WHITE,
                         bg=bg).pack(side="left", padx=4)
        tk.Frame(self._frame_mid, bg=COLOR_TEAL, height=1).pack(fill="x", padx=6, pady=(8, 2))
        foot = tk.Frame(self._frame_mid, bg=BG_HEADER)
        foot.pack(fill="x", padx=6, pady=(2, 6))
        tk.Label(foot, text="Source : Yahoo Finance  |  Euronext Paris",
                 font=FONT_SMALL, fg=COLOR_GRAY, bg=BG_HEADER).pack(padx=8, pady=2)

    def _render_crypto(self, data):
        for w in self._frame_crypto.winfo_children()[2:]: w.destroy()
        hdr = tk.Frame(self._frame_crypto, bg=BG_HEADER)
        hdr.pack(fill="x", padx=6, pady=(0, 2))
        for txt in [f"{'CRYPTO':<12}", f"{'PRIX (EUR)':>16}", f"{'24h':>8}", f"{'MARKET CAP':>12}"]:
            tk.Label(hdr, text=txt, font=FONT_HEADER,
                     fg=COLOR_ORANGE, bg=BG_HEADER).pack(side="left", padx=4)
        for i, (name, d) in enumerate(data.items()):
            bg  = BG_ROW_ODD if i % 2 == 0 else BG_ROW_EVEN
            row = tk.Frame(self._frame_crypto, bg=bg)
            row.pack(fill="x", padx=6, pady=1)
            if d and d["price"]:
                arrow, color = arrow_and_color(d["change_pct"])
                pct = f"{d['change_pct']:+.2f}%" if d["change_pct"] else "  ---"
                tk.Label(row, text=f"{name:<12}", font=FONT_DATA,
                         fg=COLOR_WHITE, bg=bg).pack(side="left", padx=4)
                tk.Label(row, text=format_price(d["price"], "€", crypto=True),
                         font=FONT_DATA_B, fg=COLOR_WHITE, bg=bg).pack(side="left", padx=4)
                tk.Label(row, text=f"{arrow} {pct:>8}", font=FONT_DATA_B,
                         fg=color, bg=bg).pack(side="left", padx=4)
                tk.Label(row, text=format_marketcap(d["market_cap"]), font=FONT_SMALL,
                         fg=COLOR_GRAY, bg=bg).pack(side="left", padx=4)
            else:
                tk.Label(row, text=f"{name:<12} — données indisponibles",
                         font=FONT_DATA, fg=COLOR_GRAY, bg=bg).pack(side="left", padx=4)
        tk.Frame(self._frame_crypto, bg=COLOR_ORANGE, height=1).pack(fill="x", padx=6, pady=(4, 2))
        foot = tk.Frame(self._frame_crypto, bg=BG_HEADER)
        foot.pack(fill="x", padx=6, pady=(2, 6))
        tk.Label(foot, text="Source : CoinGecko API  |  Variation sur 24h",
                 font=FONT_SMALL, fg=COLOR_GRAY, bg=BG_HEADER).pack(padx=8, pady=2)

    # ── Cycle de rafraîchissement ──

    def _start_refresh(self): self._refresh_thread()

    def _manual_refresh(self):
        if self._refreshing: return
        if self._countdown_id is not None:
            self.after_cancel(self._countdown_id); self._countdown_id = None
        self._next_var.set(""); self._refresh_thread()

    def _request_stop(self):
        self._stop_refresh = True
        self._stop_event.set()   # interrompt immédiatement le sleep() du retry 429
        self._btn_stop.pack_forget()
        self._btn_refresh.pack(side="right", padx=(0, 12))
        self._update_status("⏸ Annulation demandée…")

    def _refresh_thread(self):
        if self._refreshing: return
        self._refreshing = True; self._stop_refresh = False
        self._stop_event.clear()                 # réarmer pour ce nouveau cycle
        self._btn_refresh.pack_forget()
        self._btn_stop.pack(side="right", padx=(0, 12))

        def worker():
            self.after(0, lambda: self._update_status("🔄 Mise à jour en cours…"))
            if self._stop_refresh:
                self.after(0, self._on_refresh_cancelled); return
            cac_data, cac_errors = fetch_cac40()
            index_data = None
            if not self._stop_refresh:
                fr = _fetch_yf_one("CAC 40 INDEX", "^FCHI")
                index_data = fr.data if fr.ok() else None
                if not fr.ok(): cac_errors.append(fr.error)
            if self._stop_refresh:
                self.after(0, self._on_refresh_cancelled); return
            mid_data, mid_errors = fetch_midcap()
            if self._stop_refresh:
                self.after(0, self._on_refresh_cancelled); return
            us_data, us_errors = fetch_us()
            if self._stop_refresh:
                self.after(0, self._on_refresh_cancelled); return
            crypto_data, crypto_errors = fetch_crypto(stop_event=self._stop_event)
            with self._lock:
                self._cac_data    = cac_data
                self._midcap_data = mid_data
                self._us_data     = us_data
                self._crypto_data = crypto_data
                self._index_data  = index_data
                self._last_errors = cac_errors + mid_errors + us_errors + crypto_errors
            self.after(0, self._update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _on_refresh_cancelled(self):
        self._refreshing = False; self._stop_refresh = False
        self._btn_stop.pack_forget()
        self._btn_refresh.pack(side="right", padx=(0, 12))
        self._update_status("⏸ Mise à jour annulée — données précédentes affichées")
        self._start_countdown(REFRESH_INTERVAL)

    def _update_ui(self):
        with self._lock:
            cac        = dict(self._cac_data)
            midcap     = dict(self._midcap_data)
            us         = dict(self._us_data)
            crypto     = dict(self._crypto_data)
            index_data = getattr(self, "_index_data", None)
            errors     = list(self._last_errors)
        self._render_cac(cac, index_data)
        self._render_midcap(midcap)
        self._render_us(us)
        self._render_crypto(crypto)
        now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        if errors:
            n = len(errors)
            self._update_status(f"✓ Mis à jour le {now}")
            self._error_var.set(f"⚠ {n} erreur{'s' if n>1 else ''} — cliquez pour détails")
        else:
            self._update_status(f"✓ Mis à jour le {now}")
            self._error_var.set("")
        self._refreshing = False
        self._btn_stop.pack_forget()
        self._btn_refresh.pack(side="right", padx=(0, 12))
        self._start_countdown(REFRESH_INTERVAL)

    def _start_countdown(self, secs_left):
        if self._refreshing: return
        if secs_left <= 0:
            self._next_var.set(""); self._refresh_thread(); return
        self._next_var.set(f"Prochaine MàJ dans {secs_left}s")
        self._countdown_id = self.after(1000, self._start_countdown, secs_left - 1)

    def _update_status(self, msg): self._status_var.set(msg)

    def _save_config_now(self):
        with _cac_symbols_lock: sel = set(CAC40_SYMBOLS.keys())
        err = save_config(sel, self._analyse_tab.get_slots_config())
        if err:
            messagebox.showwarning(
                "Sauvegarde impossible",
                f"⚠ La configuration n'a pas pu être sauvegardée.\n\n{err}\n\n"
                "Vérifiez les droits d'écriture sur le répertoire du programme.",
                parent=self,
            )

    # ── Popup erreurs ──

    def _show_errors_popup(self):
        with self._lock: errors = list(self._last_errors)
        if not errors: return
        win = tk.Toplevel(self)
        win.title("Détail des erreurs")
        win.configure(bg=BG_MAIN); win.resizable(True, False)
        win.update_idletasks()
        try:
            win.grab_set()
        except Exception:
            pass
        tk.Label(win, text=f"⚠  {len(errors)} problème(s) lors du dernier rafraîchissement",
                 font=FONT_DATA_B, fg=COLOR_ORANGE, bg=BG_MAIN, pady=10).pack(fill="x", padx=12)
        tk.Frame(win, bg=COLOR_ORANGE, height=1).pack(fill="x", padx=10, pady=(0, 8))
        frame = tk.Frame(win, bg=BG_MAIN)
        frame.pack(fill="both", padx=12, pady=4)
        for i, err in enumerate(errors):
            bg = BG_ROW_ODD if i % 2 == 0 else BG_ROW_EVEN
            tk.Label(frame, text=f"• {err}", font=("Courier New", 8),
                     fg=COLOR_WHITE, bg=bg, anchor="w", justify="left",
                     wraplength=560, padx=8, pady=3).pack(fill="x", pady=1)
        tk.Label(win,
                 text="💡 Vérifiez votre connexion réseau. CoinGecko API : quota ~10-30 req/min.",
                 font=FONT_SMALL, fg=COLOR_BLUE, bg=BG_MAIN,
                 justify="left", anchor="w", padx=8, pady=6).pack(fill="x", padx=8)
        tk.Button(win, text="✗ Fermer", font=FONT_SMALL,
                  fg=COLOR_GRAY, bg="#252a38",
                  activeforeground=COLOR_WHITE, activebackground="#353a50",
                  relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
                  command=win.destroy).pack(pady=(4, 12))
        win.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = win.winfo_width(), win.winfo_height()
        win.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _open_selection(self):
        for w in self.winfo_children():
            if isinstance(w, SelectionWindow): w.lift(); return
        SelectionWindow(self)

# ─── FENÊTRE DE SÉLECTION CAC40 ───

class SelectionWindow(tk.Toplevel):
    COLS = 4

    def __init__(self, master, symbols_dict=None, active_set=None,
                 title="Sélection des valeurs CAC 40", accent=COLOR_GOLD):
        super().__init__(master)
        self.title(title)
        self.configure(bg=BG_MAIN); self.resizable(True, True); self.grab_set()
        self._symbols = symbols_dict if symbols_dict is not None else CAC40_ALL
        self._accent  = accent
        if active_set is None:
            with _cac_symbols_lock: active_set = set(CAC40_SYMBOLS.keys())
        self._vars = {n: tk.BooleanVar(value=(n in active_set)) for n in self._symbols}
        self._build(); self._center()

    def _build(self):
        tk.Label(self, text="📋  Sélectionnez les valeurs à afficher",
                 font=FONT_TITLE, fg=self._accent, bg=BG_MAIN, pady=10).pack(fill="x", padx=12)
        tk.Frame(self, bg=self._accent, height=1).pack(fill="x", padx=10, pady=(0, 8))
        self._count_var = tk.StringVar(); self._update_count()
        tk.Label(self, textvariable=self._count_var,
                 font=FONT_SMALL, fg=COLOR_BLUE, bg=BG_MAIN).pack(anchor="w", padx=14, pady=(0, 4))

        # Zone scrollable — indispensable si > 30 valeurs
        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=12, pady=6)
        canvas = tk.Canvas(outer, bg=BG_MAIN, highlightthickness=0)
        sb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        grid = tk.Frame(canvas, bg=BG_MAIN)
        win_id = canvas.create_window((0, 0), window=grid, anchor="nw")
        def _on_resize(event): canvas.itemconfig(win_id, width=event.width)
        canvas.bind("<Configure>", _on_resize)
        grid.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        def _sel_scroll(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _sel_scroll_up(event):
            if canvas.winfo_exists(): canvas.yview_scroll(-1, "units")
        def _sel_scroll_dn(event):
            if canvas.winfo_exists(): canvas.yview_scroll( 1, "units")
        canvas.bind("<MouseWheel>", _sel_scroll)
        canvas.bind("<Button-4>",   _sel_scroll_up)
        canvas.bind("<Button-5>",   _sel_scroll_dn)
        grid.bind("<MouseWheel>",   _sel_scroll)
        grid.bind("<Button-4>",     _sel_scroll_up)
        grid.bind("<Button-5>",     _sel_scroll_dn)
        # Propager depuis les checkbuttons enfants après leur création
        self._canvas_ref = canvas  # pour _propagate_scroll

        for idx, name in enumerate(sorted(self._symbols.keys())):
            r, c = divmod(idx, self.COLS)
            tk.Checkbutton(grid, text=f"{name:<26} {self._symbols[name]}",
                           variable=self._vars[name],
                           font=("Courier New", 9), fg=COLOR_WHITE, bg=BG_PANEL,
                           selectcolor=BG_HEADER, activeforeground=self._accent,
                           activebackground=BG_PANEL, anchor="w",
                           command=self._update_count
                           ).grid(row=r, column=c, sticky="w", padx=6, pady=2)
        # Propager la molette depuis chaque checkbutton vers le canvas
        for child in grid.winfo_children():
            child.bind("<MouseWheel>", _sel_scroll)
            child.bind("<Button-4>",   _sel_scroll_up)
            child.bind("<Button-5>",   _sel_scroll_dn)
        bar = tk.Frame(self, bg=BG_MAIN)
        bar.pack(fill="x", padx=12, pady=(8, 12))
        def _btn(t, c, cmd):
            return tk.Button(bar, text=t, font=FONT_SMALL, fg=c, bg="#252a38",
                             activeforeground=COLOR_WHITE, activebackground="#353a50",
                             relief="flat", bd=0, padx=10, pady=4, cursor="hand2", command=cmd)
        _btn("✔ Tout sélectionner",   COLOR_GREEN, self._select_all).pack(side="left",  padx=4)
        _btn("✘ Tout désélectionner", COLOR_RED,   self._deselect_all).pack(side="left", padx=4)
        _btn("✓ Appliquer",            self._accent,self._apply).pack(side="right",      padx=4)
        _btn("✗ Annuler",              COLOR_GRAY,  self.destroy).pack(side="right",     padx=4)

    def _update_count(self):
        n = sum(v.get() for v in self._vars.values())
        self._count_var.set(f"{n} valeur(s) sélectionnée(s) sur {len(self._symbols)}")

    def _select_all(self):
        for v in self._vars.values(): v.set(True); self._update_count()

    def _deselect_all(self):
        for v in self._vars.values(): v.set(False); self._update_count()

    def _apply(self):
        selection = {n for n in self._symbols if self._vars[n].get()}
        if not selection:
            messagebox.showwarning("Sélection vide",
                                   "Veuillez sélectionner au moins une valeur.", parent=self)
            return
        with _cac_symbols_lock:
            global CAC40_SYMBOLS
            CAC40_SYMBOLS = {n: CAC40_ALL[n] for n in CAC40_ALL if n in selection}
        err = save_config(selection, self.master._analyse_tab.get_slots_config())
        if err:
            messagebox.showwarning(
                "Sauvegarde impossible",
                f"⚠ La sélection a été appliquée mais n'a pas pu être sauvegardée.\n\n{err}\n\n"
                "Elle sera perdue au prochain démarrage.",
                parent=self,
            )
        self.destroy()
        self.master._manual_refresh()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

# ─── FENÊTRE DE SÉLECTION US ───

class USSelectionWindow(SelectionWindow):
    """Fenêtre de sélection pour les valeurs US (S&P500 + NASDAQ100).
    Hérite de SelectionWindow — seuls _apply et _center sont surchargés."""

    COLS = 3   # 3 colonnes pour les noms US plus longs

    def __init__(self, master):
        with _us_symbols_lock: active = set(US_SYMBOLS_ACTIVE.keys())
        super().__init__(
            master,
            symbols_dict=US_ALL_SYMBOLS,
            active_set=active,
            title="Sélection des valeurs US (S&P500 · NASDAQ100)",
            accent=COLOR_BLUE,
        )

    def _apply(self):
        selection = {n for n in US_ALL_SYMBOLS if self._vars[n].get()}
        if not selection:
            messagebox.showwarning("Sélection vide",
                                   "Veuillez sélectionner au moins une valeur.", parent=self)
            return
        with _us_symbols_lock:
            global US_SYMBOLS_ACTIVE
            US_SYMBOLS_ACTIVE = {n: US_ALL_SYMBOLS[n] for n in US_ALL_SYMBOLS if n in selection}
        # Sauvegarde étendue : on inclut la sélection US dans le JSON
        try:
            import json as _json
            cfg = {}
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = _json.load(f)
            except Exception:
                pass
            cfg["us_selection"] = sorted(selection)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                _json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showwarning(
                "Sauvegarde impossible",
                f"⚠ La sélection US n'a pas pu être sauvegardée.\n\n{e}",
                parent=self,
            )
        self.destroy()
        self.master._manual_refresh()

# ─── POINT D'ENTRÉE ───

if __name__ == "__main__":
    _config = load_config()
    with _cac_symbols_lock:
        CAC40_SYMBOLS = {k: v for k, v in CAC40_ALL.items()
                         if k in set(_config.get("cac40_selection", []))}
    with _us_symbols_lock:
        _saved_us = set(_config.get("us_selection", []))
        if _saved_us:
            US_SYMBOLS_ACTIVE = {k: v for k, v in US_ALL_SYMBOLS.items()
                                  if k in _saved_us}
    app = Dashboard(config=_config)
    app.mainloop()
