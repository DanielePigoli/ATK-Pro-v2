# === Copertura test ===
# ✔ Test realistici presenti
# ✔ Rami difensivi simulati
# ✅ Validato (logico)

import re
import sys
import os
from datetime import datetime
import requests

# === LOGGING SU FILE ===
LOG_FILE = os.path.join(os.path.expanduser("~"), "ATK-Pro_canvas_extraction.log")

def log_to_file(message):
    """Scrivi un messaggio nel file di log"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {message}\n")
    except:
        pass
    print(message)  # Stampa anche in console se disponibile

def extract_canvas_id_from_url(url: str) -> str | None:
    """
    Estrae il canvas_id dalla pagina ARK scaricando l'HTML e cercando il tag 
    Mirador.viewer con il canvasId.
    
    Esempio di markup trovato:
    windows: [{
      ...
      canvasId: 'https://antenati.cultura.gov.it/ark:/12657/an_ua19467467/0nZjWV9'
    }]
    """
    try:
        log_to_file(f"[HTML Fallback] Scarico HTML da {url}")

        # Usa requests (gestisce SSL via certifi su tutte le piattaforme, incluso macOS)
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "it-IT,it;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        log_to_file(f"[HTML Fallback] HTML scaricato: {len(html)} caratteri")
        
        # Cerca il canvasId nel markup Mirador
        # Pattern: canvasId: 'https://...../0nZjWV9'
        match = re.search(r"canvasId:\s*['\"]([^'\"]*)/([A-Za-z0-9]+)['\"]", html)
        if match:
            canvas_id = match.group(2)
            log_to_file(f"[HTML Fallback] Canvas ID trovato (JS): {canvas_id}")
            return canvas_id

        # Cerca in formato JSON (__NEXT_DATA__ o script inline)
        match = re.search(r'"canvasId"\s*:\s*"([^"]*)/([A-Za-z0-9]+)"', html)
        if match:
            canvas_id = match.group(2)
            log_to_file(f"[HTML Fallback] Canvas ID trovato (JSON): {canvas_id}")
            return canvas_id

        log_to_file("[HTML Fallback] canvasId non trovato nel markup Mirador")
            
    except Exception as e:
        log_to_file(f"[HTML Fallback] Errore scaricamento HTML: {str(e)[:100]}")
    
    # Fallback finale: estrai dal segmento finale dell'URL
    match = re.search(r'/([a-zA-Z0-9]+)$', url)
    if match:
        canvas_id = match.group(1)
        log_to_file(f"[URL Fallback] Canvas ID dall'URL: {canvas_id}")
        return canvas_id
    
    log_to_file("[Fallback] Impossibile estrarre canvas ID")
    return None


def extract_ud_canvas_id(driver) -> str | None:
    """Estrae un canvas_id dal sorgente HTML di Selenium driver."""
    print("[Canvas] Cerco canvas selezionato nella pagina...")
    try:
        html = driver.page_source
        match = re.search(
            r'"@id"\s*:\s*"https://dam-antenati\.cultura\.gov\.it/iiif/2/([^"/]+)',
            html
        )
        if match:
            canvas_id = match.group(1).strip()
            print(f"[Canvas] ID canvas identificato: {canvas_id}")
            return canvas_id
    except Exception as e:
        print(f"[Warning] Errore nell'estrazione dell'ID canvas: {e}")
    print("[Canvas] Nessun ID canvas trovato nella pagina.")
    return None


def extract_ud_canvas_id_from_infojson_xhr(url: str, timeout_ms: int = 30000) -> str | None:
    """
    Estrae il canvas_id per documenti an_ud usando Playwright.
    Per ora, ritorna None per far ricadere su fallback (dato che Playwright 
    non funziona affidabilmente nel PyInstaller compilato).
    Il fallback in elaborazione.py userà extract_canvas_id_from_url().
    """
    # NOTA: Playwright fallisce silenziosamente nel PyInstaller compilato
    # perché non ha stdout/stderr. Disabilitato per ora.
    # TODO: Implementare un metodo basato su requests HTTP + DOM parsing
    log_to_file("[UD] extract_ud_canvas_id_from_infojson_xhr: Playwright disabilitato nel PyInstaller compilato")
    return None
