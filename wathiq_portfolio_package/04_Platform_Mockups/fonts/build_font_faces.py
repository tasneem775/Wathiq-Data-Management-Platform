"""Extracts the 'latin' subset @font-face blocks from fonts.css, downloads each
woff2, base64-encodes it, and writes fonts_inline.css with data-URI @font-face
rules only (no external requests at render time)."""
import re
import base64
import urllib.request

with open("fonts.css", "r", encoding="utf-8") as f:
    css = f.read()

blocks = re.findall(
    r"/\*\s*(latin)\s*\*/\s*@font-face\s*\{([^}]*)\}", css, re.MULTILINE
)

out_rules = []
for subset, body in blocks:
    family = re.search(r"font-family:\s*'([^']+)'", body).group(1)
    weight = re.search(r"font-weight:\s*(\d+)", body).group(1)
    url = re.search(r"url\(([^)]+)\)\s*format\('woff2'\)", body).group(1)
    print(f"Downloading {family} {weight} ...")
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    b64 = base64.b64encode(data).decode("ascii")
    out_rules.append(
        f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
        f"font-display:swap;src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
    )

with open("fonts_inline.css", "w", encoding="utf-8") as f:
    f.write("\n".join(out_rules))

print("Done. Wrote fonts_inline.css with", len(out_rules), "face(s).")
