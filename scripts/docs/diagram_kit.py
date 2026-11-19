"""Drawing kit for the documentation diagrams: Excalidraw elements in one visual language.

Components are coloured boxes with a numbered badge, notes are dashed boxes in the same
colour with lettered steps, tables are framed field lists, and a red box marks a trust
boundary. The language of every label is chosen once per diagram with ``use_language``.

Example:
    kit = Kit("pt")
    kit.title(kit.tr("Arquitectura", "Architecture"), "visão geral")
    kit.box(40, 120, 200, 56, ORANGE, "API", badge="1")
    kit.save(Path("docs/diagramas/documentacao/pt/01-arquitectura.excalidraw"))
"""

import hashlib
import json
from pathlib import Path

ORANGE = ("#e8590c", "#fff4e6")
PURPLE = ("#862e9c", "#f8f0fc")
BLUE = ("#1971c2", "#e7f5ff")
GREEN = ("#2f9e44", "#ebfbee")
YELLOW = ("#e67700", "#fff9db")
RED = ("#c92a2a", "#fff5f5")
GRAY = ("#495057", "#f8f9fa")
INK = ("#1e1e1e", "#ffffff")
MUTED = "#868e96"
HAND, MONO = 1, 3
CHAR_WIDTH = {HAND: 0.54, MONO: 0.61}


class Kit:
    """Collects the elements of one diagram in one language."""

    def __init__(self, language: str) -> None:
        self.language = language
        self.elements: list[dict] = []

    def tr(self, portuguese: str, english: str) -> str:
        return portuguese if self.language == "pt" else english

    # -- primitives -------------------------------------------------------------------

    def _add(self, kind: str, x: float, y: float, w: float, h: float, **over) -> dict:
        key = f"{kind}-{len(self.elements)}"
        seed = int(hashlib.sha256(key.encode()).hexdigest()[:7], 16)
        element = {
            "id": key, "type": kind, "x": x, "y": y, "width": w, "height": h, "angle": 0,
            "strokeColor": INK[0], "backgroundColor": "transparent", "fillStyle": "solid",
            "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1, "opacity": 100,
            "groupIds": [], "frameId": None, "roundness": None, "seed": seed, "version": 1,
            "versionNonce": seed, "isDeleted": False, "boundElements": [], "updated": 1,
            "link": None, "locked": False,
        }
        element.update(over)
        if isinstance(element["strokeColor"], tuple):
            element["strokeColor"] = element["strokeColor"][0]
        self.elements.append(element)
        return element

    def shape(self, kind, x, y, w, h, colors, *, dashed=False, width=2, fill=True, rounded=True):
        return self._add(
            kind, x, y, w, h, strokeColor=colors[0],
            backgroundColor=colors[1] if fill else "transparent", strokeWidth=width,
            strokeStyle="dashed" if dashed else "solid",
            roundness={"type": 3} if rounded and kind == "rectangle" else None,
        )

    def text(self, value, x, y, w, *, size=16, color=INK[0], align="left", family=HAND):
        value = wrap(value, w, size, family)
        lines = value.count("\n") + 1
        self._add(
            "text", x, y, w, round(size * 1.25 * lines), strokeColor=color, text=value,
            originalText=value, fontSize=size, fontFamily=family, textAlign=align,
            verticalAlign="top", containerId=None, lineHeight=1.25,
        )
        return y + round(size * 1.25 * lines)

    def arrow(self, points, color=INK[0], *, dashed=False, both=False, label=None, at=None, width=2):
        x0, y0 = points[0]
        relative = [[px - x0, py - y0] for px, py in points]
        xs, ys = [p[0] for p in relative], [p[1] for p in relative]
        self._add(
            "arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys), strokeColor=color,
            strokeWidth=width, strokeStyle="dashed" if dashed else "solid",
            roundness={"type": 2} if len(points) == 2 else None, points=relative,
            lastCommittedPoint=None, startBinding=None, endBinding=None,
            startArrowhead="arrow" if both else None, endArrowhead="arrow",
        )
        if label:
            lx, ly = at if at else ((points[0][0] + points[-1][0]) / 2 + 6, (points[0][1] + points[-1][1]) / 2 - 22)
            self.text(label, lx, ly, 220, size=14, color=color)

    # -- components ---------------------------------------------------------------------

    def title(self, value: str, subtitle: str) -> None:
        self.text(value, 30, 22, 900, size=34)
        self.text(subtitle, 32, 70, 900, size=16, color=MUTED)

    def legend(self, items, right=1290, y=26) -> None:
        x = right
        for label, colors in reversed(items):
            w = max(110, len(label) * 9 + 36)
            x -= w + 14
            self.shape("rectangle", x, y, w, 36, colors)
            self.text(label, x, y + 8, w, size=15, color=colors[0], align="center")

    def badge(self, number: str, x: float, y: float, colors) -> None:
        self.shape("ellipse", x, y, 28, 28, colors)
        self.text(number, x, y + 5, 28, size=14, color=colors[0], align="center")

    def box(self, x, y, w, h, colors, label, *, badge=None, size=17, sub=None, dashed=False):
        self.shape("rectangle", x, y, w, h, colors, dashed=dashed)
        label_lines = wrap(label, w - 16, size).count("\n") + 1
        body = round(size * 1.25 * label_lines) + (round(13 * 1.25 * (wrap(sub, w - 16, 13).count("\n") + 1)) + 4 if sub else 0)
        top = y + max(6, (h - body) / 2)
        bottom = self.text(label, x + 8, top, w - 16, size=size, color=colors[0], align="center")
        if sub:
            self.text(sub, x + 8, bottom + 4, w - 16, size=13, color=INK[0], align="center")
        if badge:
            self.badge(badge, x - 12, y - 14, colors)

    def stack(self, x, y, w, h, colors, label, *, badge=None, copies=3):
        for i in range(copies - 1, 0, -1):
            self.shape("rectangle", x + 12 * i, y - 12 * i, w, h, colors)
        self.box(x, y, w, h, colors, label, badge=badge)

    def note(self, x, y, w, lines, colors, *, badge=None, size=14):
        body = "\n".join(wrap_item(line, w - 28, size) for line in lines)
        h = round(size * 1.25 * (body.count("\n") + 1)) + 26
        self.shape("rectangle", x, y, w, h, colors, dashed=True, fill=False, width=1)
        self.text(body, x + 14, y + 13, w - 28, size=size, color=colors[0])
        if badge:
            self.badge(badge, x - 12, y - 14, colors)
        return y + h

    def table(self, x, y, w, title, fields, *, colors=INK, size=14, framed=False, badge=None):
        pad = 14
        title_h = 34
        body = "\n".join(wrap_item(field, w - 2 * pad, size) for field in fields)
        h = title_h + round(size * 1.25 * (body.count("\n") + 1)) + 2 * pad
        if framed:
            self.shape("rectangle", x - 12, y - 12, w + 24, h + 24, colors, width=2, fill=False)
        self.shape("rectangle", x, y, w, h, (colors[0], "#ffffff"), width=2)
        self.text(title, x + pad, y + pad - 2, w - 2 * pad, size=19, color=colors[0])
        self.text(body, x + pad, y + pad + title_h - 4, w - 2 * pad, size=size, color=INK[0])
        if badge:
            self.badge(badge, x - 24 if framed else x - 12, y - 26 if framed else y - 14, colors)
        return y + h

    def code(self, x, y, w, title, lines, colors=RED, *, size=13):
        body = "\n".join(wrap_item(line, w - 28, size, MONO) for line in lines)
        title_h = round(15 * 1.25 * (wrap(title, w - 28, 15).count("\n") + 1))
        h = title_h + 30 + round(size * 1.25 * (body.count("\n") + 1)) + 14
        self.shape("rectangle", x, y, w, h, colors, width=2)
        self.text(title, x + 14, y + 10, w - 28, size=15, color=colors[0])
        self.text(body, x + 14, y + title_h + 20, w - 28, size=size, color=INK[0], family=MONO)
        return y + h

    def listing(self, x, y, w, heading, items, colors=GREEN, *, size=14):
        bottom = self.text(heading, x, y, w, size=15, color=colors[0])
        body = "\n".join(wrap_item(item, w, size) for item in items)
        return self.text(body, x, bottom + 6, w, size=size, color=colors[0])

    def group(self, x, y, w, h, caption=None, *, colors=GRAY, caption_right=None):
        self.shape("rectangle", x, y, w, h, colors, dashed=True, fill=False, width=1)
        if caption:
            self.text(caption, x + 14, y + h - 26, w - 28, size=13, color=MUTED)
        if caption_right:
            self.text(caption_right, x + w / 2, y + h - 26, w / 2 - 14, size=13, color=MUTED, align="right")

    def people(self, x, y, label, colors=GRAY) -> None:
        for dx, dy in ((22, 0), (0, 36), (44, 36)):
            self.shape("ellipse", x + dx + 6, y + dy, 20, 20, colors)
            self.shape("rectangle", x + dx, y + dy + 20, 32, 18, colors)
        self.text(label, x - 20, y + 82, 116, size=15, align="center")

    def diamond(self, x, y, w, h, colors, label, *, size=15):
        self.shape("diamond", x, y, w, h, colors)
        lines = wrap(label, w * 0.6, size).count("\n") + 1
        self.text(label, x + w * 0.2, y + h / 2 - size * 1.25 * lines / 2, w * 0.6, size=size, color=colors[0], align="center")

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
            "elements": self.elements,
            "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"}, "files": {},
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def text_width(value: str, size: int, family: int = HAND) -> float:
    """Estimated width in pixels: Virgil capitals are much wider than its lower case."""
    if family == MONO:
        return len(value) * size * CHAR_WIDTH[MONO]
    widths = {True: 0.7, False: 0.535}
    return sum(size * (0.28 if ch == " " else widths[ch.isupper() or ch.isdigit()]) for ch in value)


def _fill(paragraph: str, width: float, size: int, family: int, indent: str = "") -> list[str]:
    lines, current = [], ""
    for word in paragraph.split(" "):
        candidate = f"{current} {word}" if current else word
        if current and text_width(candidate, size, family) > width:
            lines.append(current)
            current = indent + word
        else:
            current = candidate
    return lines + [current]


def wrap(value: str, width: float, size: int, family: int = HAND) -> str:
    """Break each paragraph of ``value`` so no line is wider than ``width`` pixels."""
    return "\n".join("\n".join(_fill(part, width, size, family)) for part in value.split("\n"))


def wrap_item(value: str, width: float, size: int, family: int = HAND) -> str:
    """Wrap a list item, indenting its continuation lines under its first word."""
    marker = value.split(" ", 1)[0]
    indent = "\u00a0" * (len(marker) + 2) if len(marker) <= 2 and marker.endswith((".", "·", "-")) else ""
    return "\n".join(_fill(value, width, size, family, indent))
