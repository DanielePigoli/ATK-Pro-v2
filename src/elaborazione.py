# -*- coding: utf-8 -*-
import os
import re
import json
import time
import logging
import concurrent.futures
from logging.handlers import RotatingFileHandler
import shutil
from PIL import Image

from manifest_utils import download_manifest, robust_find_manifest
from canvas_id_extractor import extract_canvas_id_from_url, extract_ud_canvas_id_from_infojson_xhr
from browser_setup import setup_selenium, setup_playwright
try:
    from src.user_prompts import ask_generate_pdf, ask_image_formats
except ImportError:
    from user_prompts import ask_generate_pdf, ask_image_formats
# ProgressDialog viene importato all'occorrenza per evitare problemi di circular import
from image_downloader import download_info_json
from tile_downloader import download_tiles
from tile_rebuilder import rebuild_image, build_image_metadata
from manifest_parser import estrai_metadati_da_manifest, build_manifest_url
from pdf_generator import create_pdf_from_images, enrich_pdf_metadata
from metadata_utils import embed_metadata_and_save, _save_sidecar_json_once



# --- Logging configurabile per ambiente ---
ATKPRO_ENV = os.environ.get("ATKPRO_ENV", "development").lower()
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    # Log su terminale sempre attivo
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG if ATKPRO_ENV != "production" else logging.WARNING)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Log su file solo se non in produzione
    if ATKPRO_ENV != "production":
        file_handler = RotatingFileHandler('atkpro_output.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG if ATKPRO_ENV != "production" else logging.WARNING)

# State globale per GUI/main

def get_msg(glossario_data, chiave, lingua="IT"):
    """Restituisce un messaggio localizzato dal glossario.
    Supporta il formato JSON del glossario ({sezione: [{messaggio, IT, FR, ...}]}).
    Se non trovato, ritorna la chiave originale.
    """
    try:
        if glossario_data:
            lingua_up = lingua.upper() if lingua else "IT"
            if lingua_up == "DK":
                lingua_up = "DA"
            if lingua_up == "VN":
                lingua_up = "VI"
            for section in glossario_data.values():
                if isinstance(section, list):
                    for voce in section:
                        if voce.get("messaggio") == chiave:
                            return voce.get(lingua_up, voce.get("IT", None))
    except Exception:
        pass
    return chiave


def _parse_ua_from_url(url: str):
    """Estrae l'UA (Unità Archivistica) da un URL antenati."""
    m = re.search(r'/ark:/12657/(an_[u][ad]\d+)', url)
    if m:
        return m.group(1)
    return None


def _parse_ark_from_url(url: str):
    """Estrae l'ARK completo da un URL antenati."""
    m = re.search(r'/ark:/12657/([^/#\s]+(?:/[^#\s]+)?)', url)
    if m:
        return "ark:/12657/" + m.group(1)
    return None


def _last_segment(s: str):
    """Estrae l'ultimo segmento di un percorso/URL."""
    if not s:
        return None
    s = s.rstrip('/').split('/')[-1]
    return s or None


def _normalize_format(fmt):
    """Normalizza il nome del formato (JPG->JPEG, TIF->TIFF)."""
    fmt_upper = fmt.upper().strip()
    if fmt_upper in ('JPG', 'JPEG'):
        return 'JPEG'
    elif fmt_upper in ('TIF', 'TIFF'):
        return 'TIFF'
    elif fmt_upper == 'PNG':
        return 'PNG'
    elif fmt_upper == 'PDF':
        return 'PDF'
    return fmt_upper


def save_image_variants(image: Image.Image, output_folder: str, base_filename: str, 
                       formats=['PNG', 'JPEG', 'TIFF'], meta: dict = None):
    """
    Salva immagine in più formati con metadati embed.
    Supporta PNG, JPEG (JPG), TIFF (TIF) con sidecar JSON.
    """
    os.makedirs(output_folder, exist_ok=True)
    
    # Normalizza i formati ricevuti (es. ['PNG', 'JPG', 'TIF'] -> ['PNG', 'JPEG', 'TIFF'])
    formats = [_normalize_format(f) for f in formats]
    
    logger.debug(f"[save_image_variants] image={image}, output={output_folder}, filename={base_filename}, formats={formats}")
    
    if image is None:
        logger.error("[Error] save_image_variants ricevuto image=None")
        return
    
    # Sidecar JSON (una sola volta) — usa helper centralizzato
    if meta and "_json" in meta:
        try:
            _save_sidecar_json_once(output_folder, base_filename, meta)
        except Exception as e:
            logger.warning(f"[Warning] Impossibile salvare sidecar JSON per {base_filename}: {e}")

    # --- LOGICA SUFFISSO UNIVOCO ---

    # --- LOGICA SUFFISSO UNIVOCO PER SESSIONE ---
    if not hasattr(save_image_variants, "_session_filenames") or save_image_variants._session_filenames is None:
        save_image_variants._session_filenames = {}
    session_filenames = save_image_variants._session_filenames
    key = os.path.abspath(output_folder)
    if key not in session_filenames:
        session_filenames[key] = set()

    def get_unique_filename_session(folder, filename, ext):
        used = session_filenames[os.path.abspath(folder)]
        candidate = filename
        i = 2
        while f"{candidate}.{ext}" in used:
            candidate = f"{filename}_rec{i}"
            i += 1
        used.add(f"{candidate}.{ext}")
        return candidate

    # PNG
    if 'PNG' in formats:
        unique_filename = get_unique_filename_session(output_folder, base_filename, "png")
        path = os.path.join(output_folder, f"{unique_filename}.png")
        try:
            try:
                embed_metadata_and_save(image, path, meta)
            except Exception:
                image.save(path, format='PNG')
            logger.info(f"[PNG] Salvata immagine: {path}")
        except Exception as e:
            logger.error(f"[Error] Errore salvataggio PNG {path}: {e}")

    # JPEG
    if 'JPEG' in formats:
        unique_filename = get_unique_filename_session(output_folder, base_filename, "jpg")
        path = os.path.join(output_folder, f"{unique_filename}.jpg")
        try:
            try:
                embed_metadata_and_save(image, path, meta)
            except Exception:
                img_rgb = image.convert("RGB") if image.mode != "RGB" else image
                img_rgb.save(path, format='JPEG', quality=95, progressive=True, optimize=True)
            logger.info(f"[JPEG] Salvata immagine: {path}")
        except Exception as e:
            logger.error(f"[Error] Errore salvataggio JPEG {path}: {e}")

    # TIFF
    if 'TIFF' in formats:
        path = os.path.join(output_folder, f"{base_filename}.tif")
        try:
            try:
                embed_metadata_and_save(image, path, meta)
            except Exception:
                image.save(path, format='TIFF', compression='tiff_lzw')
            logger.info(f"[TIFF] Salvata immagine: {path}")
        except Exception as e:
            logger.error(f"[Error] Errore salvataggio TIFF {path}: {e}")


def _make_placeholder_image(service_id: str, width: int = 800, height: int = 1200,
                             glossario_data=None, lingua: str = "IT",
                             canvas_url: str = None) -> Image.Image:
    """Genera immagine placeholder per download falliti, da includere nel PDF."""
    from PIL import ImageDraw, ImageFont
    img = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    font_large = font_medium = font_small = None
    for font_name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            font_large = ImageFont.truetype(font_name, 36)
            font_medium = ImageFont.truetype(font_name, 24)
            font_small = ImageFont.truetype(font_name, 18)
            break
        except Exception:
            continue
    if font_large is None:
        font_large = font_medium = font_small = ImageFont.load_default()
    title = get_msg(glossario_data, "Download fallito", lingua) or "Download fallito"
    subtitle = get_msg(glossario_data, "Riprova usando il seguente link:", lingua) or "Riprova usando il seguente link:"
    draw.text((50, 80), title, fill=(200, 0, 0), font=font_large)
    draw.text((50, 160), subtitle, fill=(60, 60, 60), font=font_medium)
    url_to_show = canvas_url or service_id
    url_parts = [url_to_show[i:i+70] for i in range(0, len(url_to_show), 70)]
    y = 220
    for part in url_parts:
        draw.text((50, y), part, fill=(0, 0, 180), font=font_small)
        y += 28
    return img


class Elaborazione:
    def __init__(self, record_type: str, ark_url: str, output_dir: str, glossario_data=None, lingua="IT"):
        self.record_type = record_type.upper()
        self.ark_url = ark_url
        self.output_dir = output_dir
        self.nome_file = ""
        self.manifest = None
        self.manifest_path = None
        self.glossario_data = glossario_data
        self.lingua = lingua

    def set_nome_file(self, nome: str):
        """Imposta il nome file per il record."""
        self.nome_file = nome

    def set_formats(self, formats):
        """Imposta i formati di output desiderati."""
        self.formats = formats
        return self

    def run(self, formats=None):
        """Orchestratore principale: scarica manifest e elabora record.
        Se formats è passato, lo usa; altrimenti usa self.formats."""
        if formats:
            self.formats = formats
        logger.info(f"[Elaborazione] Avvio run: output_dir={self.output_dir} nome_file={self.nome_file}")
        try:
            # Download manifest
            self.manifest = self._fetch_manifest()
            logger.info(f"[Elaborazione] Manifest scaricato: {self.manifest_path if self.manifest_path else 'N/A'}")
            if not self.manifest:
                logger.error("[Error] Manifest non disponibile")
                return False

            # Estrai canvas/tiles info
            tiles_info = self.manifest.get("sequences", [{}])[0].get("canvases", [])
            if not tiles_info:
                logger.error("[Error] Nessun canvas nel manifest")
                return False

            metadata = self.manifest.get("metadata", {})

            # Processa in base al tipo
            if self.record_type == "D":
                logger.info(f"[Elaborazione] Tipo D: {self.nome_file}")
                return self._process_document(tiles_info, metadata)
            elif self.record_type == "R":
                logger.info(f"[Elaborazione] Tipo R: {self.nome_file}")
                return self._process_register(tiles_info, metadata)
            else:
                raise ValueError(f"Tipo record non riconosciuto: {self.record_type}")
        except Exception as e:
            logger.error(f"[Error] Errore elaborazione: {e}", exc_info=True)
            return False

    def _fetch_manifest(self):
        """Scarica il manifest IIIF."""
        try:
            manifest_url = self._get_manifest_url()
            if not manifest_url:
                logger.error("[Error] Manifest URL non disponibile")
                return None

            # Crea sottocartella di lavoro univoca nella cartella scelta per l'output
            output_base = self.output_dir  # output_dir è la cartella scelta dall'utente
            container_id = manifest_url.strip("/").split("/")[-2]
            titolo_pulito = re.sub(r'[\\/*?:"<>|]', "", self.nome_file).replace(" ", "_")
            base_folder_name = f"{container_id}_{titolo_pulito}"
            working_folder = os.path.join(output_base, base_folder_name)
            # Se la cartella esiste già, aggiungi suffisso univoco
            if os.path.exists(working_folder):
                i = 2
                while True:
                    candidate = os.path.join(output_base, f"{base_folder_name}_rec{i}")
                    if not os.path.exists(candidate):
                        working_folder = candidate
                        break
                    i += 1
            os.makedirs(working_folder, exist_ok=True)

            # Scarica manifest
            manifest = download_manifest(manifest_url, working_folder, self.nome_file)
            if not manifest:
                logger.error("[Error] Download manifest fallito")
                return None
            
            # Determina percorso manifest (same logic as download_manifest)
            manifest_filename = f"manifest_{container_id}_{titolo_pulito}.json"
            self.manifest_path = os.path.join(working_folder, manifest_filename)
            self.output_dir = working_folder  # Aggiorna output_dir a cartella di lavoro
            
            logger.info(f"[OK] Manifest caricato: {self.manifest_path}")
            return manifest
        except Exception as e:
            logger.error(f"[Error] Errore fetch manifest: {e}", exc_info=True)
            return None

    def _get_manifest_url(self):
        """Ricava URL manifest da selenium/playwright o mappatura hardcoded."""
        # Tentativo 1: Prova browser automation
        try:
            driver = setup_selenium()
            if driver:
                driver.get(self.ark_url)
                import time
                time.sleep(3)
                html = driver.page_source
                driver.quit()
                manifest_url = robust_find_manifest(self.ark_url, html)
                if manifest_url:
                    logger.info(f"Manifest trovato (Selenium): {manifest_url}")
                    return manifest_url
        except Exception as e:
            logger.debug(f"[Selenium] Errore: {e}")

        # Tentativo 2: Fallback Playwright
        try:
            html = setup_playwright(self.ark_url)
            if html:
                manifest_url = robust_find_manifest(self.ark_url, html)
                if manifest_url:
                    logger.info(f"Manifest trovato (Playwright): {manifest_url}")
                    return manifest_url
        except Exception as e:
            logger.debug(f"[Playwright] Errore: {e}")

        # Tentativo 3: HTTP GET diretto sulla pagina (senza browser, cerca containers/manifest nell'HTML)
        try:
            manifest_url = robust_find_manifest(self.ark_url)
            if manifest_url:
                logger.info(f"Manifest trovato (HTTP GET diretto): {manifest_url}")
                return manifest_url
        except Exception as e:
            logger.debug(f"[HTTP Diretto] Errore robust_find_manifest: {e}")

        # Tentativo 4: Usa costruzione URL standard come ultimo resort
        logger.info("Usando fallback build_manifest_url (costruzione URL standard)")
        try:
            manifest_url = build_manifest_url(self.ark_url)
            logger.info(f"Manifest URL costruito: {manifest_url}")
            return manifest_url
        except Exception as e:
            logger.error(f"Errore build_manifest_url: {e}")
            return None

    def _process_document(self, tiles_info, metadata):
        """Elabora documento singolo (D/d) con verifica immagini finali e richiesta PDF opzionale."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            # Calcola formati (incluso PDF) all'inizio per logica placeholder e salvataggio
            formats = self.formats if hasattr(self, 'formats') and self.formats else state.get('formats', [])
            if not formats:
                formats = ['PNG', 'JPEG', 'TIFF']
            _norm_formats = [_normalize_format(f) for f in formats]
            pdf_in_formats = 'PDF' in _norm_formats
            image_formats = [f for f in formats if _normalize_format(f) != 'PDF']
            only_pdf = pdf_in_formats and not image_formats
            temp_pdf_dir = os.path.join(self.output_dir, "_tmp_pdf_images") if only_pdf else None
            if temp_pdf_dir:
                os.makedirs(temp_pdf_dir, exist_ok=True)
            # ...estrazione canvas come prima...
            target_canvas_id = None
            if "an_ud" in self.ark_url:
                logger.info("[Canvas] Estrazione UD - Caricamento pagina ARK con viewer IIIF")
                try:
                    target_canvas_id = extract_ud_canvas_id_from_infojson_xhr(self.ark_url, timeout_ms=30000)
                    logger.info(f"[Canvas] Risultato estrazione Playwright: {target_canvas_id}")
                except Exception as e:
                    logger.warning(f"[Canvas] Estrazione Playwright fallita: {e}")
                if not target_canvas_id:
                    logger.warning("[Canvas] Estrazione UD fallita, provo fallback con URL diretto")
                    target_canvas_id = extract_canvas_id_from_url(self.ark_url)
                    logger.info(f"[Canvas] Risultato fallback: {target_canvas_id}")
            else:
                target_canvas_id = extract_canvas_id_from_url(self.ark_url)
            if not target_canvas_id:
                if tiles_info:
                    target_canvas_id = _last_segment(tiles_info[0].get("@id") or tiles_info[0].get("id") or "")
                    logger.warning(f"[Canvas] Estrazione canvas ID fallita, uso fallback primo canvas: {target_canvas_id}")
            if not target_canvas_id:
                logger.error("[Error] Impossibile ricavare canvas ID documento (strict mode).")
                return False
            canvas = None
            for c in tiles_info:
                canvas_id = c.get("@id") or c.get("id") or ""
                if target_canvas_id in canvas_id:
                    canvas = c
                    break
            if not canvas:
                if tiles_info:
                    canvas = tiles_info[0]
                    canvas_id = canvas.get("@id") or canvas.get("id") or "(sconosciuto)"
                    logger.warning(f"[Canvas] {target_canvas_id} non trovato, uso primo canvas {canvas_id}")
                else:
                    logger.error(f"[Error] Canvas {target_canvas_id} non trovato nel manifest")
                    return False
            service_info = canvas['images'][0]['resource'].get('service')
            service_id = service_info[0].get('@id') if isinstance(service_info, list) else service_info.get('@id')
            image_info_url = service_id.rstrip('/') + '/info.json'
            logger.info(f"[Canvas] Service ID: {service_id}")
            logger.info(f"[Canvas] Info URL: {image_info_url}")
            info = download_info_json(image_info_url)
            if not info:
                logger.error(f"[Error] Impossibile scaricare info.json da {image_info_url}")
                return False
            logger.info(f"[Tiles] Scaricando tiles da info.json")
            tile_dir = os.path.join(self.output_dir, "tiles_doc")
            os.makedirs(tile_dir, exist_ok=True)
            tiles_ok, tiles_missing = download_tiles(info, tile_dir)
            if tiles_missing:
                logger.warning(f"[Elaborazione] Tile mancanti per {self.nome_file}: {len(tiles_missing)}")
                for mf in tiles_missing:
                    logger.warning(f"[Elaborazione] Tile mancante: {mf}")
                self.tiles_missing = tiles_missing
            else:
                self.tiles_missing = []
            logger.info(f"[Rebuild] Ricostruendo immagine dai tiles")
            final_img = rebuild_image(info, tile_dir)
            if final_img is None:
                if pdf_in_formats:
                    logger.warning(f"[PDF] Immagine non ricostruita, genero placeholder per {self.nome_file}")
                    final_img = _make_placeholder_image(service_id,
                        glossario_data=self.glossario_data, lingua=self.lingua,
                        canvas_url=canvas.get('@id') or canvas.get('id'))
                else:
                    logger.error(f"[Error] Fallita ricostruzione immagine")
                    return False
            page_label = canvas.get('label', None)
            try:
                if hasattr(self, 'progress_cb') and callable(self.progress_cb):
                    try:
                        self.progress_cb(1, 1, page_label)
                    except Exception:
                        try:
                            self.progress_cb(1, 1)
                        except Exception:
                            pass
            except Exception:
                pass
            ua = _parse_ua_from_url(self.ark_url)
            ark = _parse_ark_from_url(self.ark_url)
            canvas_id_full = canvas.get("@id") or canvas.get("id") or ""
            canvas_tail = _last_segment(service_id) or _last_segment(canvas_id_full) or target_canvas_id
            description = self.nome_file
            meta = build_image_metadata(
                ua=ua,
                ark=ark,
                canvas_id=canvas_tail,
                page_label=page_label,
                description=description,
                source_url=self.ark_url,
                atk_version="2.0"
            )
            formats = self.formats if hasattr(self, 'formats') and self.formats else state.get('formats', [])
            if not formats:
                formats = ['PNG', 'JPEG', 'TIFF']
            # Salvataggio formati immagine (escluso PDF, gestito separatamente)
            if image_formats:
                save_image_variants(final_img, self.output_dir, self.nome_file, image_formats, meta=meta)
            if only_pdf and temp_pdf_dir:
                _pdf_png_path = os.path.join(temp_pdf_dir, f"{self.nome_file}_pdftmp.png")
                try:
                    final_img.save(_pdf_png_path, format='PNG')
                    logger.info(f"[PDF] Salvata PNG temporanea per PDF: {_pdf_png_path}")
                except Exception as _e:
                    logger.error(f"[PDF] Errore salvataggio PNG temporanea: {_e}")
            # Verifica immagini finali e retry (max 3 tentativi, solo per formati immagine)
            _img_norm = [_normalize_format(f) for f in image_formats]
            immagini_attese = [f"{self.nome_file}.{ext.lower()}" for ext in ['png','jpg','tif'] if _normalize_format(ext.upper()) in _img_norm]
            mancanti = [img for img in immagini_attese if not os.path.exists(os.path.join(self.output_dir, img))]
            retry_count = 0
            max_retries = 3
            while mancanti and retry_count < max_retries:
                logger.warning(f"[Verifica] Mancano immagini finali: {mancanti}. Retry {retry_count+1}/{max_retries}")
                final_img = rebuild_image(info, tile_dir)
                if final_img is not None:
                    save_image_variants(final_img, self.output_dir, self.nome_file, image_formats, meta=meta)
                mancanti = [img for img in immagini_attese if not os.path.exists(os.path.join(self.output_dir, img))]
                retry_count += 1
            if mancanti:
                logger.error(f"[Verifica] Immagini finali NON generate dopo {max_retries} tentativi: {mancanti}")
                self.immagini_mancanti = mancanti
            else:
                self.immagini_mancanti = []
            shutil.rmtree(tile_dir, ignore_errors=True)
            logger.info(f"[Cleanup] Cartella tiles eliminata: {tile_dir}")
            # Aggiorna metadati manifest con file generati
            if self.manifest_path and os.path.exists(self.manifest_path):
                _nfmts = [_normalize_format(f) for f in image_formats]
                immagini_generate_meta = []
                for _ext, _nfmt in [('png', 'PNG'), ('jpg', 'JPEG'), ('tif', 'TIFF')]:
                    if _nfmt in _nfmts:
                        immagini_generate_meta.append(f"{self.nome_file}.{_ext}")
                estrai_metadati_da_manifest(
                    self.manifest_path,
                    record_prefix="D",
                    record_url=self.ark_url,
                    record_nome_file=self.nome_file,
                    immagini_generate=immagini_generate_meta
                )
            # Richiesta PDF anche per i documenti singoli
            gen_pdf = False
            if pdf_in_formats:
                gen_pdf = True  # PDF già scelto nella maschera formati, nessun popup
            elif hasattr(self, 'force_gen_pdf') and self.force_gen_pdf is not None:
                gen_pdf = bool(self.force_gen_pdf)
            else:
                if hasattr(self, 'ask_pdf_cb') and callable(self.ask_pdf_cb):
                    try:
                        logger.info("[Elaborazione] Invoco callback richiesta PDF per documento singolo")
                        gen_pdf = bool(self.ask_pdf_cb(self.nome_file))
                        self.force_gen_pdf = gen_pdf
                    except Exception as e:
                        logger.error(f"[Elaborazione] Errore callback richiesta PDF: {e}")
                        gen_pdf = False
            if gen_pdf:
                if only_pdf:
                    pdf_path = self._generate_register_pdf(
                        [f"{self.nome_file}_pdftmp.png"], image_dir=temp_pdf_dir)
                elif pdf_in_formats:
                    # PDF + altri formati: usa immagini già in output_dir
                    _pdf_src = []
                    for _ext in ['.tif', '.tiff', '.png', '.jpg', '.jpeg']:
                        _c = self.nome_file + _ext
                        if os.path.exists(os.path.join(self.output_dir, _c)):
                            _pdf_src.append(_c)
                    pdf_path = self._generate_register_pdf(_pdf_src)
                else:
                    pdf_path = self._generate_register_pdf(
                        [os.path.basename(p) for p in immagini_attese
                         if os.path.exists(os.path.join(self.output_dir, p))])
                if pdf_path:
                    logger.info(f"[OK] PDF generato per documento singolo: {pdf_path}")
            if only_pdf and temp_pdf_dir and os.path.exists(temp_pdf_dir):
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)
                logger.info(f"[Cleanup] Cartella temp PDF eliminata: {temp_pdf_dir}")
            logger.info(f"[OK] Documento elaborato: {self.nome_file}")
            return True
        except Exception as e:
            logger.error(f"[Error] Errore elaborazione documento: {e}", exc_info=True)
            return False


    def _process_register(self, tiles_info, metadata):
        """Elabora registro (R/r) in parallelo per canvas."""
        import concurrent.futures
        try:
            logger.info(f"[Elaborazione] _process_register: output_dir={self.output_dir}")
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"[Elaborazione] Cartella output creata/esistente: {self.output_dir}")
            immagini_generate = []
            formats = self.formats if hasattr(self, 'formats') and self.formats else state.get('formats', [])
            if not formats:
                formats = ['PNG', 'JPEG', 'TIFF']
            _norm_formats = [_normalize_format(f) for f in formats]
            pdf_in_formats = 'PDF' in _norm_formats
            image_formats = [f for f in formats if _normalize_format(f) != 'PDF']
            only_pdf = pdf_in_formats and not image_formats
            temp_pdf_dir = os.path.join(self.output_dir, "_tmp_pdf_images") if pdf_in_formats else None
            if temp_pdf_dir:
                os.makedirs(temp_pdf_dir, exist_ok=True)

            from threading import Lock
            immagini_lock = Lock()
            def process_canvas(idx, canvas):
                logger.info(f"[Canvas] Elaborazione {idx}/{len(tiles_info)}")

                # Report start of this canvas to caller (worker -> ProgressDialog)
                try:
                    if hasattr(self, 'progress_cb') and callable(self.progress_cb):
                        try:
                            page_label = canvas.get('label', None)
                            self.progress_cb(idx, len(tiles_info), page_label)
                        except Exception:
                            self.progress_cb(idx, len(tiles_info))
                except Exception:
                    pass

                service_info = canvas['images'][0]['resource'].get('service')
                service_id = service_info[0].get('@id') if isinstance(service_info, list) else service_info.get('@id')
                image_info_url = service_id.rstrip('/') + '/info.json'
                nome_base = f"{self.nome_file}_canvas_{idx}"
                tile_dir = os.path.join(self.output_dir, f"tiles_canvas_{idx}")

                try:
                    info = download_info_json(image_info_url)
                    os.makedirs(tile_dir, exist_ok=True)
                    tiles_ok, tiles_missing = download_tiles(info, tile_dir)
                    if tiles_missing:
                        logger.warning(f"[Elaborazione] Tile mancanti per {nome_base}: {len(tiles_missing)}")
                        for mf in tiles_missing:
                            logger.warning(f"[Elaborazione] Tile mancante: {mf}")
                        if not hasattr(self, 'tiles_missing_all'):
                            self.tiles_missing_all = []
                        self.tiles_missing_all.extend(tiles_missing)
                    final_img = rebuild_image(info, tile_dir)
                    ua = _parse_ua_from_url(self.ark_url)
                    ark = _parse_ark_from_url(self.ark_url)
                    canvas_tail = _last_segment(service_id)
                    page_label = canvas.get('label', None)
                    meta = build_image_metadata(
                        ua=ua,
                        ark=ark,
                        canvas_id=canvas_tail,
                        page_label=page_label,
                        description=self.nome_file,
                        source_url=self.ark_url,
                        atk_version="2.0"
                    )
                    _use_img = final_img if final_img is not None else _make_placeholder_image(
                        service_id, glossario_data=self.glossario_data, lingua=self.lingua,
                        canvas_url=canvas.get('@id') or canvas.get('id'))
                    if image_formats:
                        save_image_variants(_use_img, self.output_dir, nome_base, image_formats, meta=meta)
                    if pdf_in_formats:
                        _pdf_png_path = os.path.join(temp_pdf_dir, f"{nome_base}_pdftmp.png")
                        try:
                            _use_img.save(_pdf_png_path, format='PNG')
                        except Exception as _e:
                            logger.error(f"[PDF] Errore salvataggio PNG canvas {idx}: {_e}")
                    # Elimina la cartella dei tile dopo la ricostruzione
                    shutil.rmtree(tile_dir, ignore_errors=True)
                    logger.info(f"[Cleanup] Cartella tiles eliminata: {tile_dir}")
                except Exception as e:
                    logger.error(f"[Error] Errore canvas {idx}: {e}", exc_info=True)
                    # Genera placeholder per questo canvas e pulisce la cartella tile
                    try:
                        _ph = _make_placeholder_image(service_id, glossario_data=self.glossario_data, lingua=self.lingua,
                        canvas_url=canvas.get('@id') or canvas.get('id'))
                        if image_formats:
                            save_image_variants(_ph, self.output_dir, nome_base, image_formats)
                        if pdf_in_formats:
                            _ph.save(os.path.join(temp_pdf_dir, f"{nome_base}_pdftmp.png"), format='PNG')
                            logger.info(f"[PDF] Placeholder salvato per canvas {idx} fallito")
                    except Exception as _ep:
                        logger.error(f"[Error] Errore salvataggio placeholder canvas {idx}: {_ep}")
                    finally:
                        shutil.rmtree(tile_dir, ignore_errors=True)
                        logger.info(f"[Cleanup] Cartella tiles eliminata (dopo errore): {tile_dir}")

            # Parallelizzazione automatica: usa metà dei core disponibili, minimo 2, massimo 8
            # import os rimosso, già presente in testa al file
            try:
                cpu_count = os.cpu_count() or 4
                max_workers = min(8, max(2, cpu_count // 2))
            except Exception:
                max_workers = 4
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_canvas, idx, canvas) for idx, canvas in enumerate(tiles_info, 1)]
                for f in concurrent.futures.as_completed(futures):
                    pass  # errori già loggati

            # Verifica immagini finali e retry (max 3 tentativi) per tutte le pagine
            _img_norm_r = [_normalize_format(f) for f in image_formats]
            immagini_attese = []
            for idx, canvas in enumerate(tiles_info, 1):
                nome_base = f"{self.nome_file}_canvas_{idx}"
                for ext in ['png','jpg','tif']:
                    if _normalize_format(ext.upper()) in _img_norm_r:
                        immagini_attese.append(f"{nome_base}.{ext}")
            mancanti = [img for img in immagini_attese if not os.path.exists(os.path.join(self.output_dir, img))]
            retry_count = 0
            max_retries = 3
            while mancanti and retry_count < max_retries:
                logger.warning(f"[Verifica] Mancano immagini finali: {mancanti}. Retry {retry_count+1}/{max_retries}")
                # Per ogni pagina mancante, tenta la ricostruzione
                for img in mancanti:
                    # Ricava idx da nome file
                    try:
                        idx_str = img.split('_canvas_')[-1].split('.')[0]
                        idx_canvas = int(idx_str)
                        canvas = tiles_info[idx_canvas-1]
                        service_info = canvas['images'][0]['resource'].get('service')
                        service_id = service_info[0].get('@id') if isinstance(service_info, list) else service_info.get('@id')
                        image_info_url = service_id.rstrip('/') + '/info.json'
                        info = download_info_json(image_info_url)
                        tile_dir = os.path.join(self.output_dir, f"tiles_canvas_{idx_canvas}")
                        final_img = rebuild_image(info, tile_dir)
                        nome_base = f"{self.nome_file}_canvas_{idx_canvas}"
                        meta = build_image_metadata(
                            ua=_parse_ua_from_url(self.ark_url),
                            ark=_parse_ark_from_url(self.ark_url),
                            canvas_id=_last_segment(service_id),
                            page_label=canvas.get('label', None),
                            description=self.nome_file,
                            source_url=self.ark_url,
                            atk_version="2.0"
                        )
                        save_image_variants(final_img, self.output_dir, nome_base, image_formats, meta=meta)
                        # Elimina la cartella dei tile dopo la ricostruzione anche nei retry
                        shutil.rmtree(tile_dir, ignore_errors=True)
                        logger.info(f"[Cleanup] Cartella tiles eliminata (retry): {tile_dir}")
                    except Exception as e:
                        logger.error(f"[Retry] Errore retry immagine {img}: {e}")
                mancanti = [img for img in immagini_attese if not os.path.exists(os.path.join(self.output_dir, img))]
                retry_count += 1
            if mancanti:
                logger.error(f"[Verifica] Immagini finali NON generate dopo {max_retries} tentativi: {mancanti}")
                self.immagini_mancanti = mancanti
            else:
                self.immagini_mancanti = []

            # Popola immagini_generate con tutti i file effettivamente prodotti
            # (nota: process_canvas non aggiunge a immagini_generate per thread-safety)
            for _img in immagini_attese:
                if os.path.exists(os.path.join(self.output_dir, _img)):
                    immagini_generate.append(_img)

            logger.info(f"[Elaborazione] File generati: {immagini_generate}")
            # --- RICHIESTA PDF DOPO ULTIMO CANVAS ---
            gen_pdf = False
            if pdf_in_formats:
                gen_pdf = True  # PDF già scelto nella maschera formati, nessun popup
            elif hasattr(self, 'force_gen_pdf') and self.force_gen_pdf is not None:
                gen_pdf = bool(self.force_gen_pdf)
            else:
                if hasattr(self, 'ask_pdf_cb') and callable(self.ask_pdf_cb):
                    try:
                        logger.info("[Elaborazione] Invoco callback richiesta PDF dopo ultimo canvas")
                        gen_pdf = bool(self.ask_pdf_cb(self.nome_file))
                        self.force_gen_pdf = gen_pdf
                    except Exception as e:
                        logger.error(f"[Elaborazione] Errore callback richiesta PDF: {e}")
                        gen_pdf = False

            # Genera PDF
            if gen_pdf:
                if pdf_in_formats:
                    if only_pdf:
                        # Usa immagini temporanee da temp_pdf_dir (ordinate per idx)
                        _pdf_imgs = [
                            f"{self.nome_file}_canvas_{i}_pdftmp.png"
                            for i in range(1, len(tiles_info) + 1)
                            if os.path.exists(os.path.join(temp_pdf_dir,
                               f"{self.nome_file}_canvas_{i}_pdftmp.png"))
                        ]
                        pdf_path = self._generate_register_pdf(_pdf_imgs, image_dir=temp_pdf_dir)
                    else:
                        # PDF + altri formati: usa PNG temporanee da temp_pdf_dir (ordinate per idx)
                        _pdf_imgs = [
                            f"{self.nome_file}_canvas_{i}_pdftmp.png"
                            for i in range(1, len(tiles_info) + 1)
                            if os.path.exists(os.path.join(temp_pdf_dir,
                               f"{self.nome_file}_canvas_{i}_pdftmp.png"))
                        ]
                        pdf_path = self._generate_register_pdf(_pdf_imgs, image_dir=temp_pdf_dir)
                    if pdf_path:
                        immagini_generate.append(os.path.basename(pdf_path))
                else:
                    mancanti_pdf = [img for img in immagini_attese if not os.path.exists(os.path.join(self.output_dir, img))]
                    if mancanti_pdf:
                        try:
                            from user_prompts import ask_generate_pdf_missing_images
                            parent = getattr(self, 'parent', None) if hasattr(self, 'parent') else None
                            glossario = getattr(self, 'glossario_data', None) if hasattr(self, 'glossario_data') else None
                            lingua = getattr(self, 'lingua', 'IT') if hasattr(self, 'lingua') else 'IT'
                            dark_mode = getattr(self, 'dark_mode', False) if hasattr(self, 'dark_mode') else False
                            conferma = ask_generate_pdf_missing_images(len(mancanti_pdf), glossario, lingua, parent, dark_mode)
                        except Exception as e:
                            logger.error(f"[PDF] Errore popup immagini mancanti: {e}")
                            conferma = False
                        if conferma:
                            pdf_path = self._generate_register_pdf([img for img in immagini_attese if os.path.exists(os.path.join(self.output_dir, img))])
                            if pdf_path:
                                immagini_generate.append(os.path.basename(pdf_path))
                        else:
                            logger.error(f"[PDF] PDF NON generato: immagini mancanti: {mancanti_pdf}")
                    else:
                        pdf_path = self._generate_register_pdf(immagini_attese)
                        if pdf_path:
                            immagini_generate.append(os.path.basename(pdf_path))
            if temp_pdf_dir and os.path.exists(temp_pdf_dir):
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)
                logger.info(f"[Cleanup] Cartella temp PDF eliminata: {temp_pdf_dir}")

            # Aggiorna metadati finali
            if self.manifest_path and os.path.exists(self.manifest_path):
                estrai_metadati_da_manifest(
                    self.manifest_path,
                    record_prefix="R",
                    record_url=self.ark_url,
                    record_nome_file=self.nome_file,
                    immagini_generate=immagini_generate
                )

            logger.info(f"[OK] Registro elaborato: {self.nome_file}")
            return True
        except Exception as e:
            logger.error(f"[Error] Errore elaborazione registro: {e}", exc_info=True)
            return False

    def _get_document_canvas_id(self):
        """Ricava canvas ID per documento (D/d)."""
        if "an_ua" in self.ark_url:
            # Documento singolo UA: usa l'ultimo segmento
            logger.info("[Canvas] Tipo: UA - estrazione diretta da URL")
            canvas_id = extract_canvas_id_from_url(self.ark_url)
            logger.info(f"[Canvas] Risultato UA: {canvas_id}")
            return canvas_id
        elif "an_ud" in self.ark_url:
            # Documento UD: intercetta con Playwright
            logger.info("[Canvas] Tipo: UD - estrazione con Playwright")
            try:
                canvas_id = extract_ud_canvas_id_from_infojson_xhr(self.ark_url)
                logger.info(f"[Canvas] Risultato UD: {canvas_id}")
                return canvas_id
            except Exception as e:
                logger.error(f"[Error] Eccezione in extract_ud_canvas_id_from_infojson_xhr: {e}", exc_info=True)
                return None
        return None

    def _generate_register_pdf(self, immagini_generate, image_dir=None):
        """Genera PDF multipagina da immagini registro.
        image_dir: cartella da cui cercare le immagini (default: self.output_dir)."""
        if image_dir is None:
            image_dir = self.output_dir
        try:
            ordered_paths = []
            for img_name in immagini_generate:
                img_path = os.path.join(image_dir, img_name)
                if os.path.exists(img_path):
                    ordered_paths.append(img_path)

            if not ordered_paths:
                logger.warning("[Warning] Nessuna immagine per PDF")
                return None

            titolo_pulito = re.sub(r'[\\/*?:"<>|]', "", self.nome_file).replace(" ", "_")
            pdf_filename = f"{titolo_pulito}.pdf"
            pdf_full_path = os.path.join(self.output_dir, pdf_filename)

            # Filtra le immagini scegliendo una sola variante per pagina
            # Priorità qualitativa: TIFF -> PNG -> JPEG
            try:
                by_base = {}
                for p in ordered_paths:
                    base = os.path.splitext(os.path.basename(p))[0]
                    ext = os.path.splitext(p)[1].lower()
                    if base not in by_base:
                        by_base[base] = {}
                    by_base[base][ext] = p

                preferred_order = ['.tif', '.tiff', '.png', '.jpg', '.jpeg']
                selected_paths = []
                def _canvas_sort_key(name):
                    m = re.search(r'_canvas_(\d+)', name)
                    return int(m.group(1)) if m else 0
                for base in sorted(by_base.keys(), key=_canvas_sort_key):
                    exts_map = by_base[base]
                    chosen = None
                    for pe in preferred_order:
                        if pe in exts_map:
                            chosen = exts_map[pe]
                            break
                    if chosen:
                        selected_paths.append(chosen)

                if not selected_paths:
                    logger.warning("[Warning] Nessuna immagine selezionata dopo filtro priorità formati")
                    return None

                logger.info(f"[PDF] Immagini selezionate per PDF: {len(selected_paths)} pagine (priorità TIFF>PNG>JPEG)")
                pdf_path = create_pdf_from_images(selected_paths, pdf_full_path, resolution_dpi=400)
            except Exception as e:
                logger.error(f"[Error] Errore nel filtrare le immagini per PDF: {e}", exc_info=True)
                return None
            
            if pdf_path:
                # Arricchisci metadati PDF
                ua_doc = _parse_ua_from_url(self.ark_url)
                ark_doc = _parse_ark_from_url(self.ark_url)
                enrich_pdf_metadata(
                    pdf_path=pdf_path,
                    title=self.nome_file,
                    subject=self.nome_file,
                    ua=ua_doc,
                    ark=ark_doc
                )
                logger.info(f"[OK] PDF generato: {pdf_path}")
                return pdf_path

        except Exception as e:
            logger.error(f"[Error] Errore generazione PDF: {e}")

        return None


def esegui_elaborazione(state, glossario_data=None, lingua="IT", records=None, formats=None, parent=None):
    """
    Orchestratore principale per GUI/main: elabora i record caricati.
    Usa records e formats passati o quelli nello stato globale.
    Wrapper che adatta la classe Elaborazione alle interfacce v1.4.1.
    Ora accetta anche un parent opzionale per ProgressDialog.
    """
    logger.info(f"[STATO] output_folder: {output_folder}")
    logger.info(f"[STATO] output_folders_doc: {output_folders_doc}")
    logger.info(f"[STATO] output_folders_reg: {output_folders_reg}")
    logger.info(f"[STATO] records: {[{'modalita': r.get('modalita'), 'nome_file': r.get('nome_file'), 'output': r.get('output')} for r in records]}")
    # parent ora è un argomento esplicito

    if records is None:
        records = state["records"]
    if formats is None:
        formats = state["formats"]
    output_folder = state["output_folder"]
    output_folders_doc = state.get("output_folders_doc", [])
    output_folders_reg = state.get("output_folders_reg", [])

    if not records:
        raise RuntimeError("Nessun record caricato")
    if not formats:
        raise RuntimeError("Nessun formato selezionato")
    if not output_folder and not output_folders_doc and not output_folders_reg:
        raise RuntimeError("Nessuna cartella selezionata")

    risultati = []

    # Prova a mostrare un dialog di progresso se disponibile (PySide6)
    progress = None
    qcore = None
    # Crea ProgressDialog solo se ci sono record da elaborare e solo in modalità Qt (con parent)
    if records and parent is not None:
        try:
            from src.user_prompts import ProgressDialog
            from PySide6.QtCore import QCoreApplication
            progress = ProgressDialog(glossario_data, lingua, total=len(records), parent=parent)
            progress.show()
            qcore = QCoreApplication
            # Forza subito il refresh della GUI per evitare dialog bianco
            if qcore:
                qcore.processEvents()
        except Exception:
            progress = None
            qcore = None
    else:
        progress = None
        qcore = None

    doc_counter = 0
    reg_counter = 0
    n_doc = sum(1 for r in records if str(r.get("modalita", "")).strip().upper() == "D")
    n_reg = sum(1 for r in records if str(r.get("modalita", "")).strip().upper() == "R")
    if output_folders_doc and len(output_folders_doc) not in (1, n_doc):
        logger.warning(f"[Output] Numero cartelle documenti ({len(output_folders_doc)}) diverso dal numero di documenti ({n_doc})")
    if output_folders_reg and len(output_folders_reg) not in (1, n_reg):
        logger.warning(f"[Output] Numero cartelle registri ({len(output_folders_reg)}) diverso dal numero di registri ({n_reg})")
    for idx, record in enumerate(records):
        try:
            # Ignora sempre il campo 'output' già presente nei record: la cartella viene decisa qui
            modalita = str(record.get("modalita", "")).strip().upper()
            url = record.get("url")
            nome_file = record.get("nome_file", "documento")

            # Seleziona cartella di output robusta
            if modalita == "D":
                if output_folders_doc:
                    if len(output_folders_doc) == 1:
                        out_dir = output_folders_doc[0]
                    elif doc_counter < len(output_folders_doc):
                        out_dir = output_folders_doc[doc_counter]
                    else:
                        out_dir = output_folders_doc[-1]
                    doc_counter += 1
                else:
                    out_dir = output_folder
            elif modalita == "R":
                if output_folders_reg:
                    if len(output_folders_reg) == 1:
                        out_dir = output_folders_reg[0]
                    elif reg_counter < len(output_folders_reg):
                        out_dir = output_folders_reg[reg_counter]
                    else:
                        out_dir = output_folders_reg[-1]
                    reg_counter += 1
                else:
                    out_dir = output_folder
            else:
                raise ValueError(f"Modalità non riconosciuta: {modalita}")

            # Forza la cartella di output anche nel record (per compatibilità, ma non usata per la logica)
            record["output"] = out_dir

            logger.info(f"[Output] Record {idx+1}/{len(records)} tipo={modalita} nome={nome_file} -> cartella: {out_dir}")
            # ...existing code...
            # Esegui elaborazione con classe Elaborazione
            elab = Elaborazione(modalita.lower(), url, out_dir, glossario_data, lingua)
            elab.set_nome_file(nome_file)
            success = elab.run(formats=formats)

            # Aggiorna dialog di progresso (se presente)
            try:
                if progress:
                    progress.update(current=idx+1, name=nome_file)
                    # Forza il refresh della GUI
                    if qcore:
                        try:
                            qcore.processEvents()
                        except Exception:
                            pass
                    if getattr(progress, 'cancelled', False):
                        logger.info("[Progress] Elaborazione annullata dall'utente")
                        risultati.append({
                            "file": nome_file,
                            "modalita": modalita,
                            "output": out_dir,
                            "status": "CANCELLED"
                        })
                        break
            except Exception:
                pass

            # Dettaglio tile mancanti
            tiles_missing = []
            if hasattr(elab, 'tiles_missing') and elab.tiles_missing:
                tiles_missing = elab.tiles_missing
            if hasattr(elab, 'tiles_missing_all') and elab.tiles_missing_all:
                tiles_missing = elab.tiles_missing_all

            if success and not tiles_missing:
                risultati.append({
                    "file": nome_file,
                    "modalita": modalita,
                    "output": out_dir,
                    "formati": formats,
                    "status": "SUCCESS"
                })
            elif success and tiles_missing:
                risultati.append({
                    "file": nome_file,
                    "modalita": modalita,
                    "output": out_dir,
                    "formati": formats,
                    "status": "INCOMPLETE",
                    "tiles_missing": tiles_missing
                })
            else:
                risultati.append({
                    "file": nome_file,
                    "modalita": modalita,
                    "output": out_dir,
                    "status": "FAILED",
                    "tiles_missing": tiles_missing if tiles_missing else None
                })

        except Exception as e:
            logger.error(f"[Error] Errore elaborazione record {nome_file}: {e}", exc_info=True)
            risultati.append({
                "file": record.get("nome_file", "sconosciuto"),
                "modalita": modalita,
                "errore": str(e),
                "status": "ERROR"
            })

    # Chiudi la ProgressDialog prima di restituire i risultati
    if progress:
        try:
            progress.close()
        except Exception:
            pass

    logger.info("Operazione completata")
    return risultati
