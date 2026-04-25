from PySide6.QtGui import QBrush, QPalette, QPixmap, QIcon
from asset_cache import get_pixmap_cached, get_text_cached
from PySide6.QtCore import Qt, QFile, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QMenuBar, QMenu, QDialog, QComboBox, QCheckBox, QSizePolicy, QInputDialog, QFrame,
    QProgressDialog
)

# Versione corrente dell'applicazione
VERSION = "2.2.1"
GITHUB_REPO = "DanielePigoli/ATK-Pro-v3"

# Stato globale
state = {
    "records": [],
    "formats": [],
    "output_folder": None,
    "registri_output": [],
    "current_input_file": None  # Memorizza il percorso del file attualmente caricato
}
# Import standard all'inizio
import sys

def carica_testo_asset(percorso):
    try:
        return get_text_cached(percorso)
    except Exception:
        return ""
    except UnicodeDecodeError:
        try:
            return get_text_cached(percorso)
        except Exception:
            return ""


def show_operation_completed_dialog(parent, glossario_data, lingua, risultati=None):
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
    from PySide6.QtGui import QIcon, QFont
    from PySide6.QtCore import Qt
    try:
        from .main_gui_qt import get_msg, asset_path
    except ImportError:
        from main_gui_qt import get_msg, asset_path

    dlg = QDialog(parent)
    dlg.setWindowTitle(get_msg(glossario_data, "Operazione completata", lingua.upper()))
    try:
        dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
    except Exception:
        pass
    dlg.setStyleSheet("""
        QDialog {
            background-color: #181818;
            color: #fff;
            border: 2px solid #a67c52;
        }
        QLabel, QPushButton {
            color: #fff;
            font-size: 16px;
        }
        QPushButton {
            background-color: #222;
            border: 1px solid #a67c52;
            padding: 6px 18px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #333;
        }
    """)
    layout = QVBoxLayout()
    layout.setContentsMargins(30, 25, 30, 25)
    layout.setSpacing(18)
    msg = QLabel(get_msg(glossario_data, "Operazione completata", lingua.upper()))
    msg.setAlignment(Qt.AlignCenter)
    msg.setStyleSheet("QLabel { background: transparent; color: #fff; font-size: 20px; font-weight: bold; }")
    # Effetto ombra su QLabel
    from PySide6.QtWidgets import QGraphicsDropShadowEffect
    shadow_msg = QGraphicsDropShadowEffect()
    shadow_msg.setBlurRadius(12)
    shadow_msg.setOffset(2, 2)
    shadow_msg.setColor(Qt.black)
    msg.setGraphicsEffect(shadow_msg)
    layout.addWidget(msg)

    # Se risultati è passato, mostra un report dettagliato dei record incompleti
    if risultati:
        report_lines = []
        for rec in risultati:
            if rec.get("status") == "INCOMPLETE":
                report_lines.append(f"<b>{rec.get('file','?')}</b> - <span style='color:#ffb347;'>IMMAGINI MANCANTI</span>")
                tiles = rec.get("tiles_missing") or []
                for t in tiles[:10]:
                    report_lines.append(f"<span style='font-size:12px;'>{t}</span>")
                if len(tiles) > 10:
                    report_lines.append(f"...({len(tiles)-10} altri tile non mostrati)")
        if report_lines:
            report_text = "<br>".join(report_lines)
            report_box = QTextEdit()
            report_box.setReadOnly(True)
            report_box.setHtml(f"<div style='color:#fff;'>{report_text}</div>")
            report_box.setStyleSheet("background-color: #222; color: #fff; font-size: 14px; border: 1px solid #a67c52; border-radius: 6px; padding: 8px;")
            layout.addWidget(report_box)

    ok_btn = QPushButton(get_msg(glossario_data, "Chiudi", lingua.upper()))
    ok_btn.clicked.connect(dlg.accept)
    # Effetto ombra su QPushButton
    shadow_btn = QGraphicsDropShadowEffect()
    shadow_btn.setBlurRadius(16)
    shadow_btn.setOffset(3, 3)
    shadow_btn.setColor(Qt.black)
    ok_btn.setGraphicsEffect(shadow_btn)
    layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
    dlg.setLayout(layout)
    dlg.adjustSize()
    dlg.setFixedSize(dlg.sizeHint())
    dlg.exec()
def get_language_from_registry():
    """Legge la lingua selezionata durante l'installazione dal registro Windows."""
    try:
        import winreg
        reg_path = r"Software\\ATK-Pro"
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
            lang, _ = winreg.QueryValueEx(reg_key, "Language")
            winreg.CloseKey(reg_key)
            logging.debug(f"Lingua letta dal registro: {lang}")
            lingue_valide = ["it", "en", "es", "de", "fr", "pt", "nl", "ar", "he", "ru",
                             "da", "el", "ja", "no", "pl", "ro", "sv", "tr", "vi", "zh"]
            return lang if lang in lingue_valide else "en"
        except FileNotFoundError:
            logging.debug("Chiave registro ATK-Pro non trovata")
            return "en"
    except (ImportError, OSError) as e:
        logging.debug(f"Impossibile leggere registro: {e}")
        return "en"


_LINGUE_VALIDE = ["it", "en", "es", "de", "fr", "pt", "nl", "ar", "he", "ru",
                  "da", "el", "ja", "no", "pl", "ro", "sv", "tr", "vi", "zh"]


def _config_file_path():
    """Ritorna il percorso del file di configurazione utente.
    In modalità portable (portable.txt accanto all'exe): config.json nella cartella dell'exe.
    In modalità installata: ~/.config/atk-pro/config.json
    """
    import os as _os
    if IS_PORTABLE:
        return _os.path.join(_EXE_DIR, "config.json")
    return _os.path.join(_os.path.expanduser("~"), ".config", "atk-pro", "config.json")


def _read_config_language():
    """Legge la lingua salvata nel file di configurazione utente (Linux/macOS)."""
    import os as _os
    import json as _json
    try:
        cfg = _config_file_path()
        if _os.path.exists(cfg):
            with open(cfg, encoding="utf-8") as fh:
                data = _json.load(fh)
            lang = data.get("language", "")
            if lang in _LINGUE_VALIDE:
                logging.debug(f"Lingua letta da config file: {lang}")
                return lang
    except Exception as e:
        logging.debug(f"Errore lettura config file: {e}")
    return None


def _write_config_language(lang: str) -> None:
    """Salva la lingua scelta nel file di configurazione utente (Linux/macOS)."""
    import os as _os
    import json as _json
    try:
        cfg = _config_file_path()
        cfg_dir = _os.path.dirname(cfg)
        _os.makedirs(cfg_dir, exist_ok=True)
        data = {}
        if _os.path.exists(cfg):
            with open(cfg, encoding="utf-8") as fh:
                data = _json.load(fh)
        data["language"] = lang
        with open(cfg, "w", encoding="utf-8") as fh:
            _json.dump(data, fh, ensure_ascii=False, indent=2)
        logging.debug(f"Lingua salvata in config file: {lang}")
    except Exception as e:
        logging.debug(f"Errore scrittura config file: {e}")


def _read_config_prefs() -> dict:
    """Legge le preferenze persistenti (formati, cartelle, ultimo input) dal config JSON."""
    import os as _os
    import json as _json
    try:
        cfg = _config_file_path()
        if _os.path.exists(cfg):
            with open(cfg, encoding="utf-8") as fh:
                data = _json.load(fh)
            return {
                "formats":            data.get("formats", []),
                "last_input_file":    data.get("last_input_file", None),
                "output_folders_doc": data.get("output_folders_doc", []),
                "output_folders_reg": data.get("output_folders_reg", []),
                "output_folder_single": data.get("output_folder_single", None),
                "output_folder_doc":    data.get("output_folder_doc", None),
                "output_folder_reg":    data.get("output_folder_reg", None),
            }
    except Exception as e:
        logging.debug(f"Errore lettura prefs config: {e}")
    return {"formats": [], "last_input_file": None, "output_folders_doc": [], "output_folders_reg": [],
            "output_folder_single": None, "output_folder_doc": None, "output_folder_reg": None}


def _write_config_prefs(key: str, value) -> None:
    """Aggiorna una singola chiave delle preferenze nel config JSON."""
    import os as _os
    import json as _json
    try:
        cfg = _config_file_path()
        cfg_dir = _os.path.dirname(cfg)
        _os.makedirs(cfg_dir, exist_ok=True)
        data = {}
        if _os.path.exists(cfg):
            with open(cfg, encoding="utf-8") as fh:
                data = _json.load(fh)
        data[key] = value
        with open(cfg, "w", encoding="utf-8") as fh:
            _json.dump(data, fh, ensure_ascii=False, indent=2)
        logging.debug(f"Prefs salvate: {key}={value}")
    except Exception as e:
        logging.debug(f"Errore scrittura prefs config: {e}")


def _is_first_run() -> bool:
    """Ritorna True se il config file non esiste ancora (primo avvio)."""
    import os as _os
    return not _os.path.exists(_config_file_path())


def _read_config_disclaimer_accepted() -> bool:
    """Ritorna True se l'utente ha già accettato il disclaimer (chiave disclaimer_accepted nel config)."""
    import os as _os
    import json as _json
    try:
        cfg = _config_file_path()
        if _os.path.exists(cfg):
            with open(cfg, encoding="utf-8") as fh:
                data = _json.load(fh)
            return bool(data.get("disclaimer_accepted", False))
    except Exception:
        pass
    return False


def _write_config_disclaimer_accepted() -> None:
    """Scrive disclaimer_accepted=true nel config JSON."""
    _write_config_prefs("disclaimer_accepted", True)


def _get_default_output_dir(sub: str = "") -> str:
    """Ritorna il percorso della cartella output di default.
    In modalità portable: <cartella exe>/output/
    In modalità installata: ~/Documenti/ATK-Pro/output/
    """
    if IS_PORTABLE:
        base = os.path.join(_EXE_DIR, "output")
    else:
        from PySide6.QtCore import QStandardPaths
        docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        base = os.path.join(docs, "ATK-Pro", "output")
    return os.path.join(base, sub) if sub else base


def _ensure_default_output_dirs() -> None:
    """Crea silenziosamente le 3 cartelle output di default se non esistono."""
    for sub in ("", "doc", "reg"):
        try:
            os.makedirs(_get_default_output_dir(sub), exist_ok=True)
        except Exception as e:
            logging.debug(f"_ensure_default_output_dirs: impossibile creare {sub}: {e}")


def ask_output_mode(glossario_data, lingua) -> str:
    """Dialog per scegliere la modalità di selezione cartelle output.
    Ritorna: 'single' | 'split' | 'per_record'
    """
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QButtonGroup, QPushButton, QLabel
    dlg = QDialog()
    dlg.setWindowTitle(get_msg(glossario_data, "Cartelle output", lingua.upper()) or "Cartelle di output")
    dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
    _setup_dialog_pergamena(dlg, 440, 240)

    layout = QVBoxLayout(dlg)
    lbl = QLabel(get_msg(glossario_data, "Scegli modalità cartelle output", lingua.upper())
                 or "Scegli come organizzare le cartelle di output:")
    lbl.setWordWrap(True)
    lbl.setStyleSheet("color:#fff; font-size:14px;")
    layout.addWidget(lbl)

    grp = QButtonGroup(dlg)
    r_single     = QRadioButton(get_msg(glossario_data, "Cartella unica per tutti", lingua.upper())
                                or "Cartella unica per tutti i record")
    r_split      = QRadioButton(get_msg(glossario_data, "Cartelle separate doc/reg", lingua.upper())
                                or "Cartelle separate: Documenti e Registri")
    r_per_record = QRadioButton(get_msg(glossario_data, "Cartella per ogni record", lingua.upper())
                                or "Una cartella per ogni singolo record")
    _radio_style = """
        QRadioButton { color: #fff; font-size: 13px; padding: 4px 6px; border-radius: 4px; }
        QRadioButton:checked { background: rgba(255,255,255,0.25); color: #ffe96a; font-weight: bold; }
        QRadioButton::indicator { width: 14px; height: 14px; }
    """
    for r in (r_single, r_split, r_per_record):
        r.setStyleSheet(_radio_style)
        grp.addButton(r)
        layout.addWidget(r)

    # Preseleziona dall'ultimo uso
    _saved_mode = _read_config_prefs().get("output_mode", "per_record")
    if _saved_mode == "single":     r_single.setChecked(True)
    elif _saved_mode == "split":    r_split.setChecked(True)
    else:                           r_per_record.setChecked(True)

    btn_ok = QPushButton(get_msg(glossario_data, "Conferma", lingua.upper()) or "Conferma")
    btn_ok.clicked.connect(dlg.accept)
    layout.addWidget(btn_ok, alignment=Qt.AlignCenter)

    if dlg.exec() != QDialog.Accepted:
        # annullato: torna alla modalità salvata
        return _saved_mode
    if r_single.isChecked():     return "single"
    if r_split.isChecked():      return "split"
    return "per_record"
def asset_path(rel_path):
    return os.path.join(BASE_DIR, rel_path)
from PySide6.QtGui import QBrush, QPalette, QPixmap, QIcon
from asset_cache import get_pixmap_cached, get_text_cached
from PySide6.QtCore import Qt, QFile, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QMenuBar, QMenu, QDialog, QComboBox, QCheckBox, QSizePolicy, QInputDialog
)
# Stato globale
state = {
    "records": [],
    "formats": [],
    "output_folder": None,
    "registri_output": [],
    "current_input_file": None  # Memorizza il percorso del file attualmente caricato
}
# Import standard all'inizio
import sys

def scegli_lingua(glossario_data=None, lingua="it"):
    dlg = QDialog()
    dlg.resize(460, 180)
    dlg.setWindowTitle(get_msg(glossario_data, "Seleziona lingua", lingua.upper()) if glossario_data else "Seleziona lingua")
    dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
    try:
        _setup_dialog_pergamena(dlg, 460, 180)
    except Exception:
        pass

    layout = QVBoxLayout(dlg)
    label = QLabel(get_msg(glossario_data, "Scegli la lingua dell'interfaccia", lingua.upper()) if glossario_data else "Scegli la lingua dell'interfaccia")

    combo = QComboBox()
    import os
    import locale
    asset_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    lingue_supportate = [d for d in os.listdir(asset_dir) if os.path.isdir(os.path.join(asset_dir, d)) and d != "common"]
    nomi_lingue = {
        "it": "Italiano",
        "en": "English",
        "es": "Español",
        "fr": "Français",
        "de": "Deutsch",
        "pt": "Português",
        "ru": "Русский",
        "ar": "العربية",
        "nl": "Nederlands",
        "he": "עברית",
        "ja": "日本語",
        "zh": "中文",
        "pl": "Polski",
        "tr": "Türkçe",
        "uk": "Українська",
        "cs": "Čeština",
        "el": "Ελληνικά",
        "hu": "Magyar",
        "ro": "Română",
        "sv": "Svenska",
        "vi": "Tiếng Việt",
        "da": "Dansk"
    }
    import locale
    try:
        locale.setlocale(locale.LC_ALL, "")
        sys_locale = locale.getlocale()[0]
    except Exception:
        sys_locale = None
    sys_lang = None
    if sys_locale:
        mapping = {
            'italian': 'it', 'english': 'en', 'german': 'de', 'french': 'fr', 'spanish': 'es',
            'portuguese': 'pt', 'russian': 'ru', 'arabic': 'ar', 'dutch': 'nl', 'hebrew': 'he',
            'japanese': 'ja', 'chinese': 'zh', 'polish': 'pl', 'turkish': 'tr', 'ukrainian': 'uk',
            'czech': 'cs', 'greek': 'el', 'hungarian': 'hu', 'romanian': 'ro', 'swedish': 'sv',
            'vietnamese': 'vi', 'danish': 'da', 'norwegian': 'no'
        }
        if '_' in sys_locale:
            sys_lang = sys_locale.split('_')[0].lower()
        elif '-' in sys_locale:
            sys_lang = sys_locale.split('-')[0].lower()
        elif ' ' in sys_locale:
            sys_lang = sys_locale.split(' ')[0].lower()
        else:
            sys_lang = sys_locale.lower()
        # Normalizza sempre tramite mapping
        sys_lang = mapping.get(sys_lang, sys_lang)
    import logging
    logging.debug(f"[DEBUG LINGUA] sys_locale={sys_locale}, sys_lang={sys_lang}, lingue_supportate={lingue_supportate}")
    # Log dettagliato per selezione
    idx = 0
    if sys_lang and sys_lang in lingue_supportate:
        idx = lingue_supportate.index(sys_lang)
        logging.debug(f"[DEBUG LINGUA] Seleziono sys_lang: {sys_lang} (idx={idx})")
    elif 'en' in lingue_supportate:
        idx = lingue_supportate.index('en')
        logging.debug(f"[DEBUG LINGUA] sys_lang non trovata, seleziono 'en' (idx={idx})")
    else:
        logging.debug(f"[DEBUG LINGUA] sys_lang e 'en' non trovate, seleziono idx=0")
    import logging
    logging.debug(f"[DEBUG LINGUA] sys_locale={sys_locale}, sys_lang={sys_lang}, lingue_supportate={lingue_supportate}")
    for codice in lingue_supportate:
        nome = nomi_lingue.get(codice, codice)
        if codice == "no":
            nome = "Norsk"  # Autonimo norvegese
        combo.addItem(nome, codice)

    # Imposta come default la lingua di sistema se presente, altrimenti su 'en' se esiste
    idx = 0  # Default: prima voce
    if sys_lang and sys_lang in lingue_supportate:
        idx = lingue_supportate.index(sys_lang)
    elif 'en' in lingue_supportate:
        idx = lingue_supportate.index('en')
    combo.setCurrentIndex(idx)

    btns = QHBoxLayout()
    ok_btn = QPushButton(get_msg(glossario_data, "Conferma", lingua.upper()) if glossario_data else "Conferma")
    cancel_btn = QPushButton(get_msg(glossario_data, "Annulla", lingua.upper()) if glossario_data else "Annulla")
    ok_btn.clicked.connect(dlg.accept)
    cancel_btn.clicked.connect(dlg.reject)
    btns.addWidget(ok_btn)
    btns.addWidget(cancel_btn)

    layout.addWidget(label)
    layout.addWidget(combo)
    layout.addLayout(btns)

    if dlg.exec() == QDialog.Accepted:
        return combo.currentData()
    return "en"
import os
import json
import sys
SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import logging
import logging
import elaborazione as elaborazione_mod

from input_loader import load_input_file
from input_parser import parse_input_text

# Inizializzazione BASE_DIR subito dopo gli import
_is_frozen = getattr(sys, 'frozen', False)
if _is_frozen:
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory dell'eseguibile (per modalità portable)
# Quando frozen: cartella dell'exe reale (non sys._MEIPASS che è una dir temp)
# Quando non frozen: stessa di BASE_DIR
_EXE_DIR = os.path.dirname(sys.executable) if _is_frozen else BASE_DIR
_PORTABLE_SENTINEL = os.path.join(_EXE_DIR, "portable.txt")
IS_PORTABLE = os.path.exists(_PORTABLE_SENTINEL)


# Inizializzazione ASSET_LANG e ASSET_COMMON subito dopo BASE_DIR
ASSET_COMMON = os.path.join(BASE_DIR, "assets", "common")
ASSET_LANG = os.path.join(BASE_DIR, "assets")
# Funzioni di utilità definite subito dopo gli import

def carica_file_esempio(lingua: str) -> str:
    path = os.path.join(ASSET_LANG, lingua, "testuali", "input_link_base_v2.0.txt")
    if not os.path.exists(path):
        path = os.path.join(ASSET_LANG, "en", "testuali", "input_link_base_v2.0.txt")
    return path

def carica_glossario(lang):
    path = os.path.join(BASE_DIR, "docs_generali", "glossario_multilingua_ATK-Pro.json")
    logger = logging.getLogger(__name__)
    try:
        text = get_text_cached(path)
        return json.loads(text)
    except FileNotFoundError:
        show_error(f"Glossario non trovato: {path}", level="warning")
        return {}
    except json.JSONDecodeError as e:
        show_error(f"Errore decodifica JSON nel glossario '{path}': {e}", level="warning")
        return {}
    except Exception as e:
        show_error(f"Errore imprevisto caricando il glossario '{path}': {e}", level="error")
        return {}

def get_msg(glossario, chiave, lingua):
    lingua = lingua.upper()
    if lingua == "DK":
        lingua = "DA"
    if lingua == "VN":
        lingua = "VI"
    # Cerca in tutte le sezioni del glossario
    for section in glossario.values():
        if isinstance(section, list):
            for voce in section:
                if voce.get("messaggio") == chiave:
                    return voce.get(lingua, voce.get("IT", None))
    # Fallback: None se non trovata
    return None
def style_msgbox_pergamena(msgbox, w=820, h=200):
    """Applica lo stile nero/bianco a un QMessageBox, come per i QDialog personalizzati."""
    msgbox.setMinimumSize(w, h)
    msgbox.setStyleSheet("""
        QMessageBox {
            background-color: #181818;
            color: #fff;
            border: 2px solid #a67c52;
        }
        QLabel, QPushButton {
            color: #fff;
            font-size: 15px;
        }
        QPushButton {
            background-color: #222;
            border: 1px solid #a67c52;
            padding: 6px 18px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #333;
        }
    """)
    # Sfondo come _setup_dialog_pergamena
    bg_pixmap = get_pixmap_cached(asset_path("assets/common/grafici/Sfondo.png"))
    if bg_pixmap.isNull():
        bg_pixmap = get_pixmap_cached(asset_path("assets/common/grafici/Sfondo.webp"))
    if not bg_pixmap.isNull():
        scaled_bg = bg_pixmap.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        msgbox.setPalette(palette)


def show_msgbox_localized(parent, glossario_data, lingua, title, text, icon=QMessageBox.Information, buttons=("Conferma",), default="Conferma"):
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    # Localizza le etichette dei pulsanti tramite il glossario (i valori di ritorno rimangono le chiavi originali)
    if glossario_data is not None:
        loc_buttons = tuple(get_msg(glossario_data, b, lingua) or b for b in buttons)
    else:
        loc_buttons = buttons
    dlg = QDialog(parent) if parent is not None else QDialog()
    dlg.setWindowTitle(title)
    dlg.setStyleSheet("""
        QDialog {
            background-color: #181818;
            color: #fff;
            border: 2px solid #a67c52;
        }
        QLabel, QPushButton {
            color: #fff;
            font-size: 15px;
        }
        QPushButton {
            background-color: #222;
            border: 1px solid #a67c52;
            padding: 6px 18px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #333;
        }
    """)
    layout = QVBoxLayout(dlg)
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    label.setStyleSheet("color: #fff; font-size: 15px;")
    layout.addWidget(label)
    btn_layout = QHBoxLayout()
    btns = []
    for b_loc in loc_buttons:
        btn = QPushButton(b_loc)
        btns.append(btn)
        btn_layout.addWidget(btn)
    layout.addLayout(btn_layout)
    dlg.setLayout(layout)
    # Connessione pulsanti — il valore di ritorno usa la chiave originale (IT)
    result = default
    for i, btn in enumerate(btns):
        def handler(idx=i):
            nonlocal result
            result = buttons[idx]
            dlg.accept()
        btn.clicked.connect(handler)
    dlg.exec()
    return result

# Import standard all'inizio
import sys
import os
import json
import logging
from logging.handlers import RotatingFileHandler
# Configurazione logging IMMEDIATA
_is_frozen = getattr(sys, 'frozen', False)
ATKPRO_ENV = os.environ.get("ATKPRO_ENV", "development").lower()
_log_level = logging.WARNING if _is_frozen or ATKPRO_ENV == "production" else logging.DEBUG
_log_format = "%(levelname)s: %(message)s" if _is_frozen or ATKPRO_ENV == "production" else "DEBUG: %(message)s"
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'atkpro_debug.log')
handlers = [logging.StreamHandler(sys.stdout)]
if ATKPRO_ENV != "production":
    handlers.append(RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'))
logging.basicConfig(level=_log_level, format=_log_format, handlers=handlers)
logging.info('TEST LOG INIZIO FILE')

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QMenuBar, QMenu, QDialog, QComboBox, QCheckBox, QSizePolicy
)
from PySide6.QtGui import QFontDatabase
import urllib.request as _urllib_req
import json as _json_mod
import re as _re_mod
import tempfile as _tempfile_mod
import subprocess as _subprocess_mod
from PySide6.QtCore import QThread, Signal as _Signal


class _UpdateCheckerThread(QThread):
    """Controlla la versione disponibile su GitHub senza bloccare la UI."""
    result = _Signal(bool, str, str, object)  # is_newer, latest_version, release_url, assets

    def run(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = _urllib_req.Request(url, headers={'User-Agent': 'ATK-Pro'})
            with _urllib_req.urlopen(req, timeout=10) as resp:
                data = _json_mod.loads(resp.read().decode())
            latest_version = data.get('tag_name', '').lstrip('v')
            release_url = data.get('html_url', '')
            assets = data.get('assets', [])
            current = [int(x) for x in VERSION.split('.')]
            latest  = [int(x) for x in latest_version.split('.')]
            max_len = max(len(current), len(latest))
            current += [0] * (max_len - len(current))
            latest  += [0] * (max_len - len(latest))
            self.result.emit(latest > current, latest_version, release_url, assets)
        except Exception:
            self.result.emit(False, '', '', [])


class _DownloadThread(QThread):
    """Scarica un file in background con progress reporting."""
    progress = _Signal(int, int)    # bytes_scaricati, bytes_totali
    finished = _Signal(str)         # percorso file scaricato
    error_occurred = _Signal(str)   # messaggio errore

    def __init__(self, url: str, dest_path: str):
        super().__init__()
        self._url = url
        self._dest_path = dest_path

    def run(self):
        try:
            req = _urllib_req.Request(self._url, headers={'User-Agent': 'ATK-Pro'})
            with _urllib_req.urlopen(req, timeout=300) as resp:
                total = int(resp.headers.get('Content-Length', 0))
                downloaded = 0
                with open(self._dest_path, 'wb') as fh:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        fh.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total)
            self.finished.emit(self._dest_path)
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class MainWindow(QMainWindow):
    def cambia_lingua(self):
        nuova_lingua = scegli_lingua(self.glossario_data, self.lingua)
        if nuova_lingua and nuova_lingua != self.lingua:
            self.lingua = nuova_lingua
            # Salva sempre nel config file (Linux/macOS/sviluppo)
            _write_config_language(self.lingua)
            # Su Windows salva anche nel registro (per compatibilità installer)
            try:
                import winreg
                reg_path = r"Software\\ATK-Pro"
                reg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
                winreg.SetValueEx(reg_key, "Language", 0, winreg.REG_SZ, self.lingua)
                winreg.CloseKey(reg_key)
            except Exception as e:
                import logging
                logging.debug(f"Registro Windows non disponibile (normale su Linux/macOS): {e}")
            show_operation_completed_dialog(self, self.glossario_data, self.lingua)
            # Dialog stile "Funzione in sviluppo"
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
            dlg = QDialog(self)
            dlg.setWindowTitle(get_msg(self.glossario_data, "Riavvio richiesto", self.lingua) or "Riavvio richiesto")
            _setup_dialog_pergamena(dlg, 600, 250)
            layout = QVBoxLayout(dlg)
            msg = get_msg(self.glossario_data, "Riavvio richiesto", self.lingua)
            if not msg or msg == "Riavvio richiesto":
                msg = "Per applicare la modifica della lingua è necessario riavviare l'applicazione."
            label = QLabel(msg)
            label.setStyleSheet("color: #fff; font-size: 16px;")
            layout.addWidget(label)
            ok_btn = QPushButton(get_msg(self.glossario_data, "Chiudi", self.lingua) or "Chiudi")
            ok_btn.clicked.connect(dlg.accept)
            layout.addWidget(ok_btn)
            dlg.setLayout(layout)
            dlg.exec()

    def verifica_aggiornamenti(self):
        """Controlla se è disponibile una nuova versione su GitHub"""
        import urllib.request, json
        gm = lambda k: get_msg(self.glossario_data, k, self.lingua) or k
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'ATK-Pro'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            latest_version = data.get('tag_name', '').lstrip('v')
            release_url = data.get('html_url', '')
            assets = data.get('assets', [])
            current = [int(x) for x in VERSION.split('.')]
            latest  = [int(x) for x in latest_version.split('.')]
            max_len = max(len(current), len(latest))
            current += [0] * (max_len - len(current))
            latest  += [0] * (max_len - len(latest))
            is_newer = latest > current
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                is_newer, latest_version, release_url, assets = False, VERSION, '', []
            else:
                QMessageBox.warning(self, gm("Verifica aggiornamenti"),
                    f"{gm('Errore verifica aggiornamenti')}\n\nHTTP {exc.code}")
                return
        except Exception as exc:
            QMessageBox.warning(self, gm("Verifica aggiornamenti"),
                f"{gm('Errore verifica aggiornamenti')}\n\n{exc}")
            return
        self._mostra_dialogo_aggiornamento(is_newer, latest_version, release_url, assets)

    def _mostra_dialogo_aggiornamento(self, is_newer, latest_version, release_url, assets, silent_if_ok=False):
        """Mostra il dialogo risultato verifica aggiornamenti.
        silent_if_ok=True: non mostra nulla se la versione è già aggiornata."""
        import sys
        gm = lambda k: get_msg(self.glossario_data, k, self.lingua) or k

        if not is_newer:
            if silent_if_ok:
                return
            result_msg = (f"{gm('Nessun aggiornamento disponibile')}\n\n"
                         f"{gm('Versione corrente')}: {VERSION}")
        else:
            result_msg = (f"{gm('Nuova versione disponibile')}!\n\n"
                         f"{gm('Versione corrente')}: {VERSION}\n"
                         f"{gm('Ultima versione')}: {latest_version}")

        dlg = QDialog(self)
        dlg.setWindowTitle(gm("Verifica aggiornamenti"))
        dlg.setStyleSheet("""
            QDialog {
                background-color: #181818;
                color: #fff;
                border: 2px solid #a67c52;
            }
            QLabel, QPushButton {
                color: #fff;
                font-size: 16px;
            }
            QPushButton {
                background-color: #222;
                border: 1px solid #a67c52;
                padding: 6px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(18)

        msg_label = QLabel(result_msg)
        msg_label.setStyleSheet("QLabel { background: transparent; color: #FFFFFF; font-size: 16px; }")
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)

        if is_newer:
            # "Aggiorna automaticamente" solo per versione installata su Windows (non portable)
            # La portable deve scaricare lo ZIP dalla pagina GitHub manualmente
            if sys.platform == 'win32' and assets and not IS_PORTABLE:
                auto_btn = QPushButton(gm("Aggiorna automaticamente") or "Aggiorna automaticamente")
                auto_btn.clicked.connect(
                    lambda: (dlg.accept(), self._avvia_aggiornamento_automatico(assets, latest_version))
                )
                layout.addWidget(auto_btn, alignment=Qt.AlignCenter)

            if IS_PORTABLE:
                portable_note = QLabel(
                    gm("Versione Portable: scarica il nuovo ZIP dalla pagina GitHub.")
                )
                portable_note.setStyleSheet(
                    "QLabel { background: transparent; color: #f0c060; font-size: 13px; }"
                )
                portable_note.setAlignment(Qt.AlignCenter)
                portable_note.setWordWrap(True)
                layout.addWidget(portable_note)

            web_btn = QPushButton(gm("Apri pagina di download") or "Apri pagina di download")
            web_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(release_url)))
            layout.addWidget(web_btn, alignment=Qt.AlignCenter)

        close_btn = QPushButton(gm("Chiudi") or "Chiudi")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dlg.setLayout(layout)
        dlg.exec()

    def _avvia_aggiornamento_automatico(self, assets, latest_version):
        """Scarica e installa automaticamente il nuovo installer (solo Windows)."""
        gm = lambda k: get_msg(self.glossario_data, k, self.lingua) or k

        installer_asset = None
        for a in assets:
            name = a.get('name', '')
            if _re_mod.match(r'^ATK-Pro-Setup-v[\d.]+\.exe$', name):
                installer_asset = a
                break

        if not installer_asset:
            release_url = f"https://github.com/{GITHUB_REPO}/releases/latest"
            QMessageBox.warning(
                self, gm("Aggiornamento"),
                gm("Installer Windows non trovato nella release.") + "\n" +
                gm("Visita la pagina GitHub per scaricarlo manualmente."))
            QDesktopServices.openUrl(QUrl(release_url))
            return

        download_url = installer_asset['browser_download_url']
        asset_name = installer_asset['name']
        if not _re_mod.match(r'^[A-Za-z0-9_.\-]+$', asset_name):
            QMessageBox.critical(self, gm("Errore"), "Nome file installer non valido.")
            return

        tmp_dir = _tempfile_mod.mkdtemp(prefix='atkpro_update_')
        dest_path = os.path.join(tmp_dir, asset_name)
        if not os.path.abspath(dest_path).startswith(os.path.abspath(tmp_dir)):
            QMessageBox.critical(self, gm("Errore"), "Errore di sicurezza nel percorso file.")
            return

        total_mb = installer_asset.get('size', 0) / (1024 * 1024)
        label_text = gm("Download in corso") + f" — ATK-Pro v{latest_version}"
        if total_mb > 0:
            label_text += f"\n({total_mb:.0f} MB)"

        progress_dlg = QProgressDialog(label_text, gm("Annulla") or "Annulla", 0, 100, self)
        progress_dlg.setWindowModality(Qt.WindowModal)
        progress_dlg.setWindowTitle((gm("Aggiornamento") or "Aggiornamento") + " ATK-Pro")
        progress_dlg.setMinimumWidth(420)
        progress_dlg.setValue(0)
        progress_dlg.show()

        self._download_thread = _DownloadThread(download_url, dest_path)
        _tmp_dir_ref = tmp_dir

        def on_progress(done, total):
            if progress_dlg.wasCanceled():
                self._download_thread.terminate()
                import shutil
                shutil.rmtree(_tmp_dir_ref, ignore_errors=True)
                return
            progress_dlg.setValue(int(done * 100 / total) if total > 0 else 0)
            if not total:
                progress_dlg.setMaximum(0)

        def on_finished(path):
            progress_dlg.reset()
            progress_dlg.close()
            try:
                _subprocess_mod.Popen([path, '/SILENT', '/NORESTART'])
            except Exception as exc:
                QMessageBox.critical(
                    self, gm("Errore"),
                    gm("Impossibile avviare l'installer") + f":\n{exc}")
                return
            QApplication.instance().quit()

        def on_error(msg):
            progress_dlg.reset()
            progress_dlg.close()
            import shutil
            shutil.rmtree(_tmp_dir_ref, ignore_errors=True)
            QMessageBox.critical(
                self, gm("Errore download"),
                gm("Download fallito") + f":\n{msg}")

        self._download_thread.progress.connect(on_progress)
        self._download_thread.finished.connect(on_finished)
        self._download_thread.error_occurred.connect(on_error)
        self._download_thread.start()

    def __init__(self, glossario_data, lingua):
        super().__init__()
        self.glossario_data = glossario_data
        self.lingua = lingua

        # Ripristina titlebar nativa
        self.setWindowTitle("ATK-Pro")

        # Riga marrone sopra il motto e motto in fondo (widget assoluti)
        self.motto_separator = QLabel(self)
        self.motto_separator.setFixedHeight(4)
        self.motto_separator.setStyleSheet("background: #a67c52;")
        self.motto_separator.raise_()

        motto_path = asset_path("assets/common/testuali/Motto_latino.txt")
        try:
            with open(motto_path, "r", encoding="utf-8") as f:
                motto = f.read().strip()
        except Exception:
            motto = ""
        self.motto_label = QLabel(motto, self)
        self.motto_label.setObjectName("motto_label")
        self.motto_label.setAlignment(Qt.AlignCenter)
        # Stile motto originale: sfondo bianco, testo marrone
        self.motto_label.setStyleSheet(
            "background: #fff; color: #482e1a; font-weight: bold; padding: 4px 0; border-top: 2px solid #a67c52; "
            "font-size: 18px; font-family: 'Segoe UI', 'Arial', sans-serif; border-bottom: none; opacity: 1;"
        )
        self.motto_label.raise_()

        self.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
        self.resize(960, 700)
        # Rollback: nessuno stile trasparente su QMainWindow


        # MENU COMPLETO secondo guida.html (localizzato)
        menubar = self.menuBar()
        gm = lambda chiave: get_msg(self.glossario_data, chiave, self.lingua) or chiave

        # --- File input ---
        file_menu = QMenu(gm("File input"), self)
        file_menu.addAction(gm("Esempio input"), self.mostra_esempio_input)
        file_menu.addAction(gm("Apri input"), self.apri_input)
        file_menu.addAction(gm("Modifica input"), self.modifica_input)
        menubar.addMenu(file_menu)

        # --- Output ---
        output_menu = QMenu(gm("Output"), self)
        output_menu.addAction(gm("Elabora"), self.elabora_output)
        output_menu.addAction(gm("Apri cartella output"), self.apri_cartella_output)
        output_menu.addAction(gm("Visualizza elaborazioni precedenti"), self.visualizza_elaborazioni_precedenti)
        menubar.addMenu(output_menu)

        # --- Servizi ---
        servizi_menu = QMenu(gm("Servizi"), self)
        servizi_menu.addAction(gm("Visualizzazione Immagini"), self.apri_visualizzatore_immagini)
        servizi_menu.addAction(gm("Visualizzazione Metadati JSON"), self.apri_visualizzatore_metadati)
        servizi_menu.addAction(gm("OCR Avanzato"), self.funzione_in_sviluppo)
        servizi_menu.addAction(gm("Traduzione OCR"), self.funzione_in_sviluppo)
        servizi_menu.addAction(gm("Esportazione GEDCOM"), self.apri_esportazione_gedcom)
        menubar.addMenu(servizi_menu)

        # --- Documenti ---
        documenti_menu = QMenu(gm("Documenti"), self)
        documenti_menu.addAction(gm("Disclaimer"), self.mostra_disclaimer)
        documenti_menu.addAction(gm("Presentazione autore"), self.mostra_autore)
        documenti_menu.addAction(gm("Presentazione progetto"), self.mostra_progetto)
        documenti_menu.addAction(gm("Guida"), self.mostra_guida)
        documenti_menu.addAction(gm("Informazioni"), self.mostra_info)
        menubar.addMenu(documenti_menu)

        # --- Impostazioni ---
        impostazioni_menu = QMenu(gm("Impostazioni"), self)
        impostazioni_menu.addAction(gm("Cambia lingua"), self.cambia_lingua)
        impostazioni_menu.addAction(gm("Seleziona formati immagine"), self.seleziona_formati_immagine)
        impostazioni_menu.addAction(gm("Seleziona cartella output"), self.seleziona_cartella_output)
        impostazioni_menu.addAction(gm("Esporta configurazione"), self.esporta_configurazione)
        impostazioni_menu.addAction(gm("Importa configurazione"), self.importa_configurazione)
        impostazioni_menu.addAction(gm("Verifica aggiornamenti"), self.verifica_aggiornamenti)
        impostazioni_menu.addAction(gm("Chiudi"), self.close)
        menubar.addMenu(impostazioni_menu)

        # Stile menubar originale (nessuna forzatura colore bianco sulle voci)
        menubar.setStyleSheet("QMenuBar { background: #d2bb8a; color: #222; font-weight: bold; border: none; } "
                  "QMenuBar::item:selected { background: #e5d3b3; color: #222; } "
                  "QMenu { background: #f5e6c3; color: #222; } ")

        # Riga marrone sotto il menu (widget separato, non nel layout centrale)
        self.menu_separator = QLabel(self)
        self.menu_separator.setFixedHeight(4)
        self.menu_separator.setStyleSheet("background: #a67c52;")
        self.menu_separator.setGeometry(0, menubar.height(), self.width(), 4)
        self.menu_separator.raise_()
        self.menuBar().installEventFilter(self)

        # LAYOUT CENTRALE
        central = QWidget()
        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        central.setLayout(vlayout)
        self.setCentralWidget(central)

        # Sfondo pergamena responsivo
        self.bg_label = QLabel(self)
        bg_pixmap = get_pixmap_cached(asset_path("assets/common/grafici/Sfondo.png"))
        if bg_pixmap.isNull():
            bg_pixmap = get_pixmap_cached(asset_path("assets/common/grafici/Sfondo.webp"))
        self.bg_pixmap = bg_pixmap
        self.bg_label.setPixmap(self.bg_pixmap)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

        # Logo centrale proporzionato
        self.logo_label = QLabel(central)
        logo_pixmap = get_pixmap_cached(asset_path("assets/common/grafici/Logo.webp"))
        if logo_pixmap.isNull():
            logo_pixmap = get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro-logo.png"))
        self.logo_pixmap = logo_pixmap
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setScaledContents(True)
        self.logo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.logo_label.setStyleSheet("background: transparent;")
        vlayout.addStretch(1)
        vlayout.addWidget(self.logo_label, alignment=Qt.AlignCenter)
        vlayout.addStretch(1)

        # Applica stile bianco a tutti i QPushButton della finestra principale
        self.setStyleSheet(self.styleSheet() + "\nQPushButton { background-color: #222; color: #fff; border: 1px solid #a67c52; padding: 6px 18px; border-radius: 6px; font-size: 15px; font-weight: bold; } QPushButton:hover { background-color: #333; }")
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Sfondo
        if hasattr(self, 'bg_label') and hasattr(self, 'bg_pixmap'):
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
            self.bg_label.setPixmap(self.bg_pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        # Logo proporzionato (max 40% larghezza, max 30% altezza)
        if hasattr(self, 'logo_label') and hasattr(self, 'logo_pixmap'):
            w = int(self.width() * 0.4)
            h = int(self.height() * 0.3)
            scaled = self.logo_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled)
        # Aggiorna larghezza separatore menu
        if hasattr(self, 'menu_separator'):
            self.menu_separator.setGeometry(0, self.menuBar().height(), self.width(), 4)
        # Motto e separatore in fondo (senza riga in calce)
        if hasattr(self, 'motto_separator') and hasattr(self, 'motto_label'):
            motto_h = self.motto_label.sizeHint().height()
            sep_h = self.motto_separator.height()
            self.motto_separator.setGeometry(0, self.height() - motto_h - sep_h, self.width(), sep_h)
            self.motto_label.setGeometry(0, self.height() - motto_h, self.width(), motto_h)

    # --- Placeholder per azioni menu ---

    def mostra_esempio_input(self):
        # Collega al flusso reale
        action_show_example_input(self.glossario_data, self.lingua, self)


    def apri_input(self):
        action_open_input(self.glossario_data, self.lingua, self)


    def modifica_input(self):
        action_modify_input(self.glossario_data, self.lingua, self)

    def elabora_output(self):

        records = state.get("records") or []
        formats = state.get("formats") or []
        glossario = self.glossario_data
        lingua = self.lingua
        output_folders_doc = state.get('output_folders_doc', [])
        output_folders_reg = state.get('output_folders_reg', [])

        # Blocca se nessuna cartella valida
        if not (output_folders_doc and len(output_folders_doc) > 0) and not (output_folders_reg and len(output_folders_reg) > 0):
            show_msgbox_localized(
                self,
                glossario,
                lingua,
                "Cartella output",
                get_msg(glossario, "Devi selezionare almeno una cartella di output valida per documenti o registri. Nessun file verrà salvato.", lingua) or "Devi selezionare almeno una cartella di output valida per documenti o registri. Nessun file verrà salvato.",
                icon=QMessageBox.Warning
            )
            return

        # Conta i record per modalità
        doc_indices = [i for i, r in enumerate(records) if str(r.get('modalita', '')).strip().upper() == 'D']
        reg_indices = [i for i, r in enumerate(records) if str(r.get('modalita', '')).strip().upper() == 'R']
        if len(output_folders_doc) != len(doc_indices):
            _tmpl_doc = get_msg(glossario, "Numero di cartelle documento selezionate ({doc_count}) diverso dal numero di record documento ({doc_total}).", lingua) or "Numero di cartelle documento selezionate ({doc_count}) diverso dal numero di record documento ({doc_total})."
            show_msgbox_localized(self, glossario, lingua, "ATK-Pro", _tmpl_doc.format(doc_count=len(output_folders_doc), doc_total=len(doc_indices)), QMessageBox.Critical, buttons=("Conferma",), default="Conferma")
            return
        if len(output_folders_reg) != len(reg_indices):
            _tmpl_reg = get_msg(glossario, "Numero di cartelle registro selezionate ({reg_count}) diverso dal numero di record registro ({reg_total}).", lingua) or "Numero di cartelle registro selezionate ({reg_count}) diverso dal numero di record registro ({reg_total})."
            show_msgbox_localized(self, glossario, lingua, "ATK-Pro", _tmpl_reg.format(reg_count=len(output_folders_reg), reg_total=len(reg_indices)), QMessageBox.Critical, buttons=("Conferma",), default="Conferma")
            return

        doc_counter = 0
        reg_counter = 0
        for rec in records:
            try:
                modalita = str(rec.get('modalita', '')).strip().upper()
            except Exception:
                modalita = ''
            out_dir = None
            if modalita == 'D':
                out_dir = output_folders_doc[doc_counter]
                doc_counter += 1
            elif modalita == 'R':
                out_dir = output_folders_reg[reg_counter]
                reg_counter += 1
            else:
                _tmpl_m = get_msg(glossario, "Modalità record non riconosciuta: {modalita}", lingua) or "Modalità record non riconosciuta: {modalita}"
                show_msgbox_localized(self, glossario, lingua, "ATK-Pro", _tmpl_m.format(modalita=modalita), QMessageBox.Critical, buttons=("Conferma",), default="Conferma")
                return
            try:
                rec['output'] = out_dir
            except Exception:
                pass

        import traceback
        try:
            if not records:
                return
            if not formats:
                return

            # Import dinamico per evitare problemi di import circolare
            import elaborazione
            from user_prompts import ProgressDialog
            from qt_worker import ElaborazioneWorker
            from PySide6.QtCore import QCoreApplication

            records = state["records"]
            formats = state["formats"]
            glossario = self.glossario_data
            lingua = self.lingua

            progress_dialog = ProgressDialog(glossario, lingua, total=len(records), parent=self)
            worker = ElaborazioneWorker(records, formats, glossario, lingua)

            def on_progress(cur, tot, name, page, page_total):
                import re
                if name:
                    name = re.sub(r'—?\s*pag\.\s*\d+\s*$', '', name).strip()
                progress_dialog.update(cur, name, page, page_total)
                QCoreApplication.processEvents()

            def on_cancel():
                worker.cancel()
                progress_dialog.close()

            progress_dialog.cancel_btn.clicked.disconnect()
            progress_dialog.cancel_btn.clicked.connect(on_cancel)
            worker.signals.progress.connect(on_progress)

            def on_need_pdf(idx, name):
                from user_prompts import ask_generate_pdf
                import logging
                from PySide6.QtCore import QTimer
                logger = logging.getLogger("pdf_prompt")
                logger.info(f"[PDF_PROMPT] Richiesta conferma PDF per idx={idx} name={name}")
                result_holder = {"res": None}
                def show_prompt():
                    logger.info(f"[PDF_PROMPT] Mostro dialog PDF per idx={idx} name={name}")
                    progress_dialog.close()
                    try:
                        # Forza stile scuro nella dialog PDF
                        res = ask_generate_pdf(glossario, lingua, parent=self, dark_mode=True)
                        logger.info(f"[PDF_PROMPT] Dialog PDF risposta: {res}")
                    except Exception as e:
                        logger.error(f"[PDF_PROMPT] Errore dialog PDF: {e}")
                        res = False
                    result_holder["res"] = res
                    progress_dialog.show()
                QTimer.singleShot(0, show_prompt)
                import time
                start = time.time()
                while result_holder["res"] is None and (time.time() - start) < 120:
                    from PySide6.QtWidgets import QApplication
                    QApplication.processEvents()
                    time.sleep(0.05)
                logger.info(f"[PDF_PROMPT] Risposta PDF idx={idx}: {result_holder['res']}")
                records[idx]["gen_pdf"] = bool(result_holder["res"])
                # RIMOSSA la chiamata a show_operation_completed_dialog qui

            worker.signals.need_pdf_confirmation.connect(on_need_pdf)

            progress_dialog.show()
            worker.start()
            operazione_completata = True
            while worker.isRunning():
                QCoreApplication.processEvents()
                if progress_dialog.cancelled:
                    worker.cancel()
                    worker.terminate()
                    progress_dialog.close()
                    operazione_completata = False
                    break
            # Chiudi subito la dialog di progresso appena il worker termina
            progress_dialog.close()
            # Mostra la finestra "Operazione completata" SOLO qui, dopo tutto (PDF incluso)
            if operazione_completata:
                try:
                    # Recupera risultati batch
                    risultati = None
                    try:
                        risultati = worker.results if hasattr(worker, 'results') else None
                    except Exception:
                        risultati = None
                    # Se non disponibili dal worker, prova a ricaricare da stato globale
                    if not risultati and hasattr(elaborazione, 'esegui_elaborazione'):
                        try:
                            risultati = elaborazione.esegui_elaborazione(state, glossario, lingua, records, formats)
                        except Exception:
                            risultati = None
                    show_operation_completed_dialog(self, self.glossario_data, self.lingua, risultati=risultati)
                except Exception as e:
                    logging.warning(f"Impossibile mostrare dialog operazione completata: {e}")
        except Exception as e:
            logging.error(f"Errore durante l'elaborazione: {e}\n{traceback.format_exc()}")
            try:
                show_operation_completed_dialog(self, self.glossario_data, self.lingua)
            except Exception as ex:
                logging.warning(f"Impossibile mostrare dialog operazione completata dopo errore: {ex}")
            show_msgbox_localized(self, self.glossario_data, self.lingua, "Errore", f'{get_msg(self.glossario_data, "Errore durante l'elaborazione", self.lingua)}: {str(e)}', icon=QMessageBox.Critical)


    def apri_cartella_output(self):
        folder = state.get("output_folder")
        if not folder or not os.path.isdir(folder):
            show_msgbox_localized(self, self.glossario_data, self.lingua, "Cartella output", get_msg(self.glossario_data, "Nessuna cartella output selezionata o non esistente.", self.lingua) or "Nessuna cartella output selezionata o non esistente.", icon=QMessageBox.Warning)
            return
        import platform
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            os.system(f"open '{folder}'")
        else:
            os.system(f"xdg-open '{folder}'")
        # Usa dialogo stile "Operazione completata"
        show_operation_completed_dialog(self, self.glossario_data, self.lingua)

    def visualizza_elaborazioni_precedenti(self):
        import os
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem
        from PySide6.QtCore import Qt, QUrl
        from PySide6.QtGui import QCursor
        from PySide6.QtGui import QDesktopServices
        folder = state.get("output_folder")
        if not folder or not os.path.isdir(folder):
            show_operation_completed_dialog(self, self.glossario_data, self.lingua)
            return
        # Ricerca ricorsiva di file rilevanti
        estensioni = ('.json', '.pdf', '.png', '.jpg', '.jpeg', '.txt')
        files = []
        for root, _, filenames in os.walk(folder):
            for f in filenames:
                if f.lower().endswith(estensioni):
                    rel_path = os.path.relpath(os.path.join(root, f), folder)
                    files.append(rel_path)
        # Finestra riepilogativa stile scuro, omogenea alle altre
        dlg = QDialog(self)
        dlg.setWindowTitle(get_msg(self.glossario_data, "Visualizza elaborazioni precedenti", self.lingua) or "Elaborazioni precedenti")
        dlg.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        dlg.resize(700, 500)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #181818;
                color: #fff;
                border: 2px solid #a67c52;
            }
            QTextEdit {
                background-color: #222;
                color: #fff;
                font-size: 15px;
                border: 1px solid #a67c52;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton {
                background-color: #222;
                color: #fff;
                border: 1px solid #a67c52;
                padding: 6px 18px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        layout = QVBoxLayout(dlg)
        if files:
            list_widget = QListWidget()
            list_widget.setStyleSheet("background-color: #222; color: #fff; font-size: 15px; border: 1px solid #a67c52; border-radius: 6px; padding: 8px;")
            for rel_path in files:
                item = QListWidgetItem(rel_path)
                item.setToolTip(rel_path)
                list_widget.addItem(item)
            def open_file(item):
                abs_path = os.path.abspath(os.path.join(folder, item.text()))
                QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
            list_widget.itemClicked.connect(open_file)
            layout.addWidget(list_widget)
        else:
            from PySide6.QtWidgets import QLabel
            msg = get_msg(self.glossario_data, "Nessuna elaborazione trovata", self.lingua)
            if not msg or msg == "Nessuna elaborazione trovata":
                msg = "Nessuna elaborazione precedente trovata nella cartella selezionata."
            label = QLabel(msg)
            label.setStyleSheet("color: #fff; font-size: 15px;")
            layout.addWidget(label)
        ok_btn = QPushButton(get_msg(self.glossario_data, "Chiudi", self.lingua) or "Chiudi")
        ok_btn.clicked.connect(dlg.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
        dlg.setLayout(layout)
        dlg.exec()
    def apri_esportazione_gedcom(self):
        from src.genealogy_dialog import GenealogyDialog
        dialog = GenealogyDialog(self, self.glossario_data, self.lingua)
        dialog.exec()

    def funzione_in_sviluppo(self):
        # Messaggio placeholder localizzato per tutte le voci Servizi
        msg = get_msg(self.glossario_data, "Funzione in sviluppo", self.lingua)
        if not msg or msg == "Funzione in sviluppo":
            msg = "Questa funzione è in sviluppo."
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle(get_msg(self.glossario_data, "Funzione in sviluppo", self.lingua) or "Funzione in sviluppo")
        dlg.setStyleSheet("""
            QDialog {
                background-color: #181818;
                color: #fff;
                border: 2px solid #a67c52;
            }
            QLabel, QPushButton {
                color: #fff;
                font-size: 16px;
            }
            QPushButton {
                background-color: #222;
                border: 1px solid #a67c52;
                padding: 6px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        layout = QVBoxLayout(dlg)
        label = QLabel(msg)
        label.setStyleSheet("color: #fff; font-size: 16px;")
        layout.addWidget(label)
        ok_btn = QPushButton(get_msg(self.glossario_data, "Chiudi", self.lingua) or "Chiudi")
        ok_btn.clicked.connect(dlg.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
        dlg.setLayout(layout)
        dlg.exec()

    # ------------------------------------------------------------------
    # Visualizzazione Immagini
    # ------------------------------------------------------------------
    def apri_visualizzatore_immagini(self):
        try:
            from image_metadata_viewer import apri_visualizzatore_immagini
        except ImportError:
            from src.image_metadata_viewer import apri_visualizzatore_immagini
        apri_visualizzatore_immagini(
            parent=self,
            glossario_data=self.glossario_data,
            lingua=self.lingua,
            output_folder=state.get("output_folder") or "",
        )

    # ------------------------------------------------------------------
    # Visualizzazione Metadati JSON
    # ------------------------------------------------------------------
    def apri_visualizzatore_metadati(self):
        try:
            from image_metadata_viewer import apri_visualizzatore_metadati
        except ImportError:
            from src.image_metadata_viewer import apri_visualizzatore_metadati
        apri_visualizzatore_metadati(
            parent=self,
            glossario_data=self.glossario_data,
            lingua=self.lingua,
            output_folder=state.get("output_folder") or "",
        )

    def mostra_disclaimer(self):
        percorso_html = asset_path(f"assets/{self.lingua}/testuali/disclaimer_legale_ATK-Pro.html")
        percorso_txt = asset_path(f"assets/{self.lingua}/testuali/disclaimer_legale_ATK-Pro.txt")
        try:
            if os.path.exists(percorso_html):
                self._mostra_html("Disclaimer", percorso_html)
            else:
                msg = get_msg(self.glossario_data, "Disclaimer non disponibile", self.lingua)
                testo = carica_testo_asset(percorso_txt) or msg or "Disclaimer non disponibile."
                self._mostra_testo_lungo("Disclaimer", testo)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            msg = get_msg(self.glossario_data, "Impossibile aprire il disclaimer", self.lingua)
            QMessageBox.critical(self, get_msg(self.glossario_data, "Errore", self.lingua) or "Errore", msg or f"Impossibile aprire il disclaimer: {e}")

    def mostra_autore(self):
        percorso_html = asset_path(f"assets/{self.lingua}/testuali/presentazione_autore.html")
        percorso_txt = asset_path(f"assets/{self.lingua}/testuali/presentazione_autore.txt")
        _titolo_au = get_msg(self.glossario_data, "Presentazione autore", self.lingua) or "Presentazione autore"
        if os.path.exists(percorso_html):
            self._mostra_html(_titolo_au, percorso_html)
        else:
            msg = get_msg(self.glossario_data, "Presentazione autore non disponibile", self.lingua)
            testo = carica_testo_asset(percorso_txt) or msg or "Presentazione autore non disponibile."
            self._mostra_testo_lungo(_titolo_au, testo)

    def mostra_progetto(self):
        percorso_html = asset_path(f"assets/{self.lingua}/testuali/presentazione_progetto_ATK-Pro.html")
        percorso_md = asset_path(f"assets/{self.lingua}/testuali/presentazione_progetto_ATK-Pro.md")
        _titolo_pr = get_msg(self.glossario_data, "Presentazione progetto", self.lingua) or "Presentazione progetto"
        if os.path.exists(percorso_html):
            self._mostra_html(_titolo_pr, percorso_html)
        else:
            msg = get_msg(self.glossario_data, "Presentazione progetto non disponibile", self.lingua)
            testo = carica_testo_asset(percorso_md) or msg or "Presentazione progetto non disponibile."
            self._mostra_testo_lungo(_titolo_pr, testo)

    def mostra_guida(self):
        percorso_html = asset_path(f"assets/{self.lingua}/testuali/guida.html")
        percorso_txt = asset_path(f"assets/{self.lingua}/testuali/guida.txt")
        _titolo_gu = get_msg(self.glossario_data, "Guida", self.lingua) or "Guida"
        if os.path.exists(percorso_html):
            self._mostra_html(_titolo_gu, percorso_html)
        else:
            msg = get_msg(self.glossario_data, "Guida non disponibile", self.lingua)
            testo = carica_testo_asset(percorso_txt) or msg or "Guida non disponibile."
            self._mostra_testo_lungo(_titolo_gu, testo)

    def mostra_info(self):
        # Mostra tre righe testuali come richiesto, stile "Operazione completata"
        email_path = asset_path("assets/common/testuali/email.txt")
        try:
            with open(email_path, "r", encoding="utf-8") as f:
                email = f.read().strip()
        except Exception:
            email = "info@atk-pro.org"
        righe = [f"ATK-Pro v{VERSION}", "©2026 Daniele Pigoli", email]
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle(get_msg(self.glossario_data, "Informazioni", self.lingua) or "Informazioni")
        dlg.setStyleSheet("""
            QDialog {
                background-color: #181818;
                color: #fff;
                border: 2px solid #a67c52;
            }
            QLabel, QPushButton {
                color: #fff;
                font-size: 16px;
            }
            QPushButton {
                background-color: #222;
                border: 1px solid #a67c52;
                padding: 6px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        layout = QVBoxLayout(dlg)
        for riga in righe:
            lbl = QLabel(riga)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("QLabel { background: transparent; color: #FFFFFF; font-size: 16px; }")
            layout.addWidget(lbl)
        btn = QPushButton(get_msg(self.glossario_data, "Chiudi", self.lingua) or "Chiudi")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        dlg.setLayout(layout)
        dlg.exec()

    def _mostra_html(self, titolo, percorso_html):
        # Su macOS QWebEngineView richiede entitlements Chromium non disponibili
        # con firma ad-hoc → apre il browser di sistema (automatico, nessuna azione utente)
        if sys.platform == "darwin":
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(percorso_html)))
            return
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtCore import QUrl, Qt
        from PySide6.QtGui import QIcon
        dlg = QDialog(self)
        dlg.setWindowTitle(titolo)
        dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
        dlg.resize(900, 700)
        dlg.setMinimumSize(600, 400)
        dlg.setSizeGripEnabled(True)
        # Sostituisce TUTTI i flag per evitare che Qt.Dialog blocchi min/max
        dlg.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        layout = QVBoxLayout(dlg)
        try:
            web = QWebEngineView()
            url = QUrl.fromLocalFile(os.path.abspath(percorso_html))
            web.load(url)
            layout.addWidget(web)
        except Exception as e:
            from PySide6.QtWidgets import QLabel
            _err_html = get_msg(self.glossario_data, "Errore caricamento HTML", self.lingua) or "Errore caricamento HTML"
            layout.addWidget(QLabel(f"{_err_html}: {e}"))
        # Pulsanti di controllo in basso
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton(get_msg(self.glossario_data, "Chiudi", self.lingua) or "Chiudi")
        btn_close.clicked.connect(dlg.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        dlg.setLayout(layout)
        dlg.exec()

    def _mostra_info_centrata(self, info_html=None):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        dlg = QDialog(self)
        dlg.setWindowTitle(get_msg(self.glossario_data, "Informazioni", self.lingua) or "Informazioni")
        dlg.setMinimumSize(500, 250)
        layout = QVBoxLayout(dlg)
        label = QLabel(info_html or "")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        dlg.exec()
    def _mostra_testo_lungo(self, titolo, testo):
        from PySide6.QtGui import QIcon
        dlg = QDialog(self)
        dlg.setWindowTitle(titolo)
        dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
        dlg.resize(700, 500)
        dlg.setMinimumSize(400, 300)
        dlg.setSizeGripEnabled(True)
        dlg.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        dlg.setStyleSheet("QDialog { background: #fff; } QTextEdit { background: #fff; color: #222; font-size: 15px; }")
        layout = QVBoxLayout(dlg)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(testo)
        layout.addWidget(text)
        btn = QPushButton(get_msg(self.glossario_data, "Chiudi", self.lingua) or "Chiudi")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec()

    def seleziona_formati_immagine(self):
        scelti = ask_image_formats(self.glossario_data, self.lingua)
        if scelti:
            state["formats"] = scelti

    def seleziona_cartella_output(self):
        # Attiva la selezione multipla per documenti e registri
        action_select_output(self.glossario_data, self.lingua)

    def esporta_configurazione(self):
        import os
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents", "ATK-Pro")
        os.makedirs(documents_dir, exist_ok=True)
        default_path = os.path.join(documents_dir, "configurazione.json")
        path, _ = QFileDialog.getSaveFileName(self, get_msg(self.glossario_data, "Esporta configurazione", self.lingua.upper()), default_path, "JSON Files (*.json)", options=_qfd_options())
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            # Mostra contenuto file salvato
            with open(path, "r", encoding="utf-8") as f:
                contenuto = f.read()
            dlg = QDialog(self)
            dlg.setWindowTitle(get_msg(self.glossario_data, "Operazione completata", self.lingua) or "Configurazione esportata")
            _setup_dialog_pergamena(dlg, 700, 500)
            layout = QVBoxLayout(dlg)
            text = QTextEdit()
            text.setReadOnly(True)
            text.setPlainText(contenuto)
            layout.addWidget(text)
            ok_btn = QPushButton(get_msg(self.glossario_data, "Chiudi", self.lingua) or "Chiudi")
            ok_btn.clicked.connect(dlg.accept)
            layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
            dlg.setLayout(layout)
            dlg.exec()

    def importa_configurazione(self):
        import os
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents", "ATK-Pro")
        os.makedirs(documents_dir, exist_ok=True)
        default_path = os.path.join(documents_dir, "configurazione.json")
        path, _ = QFileDialog.getOpenFileName(self, get_msg(self.glossario_data, "Importa configurazione", self.lingua.upper()), default_path, "JSON Files (*.json)", options=_qfd_options())
        if path:
            with open(path, "r", encoding="utf-8") as f:
                dati = json.load(f)
                state.update(dati)
                contenuto = json.dumps(dati, ensure_ascii=False, indent=2)
            # Aggiorna la UI dopo l'import
            if hasattr(self, "aggiorna_ui_da_state"):
                self.aggiorna_ui_da_state()
            # Mostra contenuto file importato con stile SCURO
            dlg = QDialog(self)
            dlg.setWindowTitle(get_msg(self.glossario_data, "Operazione completata", self.lingua) or "Configurazione importata")
            _setup_dialog_pergamena(dlg, 700, 500)
            # Forza stile SCURO anche sulla dialog
            dlg.setStyleSheet("QDialog { background-color: #181818; }")
            layout = QVBoxLayout(dlg)
            text = QTextEdit()
            text.setReadOnly(True)
            text.setPlainText(contenuto)
            text.setStyleSheet("background-color: #181818; color: #fff; font-size: 15px; border: 1px solid #a67c52;")
            layout.addWidget(text)
            ok_btn = QPushButton(get_msg(self.glossario_data, "Chiudi", self.lingua) or "Chiudi")
            ok_btn.setStyleSheet("background-color: #222; color: #fff; border: 1px solid #a67c52; padding: 8px 24px; border-radius: 8px; font-size: 15px; font-weight: bold;")
            ok_btn.clicked.connect(dlg.accept)
            layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
            dlg.setLayout(layout)
            dlg.exec()


def _setup_dialog_pergamena(dlg, w=900, h=650, use_old_bg=False):
    dlg.resize(w, h)
    dlg.setStyleSheet("QDialog { background: transparent; }")
    dlg.setAutoFillBackground(True)

    bg_pixmap = QPixmap(asset_path("assets/common/grafici/Sfondo.webp"))
    if not bg_pixmap.isNull():
        scaled_bg = bg_pixmap.scaled(dlg.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        dlg.setPalette(palette)


def _styled_text_edit(read_only=True, initial_text=""):
    text = QTextEdit()
    text.setReadOnly(read_only)
    if initial_text:
        text.setPlainText(initial_text)
    text.setStyleSheet("""
        QTextEdit {
            background-color: rgba(255, 255, 255, 220);  /* overlay chiaro */
            color: #000000;
            border: none;
            font-size: 14px;
        }
    """)
    return text


def mostra_disclaimer(glossario_data, lingua):
    disclaimer_path = os.path.join(ASSET_LANG, lingua, "testuali", "disclaimer_legale_ATK-Pro.txt")
    msg = get_msg(glossario_data, "Disclaimer non disponibile", lingua.upper())
    disclaimer_text = carica_testo_asset(disclaimer_path) or msg or "Disclaimer non disponibile"

    dlg = QDialog()
    dlg.setWindowTitle(get_msg(glossario_data, "Disclaimer", lingua.upper()))
    dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
    dlg.setStyleSheet("""
        QDialog {
            background-color: #181818;
            color: #fff;
            border: 2px solid #a67c52;
        }
        QLabel, QPushButton {
            color: #fff;
            font-size: 15px;
        }
        QPushButton {
            background-color: #222;
            border: 1px solid #a67c52;
            padding: 6px 18px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #333;
        }
    """)
    dlg.resize(900, 650)

    layout = QVBoxLayout(dlg)
    text = _styled_text_edit(read_only=True, initial_text=disclaimer_text)
    layout.addWidget(text)

    domanda = QLabel(get_msg(glossario_data, "Accetti", lingua.upper()))
    layout.addWidget(domanda)

    btns = QHBoxLayout()
    si_btn = QPushButton(get_msg(glossario_data, "Si", lingua.upper()))
    no_btn = QPushButton(get_msg(glossario_data, "No", lingua.upper()))
    si_btn.clicked.connect(dlg.accept)
    no_btn.clicked.connect(dlg.reject)
    btns.addWidget(si_btn)
    btns.addWidget(no_btn)
    layout.addLayout(btns)

    return dlg.exec() == QDialog.Accepted


def action_show_example_input(glossario_data, lingua, parent=None):
    example_path = os.path.join(ASSET_LANG, lingua.lower(), "testuali", "input_link_base_v2.0.txt")
    try:
        raw_text = load_input_file(example_path)
        records = parse_input_text(raw_text)
        state["records"] = records
        logging.info(f"{len(records)} record di esempio caricati")

        # Mostra contenuto in una dialog coerente con 'modifica input'
        dialog = QDialog(parent)
        dialog.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
        dialog.setWindowTitle(get_msg(glossario_data, "Esempio input", lingua.upper()))
        dialog.setMinimumSize(820, 600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #111216;
                color: #fff;
                border: 2px solid #a67c52;
            }
            QLabel, QPushButton, QTextEdit {
                color: #fff;
                font-size: 15px;
            }
            QTextEdit {
                background-color: #181818;
                color: #fff;
                border: 1px solid #a67c52;
            }
            QPushButton {
                background-color: #222;
                border: 1px solid #a67c52;
                padding: 6px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        layout = QVBoxLayout(dialog)

        # Area testo per mostrare il file (sola lettura)
        text_edit = QTextEdit(dialog)
        text_edit.setPlainText(raw_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        # Pulsante Chiudi
        btn_layout = QHBoxLayout()
        btn_close = QPushButton(get_msg(glossario_data, "Chiudi", lingua.upper()), dialog)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        btn_close.clicked.connect(dialog.accept)

        dialog.setLayout(layout)
        dialog.exec()
    except Exception as e:
        show_msgbox_localized(parent, glossario_data, lingua, get_msg(glossario_data, "Attenzione", lingua.upper()), f"{get_msg(glossario_data, 'Errore caricamento esempio input', lingua.upper())}: {str(e)}", icon=QMessageBox.Critical)


def action_modify_input(glossario_data, lingua, parent=None):
    try:
        # Prova prima il file memorizzato in stato (da "Apri input")
        modified_path = state.get("current_input_file")
        # Se non trovato nello stato, prova la cartella input/ (modalità sviluppo)
        if not modified_path or not os.path.exists(modified_path):
            modified_path = os.path.join(BASE_DIR, "input", "input_link.txt")
        # Se ancora non esiste, chiedi all'utente di selezionare il file
        if not os.path.exists(modified_path):
            modified_path, _ = QFileDialog.getOpenFileName(
                parent,
                get_msg(glossario_data, "Seleziona file input da modificare", lingua.upper()),
                options=_qfd_options()
            )

        raw_text = load_input_file(modified_path)
        records = parse_input_text(raw_text)
        state["records"] = records
        logging.info(f"{len(state.get('records', []))} record modificati caricati (pre-edit)")

        # Dialog editor con titolo corretto e dimensioni adeguate
        dialog = QDialog(parent)
        dialog.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
        dialog.setWindowTitle(get_msg(glossario_data, "Modifica input", lingua.upper()))
        dialog.setMinimumSize(820, 600)
        # Sfondo più scuro, simile a "Esempio input"
        dialog.setStyleSheet("""
            QDialog {
                background-color: #181818;
                color: #fff;
                border: 2px solid #a67c52;
            }
            QLabel, QPushButton, QTextEdit {
                color: #fff;
                font-size: 15px;
            }
            QTextEdit {
                background-color: #181818;
                color: #fff;
                border: 1px solid #a67c52;
            }
            QPushButton {
                background-color: #222;
                border: 1px solid #a67c52;
                padding: 6px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        layout = QVBoxLayout(dialog)

        # Area testo per mostrare e modificare il file
        text_edit = QTextEdit(dialog)
        text_edit.setPlainText(raw_text)
        layout.addWidget(text_edit)

        # Pulsanti localizzati
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(get_msg(glossario_data, "Salva", lingua.upper()), dialog)
        btn_cancel = QPushButton(get_msg(glossario_data, "Annulla", lingua.upper()), dialog)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        # Funzione di salvataggio
        def save_changes():
            new_text = text_edit.toPlainText()
            try:
                with open(modified_path, "w", encoding="utf-8") as f:
                    f.write(new_text)
                # Aggiorna lo stato con i record modificati
                state["records"] = parse_input_text(new_text)
                logging.info(f"{len(state['records'])} record modificati caricati (post-save)")
                dialog.accept()
            except Exception as e:
                show_msgbox_localized(parent, glossario_data, lingua, get_msg(glossario_data, "Attenzione", lingua.upper()), f"{get_msg(glossario_data, 'Errore salvataggio input', lingua.upper())}: {str(e)}", QMessageBox.Critical, buttons=("Conferma",), default="Conferma")

        btn_save.clicked.connect(save_changes)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.setLayout(layout)
        dialog.exec()

    except FileNotFoundError:
        show_msgbox_localized(parent, glossario_data, lingua, get_msg(glossario_data, "Attenzione", lingua.upper()), get_msg(glossario_data, "File da modificare non trovato", lingua.upper()), QMessageBox.Critical, buttons=("Conferma",), default="Conferma")
    except Exception as e:
        show_msgbox_localized(parent, glossario_data, lingua, get_msg(glossario_data, "Attenzione", lingua.upper()), f"{get_msg(glossario_data, 'Errore caricamento input modificato', lingua.upper())}: {str(e)}", QMessageBox.Critical, buttons=("Conferma",), default="Conferma")


def ask_language(glossario_data, lingua_attuale, parent):
    """Permette all'utente di cambiare la lingua dell'interfaccia."""
    lingue_disponibili = [
        "IT", "EN", "ES", "FR", "DE", "PT", "RU", "AR", "NL", "HE",
        "JA", "ZH", "PL", "TR", "DA", "NO", "VI", "EL", "RO", "SV"
    ]
    nomi_lingue = {
        "IT": "Italiano",
        "EN": "English",
        "ES": "Español",
        "FR": "Français",
        "DE": "Deutsch",
        "PT": "Português",
        "RU": "Русский",
        "AR": "العربية",
        "NL": "Nederlands",
        "HE": "עברית",
        "JA": "日本語",
        "ZH": "中文",
        "PL": "Polski",
        "TR": "Türkçe",
        "UK": "Українська",
        "CS": "Čeština",
        "EL": "Ελληνικά",
        "HU": "Magyar",
        "RO": "Română",
        "SV": "Svenska",
        "VI": "Tiếng Việt",
        "DA": "Dansk"
    }
    
    # Dialog per selezionare lingua
    dlg = QDialog(parent)
    dlg.setWindowTitle(get_msg(glossario_data, "Cambia lingua", lingua_attuale.upper()))
    dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
    dlg.setStyleSheet("""
        QDialog {
            background-color: #181818;
            color: #fff;
            border: 2px solid #a67c52;
        }
        QLabel {
            color: #fff;
            font-size: 17px;
            background: transparent;
        }
        QComboBox {
            background-color: #222;
            color: #fff;
            border: 1px solid #a67c52;
            font-size: 16px;
            padding: 4px 8px;
            border-radius: 6px;
        }
        QComboBox QAbstractItemView {
            background: #222;
            color: #fff;
            selection-background-color: #a67c52;
            selection-color: #222;
        }
        QPushButton {
            background-color: #222;
            color: #fff;
            border: 1px solid #a67c52;
            padding: 8px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
        }
        QPushButton:disabled {
            background-color: #444;
            color: #aaa;
            border: 1px solid #555;
        }
        QPushButton:hover {
            background-color: #333;
        }
    """)
    dlg.setGeometry(100, 100, 400, 220)

    layout = QVBoxLayout(dlg)
    # Titolo descrittivo
    label = QLabel(get_msg(glossario_data, "Scegli la lingua dell'interfaccia", lingua_attuale.upper()) if glossario_data else "Scegli la lingua dell'interfaccia")

    combo = QComboBox()

    # Solo lingue effettivamente supportate (cartelle assets)
    import os
    asset_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    lingue_supportate = [d for d in os.listdir(asset_dir) if os.path.isdir(os.path.join(asset_dir, d)) and d != "common"]
    # Mappa sigla → nome localizzato
    nomi_lingue = {
        "it": "Italiano",
        "en": "English",
        "es": "Español",
        "fr": "Français",
        "de": "Deutsch",
        "pt": "Português",
        "ru": "Русский",
        "ar": "العربية",
        "nl": "Nederlands",
        "he": "עברית",
        "ja": "日本語",
        "zh": "中文",
        "pl": "Polski",
        "tr": "Türkçe",
        "uk": "Українська",
        "cs": "Čeština",
        "el": "Ελληνικά",
        "hu": "Magyar",
        "ro": "Română",
        "sv": "Svenska",
        "vi": "Tiếng Việt",
        "da": "Dansk"
    }
    import locale
    import locale
    try:
        locale.setlocale(locale.LC_ALL, "")
        sys_locale = locale.getlocale()[0]
    except Exception:
        sys_locale = None
    sys_lang = None
    if sys_locale:
        sys_lang = sys_locale.split('_')[0]
    # Forza sempre l'autonimo per norvegese
    for codice in lingue_supportate:
        nome = nomi_lingue.get(codice, codice)
        if codice == "no":
            nome = "Norsk"  # Autonimo norvegese
        combo.addItem(nome, codice)
    # Imposta come default la lingua di sistema se presente
    if sys_lang and sys_lang in lingue_supportate:
        idx = lingue_supportate.index(sys_lang)
        combo.setCurrentIndex(idx)

    btns = QHBoxLayout()
    ok_btn = QPushButton(get_msg(glossario_data, "Conferma", lingua_attuale.upper()) if glossario_data else "Conferma")
    cancel_btn = QPushButton(get_msg(glossario_data, "Annulla", lingua_attuale.upper()) if glossario_data else "Annulla")
    ok_btn.clicked.connect(dlg.accept)
    cancel_btn.clicked.connect(dlg.reject)
    btns.addWidget(ok_btn)
    btns.addWidget(cancel_btn)

    layout.addWidget(label)
    layout.addWidget(combo)
    layout.addLayout(btns)

    if dlg.exec() == QDialog.Accepted:
        # Restituisce la sigla associata al nome scelto
        return combo.currentData()
    return "en"


def ask_image_formats(glossario_data, lingua):
    dlg = QDialog()
    dlg.resize(270, 310)  # altezza aumentata per checkbox PDF
    dlg.setWindowTitle(get_msg(glossario_data, "Seleziona formati immagine", lingua.upper()))
    dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
    _setup_dialog_pergamena(dlg, 270, 310)

    layout = QVBoxLayout(dlg)
    checks_layout = QHBoxLayout()

    png = QCheckBox("PNG")
    jpg = QCheckBox("JPG")
    tiff = QCheckBox("TIFF")

    # Pre-seleziona i formati dall'ultimo uso (state ha priorità, poi config)
    _saved_fmts = state.get("formats") or _read_config_prefs().get("formats", [])
    _saved_fmts_upper = [f.upper() for f in _saved_fmts]
    if "PNG" in _saved_fmts_upper:  png.setChecked(True)
    if "JPG" in _saved_fmts_upper:  jpg.setChecked(True)
    if "TIF" in _saved_fmts_upper or "TIFF" in _saved_fmts_upper:  tiff.setChecked(True)

    checks_layout.addWidget(png)
    checks_layout.addWidget(jpg)
    checks_layout.addWidget(tiff)
    layout.addLayout(checks_layout)

    # Separatore e checkbox PDF
    separator = QFrame()
    separator.setFrameShape(QFrame.HLine)
    separator.setFrameShadow(QFrame.Sunken)
    separator.setStyleSheet("color: #a67c52;")
    layout.addWidget(separator)

    pdf_label = QLabel(get_msg(glossario_data, "Documento PDF", lingua.upper()) or "Documento PDF")
    pdf_label.setStyleSheet("font-weight: bold; font-size: 12px;")
    layout.addWidget(pdf_label)

    pdf_cb = QCheckBox("PDF")
    if "PDF" in _saved_fmts_upper:
        pdf_cb.setChecked(True)
    layout.addWidget(pdf_cb)

    btns = QHBoxLayout()
    ok_btn = QPushButton(get_msg(glossario_data, "Conferma", lingua.upper()))
    cancel_btn = QPushButton(get_msg(glossario_data, "Annulla", lingua.upper()))
    ok_btn.clicked.connect(dlg.accept)
    cancel_btn.clicked.connect(dlg.reject)
    btns.addWidget(ok_btn)
    btns.addWidget(cancel_btn)
    layout.addLayout(btns)

    if dlg.exec() == QDialog.Accepted:
        scelti = []
        if png.isChecked(): scelti.append("PNG")
        if jpg.isChecked(): scelti.append("JPG")
        if tiff.isChecked(): scelti.append("TIF")
        if pdf_cb.isChecked(): scelti.append("PDF")

        if scelti:
            state["formats"] = scelti
            _write_config_prefs("formats", scelti)
            logging.info(f"Formati selezionati: {scelti}")
            # Usa una label di fallback se la chiave non esiste o è None
            label = get_msg(glossario_data, 'Formati selezionati', lingua.upper())
            if not label or label == 'None':
                label = "Formati selezionati"
            # Finestra di conferma con stile "Operazione completata"
            conferma = QDialog(dlg)
            conferma.setWindowTitle("ATK-Pro")
            _setup_dialog_pergamena(conferma, 500, 200)
            layout = QVBoxLayout(conferma)
            label_widget = QLabel(f"{label}: {', '.join(scelti)}")
            label_widget.setAlignment(Qt.AlignCenter)
            label_widget.setStyleSheet("color: #fff; font-size: 16px;")
            layout.addWidget(label_widget)
            ok_btn = QPushButton(get_msg(glossario_data, "Conferma", lingua.upper()) or "Conferma")
            ok_btn.clicked.connect(conferma.accept)
            layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
            conferma.setLayout(layout)
            conferma.exec()
        return scelti
    return []


def action_open_input(glossario_data, lingua, parent=None):
    path = QFileDialog.getOpenFileName(
        parent,
        get_msg(glossario_data, "Apri input", lingua.upper()),
        os.path.join(BASE_DIR, "input"),
        "Text (*.txt);;All (*.*)",
        options=_qfd_options()
    )[0]
    if not path:
        return
    try:
        raw_text = load_input_file(path)
        records = parse_input_text(raw_text)
        state["records"] = records
        state["current_input_file"] = path
        _write_config_prefs("last_input_file", path)
        logging.info(f"{len(records)} record caricati")

        # Ripristina formati dall'ultimo uso
        prefs = _read_config_prefs()
        if prefs["formats"] and not state.get("formats"):
            state["formats"] = prefs["formats"]
            logging.debug(f"Formati ripristinati dal config: {prefs['formats']}")

        # Ripristina cartelle output solo se compatibili con il nuovo file
        num_doc = sum(1 for r in records if r.get("modalita", "").strip().upper() == "D")
        num_reg = sum(1 for r in records if r.get("modalita", "").strip().upper() == "R")
        saved_mode = prefs.get("output_mode", "per_record")
        folders_restored = False

        if saved_mode == "single":
            sf = prefs.get("output_folder_single", "")
            if sf and os.path.isdir(sf):
                state["output_folders_doc"] = [sf] * num_doc
                state["output_folders_reg"] = [sf] * num_reg
                state["output_folder"] = sf
                state["output_mode"] = "single"
                folders_restored = True
                logging.debug(f"Cartella unica ripristinata: {sf}")

        elif saved_mode == "split":
            sd = prefs.get("output_folder_doc", "")
            sr = prefs.get("output_folder_reg", "")
            if sd and sr and os.path.isdir(sd) and os.path.isdir(sr):
                state["output_folders_doc"] = [sd] * num_doc
                state["output_folders_reg"] = [sr] * num_reg
                state["output_folder"] = sd
                state["output_mode"] = "split"
                folders_restored = True
                logging.debug(f"Cartelle split ripristinate: doc={sd}, reg={sr}")

        else:  # per_record
            pd = prefs.get("output_folders_doc", [])
            pr = prefs.get("output_folders_reg", [])
            if (len(pd) == num_doc and len(pr) == num_reg
                    and all(os.path.isdir(f) for f in pd + pr)):
                state["output_folders_doc"] = pd
                state["output_folders_reg"] = pr
                state["output_folder"] = pd[0] if pd else (pr[0] if pr else None)
                state["output_mode"] = "per_record"
                folders_restored = True
                logging.debug(f"Cartelle per record ripristinate: {pd}, {pr}")

        if not folders_restored:
            state["output_folders_doc"] = []
            state["output_folders_reg"] = []
            state["output_folder"] = None
            state.pop("output_mode", None)
            logging.debug("Cartelle output azzerate: incompatibili o mancanti")
            _needs_folder_selection = True
        else:
            _needs_folder_selection = False

        # Conferma con solo il path, stile uniforme
        msg = QMessageBox(parent)
        msg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
        msg.setWindowTitle(get_msg(glossario_data, "File aperto", lingua.upper()))
        msg.setText(path)
        style_msgbox_pergamena(msg)
        msg.exec()

        # 1) Selezione formati immagine (pre-seleziona quelli salvati nel config)
        scelti = ask_image_formats(glossario_data, lingua)
        if scelti:
            state["formats"] = scelti
            _write_config_prefs("formats", scelti)

        # 2) Selezione cartelle output:
        #    - se incompatibili: avvisa e apre il dialog
        #    - se compatibili e già ripristinate: chiede conferma o ri-selezione
        if _needs_folder_selection:
            show_msgbox_localized(
                parent, glossario_data, lingua,
                get_msg(glossario_data, "Cartelle output", lingua.upper()) or "Cartelle di output",
                get_msg(glossario_data, "Cartelle output azzerate", lingua.upper())
                    or "Le cartelle di output non sono compatibili con il nuovo file. Selezionare le cartelle nuovamente.",
                QMessageBox.Information,
                buttons=(get_msg(glossario_data, "Conferma", lingua.upper()) or "Conferma",),
                default=get_msg(glossario_data, "Conferma", lingua.upper()) or "Conferma"
            )
            action_select_output(glossario_data, lingua)
        else:
            action_select_output(glossario_data, lingua)

    except Exception as e:
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
        msg.setWindowTitle(get_msg(glossario_data, "Attenzione", lingua.upper()))
        msg.setText(f"{get_msg(glossario_data, 'Errore caricamento input', lingua.upper())}: {str(e)}")
        style_msgbox_pergamena(msg)
        msg.exec()
def parse_record_types_from_file(path: str):
    num_doc, num_reg = 0, 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("D ") or line.startswith("d "):
                    num_doc += 1
                elif line.startswith("R ") or line.startswith("r "):
                    num_reg += 1
    except Exception:
        pass
    if num_doc == 0 and num_reg == 0:
        num_doc = 1
    return num_doc, num_reg


def _qfd_options():
    """Su macOS restituisce DontUseNativeDialog per evitare il picker nativo illeggibile."""
    import sys as _sys
    if _sys.platform == "darwin":
        return QFileDialog.Option.DontUseNativeDialog
    return QFileDialog.Option(0)


def _pick_folder(title: str, default: str) -> str:
    """Apre QFileDialog partendo dalla cartella default; ritorna la scelta o '' se annullato."""
    return QFileDialog.getExistingDirectory(None, title, default, _qfd_options())


def action_select_output(glossario_data, lingua):
    records = state.get("records") or []
    if not records:
        show_msgbox_localized(None, glossario_data, lingua,
            get_msg(glossario_data, "Attenzione", lingua.upper()),
            get_msg(glossario_data, "Nessun input caricato", lingua.upper()),
            QMessageBox.Warning, buttons=("Conferma",), default="Conferma")
        return

    num_doc = sum(1 for r in records if r.get("modalita", "").strip().upper() == "D")
    num_reg = sum(1 for r in records if r.get("modalita", "").strip().upper() == "R")
    lbl_conf  = get_msg(glossario_data, "Conferma", lingua.upper()) or "Conferma"
    lbl_att   = get_msg(glossario_data, "Attenzione", lingua.upper()) or "Attenzione"
    lbl_obbl  = get_msg(glossario_data, "Selezione cartella obbligatoria", lingua.upper()) or "Selezione cartella obbligatoria"
    lbl_doc   = get_msg(glossario_data, "Documento", lingua.upper()) or "Documento"
    lbl_reg   = get_msg(glossario_data, "Registro", lingua.upper()) or "Registro"
    lbl_docs  = get_msg(glossario_data, "Documenti", lingua.upper()) or "Documenti"
    lbl_regs  = get_msg(glossario_data, "Registri", lingua.upper()) or "Registri"

    # Scelta modalità
    mode = ask_output_mode(glossario_data, lingua)
    folders_doc, folders_reg = [], []
    _prefs = _read_config_prefs()

    if mode == "single":
        # --- Modalità: cartella unica per tutti ---
        default = _prefs.get("output_folder_single") or _get_default_output_dir()
        folder = None
        while not folder:
            folder = _pick_folder(
                get_msg(glossario_data, "Cartella unica per tutti", lingua.upper()) or "Cartella output",
                default)
            if not folder:
                show_msgbox_localized(None, glossario_data, lingua, lbl_att, lbl_obbl,
                    QMessageBox.Warning, buttons=(lbl_conf,), default=lbl_conf)
        folders_doc = [folder] * num_doc
        folders_reg = [folder] * num_reg
        _write_config_prefs("output_mode", "single")
        _write_config_prefs("output_folder_single", folder)

    elif mode == "split":
        # --- Modalità: cartella separata per D e per R ---
        if num_doc > 0:
            folder_doc = None
            while not folder_doc:
                folder_doc = _pick_folder(
                    f"{lbl_docs} — {get_msg(glossario_data, 'Cartella output', lingua.upper()) or 'Cartella output'}",
                    _prefs.get("output_folder_doc") or _get_default_output_dir("doc"))
                if not folder_doc:
                    show_msgbox_localized(None, glossario_data, lingua, lbl_att, lbl_obbl,
                        QMessageBox.Warning, buttons=(lbl_conf,), default=lbl_conf)
            folders_doc = [folder_doc] * num_doc
            _write_config_prefs("output_folder_doc", folder_doc)

        if num_reg > 0:
            folder_reg = None
            while not folder_reg:
                folder_reg = _pick_folder(
                    f"{lbl_regs} — {get_msg(glossario_data, 'Cartella output', lingua.upper()) or 'Cartella output'}",
                    _prefs.get("output_folder_reg") or _get_default_output_dir("reg"))
                if not folder_reg:
                    show_msgbox_localized(None, glossario_data, lingua, lbl_att, lbl_obbl,
                        QMessageBox.Warning, buttons=(lbl_conf,), default=lbl_conf)
            folders_reg = [folder_reg] * num_reg
            _write_config_prefs("output_folder_reg", folder_reg)

        _write_config_prefs("output_mode", "split")

    else:
        # --- Modalità: una cartella per ogni record (comportamento originale) ---
        _last_doc = _prefs.get("output_folder_doc") or _get_default_output_dir("doc")
        for i in range(num_doc):
            folder = None
            while not folder:
                folder = _pick_folder(
                    f"{lbl_doc} {i+1}/{num_doc}",
                    _last_doc)
                if not folder:
                    show_msgbox_localized(None, glossario_data, lingua, lbl_att, lbl_obbl,
                        QMessageBox.Warning, buttons=(lbl_conf,), default=lbl_conf)
            folders_doc.append(folder)
            _last_doc = folder  # la prossima apertura parte dall'ultima scelta

        _last_reg = _prefs.get("output_folder_reg") or _get_default_output_dir("reg")
        for i in range(num_reg):
            folder = None
            while not folder:
                folder = _pick_folder(
                    f"{lbl_reg} {i+1}/{num_reg}",
                    _last_reg)
                if not folder:
                    show_msgbox_localized(None, glossario_data, lingua, lbl_att, lbl_obbl,
                        QMessageBox.Warning, buttons=(lbl_conf,), default=lbl_conf)
            folders_reg.append(folder)
            _last_reg = folder  # la prossima apertura parte dall'ultima scelta

        _write_config_prefs("output_mode", "per_record")
        _write_config_prefs("output_folders_doc", folders_doc)
        _write_config_prefs("output_folders_reg", folders_reg)

    # Aggiorna stato globale
    state["output_folders_doc"] = folders_doc
    state["output_folders_reg"] = folders_reg
    state["registri_output"] = folders_doc + folders_reg
    state["output_mode"] = mode
    if folders_doc:
        state["output_folder"] = folders_doc[0]
    elif folders_reg:
        state["output_folder"] = folders_reg[0]

    # Riepilogo
    riepilogo = []
    seen = set()
    for idx, folder in enumerate(folders_doc):
        if folder not in seen:
            riepilogo.append(f"<b>{lbl_docs}:</b> {folder}")
            seen.add(folder)
        elif mode == "per_record":
            riepilogo.append(f"{lbl_doc} {idx+1}: {folder}")
    for idx, folder in enumerate(folders_reg):
        if folder not in seen:
            riepilogo.append(f"<b>{lbl_regs}:</b> {folder}")
            seen.add(folder)
        elif mode == "per_record":
            riepilogo.append(f"{lbl_reg} {idx+1}: {folder}")

    conferma = QDialog()
    conferma.setWindowTitle("ATK-Pro")
    _setup_dialog_pergamena(conferma, 620, 300)
    layout = QVBoxLayout(conferma)
    label_widget = QLabel("<br>".join(riepilogo))
    label_widget.setAlignment(Qt.AlignLeft)
    label_widget.setStyleSheet("color: #fff; font-size: 15px;")
    label_widget.setTextFormat(Qt.RichText)
    layout.addWidget(label_widget)
    ok_btn = QPushButton(lbl_conf)
    ok_btn.clicked.connect(conferma.accept)
    layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
    conferma.setLayout(layout)
    conferma.exec()


def action_process(glossario_data, lingua, parent=None):
    records = state.get("records") or []
    if not records:
        show_msgbox_localized(parent, glossario_data, lingua, "ATK-Pro", get_msg(glossario_data, "Nessun record caricato", lingua.upper()), QMessageBox.Warning, buttons=("Conferma",), default="Conferma")
        logging.warning("Tentativo di elaborazione senza record")
        return

    selected_formats = state.get("formats") or []
    if not selected_formats:
        show_msgbox_localized(parent, glossario_data, lingua, "ATK-Pro", get_msg(glossario_data, "Nessun formato selezionato", lingua.upper()), QMessageBox.Warning, buttons=("Conferma",), default="Conferma")
        logging.warning("Elaborazione bloccata: nessun formato selezionato")
        return

    logging.info(f"Formati da elaborare: {selected_formats}")

    try:
        # Prima di avviare il worker: risolvi cartelle di output per ciascun record
        output_folder = state.get('output_folder')
        output_folders_doc = state.get('output_folders_doc', [])
        output_folders_reg = state.get('output_folders_reg', [])
        # Blocca se nessuna cartella valida
        if not output_folder and not (output_folders_doc and len(output_folders_doc) > 0) and not (output_folders_reg and len(output_folders_reg) > 0):
            show_msgbox_localized(parent, glossario_data, lingua, "ATK-Pro", get_msg(glossario_data, "Nessuna cartella di output valida selezionata!", lingua) or "Nessuna cartella di output valida selezionata!", QMessageBox.Critical, buttons=("Conferma",), default="Conferma")
            return
        # Conta i record per modalità
        doc_indices = [i for i, r in enumerate(records) if str(r.get('modalita', '')).strip().upper() == 'D']
        reg_indices = [i for i, r in enumerate(records) if str(r.get('modalita', '')).strip().upper() == 'R']
        if len(output_folders_doc) != len(doc_indices):
            _tmpl_doc = get_msg(glossario_data, "Numero di cartelle documento selezionate ({doc_count}) diverso dal numero di record documento ({doc_total}).", lingua) or "Numero di cartelle documento selezionate ({doc_count}) diverso dal numero di record documento ({doc_total})."
            show_msgbox_localized(parent, glossario_data, lingua, "ATK-Pro", _tmpl_doc.format(doc_count=len(output_folders_doc), doc_total=len(doc_indices)), QMessageBox.Critical, buttons=("Conferma",), default="Conferma")
            return
        if len(output_folders_reg) != len(reg_indices):
            _tmpl_reg = get_msg(glossario_data, "Numero di cartelle registro selezionate ({reg_count}) diverso dal numero di record registro ({reg_total}).", lingua) or "Numero di cartelle registro selezionate ({reg_count}) diverso dal numero di record registro ({reg_total})."
            show_msgbox_localized(parent, glossario_data, lingua, "ATK-Pro", _tmpl_reg.format(reg_count=len(output_folders_reg), reg_total=len(reg_indices)), QMessageBox.Critical, buttons=("Conferma",), default="Conferma")
            return
        doc_counter = 0
        reg_counter = 0
        for idx, rec in enumerate(records):
            try:
                modalita = str(rec.get('modalita', '')).strip().upper()
            except Exception:
                modalita = ''
            out_dir = None
            if modalita == 'D':
                out_dir = output_folders_doc[doc_counter]
                doc_counter += 1
            elif modalita == 'R':
                out_dir = output_folders_reg[reg_counter]
                reg_counter += 1
                # Prompt PDF PRIMA di avviare il worker, sempre
                from src.user_prompts import ask_generate_pdf
                resp = ask_generate_pdf(glossario_data, lingua, parent)
                rec['gen_pdf'] = bool(resp)
            else:
                _tmpl_m2 = get_msg(glossario_data, "Modalità record non riconosciuta: {modalita}", lingua) or "Modalità record non riconosciuta: {modalita}"
                show_msgbox_localized(parent, glossario_data, lingua, "ATK-Pro", _tmpl_m2.format(modalita=modalita), QMessageBox.Critical, buttons=("Conferma",), default="Conferma")
                return
            try:
                rec['output'] = out_dir
            except Exception:
                pass

        # Non chiedere qui le conferme PDF (eviterebbe che compaiano tutte
        # insieme all'avvio). La richiesta verrà fatta dal worker per ogni
        # registro 'R' al momento dell'elaborazione: il worker emette un
        # segnale che il main thread gestisce mostrando il dialog.
        from src.user_prompts import ask_generate_pdf, ProgressDialog

        # Tentativo: eseguire l'elaborazione in background usando il worker Qt
        try:
            from src.qt_worker import ElaborazioneWorker
            from PySide6.QtCore import QCoreApplication
        except Exception:
            pass

            pd = ProgressDialog(glossario_data, lingua, total=len(records), parent=parent)
            pd.show()
            # Forza colore bianco sulla barra di avanzamento e aggiungi label n/N accanto
            try:
                pd.pbar.setStyleSheet("QProgressBar { color: #fff; font-weight: bold; font-size: 15px; text-align: center; } QProgressBar::chunk { background: #a67c52; }")
                from PySide6.QtWidgets import QLabel
                if not hasattr(pd, 'count_label'):
                    pd.count_label = QLabel()
                    pd.count_label.setStyleSheet("color: #fff; font-size: 15px; font-weight: bold; background: transparent;")
                    pd.layout().addWidget(pd.count_label)
            except Exception:
                pass

            # Worker: useremo i record già arricchiti (output, gen_pdf)
            worker = ElaborazioneWorker(records, formats=selected_formats, glossario_data=glossario_data, lingua=lingua)

            def on_progress(current, total, name, page=None, page_total=None):
                try:
                    pd.update(current=current, name=name, page=page, page_total=page_total)
                    # Aggiorna la label n/N accanto alla barra
                    if hasattr(pd, 'count_label'):
                        pd.count_label.setText(f"{current}/{total}")
                    logging.debug(f"[GUI] on_progress: current={current} total={total} name={name} page={page} page_total={page_total}")
                except Exception:
                    pass

            def on_finished(results):
                try:
                    pd.close()
                except Exception:
                    pass
                # Eliminato: dialogo ridondante
                logging.info("Elaborazione completata (worker)")
                # Pulizia finale: assicurati che il worker sia terminato e rimosso
                try:
                    # se disponibile, chiedi cancellazione e attendi brevemente
                    worker.cancel()
                except Exception:
                    pass
                try:
                    worker.wait(3000)
                except Exception:
                    pass
                try:
                    # deleteLater per sicurezza nella loop Qt
                    worker.deleteLater()
                except Exception:
                    pass

            dlg = QDialog(parent)
            dlg.setWindowTitle(get_msg(glossario_data, "Informazioni", lingua.upper()))
            dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
            dlg.setStyleSheet("QDialog { background: #fff; border: 2px solid #a67c52; } QLabel, QPushButton { color: #482e1a; font-size: 16px; } QPushButton { background-color: #d2bb8a; border: 1px solid #a67c52; padding: 6px 18px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #e5d3b3; }")
            layout = QVBoxLayout()
            layout.setContentsMargins(20, 15, 20, 15)
            layout.setSpacing(2)
            email_path = os.path.join(ASSET_COMMON, "testuali", "email.txt")
            email = (carica_testo_asset(email_path) or "").strip()
            r1 = QLabel(f"ATK-Pro v{VERSION}")
            r2 = QLabel("©2026 Daniele Pigoli")
            msg = get_msg(self.glossario_data, "email non disponibile", self.lingua)
            r3 = QLabel(email if email else msg or "email non disponibile")
            for lbl in (r1, r2, r3):
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("QLabel { background: transparent; color: #482e1a; font-size: 16px; }")
                layout.addWidget(lbl)
            ok_btn = QPushButton(get_msg(glossario_data, "Chiudi", lingua.upper()))
            ok_btn.clicked.connect(dlg.accept)
            layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
            dlg.setLayout(layout)
            dlg.adjustSize()
            dlg.setFixedSize(dlg.sizeHint())
            dlg.exec()

            

            # Pulizia: rimuovi il riferimento quando finisce
            def _cleanup_worker(results=None):
                # Helper per fermare il worker in modo robusto
                def _ensure_worker_stopped(w, timeout_ms=5000):
                    try:
                        # indica al lavoro di terminare
                        try:
                            w.cancel()
                        except Exception:
                            pass
                        # Se il thread supporta quit(), usalo
                        try:
                            w.quit()
                        except Exception:
                            pass
                        # Attendi che termini
                        try:
                            w.wait(timeout_ms)
                        except Exception:
                            pass
                        # Se ancora in esecuzione, forza la terminazione (ultima risorsa)
                        try:
                            if getattr(w, 'isRunning', lambda: False)():
                                try:
                                    w.terminate()
                                except Exception:
                                    pass
                                try:
                                    w.wait(2000)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        # deleteLater per pulire l'oggetto Qt
                        try:
                            w.deleteLater()
                        except Exception:
                            pass
                    except Exception:
                        pass

                try:
                    if parent is not None and getattr(parent, '_active_worker', None) is worker:
                        _ensure_worker_stopped(worker, timeout_ms=5000)
                        parent._active_worker = None
                except Exception:
                    pass
                # Rimosso: gestione legacy di elaborazione.state
                # Ora non serve più, lo stato è solo in main_gui_qt.py
                pass

            try:
                worker.signals.finished.connect(_cleanup_worker)
            except Exception:
                pass
                try:
                    # ...existing code...
                    try:
                        from src.qt_worker import ElaborazioneWorker
                        from PySide6.QtCore import QCoreApplication
                        pd = ProgressDialog(glossario_data, lingua, total=len(records), parent=parent)
                    except Exception:
                        pass
                        pd.show()
                        worker = ElaborazioneWorker(records, formats=selected_formats, glossario_data=glossario_data, lingua=lingua)
                        def on_progress(current, total, name):
                            try:
                                pd.update(current=current, name=name)
                                logging.debug(f"[GUI] on_progress: current={current} total={total} name={name}")
                            except Exception:
                                pass
                        def on_finished(results):
                            try:
                                pd.close()
                            except Exception:
                                pass
                            # Verifica se tutti i risultati sono SUCCESS
                            all_success = all(r.get('status') == 'SUCCESS' for r in (results or []))
                            if all_success:
                                show_operation_completed_dialog(parent, glossario_data, lingua)
                                logging.info("Elaborazione completata (worker)")
                            else:
                                show_msgbox_localized(parent, glossario_data, lingua, "ATK-Pro", get_msg(glossario_data, "Operazione terminata con errori. Alcuni record non sono stati elaborati correttamente.", lingua) or "Operazione terminata con errori. Alcuni record non sono stati elaborati correttamente.", QMessageBox.Critical, buttons=("Chiudi",), default="Chiudi")
                                logging.warning("Elaborazione terminata con errori (worker)")
                            try:
                                worker.cancel()
                            except Exception:
                                pass
                            try:
                                worker.wait(3000)
                            except Exception:
                                pass
                            try:
                                worker.deleteLater()
                            except Exception:
                                pass
                        def on_error(err):
                            logging.error(f"Errore worker: {err}")
                            QMessageBox.critical(parent, get_msg(glossario_data, "Attenzione", lingua.upper()), f"{get_msg(glossario_data, 'Errore durante l\'elaborazione (worker)', lingua.upper())}: {err}")
                        worker.signals.progress.connect(on_progress)
                        def _handle_need_pdf_confirmation(idx, nome_file):
                            try:
                                resp = ask_generate_pdf(glossario_data, lingua, parent)
                                try:
                                    records[idx]['gen_pdf'] = bool(resp)
                                except Exception:
                                    pass
                            except Exception as e:
                                logging.debug(f"Errore mostrare richiesta PDF per {nome_file}: {e}")
                        try:
                            worker.signals.need_pdf_confirmation.connect(_handle_need_pdf_confirmation)
                        except Exception:
                            pass
                        worker.signals.finished.connect(on_finished)
                        worker.signals.error.connect(on_error)
                        try:
                            worker._ref = worker
                        except Exception:
                            pass
                        worker.start()
                        return
                    except Exception as e:
                        msg = get_msg(self.glossario_data, "Worker Qt non disponibile", self.lingua)
                        logging.debug(msg or f"Worker Qt non disponibile o inizializzazione fallita: {e}")
                    risultati = elaborazione_mod.esegui_elaborazione(
                        state,
                        glossario_data=glossario_data,
                        lingua=lingua,
                        records=records,
                        formats=selected_formats
                    )
                    # Mostra dialog coerente con esito
                    all_success = all(r.get('status') == 'SUCCESS' for r in (risultati or []))
                    if all_success:
                        show_operation_completed_dialog(parent, glossario_data, lingua)
                        logging.info("Elaborazione completata (no worker)")
                    else:
                        show_msgbox_localized(parent, glossario_data, lingua, "ATK-Pro", get_msg(glossario_data, "Operazione terminata con errori. Alcuni record non sono stati elaborati correttamente.", lingua) or "Operazione terminata con errori. Alcuni record non sono stati elaborati correttamente.", QMessageBox.Critical, buttons=("Chiudi",), default="Chiudi")
                        logging.warning("Elaborazione terminata con errori (no worker)")
                except Exception as e:
                    QMessageBox.critical(parent, get_msg(glossario_data, "Attenzione", lingua.upper()), f"{get_msg(glossario_data, 'Errore durante l\'elaborazione', lingua.upper())}: {str(e)}")
                    logging.exception("Errore durante l'elaborazione")
        
        # Blocco legacy per visualizzazione elaborazioni precedenti rimosso (manifest_files non definito)

    except Exception:
        pass
        # Fine blocco riscritto


def action_placeholder(glossario_data, lingua, voce):
    from pathlib import Path
    documents_dir = str(Path.home() / 'Documents' / 'ATK-Pro')
    if voce == "Esporta configurazione":
        default_path = os.path.join(documents_dir, "ATK-Pro-config.json")
        path, _ = QFileDialog.getSaveFileName(None, get_msg(glossario_data, "Esporta configurazione", lingua.upper()) or "Esporta configurazione", default_path, "File JSON (*.json)", options=_qfd_options())
        if not path:
            return
        # Aggiorna lo stato prima di salvare: prendi i dati reali dai widget/variabili
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        for w in app.topLevelWidgets():
            if isinstance(w, MainWindow):
                w.aggiorna_state_da_ui()
                w.mostra_valori_configurazione()
                w.resizeEvent(None)
                w.esporta_configurazione()
                break
        msg = QMessageBox()
        msg.setWindowIcon(QIcon(asset_path("assets/common/grafici/ATK-Pro.ico")))
        msg.setMinimumSize(700, 200)
        msg.setWindowTitle(get_msg(glossario_data, voce, lingua.upper()))
        msg.setText(get_msg(glossario_data, "Operazione completata", lingua.upper()) or "Configurazione esportata correttamente.")
        msg.exec()
    elif voce == "Importa configurazione":
        default_path = os.path.join(documents_dir, "ATK-Pro-config.json")
        path, _ = QFileDialog.getOpenFileName(None, get_msg(glossario_data, "Importa configurazione", lingua.upper()) or "Importa configurazione", default_path, "File JSON (*.json)", options=_qfd_options())
        if not path:
            return
        for w in app.topLevelWidgets():
            if isinstance(w, MainWindow):
                w.importa_configurazione()
                break
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        for w in app.topLevelWidgets():
            if isinstance(w, MainWindow):
                w.aggiorna_ui_da_state()
                w.mostra_valori_configurazione()
                w.resizeEvent(None)
                break
        msg = QMessageBox()
        msg.setWindowIcon(QIcon(asset_path("assets/common/grafici/ATK-Pro.ico")))
        msg.setMinimumSize(700, 200)
        msg.setWindowTitle(get_msg(glossario_data, voce, lingua.upper()))
        msg.setText(get_msg(glossario_data, "Operazione completata", lingua.upper()) or "Configurazione importata correttamente.")
        msg.exec()
    else:
        msg = QMessageBox()
        msg.setWindowIcon(QIcon(asset_path("assets/common/grafici/ATK-Pro.ico")))
        msg.setMinimumSize(700, 200)
        msg.setWindowTitle(get_msg(glossario_data, voce, lingua.upper()))
        msg.setText(get_msg(glossario_data, "Funzione in sviluppo", lingua.upper()))
        msg.exec()


def mostra_banner_chiusura(glossario_data, lingua, banner_path, paypal_url_path, parent=None):
    dlg = QDialog(parent)
    dlg.setWindowTitle(get_msg(glossario_data, "Sostieni il progetto", lingua.upper()))
    dlg.setWindowIcon(QIcon(get_pixmap_cached(asset_path("assets/common/grafici/ATK-Pro.ico"))))
    dlg.setStyleSheet("QDialog { background: transparent; }")
    dlg.setAutoFillBackground(True)

    layout = QVBoxLayout()

    if banner_path and os.path.exists(banner_path):
        try:
            pixmap = QPixmap(banner_path)
            if not pixmap.isNull():
                # Dimensione stretta attorno al banner
                max_w, max_h = 560, 360
                scaled = pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # Ridimensiona dialog in modo aderente all'immagine + margine minimo
                pad_w, pad_h = 32, 24
                dlg.resize(min(scaled.width() + pad_w, max_w + pad_w),
                           min(scaled.height() + pad_h, max_h + pad_h))

                def apri_paypal():
                    if not os.path.exists(paypal_url_path):
                        logging.warning(f"PayPal: file non trovato: {paypal_url_path}")
                        return
                    raw = carica_testo_asset(paypal_url_path).strip()
                    # Supporta sia plain URL che formato INI Windows (.url)
                    url = None
                    for line in raw.splitlines():
                        s = line.strip()
                        if s.upper().startswith("URL="):
                            url = s[4:].strip()
                            break
                    if not url and raw.startswith("http"):
                        url = raw.split()[0]
                    if not url:
                        logging.warning("PayPal: URL non trovato nel file")
                        return
                    logging.debug(f"Apro PayPal URL: {url}")
                    opened = False
                    # QProcess.startDetached non eredita LD_LIBRARY_PATH del bundle
                    # PyInstaller: è il metodo corretto per aprire URL da app Qt.
                    try:
                        from PySide6.QtCore import QProcess
                        import platform
                        _sys = platform.system()
                        if _sys == "Linux":
                            for _prog, _args in [
                                ("/usr/bin/gio", ["open", url]),
                                ("/usr/bin/xdg-open", [url]),
                                ("xdg-open", [url]),
                            ]:
                                if QProcess.startDetached(_prog, _args):
                                    opened = True
                                    logging.debug(f"PayPal: aperto con {_prog}")
                                    break
                        elif _sys == "Darwin":
                            opened = QProcess.startDetached("open", [url])
                            logging.debug(f"PayPal: open (macOS) -> {opened}")
                        else:
                            opened = QDesktopServices.openUrl(QUrl(url))
                            logging.debug(f"PayPal: QDesktopServices -> {opened}")
                    except Exception as e:
                        logging.debug(f"PayPal QProcess fallito: {e}")
                    # Fallback: QDesktopServices
                    if not opened:
                        try:
                            opened = QDesktopServices.openUrl(QUrl(url))
                            logging.debug(f"PayPal: QDesktopServices.openUrl -> {opened}")
                        except Exception as e:
                            logging.debug(f"QDesktopServices fallito: {e}")
                    # Fallback finale: webbrowser
                    if not opened:
                        try:
                            import webbrowser
                            opened = bool(webbrowser.open(url))
                            logging.debug(f"PayPal: webbrowser.open -> {opened}")
                        except Exception as e:
                            logging.warning(f"Impossibile aprire URL PayPal: {e}")

                # QPushButton flat: 'clicked' è un segnale Qt nativo e sempre
                # affidabile (QLabel.mousePressEvent in PySide6 non intercetta
                # gli eventi C++ via monkey-patch su istanza)
                btn_paypal = QPushButton()
                btn_paypal.setFlat(True)
                btn_paypal.setStyleSheet(
                    "QPushButton { border: none; background: transparent; margin: 0; padding: 0; }"
                )
                btn_paypal.setIcon(QIcon(scaled))
                btn_paypal.setIconSize(scaled.size())
                btn_paypal.setCursor(Qt.PointingHandCursor)
                btn_paypal.clicked.connect(apri_paypal)
                layout.addWidget(btn_paypal)
        except Exception as e:
            logging.debug(f"Errore caricamento banner: {e}")
            layout.addWidget(QLabel(get_msg(glossario_data, "Banner non disponibile", lingua.upper())))
    else:
        layout.addWidget(QLabel(get_msg(glossario_data, "Banner non disponibile", lingua.upper())))

    chiudi_btn = QPushButton(get_msg(glossario_data, "Chiudi", lingua.upper()))
    chiudi_btn.clicked.connect(dlg.accept)
    layout.addWidget(chiudi_btn)

    dlg.setLayout(layout)
    dlg.exec()


def main():
    logging.info("Test log avvio")
    logging.debug("Avvio main_gui_qt.py")

    # Su Linux, disabilita il sandbox Chromium solo in ambienti CI/headless
    # (dove il kernel non supporta user namespaces per il renderer QtWebEngine).
    # Su desktop reale (con DISPLAY o WAYLAND_DISPLAY) il sandbox rimane attivo.
    if sys.platform.startswith("linux"):
        in_ci = os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS")
        has_display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        if in_ci or not has_display:
            os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
            os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox")

    app = QApplication(sys.argv)

    # Font custom (usa asset_path per supportare bundle macOS/Windows)
    font1_path = asset_path("assets/common/fonts/Aref_Ruqaa/ArefRuqaa-Regular.ttf")
    font2_path = asset_path("assets/common/fonts/Crimson_Text/CrimsonText-Regular.ttf")
    QFontDatabase.addApplicationFont(font1_path)
    QFontDatabase.addApplicationFont(font2_path)
    logging.debug(f"Font custom caricati: {font1_path}, {font2_path}")

    # Su macOS usa Fusion: Aqua nativo ignora parzialmente i fogli di stile QSS
    if sys.platform == "darwin":
        app.setStyle("Fusion")
        # Forza tutte le dialog (QFileDialog, QMessageBox) a usare il renderer Qt
        # invece del picker nativo macOS, che ignora QPalette e QSS
        from PySide6.QtCore import Qt as _Qt
        app.setAttribute(_Qt.AA_DontUseNativeDialogs)
        # Palette dark globale: garantisce che QDialog e tutti i widget
        # ereditino sfondo scuro e testo bianco, indipendentemente dal QSS
        from PySide6.QtGui import QPalette as _QPalette, QColor as _QColor
        _pal = _QPalette()
        _pal.setColor(_QPalette.Window,          _QColor(24, 24, 24))
        _pal.setColor(_QPalette.WindowText,      _QColor(255, 255, 255))
        _pal.setColor(_QPalette.Base,            _QColor(34, 34, 34))
        _pal.setColor(_QPalette.AlternateBase,   _QColor(45, 45, 45))
        _pal.setColor(_QPalette.Text,            _QColor(255, 255, 255))
        _pal.setColor(_QPalette.Button,          _QColor(34, 34, 34))
        _pal.setColor(_QPalette.ButtonText,      _QColor(255, 255, 255))
        _pal.setColor(_QPalette.Highlight,       _QColor(166, 124, 82))
        _pal.setColor(_QPalette.HighlightedText, _QColor(255, 255, 255))
        app.setPalette(_pal)

    # Stile ATK da QSS
    file = QFile(asset_path("assets/common/testuali/atk_style.qss"))
    if file.open(QFile.ReadOnly | QFile.Text):
        app.setStyleSheet(str(file.readAll(), encoding="utf-8"))
        logging.debug("Stile ATK applicato da atk_style.qss")
    else:
        logging.debug("Errore: impossibile caricare atk_style.qss")

    # Su macOS: appende override dark per QMessageBox (QPalette non basta per il background)
    if sys.platform == "darwin":
        app.setStyleSheet(app.styleSheet() + """
QMessageBox {
    background-color: #181818;
    color: #ffffff;
}
QMessageBox QLabel {
    color: #ffffff;
    background-color: transparent;
}
QMessageBox QPushButton {
    background-color: #222222;
    color: #ffffff;
    border: 1px solid #a67c52;
    padding: 4px 16px;
    border-radius: 4px;
    font-weight: bold;
}
QMessageBox QPushButton:hover {
    background-color: #333333;
}
""")

    # Selezione lingua e gestione primo avvio
    _is_frozen = getattr(sys, 'frozen', False)
    primo_avvio = False

    if _is_frozen and sys.platform == "win32":
        if IS_PORTABLE:
            # Portable: nessun installer → usa config file, non il registro Windows
            saved = _read_config_language()
            _disc_ok = _read_config_disclaimer_accepted()
            if saved and _disc_ok:
                lingua = saved
                primo_avvio = False
                logging.debug(f"Portable: lingua da config file: {lingua}")
            else:
                # Primo avvio portable: scegli lingua poi mostra disclaimer
                primo_avvio = True
                glossario_data_tmp = carica_glossario("en")
                lingua = scegli_lingua(glossario_data_tmp, "en")
                _write_config_language(lingua)
                logging.debug(f"Portable primo avvio: lingua scelta: {lingua}")
        else:
            # Installer: leggi la lingua dal registro (settata dall'Inno Setup installer)
            lingua = get_language_from_registry()
            logging.debug(f"Windows EXE: lingua dal registro: {lingua}")

    elif _is_frozen and sys.platform in ("linux", "darwin"):
        # Linux/macOS bundle: usa file di configurazione utente
        saved = _read_config_language()
        if saved:
            lingua = saved
            _disc_ok = _read_config_disclaimer_accepted()
            if sys.platform == "darwin" and not _disc_ok:
                primo_avvio = True  # disclaimer non ancora accettato
                logging.debug("macOS: lingua salvata ma disclaimer non accettato, forzo primo avvio")
            else:
                primo_avvio = False
            logging.debug(f"Linux/macOS EXE: lingua da config file: {lingua}")
        else:
            # Fallback: leggi /etc/atk-pro/defaults.json (scritto dal postinst)
            # Questo copre i casi in cui il postinst non ha trovato SUDO_USER
            # (es. installazione via polkit/GNOME Software)
            _sys_default = None
            try:
                import json as _jj
                with open("/etc/atk-pro/defaults.json", encoding="utf-8") as _fh:
                    _dd = _jj.load(_fh)
                _cl = _dd.get("language", "").strip().lower()
                if _cl in _LINGUE_VALIDE:
                    _sys_default = _cl
                    logging.debug(f"Lingua da /etc/atk-pro/defaults.json: {_sys_default}")
            except Exception as _ex:
                logging.debug(f"defaults.json non leggibile: {_ex}")

            if _sys_default:
                lingua = _sys_default
                primo_avvio = False
                _write_config_language(lingua)  # propaga in ~/.config
                logging.debug(f"Linux/macOS: lingua da defaults di sistema: {lingua}")
            else:
                # Solo se nessun default è disponibile → mostra dialog scelta lingua
                primo_avvio = True
                glossario_data_tmp = carica_glossario("en")
                lingua = scegli_lingua(glossario_data_tmp, "en")
                _write_config_language(lingua)
                logging.debug(f"Linux/macOS primo avvio: lingua scelta: {lingua}")

        # Installazione GUI (.deb via GDebi/GNOME Software/etc.): il preinst
        # scrive il flag pending-disclaimer e non mostra nulla sullo schermo.
        # Al primo avvio qui forziamo la selezione lingua esplicita da parte
        # dell'utente, indipendentemente dal default di sistema impostato dal postinst.
        _PENDING_FLAG_EARLY = "/var/lib/atk-pro/pending-disclaimer"
        if (not primo_avvio
                and sys.platform == "linux"
                and os.path.exists(_PENDING_FLAG_EARLY)):
            logging.debug("Pending-disclaimer flag rilevato: forzo selezione lingua prima del disclaimer")
            glossario_data_tmp = carica_glossario(lingua)
            lingua = scegli_lingua(glossario_data_tmp, lingua)
            _write_config_language(lingua)
            logging.debug(f"Lingua scelta dopo installazione GUI: {lingua}")

    else:
        # Modalità sviluppo: stessa logica Linux/macOS (config file per primo avvio)
        saved = _read_config_language()
        if saved:
            lingua = saved
            primo_avvio = False
            logging.debug(f"Sviluppo: lingua da config file: {lingua}")
        else:
            primo_avvio = True
            glossario_data_tmp = carica_glossario("en")
            lingua = scegli_lingua(glossario_data_tmp, "en")
            _write_config_language(lingua)
            logging.debug(f"Sviluppo primo avvio: lingua scelta: {lingua}")

    glossario_data = carica_glossario(lingua)

    # Crea cartelle output di default (silenzioso, exist_ok=True)
    _ensure_default_output_dirs()

    # Carica file di esempio localizzato
    example_path = carica_file_esempio(lingua)
    state["records"].append(example_path)
    logging.debug(f"File di esempio caricato: {example_path}")

    # Creazione finestra principale
    window = MainWindow(glossario_data, lingua)
    window.show()

    # Check aggiornamenti automatico all'avvio (silenzioso se già aggiornato)
    from PySide6.QtCore import QTimer
    window._startup_checker = _UpdateCheckerThread()
    def _on_startup_update(is_newer, latest_version, release_url, assets):
        if is_newer:
            window._mostra_dialogo_aggiornamento(is_newer, latest_version, release_url, assets, silent_if_ok=False)
    window._startup_checker.result.connect(_on_startup_update)
    QTimer.singleShot(3000, window._startup_checker.start)  # 3s dopo l'avvio

    # Mostra disclaimer al primo avvio oppure dopo installazione silente (GNOME Software)
    _PENDING_FLAG = "/var/lib/atk-pro/pending-disclaimer"
    _ha_flag_pendente = (
        not primo_avvio
        and sys.platform.startswith("linux")
        and _is_frozen
        and os.path.exists(_PENDING_FLAG)
    )
    if primo_avvio or _ha_flag_pendente:
        accettato = mostra_disclaimer(glossario_data, lingua)
        if _ha_flag_pendente and accettato:
            # Rimuovi flag solo se accettato; se rifiutato rimane per il prossimo avvio
            try:
                os.remove(_PENDING_FLAG)
                logging.info("Flag pending-disclaimer rimosso dopo accettazione")
            except OSError as e:
                logging.warning(f"Impossibile rimuovere flag pending-disclaimer: {e}")
        if (IS_PORTABLE or sys.platform == "darwin") and accettato:
            # Portable/macOS: persisti l'accettazione nel config affinché non venga richiesta al prossimo avvio
            _write_config_disclaimer_accepted()
            logging.info("Portable/macOS: disclaimer accettato, salvato in config.json")
        if not accettato:
            logging.warning("Disclaimer rifiutato → chiusura applicazione")
            # Cancella lingua salvata: al prossimo avvio primo_avvio=True / flag ancora presente
            try:
                _cfg = _config_file_path()
                if os.path.exists(_cfg):
                    os.remove(_cfg)
                    logging.info("Config lingua cancellata dopo rifiuto disclaimer")
            except OSError as _e:
                logging.warning(f"Impossibile cancellare config lingua: {_e}")
            sys.exit(1)

    # Gestione chiusura con banner
    def on_close():
        logging.debug("Chiusura applicazione")
        lingua_norm = lingua.strip().lower()
        lingua_alt = lingua.strip().upper() if lingua_norm != lingua.strip().upper() else lingua.strip().lower()
        # Prova prima in minuscolo, poi maiuscolo
        paths = [
            os.path.join(ASSET_LANG, lingua_norm, "grafici", "sostieni_banner_qr.png"),
            os.path.join(ASSET_LANG, lingua_norm, "grafici", "sostieni_banner_qr.webp"),
            os.path.join(ASSET_LANG, lingua_alt, "grafici", "sostieni_banner_qr.png"),
            os.path.join(ASSET_LANG, lingua_alt, "grafici", "sostieni_banner_qr.webp")
        ]
        banner_path = None
        for p in paths:
            logging.debug(f"Verifica banner: {p} -> {'OK' if os.path.exists(p) else 'MANCANTE'}")
            if os.path.exists(p):
                banner_path = p
                break
        if not banner_path:
            logging.error(f"Nessun banner trovato nei path: {paths}")
        else:
            logging.info(f"Banner path selezionato: {banner_path}")
        paypal_url_path = os.path.join(ASSET_COMMON, "testuali", "PayPal.Me.url")
        mostra_banner_chiusura(glossario_data, lingua_norm, banner_path, paypal_url_path, parent=window)

    app.aboutToQuit.connect(on_close)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

