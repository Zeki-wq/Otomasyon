#!/usr/bin/env python3
"""
Oto Yedek Parça Otomasyonu - Ana Başlatıcı (Main Launcher)
Çapraz platform (Windows, Debian/Ubuntu, Fedora/RHEL) başlatıcı betiği.
"""

import sys
from pathlib import Path

# Proje kök dizinini Python yoluna ekle
KOK_DIZIN = Path(__file__).resolve().parent
if str(KOK_DIZIN) not in sys.path:
    sys.path.insert(0, str(KOK_DIZIN))

from app.main import main

if __name__ == "__main__":
    main()
