#!/usr/bin/env python3
"""
Gera o tileset "Tokyo" (bairro japones) para o pokeemerald-expansion.  (versao 2)

Novidade da v2: alem das pecas desenhadas pelo script, acrescenta no FIM do
tileset os predios das imagens que estiverem na pasta "extras" (ao lado do script):
    extras/predio_vermelho.png
    extras/predio_azul.png
As pecas antigas continuam nas mesmas posicoes, entao o mapa que voce ja pintou nao muda.

Antes de rodar: o tileset SECUNDARIO "Tokyo" ja deve existir (criado no Porymap).

Uso (na raiz do projeto, no Codespaces):
    pip install pillow
    python3 make_tokyo_tileset_v2.py data/tilesets/secondary/tokyo

Opcoes:
    --attr-bytes=2 ou --attr-bytes=4   (so se o script nao conseguir detectar sozinho)
    --extras=caminho/da/pasta          (se as imagens estiverem em outro lugar)

ATENCAO: o script reescreve tiles.png, metatiles.bin, metatile_attributes.bin e as
paletas do tileset. Se voce editou comportamentos/atributos desse tileset no Porymap,
eles serao sobrescritos.
"""
import os
import shutil
import sys

from PIL import Image

# ---------------------------------------------------------------- paleta base (16 cores)
PAL = [
    (255, 0, 255),    # 0  transparente
    (32, 32, 40),     # 1  contorno
    (248, 248, 248),  # 2  branco
    (200, 200, 208),  # 3  concreto claro
    (112, 112, 124),  # 4  asfalto
    (152, 152, 164),  # 5  concreto escuro / emendas
    (64, 104, 184),   # 6  telhado azul
    (40, 64, 128),    # 7  telhado azul escuro
    (240, 224, 184),  # 8  parede creme
    (136, 88, 48),    # 9  madeira
    (216, 56, 56),    # 10 vermelho
    (96, 176, 88),    # 11 grama
    (48, 120, 64),    # 12 folha escura
    (248, 176, 200),  # 13 sakura
    (224, 120, 160),  # 14 sakura escura
    (152, 208, 240),  # 15 vidro
]
T, K, W, C, A, D, RB, RD, WL, BR, RED, GR, LG, SK, SD, GL = range(16)

PAL_SLOT = 6          # secondary tilesets usam as paletas 6 a 12
TILE_BASE = 512       # tiles do secundario comecam no indice 512
GRID_W = 8            # metatiles por linha no seletor do Porymap
CONCRETE = PAL[C]

# Imagens extras (NAO mude a ordem, so acrescente no fim).
# (nome, arquivo, slot de paleta: de 7 a 12)
EXTRAS = [
    ("predio_vermelho", "predio_vermelho.png", 7),
    ("predio_azul", "predio_azul.png", 8),
]


# ---------------------------------------------------------------- canvas simples
class Canvas:
    def __init__(self, w, h, bg=C):
        self.w, self.h = w, h
        self.p = [[bg] * w for _ in range(h)]

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, c)

    def frame(self, x, y, w, h, c):
        self.rect(x, y, w, 1, c)
        self.rect(x, y + h - 1, w, 1, c)
        self.rect(x, y, 1, h, c)
        self.rect(x + w - 1, y, 1, h, c)

    def box(self, x, y, w, h, fill, line=K):
        self.rect(x, y, w, h, fill)
        self.frame(x, y, w, h, line)


# ---------------------------------------------------------------- pecas 1x1
def sidewalk():
    c = Canvas(16, 16, C)
    c.rect(0, 7, 16, 1, D)
    c.rect(0, 15, 16, 1, D)
    for x in (7, 15):
        c.rect(x, 0, 1, 7, D)
    for x in (3, 11):
        c.rect(x, 8, 1, 7, D)
    return c


def grass():
    c = Canvas(16, 16, GR)
    for x, y in [(2, 3), (9, 2), (13, 6), (5, 9), (11, 12), (1, 14), (7, 6)]:
        c.px(x, y, LG)
    return c


def road():
    c = Canvas(16, 16, A)
    for x, y in [(3, 4), (11, 9), (6, 13), (13, 2)]:
        c.px(x, y, D)
    return c


def road_dash():
    c = road()
    c.rect(4, 7, 8, 2, W)
    return c


def crosswalk():
    c = road()
    for y in (1, 6, 11):
        c.rect(0, y, 16, 3, W)
    return c


def curb():
    c = Canvas(16, 16, C)
    for x in (7, 15):
        c.rect(x, 0, 1, 8, D)
    c.rect(0, 8, 16, 1, D)
    c.rect(0, 9, 16, 1, K)
    c.rect(0, 10, 16, 6, A)
    c.px(4, 13, D)
    c.px(12, 12, D)
    return c


def muro():
    c = Canvas(16, 16, C)
    c.rect(0, 2, 16, 12, WL)
    c.rect(0, 2, 16, 2, D)
    c.rect(0, 1, 16, 1, K)
    c.rect(0, 13, 16, 1, K)
    c.rect(7, 4, 1, 5, D)
    c.rect(3, 9, 1, 4, D)
    c.rect(11, 9, 1, 4, D)
    c.rect(0, 14, 16, 2, D)
    return c


def hedge():
    c = Canvas(16, 16, C)
    c.rect(0, 3, 16, 11, LG)
    c.rect(0, 2, 16, 1, K)
    c.rect(0, 14, 16, 1, K)
    for x, y in [(2, 5), (6, 8), (10, 4), (13, 9), (4, 11), (9, 11)]:
        c.px(x, y, GR)
        c.px(x + 1, y, GR)
    return c


def lamp():
    c = Canvas(16, 16, C)
    c.rect(7, 4, 2, 11, A)
    c.rect(5, 13, 6, 2, A)
    c.rect(4, 1, 8, 3, K)
    c.rect(5, 2, 6, 1, GL)
    return c


def sign():
    c = Canvas(16, 16, C)
    c.rect(7, 7, 2, 8, A)
    c.box(3, 1, 10, 7, W)
    c.rect(6, 3, 4, 3, RED)
    return c


def vending():
    c = Canvas(16, 16, C)
    c.box(3, 1, 10, 14, RED)
    c.box(5, 3, 6, 6, GL)
    c.rect(5, 11, 6, 2, K)
    c.px(11, 10, W)
    return c


# ---------------------------------------------------------------- pecas grandes
def roof(c, x, y, w, h, main, dark):
    c.rect(x, y, w, h, main)
    for yy in range(y + 3, y + h - 1, 4):
        c.rect(x, yy, w, 1, dark)
    for i, yy in enumerate(range(y, y + h - 1, 4)):
        start = x + (2 if i % 2 else 6)
        for xx in range(start, x + w, 8):
            c.rect(xx, yy, 1, 3, dark)
    c.rect(x, y, w, 1, K)
    c.rect(x, y + h - 1, w, 1, K)


def window(c, x, y):
    c.box(x, y, 12, 10, GL)
    c.rect(x + 6, y + 1, 1, 8, K)
    c.rect(x + 1, y + 5, 10, 1, K)
    c.px(x + 2, y + 2, W)
    c.px(x + 3, y + 2, W)
    c.px(x + 2, y + 3, W)
    c.rect(x - 1, y + 10, 14, 1, D)


def door(c, x, y):
    c.box(x, y, 11, 14, BR)
    c.frame(x + 2, y + 2, 7, 5, K)
    c.px(x + 8, y + 8, W)


def house(roof_main, roof_dark, gate=False):
    c = Canvas(64, 48, C)
    roof(c, 0, 0, 64, 30, roof_main, roof_dark)
    c.rect(4, 30, 56, 2, D)
    c.rect(4, 32, 56, 14, WL)
    c.rect(4, 32, 1, 14, K)
    c.rect(59, 32, 1, 14, K)
    c.rect(4, 46, 56, 1, K)
    window(c, 10, 35)
    window(c, 24, 35)
    door(c, 40, 32)
    if gate:
        c.rect(36, 33, 24, 1, K)
        for x in range(38, 58, 3):
            c.rect(x, 33, 1, 13, K)
        c.rect(36, 31, 2, 15, D)
        c.rect(58, 31, 2, 15, D)
    return c


def konbini():
    c = Canvas(64, 48, C)
    c.rect(0, 0, 64, 16, W)
    c.rect(0, 5, 64, 3, RED)
    c.rect(0, 9, 64, 3, RB)
    c.rect(0, 0, 64, 1, K)
    c.rect(0, 15, 64, 1, K)
    c.rect(0, 16, 64, 30, W)
    c.rect(0, 16, 1, 30, K)
    c.rect(63, 16, 1, 30, K)
    c.box(4, 19, 56, 24, GL)
    c.box(26, 19, 12, 24, GL)
    c.rect(30, 28, 1, 5, K)
    c.rect(33, 28, 1, 5, K)
    for i in range(5):
        c.px(8 + i, 30 - i, W)
        c.px(44 + i, 30 - i, W)
    c.rect(0, 43, 64, 3, D)
    c.rect(0, 46, 64, 1, K)
    return c


def sakura():
    c = Canvas(32, 32, C)

    def inside(x, y):
        return ((x - 15.5) / 15.5) ** 2 + ((y - 11.5) / 11.5) ** 2 <= 1.0

    for y in range(24):
        for x in range(32):
            if inside(x, y):
                edge = not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                c.px(x, y, K if edge else (SD if (x * 7 + y * 13) % 9 == 0 else SK))
    c.rect(14, 22, 4, 10, BR)
    c.rect(13, 22, 1, 10, K)
    c.rect(18, 22, 1, 10, K)
    c.rect(11, 30, 10, 2, D)
    return c


# ---------------------------------------------------------------- imagens extras
def detect_scale(img):
    """Descobre se a imagem foi ampliada por um fator inteiro (4x, 3x ou 2x)."""
    w, h = img.size
    px = img.load()
    for s in (4, 3, 2):
        bad = tot = 0
        for y in range(0, h - s + 1, s):
            for x in range(0, w - s + 1, s):
                c = px[x, y]
                tot += 1
                if any(px[x + dx, y + dy] != c for dy in range(s) for dx in range(s)):
                    bad += 1
        if tot and bad / tot < 0.01:
            return s
    return 1


def load_extra(path):
    """Le um PNG com fundo transparente e devolve (canvas, paleta de 16 cores)."""
    img = Image.open(path).convert("RGBA")
    s = detect_scale(img)
    if s > 1:
        img = img.resize((img.width // s, img.height // s), Image.NEAREST)
    mask = img.getchannel("A").point(lambda a: 255 if a > 128 else 0)
    box = mask.getbbox()
    if not box:
        raise ValueError(f"{path}: imagem totalmente transparente")
    img, mask = img.crop(box), mask.crop(box)
    w, h = img.size
    big_w, big_h = -(-w // 16) * 16, -(-h // 16) * 16
    left, top = (big_w - w) // 2, big_h - h        # centraliza e encosta embaixo
    bg = Image.new("RGB", (big_w, big_h), CONCRETE)
    bg.paste(img.convert("RGB"), (left, top), mask)
    q = bg.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    raw = q.getpalette()[:45]
    pal = [tuple(raw[i:i + 3]) for i in range(0, len(raw), 3)]
    while len(pal) < 15:
        pal.append((0, 0, 0))
    near = min(range(15), key=lambda i: sum((a - b) ** 2 for a, b in zip(pal[i], CONCRETE)))
    pal[near] = CONCRETE                            # o fundo fica igual a calcada
    cv = Canvas(big_w, big_h, 0)
    qp = q.load()
    for y in range(big_h):
        for x in range(big_w):
            cv.p[y][x] = qp[x, y] + 1
    return cv, [PAL[T]] + pal, (w, h, s)


# ---------------------------------------------------------------- montagem
def build_items(extras_dir):
    singles = [
        ("calcada", sidewalk()), ("grama", grass()), ("rua", road()),
        ("rua_faixa", road_dash()), ("faixa_pedestre", crosswalk()), ("meio_fio", curb()),
        ("muro", muro()), ("cerca_viva", hedge()), ("poste", lamp()),
        ("placa", sign()), ("maquina_venda", vending()),
    ]
    big = [
        ("casa_azul", house(RB, RD), PAL_SLOT),
        ("casa_cinza", house(A, D), PAL_SLOT),
        ("casa_portao", house(RED, K, gate=True), PAL_SLOT),
        ("konbini", konbini(), PAL_SLOT),
        ("sakura", sakura(), PAL_SLOT),
    ]
    pals = {PAL_SLOT: PAL}
    for name, filename, slot in EXTRAS:
        path = os.path.join(extras_dir, filename)
        if not os.path.isfile(path):
            print(f"(aviso) imagem nao encontrada, pulando: {path}")
            continue
        cv, pal, info = load_extra(path)
        pals[slot] = pal
        big.append((name, cv, slot))
        print(f"{name}: {info[0]}x{info[1]} px (ampliacao detectada: {info[2]}x) -> "
              f"{cv.w // 16}x{cv.h // 16} blocos, paleta {slot:02d}")
    return singles, big, pals


def layout(singles, big):
    """Posiciona as pecas numa grade de GRID_W colunas (como o seletor do Porymap)."""
    placed = []
    row = col = 0
    for name, cv in singles:
        if col >= GRID_W:
            row, col = row + 1, 0
        placed.append((name, cv, PAL_SLOT, row, col))
        col += 1
    row, col, shelf_h = row + 1, 0, 0
    for name, cv, slot in big:
        wmt, hmt = cv.w // 16, cv.h // 16
        if col + wmt > GRID_W:
            row, col, shelf_h = row + shelf_h, 0, 0
        placed.append((name, cv, slot, row, col))
        col += wmt
        shelf_h = max(shelf_h, hmt)
    return placed, row + shelf_h


def detect_attr_bytes(out):
    cur = os.path.abspath(out)
    for _ in range(8):
        ref = os.path.join(cur, "data", "tilesets", "primary", "general")
        mt = os.path.join(ref, "metatiles.bin")
        at = os.path.join(ref, "metatile_attributes.bin")
        if os.path.isfile(mt) and os.path.isfile(at):
            n = os.path.getsize(mt) // 16
            if n:
                r = os.path.getsize(at) // n
                if r in (2, 4):
                    return r
        cur = os.path.dirname(cur)
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    out = args[0]
    attr_bytes = None
    extras_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extras")
    for a in sys.argv[1:]:
        if a.startswith("--attr-bytes="):
            attr_bytes = int(a.split("=", 1)[1])
        elif a.startswith("--extras="):
            extras_dir = a.split("=", 1)[1]
    if not os.path.isdir(out):
        sys.exit(f"Pasta nao encontrada: {out}\n"
                 "Crie o tileset secundario no Porymap primeiro (File -> New Tileset) "
                 "e confira o nome exato da pasta em data/tilesets/secondary/.")
    if attr_bytes is None:
        attr_bytes = detect_attr_bytes(out)
    if attr_bytes not in (2, 4):
        sys.exit("Nao consegui detectar o formato dos atributos. Rode de novo com --attr-bytes=2 ou --attr-bytes=4.")
    layer_covered = (1 << 12) if attr_bytes == 2 else (1 << 29)

    singles, big, pals = build_items(extras_dir)
    placed, rows = layout(singles, big)

    # cada metatile = (imagem 16x16 de indices de cor, slot de paleta)
    blank16 = lambda: [[T] * 16 for _ in range(16)]
    metatiles = [(blank16(), PAL_SLOT) for _ in range(rows * GRID_W)]
    where = {}
    for name, cv, slot, r0, c0 in placed:
        wmt, hmt = cv.w // 16, cv.h // 16
        where[name] = (r0, c0, wmt, hmt, slot)
        for r in range(hmt):
            for c in range(wmt):
                idx = (r0 + r) * GRID_W + c0 + c
                img = [cv.p[r * 16 + y][c * 16: c * 16 + 16] for y in range(16)]
                metatiles[idx] = (img, slot)

    # fatia em tiles 8x8 sem repetir (a paleta fica em cada entrada do metatile)
    blank = bytes(64)
    tiles, index = [blank], {blank: 0}

    def tile_id(img, tx, ty):
        data = bytes(img[ty + y][tx + x] for y in range(8) for x in range(8))
        if data not in index:
            index[data] = len(tiles)
            tiles.append(data)
        return index[data]

    mt_bytes = bytearray()
    at_bytes = bytearray()
    empty_entry = TILE_BASE | (PAL_SLOT << 12)
    for img, slot in metatiles:
        entries = [tile_id(img, 0, 0), tile_id(img, 8, 0), tile_id(img, 0, 8), tile_id(img, 8, 8)]
        for t in entries:                       # camada de baixo
            mt_bytes += ((TILE_BASE + t) | (slot << 12)).to_bytes(2, "little")
        for _ in range(4):                      # camada de cima (transparente)
            mt_bytes += empty_entry.to_bytes(2, "little")
        at_bytes += layer_covered.to_bytes(attr_bytes, "little")

    if len(tiles) > 512:
        sys.exit(f"Tiles demais ({len(tiles)}). O limite e 512. "
                 "Use imagens menores ou menos imagens extras.")
    if len(metatiles) > 512:
        sys.exit(f"Metatiles demais ({len(metatiles)}). O limite e 512.")

    # tiles.png (4bpp, 128 de largura)
    h = ((len(tiles) + 15) // 16) * 8
    im = Image.new("P", (128, h), 0)
    im.putpalette([v for col in PAL for v in col])
    pix = im.load()
    for i, t in enumerate(tiles):
        tx, ty = (i % 16) * 8, (i // 16) * 8
        for j, v in enumerate(t):
            pix[tx + j % 8, ty + j // 8] = v
    png = os.path.join(out, "tiles.png")
    if os.path.isfile(png) and not os.path.isfile(png + ".bak"):
        shutil.copy(png, png + ".bak")
    im.save(png, bits=4)

    with open(os.path.join(out, "metatiles.bin"), "wb") as f:
        f.write(mt_bytes)
    with open(os.path.join(out, "metatile_attributes.bin"), "wb") as f:
        f.write(at_bytes)

    pal_dir = os.path.join(out, "palettes")
    os.makedirs(pal_dir, exist_ok=True)
    for slot, pal in pals.items():
        with open(os.path.join(pal_dir, f"{slot:02d}.pal"), "w", newline="") as f:
            f.write("JASC-PAL\r\n0100\r\n16\r\n")
            for r, g, b in pal:
                f.write(f"{r} {g} {b}\r\n")

    # previa visual
    scale = 3
    prev = Image.new("RGB", (GRID_W * 16 * scale, rows * 16 * scale), (230, 230, 230))
    pp = prev.load()
    for idx, (img, slot) in enumerate(metatiles):
        ox, oy = (idx % GRID_W) * 16, (idx // GRID_W) * 16
        pal = pals.get(slot, PAL)
        for y in range(16):
            for x in range(16):
                col = pal[img[y][x]] if img[y][x] != T else (225, 225, 225)
                for sy in range(scale):
                    for sx in range(scale):
                        pp[(ox + x) * scale + sx, (oy + y) * scale + sy] = col
    prev.save("tokyo_preview.png")

    print(f"OK! {len(metatiles)} metatiles, {len(tiles)} de 512 tiles, atributos de {attr_bytes} bytes.")
    print("Onde cada peca esta (linha, coluna) no seletor do tileset Tokyo:")
    for name, (r, c, w, h2, slot) in where.items():
        print(f"  {name:16s} linha {r + 1}, coluna {c + 1}  ({w}x{h2})  paleta {slot:02d}")
    print("Previa salva em tokyo_preview.png")


if __name__ == "__main__":
    main()
