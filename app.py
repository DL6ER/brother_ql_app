from flask import Flask, request, render_template, jsonify
from PIL import Image, ImageDraw, ImageFont
from html.parser import HTMLParser
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends import backend_factory
import os

app = Flask(__name__)

# Standard-Druckerkonfiguration
PRINTER_URI = os.getenv("PRINTER_URI", "tcp://192.168.1.100")
PRINTER_MODEL = os.getenv("PRINTER_MODEL", "QL-800")
LABEL_SIZE = "62"
FONT_SIZE = 50  # Standard-Schriftgröße
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

class TextParser(HTMLParser):
    """Parst HTML und speichert Text mit Formatierungen."""
    def __init__(self):
        super().__init__()
        self.parts = []
        self.current_tag = None
        self.current_attrs = {}

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)

        # <br> Tag erkennen
        if tag == "br":
            self.parts.append({"text": "<br>", "font": None, "color": None, "align": None})

    def handle_data(self, data):
        color = self.current_attrs.get("color", "black")
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)  # Schriftgröße aus globaler Variable
        bold = self.current_tag == "b"
        if bold:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE + 5)  # Bold-Schrift
        self.parts.append({"text": data.strip(), "font": font, "color": color, "align": None})

    def handle_endtag(self, tag):
        self.current_tag = None
        self.current_attrs = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/update_settings", methods=["POST"])
def update_settings():
    """Einstellungen aktualisieren."""
    global LABEL_SIZE, FONT_SIZE
    LABEL_SIZE = request.form.get("label_size", LABEL_SIZE)
    FONT_SIZE = int(request.form.get("font_size", FONT_SIZE))  # Schriftgröße aktualisieren
    return jsonify({"success": True, "message": "Einstellungen aktualisiert."})

@app.route("/api/text/", methods=["POST"])
def api_text():
    global FONT_SIZE, LABEL_SIZE  # Global-Deklaration am Anfang

    data = request.json
    text = data.get("text", "").strip()
    label_size = data.get("settings", {}).get("label_size", LABEL_SIZE)
    font_size = data.get("settings", {}).get("font_size", FONT_SIZE)
    alignment = data.get("settings", {}).get("alignment", "left")  # Neue Einstellung für Ausrichtung

    if not text:
        return jsonify({"error": "Kein Text angegeben."}), 400

    try:
        # Temporär aktualisierte Schrift- und Label-Größe anwenden
        original_font_size = FONT_SIZE
        original_label_size = LABEL_SIZE
        FONT_SIZE = int(font_size)
        LABEL_SIZE = label_size

        # Label erzeugen und drucken
        image_path = create_label_image(text, alignment)
        send_to_printer(image_path)

        # Originale Werte wiederherstellen
        FONT_SIZE = original_font_size
        LABEL_SIZE = original_label_size

        return jsonify({"success": True, "message": "Textdruckauftrag gesendet."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_label_image(html_text, alignment="left"):
    """Erstellt ein Labelbild mit dynamischer Höhe und unterstützt Ausrichtung."""
    width = 696
    parser = TextParser()
    parser.feed(html_text)

    # Gruppieren der Zeilen
    lines = []
    current_line = []
    for part in parser.parts:
        if part["text"] == "<br>":
            if current_line:
                lines.append(current_line)
            current_line = []
        else:
            current_line.append(part)
    if current_line:
        lines.append(current_line)

    # Höhe berechnen
    dummy_image = Image.new("RGB", (width, 10), "white")
    dummy_draw = ImageDraw.Draw(dummy_image)

    total_height = 10
    line_spacing = 5
    line_metrics = []

    for line in lines:
        ascent_values, descent_values = [], []
        line_width = 0
        for part in line:
            font = part["font"]
            ascent, descent = font.getmetrics()
            ascent_values.append(ascent)
            descent_values.append(descent)
            text_width = dummy_draw.textbbox((0, 0), part["text"], font=font)[2]
            line_width += text_width + 5  # 5 Pixel Abstand zwischen den Wörtern
        line_width -= 5
        max_ascent = max(ascent_values, default=0)
        max_descent = max(descent_values, default=0)
        line_height = max_ascent + max_descent
        line_metrics.append((line, max_ascent, max_descent, line_height, line_width))
        total_height += line_height + line_spacing

    total_height += 10  # Unterer Rand

    # Bild erstellen
    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)

    y = 10
    for line, max_ascent, max_descent, line_height, line_width in line_metrics:
        # Basierend auf der Ausrichtung x-Wert berechnen
        if alignment == "center":
            x = (width - line_width) // 2
        elif alignment == "right":
            x = width - line_width - 10
        else:  # Standard: left
            x = 10

        for part in line:
            font = part["font"]
            color = part["color"]
            ascent, _ = font.getmetrics()
            draw.text((x, y + max_ascent - ascent), part["text"], fill=color, font=font)
            text_width = dummy_draw.textbbox((0, 0), part["text"], font=font)[2]
            x += text_width + 5
        y += line_height + line_spacing

    image_path = "label.png"
    image.save(image_path)
    return image_path

def send_to_printer(image_path):
    """Sendet das Label an den Drucker."""
    qlr = BrotherQLRaster(PRINTER_MODEL)
    qlr.exception_on_warning = True
    instructions = convert(
        qlr=qlr,
        images=[image_path],
        label=LABEL_SIZE,
        rotate="0",
        threshold=70.0,
        dither=False,
        compress=False,
        red=True,
    )
    backend = backend_factory("network")["backend_class"](PRINTER_URI)
    backend.write(instructions)
    backend.dispose()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)