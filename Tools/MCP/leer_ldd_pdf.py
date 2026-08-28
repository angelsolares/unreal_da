"""Lee el LDD de Malkuth. Sus flujos van ASCII85 + Flate encadenados, y las
fuentes son Type1 estandar, asi que el texto sale en claro sin tabla cmap."""
import base64, re, sys, zlib

sys.stdout.reconfigure(encoding="utf-8")
buf = open(sys.argv[1], "rb").read()

ESC = [(b"\\(", b"("), (b"\\)", b")"), (b"\\\\", b"\\")]

partes = []
for m in re.finditer(rb"stream\r?\n", buf):
    e = buf.find(b"endstream", m.end())
    if e < 0:
        continue
    raw = buf[m.end():e].strip()
    try:
        d = zlib.decompress(base64.a85decode(raw, adobe=True))
    except Exception:
        continue
    if b"BT" not in d or len(d) > 200000:
        continue
    for mm in re.finditer(rb"\((?:\\.|[^\\()])*\)|Td|TD|T\*|ET", d):
        t = mm.group(0)
        if t.startswith(b"("):
            s = t[1:-1]
            for a, b in ESC:
                s = s.replace(a, b)
            partes.append(s.decode("latin-1"))
        else:
            partes.append("\n")

texto = "".join(partes)
texto = re.sub(r"[ \t]+\n", "\n", texto)
texto = re.sub(r"\n{3,}", "\n\n", texto)
print(texto)
