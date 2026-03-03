#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys
import subprocess
import shutil
import zipfile
from urllib import request, error
from urllib.parse import urlsplit
from html.parser import HTMLParser
from typing import Optional, List

DEST_FOLDER = os.path.join(os.path.expanduser("~"), "Pictures", "SteamAvatars")
USER_AGENT = "Mozilla/5.0 (compatible; SteamAvatarDownloader/1.0)"

REALESRGAN_URLS = {
    "darwin": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.2.5.0/realesrgan-ncnn-vulkan-20220424-macos.zip"
    ),
    "win32": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
    ),
}

USE_AI: bool = False
REALESRGAN_BIN: Optional[str] = None


def choose_language() -> str:
    ans = input("parliamo in Italiano? do you want to speak English? (it/en): ").strip().lower()
    return "it" if ans.startswith("it") else "en"


LANG = choose_language()

T = {
    "it": {
        "header": "SteamAvatarDownloader — versione compatta + Real-ESRGAN",
        "examples_title": "Esempi validi:",
        "examples": [
            "  iltuosteamid   (vanity id)",
            "  xxxxxxx00000000   (steamID64 — sostituisci x con le cifre)",
            "  https://steamcommunity.com/id/iltuosteamid",
            "  https://steamcommunity.com/profiles/xxxxxxx00000000",
        ],
        "saving": f"Avatar verrà salvato in: {DEST_FOLDER}",
        "prompt_profile": "Inserisci profilo (vanity, steamID64 o URL): ",
        "loading_profile": "Carico pagina profilo...",
        "no_candidates": "Nessun avatar trovato nel profilo.",
        "avatar_selected": "Avatar selezionato:",
        "downloaded": "Avatar salvato come:",
        "ask_again": "Scaricare un altro avatar? (Y/N): ",
        "goodbye": "Fine. Ciao!",
        "error_fetch": "Errore:",
        "xml_found": "Avatar trovato tramite XML:",
        "retry_other": "Vuoi provare con un altro profilo? (Y/N): ",
        "input_empty": "Input vuoto — riprova.",
        "ask_use_ai": "Vuoi usare l’upscaling AI con Real-ESRGAN? (Y/N): ",
        "esr_ai_disabled": "Upscaling AI disattivato; userò solo l’avatar originale.",
        "esr_found": "Real-ESRGAN trovato:",
        "esr_not_found_path": "Real-ESRGAN non trovato nel sistema.",
        "ask_auto_install": "Vuoi installare automaticamente Real-ESRGAN (se supportato dal sistema)? (Y/N): ",
        "esr_auto_install_start": "Avvio installazione automatica di Real-ESRGAN...",
        "esr_auto_install_ok": "Installazione Real-ESRGAN completata:",
        "esr_auto_install_fail": "Installazione Real-ESRGAN fallita:",
        "esr_auto_install_unsupported": "Installazione automatica non supportata su questo sistema. Installa Real-ESRGAN manualmente.",
        "esr_not_found_runtime": "Real-ESRGAN non disponibile al runtime; salto l’upscaling.",
        "esr_upscale_start": "Eseguo upscaling 4x con Real-ESRGAN...",
        "esr_upscale_ok": "Upscaling AI completato. File finale:",
        "esr_upscale_fail": "Upscaling AI fallito, lascio il file originale. Dettagli:",
    },
    "en": {
        "header": "SteamAvatarDownloader — compact version + Real-ESRGAN",
        "examples_title": "Valid examples:",
        "examples": [
            "  yoursteamid   (vanity id)",
            "  xxxxxxx00000000   (steamID64 — replace x with digits)",
            "  https://steamcommunity.com/id/yoursteamid",
            "  https://steamcommunity.com/profiles/xxxxxxx00000000",
        ],
        "saving": f"Avatar will be saved to: {DEST_FOLDER}",
        "prompt_profile": "Enter profile (vanity, steamID64 or URL): ",
        "loading_profile": "Loading profile page...",
        "no_candidates": "No avatar found on profile.",
        "avatar_selected": "Selected avatar:",
        "downloaded": "Avatar saved as:",
        "ask_again": "Download another avatar? (Y/N): ",
        "goodbye": "Done. Bye!",
        "error_fetch": "Error:",
        "xml_found": "Avatar found via XML:",
        "retry_other": "Try another profile? (Y/N): ",
        "input_empty": "Empty input — retry.",
        "ask_use_ai": "Use AI upscaling with Real-ESRGAN? (Y/N): ",
        "esr_ai_disabled": "AI upscaling disabled; using original avatar.",
        "esr_found": "Real-ESRGAN found:",
        "esr_not_found_path": "Real-ESRGAN not found on system.",
        "ask_auto_install": "Try automatic Real-ESRGAN install (if supported)? (Y/N): ",
        "esr_auto_install_start": "Starting automatic Real-ESRGAN installation...",
        "esr_auto_install_ok": "Real-ESRGAN installation completed:",
        "esr_auto_install_fail": "Real-ESRGAN installation failed:",
        "esr_auto_install_unsupported": "Automatic installation not supported on this OS. Please install Real-ESRGAN manually.",
        "esr_not_found_runtime": "Real-ESRGAN not available at runtime; skipping upscaling.",
        "esr_upscale_start": "Running 4x upscaling with Real-ESRGAN...",
        "esr_upscale_ok": "AI upscaling done. Final file:",
        "esr_upscale_fail": "AI upscaling failed, keeping original file. Details:",
    },
}[LANG]


def yes(s: str) -> bool:
    return s.strip().lower() in ("y", "yes", "s", "si")


def sanitize_filename(name: str, max_len: int = 200) -> str:
    cleaned = []
    for c in name:
        if c.isalnum() or c in " -_.":
            cleaned.append(c)
        else:
            cleaned.append("_")
    res = "".join(cleaned).strip()
    if not res:
        res = "avatar"
    return res[:max_len]


def normalize_input_to_url(raw: str) -> str:
    r = raw.strip()
    if not r:
        raise ValueError("empty")
    if r.startswith(("http://", "https://", "www.")):
        if r.startswith("www."):
            r = "https://" + r
        return r
    if r.isdigit():
        return f"https://steamcommunity.com/profiles/{r}"
    return f"https://steamcommunity.com/id/{r}"


def download_file(url: str, folder: str, filename: str) -> str:
    """Scarica il file in `folder` con nome base `filename`.
    Se esiste già, aggiunge _1, _2, ... prima dell'estensione.
    """
    os.makedirs(folder, exist_ok=True)
    base, ext = os.path.splitext(filename)
    if not ext:
        ext = ".jpg"
    candidate = os.path.join(folder, base + ext)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{base}_{counter}{ext}")
        counter += 1
    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    with request.urlopen(req, timeout=30) as resp, open(candidate, "wb") as out:
        out.write(resp.read())
    return candidate


class SimpleAvatarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imgs: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        d = dict(attrs)
        src = d.get("src")
        if src:
            self.imgs.append(src)


class PersonaNameParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.record = False
        self.parts: List[str] = []
        self.found = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "span":
            return
        for k, v in attrs:
            if k.lower() == "class" and v and "actual_persona_name" in v:
                self.record = True
                self.found = True
                break

    def handle_endtag(self, tag):
        if tag.lower() == "span" and self.record:
            self.record = False

    def handle_data(self, data):
        if self.record and data and not data.isspace():
            self.parts.append(data.strip())

    @property
    def name(self) -> Optional[str]:
        if not self.found:
            return None
        return " ".join(self.parts).strip() if self.parts else None


def avatar_from_profile_xml(profile_url: str) -> Optional[str]:
    try:
        xml_url = profile_url.rstrip("/") + "/?xml=1"
        req = request.Request(xml_url, headers={"User-Agent": USER_AGENT})
        with request.urlopen(req, timeout=10) as resp:
            txt = resp.read().decode("utf-8", errors="replace")
        start = txt.find("<avatarFull>")
        if start == -1:
            return None
        end = txt.find("</avatarFull>", start)
        if end == -1:
            return None
        url = txt[start + len("<avatarFull>"):end].strip()
        if url.startswith("<![CDATA[") and url.endswith("]]>"):
            url = url[len("<![CDATA["):-len("]]>")].strip()
        return url or None
    except Exception:
        return None


def find_realesrgan_binary() -> Optional[str]:
    names = ["realesrgan-ncnn-vulkan", "realesrgan"]
    if sys.platform.startswith("win"):
        names = [n + ".exe" for n in names]
    for name in names:
        p = shutil.which(name)
        if p:
            return p
    local_dir = os.path.expanduser("~/.local/realesrgan-ncnn-vulkan")
    if os.path.isdir(local_dir):
        for root, dirs, files in os.walk(local_dir):
            for name in names:
                if name in files:
                    return os.path.join(root, name)
    return None


def auto_install_realesrgan() -> Optional[str]:
    plat = sys.platform
    url = None
    if plat == "darwin":
        url = REALESRGAN_URLS.get("darwin")
    elif plat.startswith("win"):
        url = REALESRGAN_URLS.get("win32")
    if not url:
        print(T["esr_auto_install_unsupported"])
        return None
    install_dir = os.path.expanduser("~/.local/realesrgan-ncnn-vulkan")
    os.makedirs(install_dir, exist_ok=True)
    zip_path = os.path.join(install_dir, "realesrgan.zip")
    try:
        print(T["esr_auto_install_start"])
        req = request.Request(url, headers={"User-Agent": USER_AGENT})
        with request.urlopen(req, timeout=120) as resp, open(zip_path, "wb") as out:
            out.write(resp.read())
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(install_dir)
    except Exception as e:
        print(T["esr_auto_install_fail"], repr(e))
        return None
    finally:
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass
    return find_realesrgan_binary()


def init_realesrgan() -> None:
    global USE_AI, REALESRGAN_BIN
    ans = input(T["ask_use_ai"])
    if not yes(ans):
        USE_AI = False
        print(T["esr_ai_disabled"])
        return
    b = find_realesrgan_binary()
    if b:
        USE_AI = True
        REALESRGAN_BIN = b
        print(T["esr_found"], b)
        return
    print(T["esr_not_found_path"])
    ans2 = input(T["ask_auto_install"])
    if yes(ans2):
        b = auto_install_realesrgan()
        if b:
            USE_AI = True
            REALESRGAN_BIN = b
            print(T["esr_auto_install_ok"], b)
            return
    USE_AI = False


def upscale_with_realesrgan_inplace(path: str) -> Optional[str]:
    if not USE_AI:
        return None
    bin_path = REALESRGAN_BIN or find_realesrgan_binary()
    if not bin_path:
        print(T["esr_not_found_runtime"])
        return None
    base, _ = os.path.splitext(path)
    out_path = base + "_x4.png"
    cmd = [
        bin_path,
        "-i",
        path,
        "-o",
        out_path,
        "-n",
        "realesrgan-x4plus",
        "-s",
        "4",
    ]
    bin_dir = os.path.dirname(bin_path) or None
    print(T["esr_upscale_start"])
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=bin_dir,
        )
        if proc.returncode != 0:
            print(T["esr_upscale_fail"], proc.stderr.strip() or proc.stdout.strip())
            if os.path.exists(out_path):
                os.remove(out_path)
            return None
    except Exception as e:
        print(T["esr_upscale_fail"], repr(e))
        if os.path.exists(out_path):
            os.remove(out_path)
        return None
    if not os.path.exists(out_path):
        print(T["esr_upscale_fail"], "output file non trovato.")
        return None
    try:
        os.replace(out_path, path)
        print(T["esr_upscale_ok"], path)
        return path
    except Exception as e:
        print(T["esr_upscale_fail"], repr(e))
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
        except Exception:
            pass
        return None


def main() -> None:
    print(T["header"])
    print(T["examples_title"])
    for ex in T["examples"]:
        print(ex)
    print()
    print(T["saving"])
    print()
    init_realesrgan()
    print()
    while True:
        raw = input(T["prompt_profile"]).strip()
        if not raw:
            print(T["input_empty"])
            continue
        try:
            profile_url = normalize_input_to_url(raw)
        except ValueError:
            print(T["input_empty"])
            continue
        try:
            print(T["loading_profile"])
            req = request.Request(profile_url, headers={"User-Agent": USER_AGENT})
            with request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(T["error_fetch"], e)
            if yes(input(T["retry_other"])):
                continue
            break
        xml_avatar = avatar_from_profile_xml(profile_url)
        best = None
        if xml_avatar:
            print(T["xml_found"], xml_avatar)
            best = xml_avatar
        if not best:
            parser = SimpleAvatarParser()
            parser.feed(html)
            best = parser.imgs[0] if parser.imgs else None
        if not best:
            print(T["no_candidates"])
            if yes(input(T["retry_other"])):
                continue
            break
        print(T["avatar_selected"], best)
        steam_name = None
        try:
            name_parser = PersonaNameParser()
            name_parser.feed(html)
            steam_name = name_parser.name
        except Exception:
            steam_name = None
        path_parts = [p for p in urlsplit(profile_url).path.split("/") if p]
        profile_id = path_parts[-1] if path_parts else raw
        base_name = sanitize_filename(steam_name or profile_id)
        ext = os.path.splitext(urlsplit(best).path)[1] or ".jpg"
        filename = base_name + ext
        try:
            saved = download_file(best, DEST_FOLDER, filename)
            print(T["downloaded"], saved)
        except Exception as e:
            print(T["error_fetch"], e)
            saved = None
        if saved:
            upscale_with_realesrgan_inplace(saved)
        if not yes(input(T["ask_again"])):
            print(T["goodbye"])
            break


if __name__ == "__main__":
    main()
