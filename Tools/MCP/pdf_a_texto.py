import re, sys, zlib

def inflate(data):
    for f in (lambda d: zlib.decompress(d),
              lambda d: zlib.decompressobj().decompress(d),
              lambda d: zlib.decompressobj(-15).decompress(d)):
        try:
            out = f(data)
            if out:
                return out
        except Exception:
            pass
    return None

# ---------------------------------------------------------------- object table
def load(path):
    buf = open(path, 'rb').read()
    objs = {}
    for m in re.finditer(rb'(\d+)\s+(\d+)\s+obj\b', buf):
        num = int(m.group(1))
        end = buf.find(b'endobj', m.end())
        if end < 0:
            continue
        body = buf[m.end():end]
        sm = re.search(rb'stream\r?\n', body)
        if sm:
            head = body[:sm.start()]
            se = body.find(b'endstream', sm.end())
            raw = body[sm.end():se if se >= 0 else len(body)]
            objs[num] = (head, raw)
        else:
            objs[num] = (body, None)
    # expand /ObjStm
    extra = {}
    for num, (head, raw) in list(objs.items()):
        if raw is None or b'/ObjStm' not in head:
            continue
        d = inflate(raw) if b'FlateDecode' in head else raw
        if not d:
            continue
        n = int(re.search(rb'/N\s+(\d+)', head).group(1))
        first = int(re.search(rb'/First\s+(\d+)', head).group(1))
        nums = re.findall(rb'(\d+)\s+(\d+)', d[:first])
        for i in range(min(n, len(nums))):
            onum = int(nums[i][0]); off = int(nums[i][1])
            nxt = int(nums[i + 1][1]) if i + 1 < len(nums) else len(d) - first
            extra[onum] = (d[first + off: first + nxt], None)
    for k, v in extra.items():
        objs.setdefault(k, v)
    return buf, objs

def stream_of(objs, num):
    if num not in objs:
        return None
    head, raw = objs[num]
    if raw is None:
        return None
    return inflate(raw) if b'FlateDecode' in head else raw

def deref(objs, token):
    """token like b'12 0 R' -> body bytes of that object, else the token"""
    m = re.match(rb'\s*(\d+)\s+\d+\s+R', token)
    if m and int(m.group(1)) in objs:
        return objs[int(m.group(1))][0]
    return token

# ---------------------------------------------------------------- ToUnicode
def parse_cmap(data):
    m = {}
    for blk in re.findall(rb'beginbfchar(.*?)endbfchar', data, re.S):
        for src, dst in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            try:
                m[int(src, 16)] = bytes.fromhex(dst.decode()).decode('utf-16-be', 'ignore')
            except Exception:
                pass
    for blk in re.findall(rb'beginbfrange(.*?)endbfrange', data, re.S):
        for lo, hi, dst in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            try:
                a = int(lo, 16); b = int(hi, 16); base = int(dst, 16)
                for i in range(a, min(b, a + 4096) + 1):
                    m[i] = chr(base + (i - a))
            except Exception:
                pass
    return m

def font_cmaps(objs):
    """font object number -> (cmap, two_byte)"""
    out = {}
    for num, (head, raw) in objs.items():
        if b'/Font' not in head and b'/ToUnicode' not in head:
            continue
        tu = re.search(rb'/ToUnicode\s+(\d+)\s+\d+\s+R', head)
        if not tu:
            continue
        d = stream_of(objs, int(tu.group(1)))
        if not d:
            continue
        cm = parse_cmap(d)
        two = b'Identity-H' in head or b'/Type0' in head
        if not two:
            # composite subset fonts often still emit 2-byte codes
            two = bool(cm) and max(cm) > 255
        out[num] = (cm, two)
    return out

# ---------------------------------------------------------------- pages
def page_order(buf, objs):
    pages = []
    root = re.search(rb'/Root\s+(\d+)\s+\d+\s+R', buf)
    kids_seen = []
    if root:
        rb_ = objs.get(int(root.group(1)), (b'', None))[0]
        pg = re.search(rb'/Pages\s+(\d+)\s+\d+\s+R', rb_)
        if pg:
            stack = [int(pg.group(1))]
            while stack:
                n = stack.pop(0)
                body = objs.get(n, (b'', None))[0]
                if b'/Type' in body and b'/Pages' in body:
                    kids = re.search(rb'/Kids\s*\[(.*?)\]', body, re.S)
                    if kids:
                        ids = [int(x) for x in re.findall(rb'(\d+)\s+\d+\s+R', kids.group(1))]
                        stack = ids + stack
                else:
                    kids_seen.append(n)
    if kids_seen:
        return kids_seen
    for num, (head, raw) in sorted(objs.items()):
        if re.search(rb'/Type\s*/Page\b', head):
            pages.append(num)
    return pages

def page_fonts(objs, pnum):
    body = objs.get(pnum, (b'', None))[0]
    res = re.search(rb'/Resources\s*(\d+\s+\d+\s+R|<<)', body)
    if not res:
        return {}
    if res.group(1).endswith(b'R'):
        rbody = deref(objs, res.group(1))
    else:
        rbody = body[res.start(1):]
    fm = re.search(rb'/Font\s*(\d+\s+\d+\s+R|<<(?:[^<>]|<<.*?>>)*>>)', rbody, re.S)
    if not fm:
        return {}
    fbody = deref(objs, fm.group(1)) if fm.group(1).endswith(b'R') else fm.group(1)
    out = {}
    for name, onum in re.findall(rb'/([A-Za-z0-9#+.\-]+)\s+(\d+)\s+\d+\s+R', fbody):
        out[name] = int(onum)
    return out

def page_content(objs, pnum):
    body = objs.get(pnum, (b'', None))[0]
    m = re.search(rb'/Contents\s*(\[[^\]]*\]|\d+\s+\d+\s+R)', body)
    if not m:
        return b''
    ids = [int(x) for x in re.findall(rb'(\d+)\s+\d+\s+R', m.group(1))]
    return b'\n'.join(filter(None, (stream_of(objs, i) for i in ids)))

# ---------------------------------------------------------------- rendering
STR_RE = re.compile(rb'\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]*>|(?<![\d.])-?\d+(?:\.\d+)?(?![\d.]*\s*(?:Tf|Td|TD|Tm))', re.S)
OPS_RE = re.compile(
    rb"(/([A-Za-z0-9#+.\-]+)\s+[\d.]+\s+Tf)"
    rb"|(\[(?:[^\[\]\\]|\\.)*\]\s*TJ)"
    rb"|((?:\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]*>)\s*(?:Tj|'|\"))"
    rb"|(T\*)|(\bTd\b)|(\bTD\b)|(\bET\b)|(\bBT\b)", re.S)

ESC = {0x6e: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12, 0x28: 40, 0x29: 41, 0x5c: 92}

def unescape(s):
    out = bytearray(); i = 0
    while i < len(s):
        c = s[i]
        if c == 0x5c and i + 1 < len(s):
            n = s[i + 1]
            if n in ESC:
                out.append(ESC[n]); i += 2; continue
            if 0x30 <= n <= 0x37:
                j = i + 1; oct_ = b''
                while j < len(s) and 0x30 <= s[j] <= 0x37 and len(oct_) < 3:
                    oct_ += bytes([s[j]]); j += 1
                out.append(int(oct_, 8) & 0xFF); i = j; continue
            if n == 0x0a:
                i += 2; continue
            i += 1; continue
        out.append(c); i += 1
    return bytes(out)

def render(content, fonts, cmaps):
    parts = []
    cur = ({}, False)
    for m in OPS_RE.finditer(content):
        if m.group(1):
            fo = fonts.get(m.group(2))
            cur = cmaps.get(fo, ({}, False)) if fo is not None else ({}, False)
            continue
        if m.group(5) or m.group(8):
            parts.append('\n'); continue
        if m.group(6) or m.group(7):
            parts.append(' '); continue
        chunk = m.group(0)
        cm, two = cur
        for sm in STR_RE.finditer(chunk):
            tok = sm.group(0)
            if tok[:1] not in (b'(', b'<'):
                try:
                    if float(tok) < -60:
                        parts.append(' ')
                except ValueError:
                    pass
                continue
            if tok.startswith(b'<'):
                hx = re.sub(rb'\s', b'', tok[1:-1])
                if len(hx) % 2:
                    hx += b'0'
                data = bytes.fromhex(hx.decode())
            else:
                data = unescape(tok[1:-1])
            if two:
                for i in range(0, len(data) - 1, 2):
                    parts.append(cm.get((data[i] << 8) | data[i + 1], ''))
            elif cm:
                for b in data:
                    parts.append(cm.get(b, ''))
            else:
                parts.append(data.decode('latin-1'))
    return ''.join(parts)

def main(path, out):
    buf, objs = load(path)
    cmaps = font_cmaps(objs)
    pages = page_order(buf, objs)
    chunks = []
    for i, p in enumerate(pages, 1):
        c = page_content(objs, p)
        if not c:
            continue
        t = render(c, page_fonts(objs, p), cmaps)
        t = re.sub(r'[ \t]+\n', '\n', t)
        t = re.sub(r'\n{3,}', '\n\n', t)
        chunks.append('\n\n========== PAGINA %d ==========\n%s' % (i, t.strip()))
    body = '\n'.join(chunks)
    open(out, 'w', encoding='utf-8').write(body)
    print('objs=%d fonts_with_cmap=%d pages=%d chars=%d'
          % (len(objs), len(cmaps), len(pages), len(body)))

main(sys.argv[1], sys.argv[2])

# ---------------------------------------------------------------------------
# POR QUE EXISTE ESTO
#
#   "/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" \
#       pdf_a_texto.py entrada.pdf salida.txt
#
# Los PDF de diseño (Biblia Narrativa, GDD, LDD, el del bucle de combate) no se
# dejaban leer: no hay poppler instalado, no hay python en el PATH y el Read de
# PDF del asistente necesita pdftoppm. El python que trae Unreal si sirve.
#
# Dos trampas que costaron dos intentos:
#   1. Cada fuente subset trae su PROPIO ToUnicode. Fusionar todos los cmaps en
#      uno corrompe el texto ("Gabriel" salia "GabriOe"). Hay que resolver el
#      cmap POR PAGINA y POR FUENTE, siguiendo el operador Tf.
#   2. Los espacios no son caracteres: se hacen con los desplazamientos
#      negativos de los arrays TJ. Sin eso el texto sale toooooodojunto.
