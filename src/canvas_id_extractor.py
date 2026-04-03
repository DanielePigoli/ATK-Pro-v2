# === Copertura test ===
# ✔ Test realistici presenti
# ✔ Rami difensivi simulati
# ✅ Validato (logico)

import re
import sys
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import urllib.request
import urllib.error

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
        
        # Scarica l'HTML della pagina
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            log_to_file(f"[HTML Fallback] HTML scaricato: {len(html)} caratteri")
            
            # Cerca il canvasId nel markup Mirador
            # Pattern: canvasId: 'https://...../0nZjWV9'
            match = re.search(r"canvasId:\s*['\"]([^'\"]*)/([A-Za-z0-9]+)['\"]", html)
            if match:
                canvas_id = match.group(2)
                log_to_file(f"[HTML Fallback] Canvas ID trovato: {canvas_id}")
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
    Estrae il canvas_id per documenti an_ud usando Playwright headless.
    Carica la pagina e cerca il pattern canvasId nel sorgente JS-renderizzato.
    """
    log_to_file(f"[UD] Estrazione canvas ID via Playwright per: {url}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, timeout=timeout_ms)
            page.wait_for_timeout(5000)
            html = page.content()
            browser.close()
            # Cerca canvasId nel markup Mirador renderizzato
            match = re.search(r"canvasId:\s*['\"]([^'\"]*)/([A-Za-z0-9_-]+)['\"]", html)
            if match:
                canvas_id = match.group(2)
                log_to_file(f"[UD] Canvas ID trovato via Playwright: {canvas_id}")
                return canvas_id
            # Cerca anche nel formato JSON (@id nel manifest inline)
            match2 = re.search(
                r'"@id"\s*:\s*"https://(?:dam-)?antenati\.cultura\.gov\.it/[^"]+/([A-Za-z0-9_-]+)"',
                html
            )
            if match2:
                canvas_id = match2.group(1)
                log_to_file(f"[UD] Canvas ID trovato via Playwright (@id JSON): {canvas_id}")
                return canvas_id
            log_to_file("[UD] canvasId non trovato nel HTML Playwright")
    except Exception as e:
        log_to_file(f"[UD] Errore Playwright: {e}")
    return None
