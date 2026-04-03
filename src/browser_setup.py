# -*- coding: utf-8 -*-
# Modulo: browser_setup.py
# Setup Selenium e Playwright per il caricamento delle pagine
# Riallineato alla logica Antenati_Tile_Rebuilder_v1.4.1.py

import os
import sys
import logging

logger = logging.getLogger(__name__)

# Imposta il path locale per i browser Playwright inclusi nel bundle EXE
if getattr(sys, 'frozen', False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(sys._MEIPASS, "ms-playwright")

# === Selenium Setup ===
# Import lazy: evita crash all'avvio se selenium/chromedriver non disponibili

def setup_selenium():
    """
    Avvia Selenium con Chrome headless e ritorna il driver,
    oppure None se fallisce.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
    except ImportError as e:
        logger.debug(f"[Selenium] Import fallito: {e}")
        return None

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service()
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("[OK] Selenium avviato correttamente.")
        return driver
    except Exception as e:
        logger.error(f"[Selenium] Errore: {e}", exc_info=True)
        return None

# === Playwright Setup ===
# Import lazy: evita crash all'avvio se playwright/chromium non disponibili

def setup_playwright(url):
    """
    Avvia Playwright con Chromium headless, carica la pagina e ritorna l'HTML,
    oppure None se fallisce.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        logger.debug(f"[Playwright] Import fallito: {e}")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, timeout=15000)  # 15 secondi di timeout
            page.wait_for_timeout(5000)    # attesa per caricamento dinamico
            html = page.content()
            browser.close()
            logger.info("[OK] Playwright ha caricato la pagina correttamente.")
            return html
    except Exception as e:
        logger.error(f"Errore in setup_playwright: {e}", exc_info=True)
        return None
