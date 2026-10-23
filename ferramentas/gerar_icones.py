#!/usr/bin/env python3
"""GIN - gera os icones PNG do app (globo azul sobre fundo escuro) sem dependencias.
Uso: python3 ferramentas/gerar_icones.py"""
import math
import struct
import zlib
from pathlib import Path

FUNDO, AZUL = (11, 18, 32), (79, 156, 249)
DESTINO = Path(__file__).resolve().parent.parent / "app"


def desenhar(n, maskable):
    canto = 0 if maskable else n * 0.22
    cx = cy = n / 2
    raio = n * (0.30 if maskable else 0.34)
    esp = n * 0.03
    linhas = []
    for y in range(n):
        linha = bytearray([0])
        py = y + 0.5
        for x in range(n):
            px = x + 0.5
            if canto:
                dx = max(canto - px, 0, px - (n - canto))
                dy = max(canto - py, 0, py - (n - canto))
                if dx * dx + dy * dy > canto * canto:
                    linha += bytes((0, 0, 0, 0))
                    continue
            cor = FUNDO
            d = math.hypot(px - cx, py - cy)
            if abs(d - raio) <= esp:
                cor = AZUL
            elif d < raio:
                meridiano = abs(math.hypot((px - cx) / 0.45, py - cy) - raio) <= esp * 1.6
                equador = abs(py - cy) <= esp * 0.8
                paralelos = abs(abs(py - cy) - raio * 0.5) <= esp * 0.7
                eixo = abs(px - cx) <= esp * 0.8
                if meridiano or equador or paralelos or eixo:
                    cor = AZUL
            linha += bytes((*cor, 255))
        linhas.append(bytes(linha))
    return b"".join(linhas)


def gravar_png(caminho, n, bruto):
    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
           + bloco(b"IDAT", zlib.compress(bruto, 9)) + bloco(b"IEND", b""))
    caminho.write_bytes(png)
    print(f"{caminho.name}: {n}x{n}, {len(png)} bytes")


for nome, n, maskable in [("icone-192.png", 192, False), ("icone-512.png", 512, False), ("icone-maskable-512.png", 512, True)]:
    gravar_png(DESTINO / nome, n, desenhar(n, maskable))
