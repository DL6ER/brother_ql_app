from flask import Flask, request, render_template, jsonify
from PIL import Image, ImageDraw, ImageFont
from html.parser import HTMLParser
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends import backend_factory
import os
import json
import logging

app = Flask(__name__)

# Konfiguration
SETTINGS_FILE = "settings.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

DEFAULT_SETTINGS = {
    "printer_uri": "tcp://192.168.1.100",
    "printer_model": "QL-800",
    "label_size": "62",
    "font_size": 50,
    "alignment": "left",
    "rotate": "0",
    "threshold": 70.0,
    "dither": False,
    "compress": False,
    "red": False
}

logging.basicConfig(level=logging.DEBUG)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

settings = load_settings()

def merge_settings(custom_settings):
    """Zusammenführung von Standard- und benutzerdefinierten Einstellungen."""
    merged = settings.copy()
    for key, value in custom_settings.items():
        if value is not None:
            merged[key] = value
    return merged

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.current_tag = None
        self.current_attrs = {}

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)
        if tag == "br":
            self.parts.append({"text": "<br>", "font": None, "color": None, "align": None})

    def handle_data(self, data):
        color = self.current_attrs.get("color", "black")
        font_size = settings.get("font_size", 50)
        font = ImageFont.truetype(FONT_PATH, font_size)
        bold = self.current_tag == "b"
        if bold:
            font = ImageFont.truetype(FONT_PATH, font_size + 5)
        self.parts.append({"text": data.strip(), "font": font, "color": color, "align": None})

    def handle_endtag(self, tag):
        self.current_tag = None
        self.current_attrs = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/settings", methods=["GET"])
def get_settings():
    return jsonify(settings)

@app.route("/update_settings", methods=["POST"])
def update_settings():
    global settings
    settings["font_size"] = int(request.form.get("font_size", settings["font_size"]))
    settings["printer_uri"] = request.form.get("printer_uri", settings["printer_uri"])
    settings["printer_model"] = request.form.get("printer_model", settings["printer_model"])
    settings["label_size"] = request.form.get("label_size", settings["label_size"])
    settings["alignment"] = request.form.get("alignment", settings["alignment"])
    settings["rotate"] = request.form.get("rotate", settings["rotate"])
    settings["threshold"] = float(request.form.get("threshold", settings["threshold"]))
    settings["dither"] = request.form.get("dither", "false").lower() == "true"
    settings["red"] = request.form.get("red", "false").lower() == "true"
    save_settings(settings)
    return jsonify({"success": True, "message": "Einstellungen gespeichert."})

@app.route("/api/text/", methods=["POST"])
def api_text():
    data = request.json
    text = data.get("text", "").strip()
    api_settings = data.get("settings", {})
    current_settings = merge_settings(api_settings)

    if not text:
        return jsonify({"error": "Kein Text angegeben."}), 400

    try:
        image_path = create_label_image(
            text,
            font_size=int(current_settings["font_size"]),
            alignment=current_settings["alignment"]
        )
        rotated_path = apply_rotation(image_path, int(current_settings["rotate"]))
        logging.debug(f"Label-Bild erstellt: {rotated_path}")
        send_to_printer(rotated_path, current_settings)
        return jsonify({"success": True, "message": "Text erfolgreich gedruckt!"})
    except Exception as e:
        logging.error(f"Fehler beim Textdruck: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/image/", methods=["POST"])
def print_image():
    if "image" not in request.files:
        logging.error("Kein Bild hochgeladen.")
        return jsonify({"error": "Kein Bild hochgeladen."}), 400

    image_file = request.files["image"]
    if image_file.filename == "":
        logging.error("Kein Bild ausgewählt.")
        return jsonify({"error": "Kein Bild ausgewählt."}), 400

    api_settings = request.form.to_dict()
    current_settings = merge_settings(api_settings)

    try:
        image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
        image_file.save(image_path)
        logging.debug(f"Bild hochgeladen: {image_path}")
        resized_path = resize_image(image_path)
        rotated_path = apply_rotation(resized_path, int(current_settings["rotate"]))
        logging.debug(f"Bild skaliert und gedreht: {rotated_path}")
        send_to_printer(rotated_path, current_settings)
        return jsonify({"success": True, "message": "Bild erfolgreich gedruckt!"})
    except Exception as e:
        logging.error(f"Fehler beim Bilddruck: {e}")
        return jsonify({"error": str(e)}), 500

def create_label_image(html_text, font_size, alignment="left"):
    width = 696
    parser = TextParser()
    parser.feed(html_text)

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

    dummy_image = Image.new("RGB", (width, 10), "white")
    dummy_draw = ImageDraw.Draw(dummy_image)

    total_height = 10
    line_spacing = 5
    line_metrics = []

    for line in lines:
        ascent_values, descent_values = [], []
        line_width = 0
        for part in line:
            font = ImageFont.truetype(FONT_PATH, font_size)
            ascent, descent = font.getmetrics()
            ascent_values.append(ascent)
            descent_values.append(descent)
            text_width = dummy_draw.textbbox((0, 0), part["text"], font=font)[2]
            line_width += text_width + 5
        line_width -= 5
        max_ascent = max(ascent_values, default=0)
        max_descent = max(descent_values, default=0)
        line_height = max_ascent + max_descent
        line_metrics.append((line, max_ascent, max_descent, line_height, line_width))
        total_height += line_height + line_spacing

    total_height += 10
    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)

    y = 10
    for line, max_ascent, max_descent, line_height, line_width in line_metrics:
        if alignment == "center":
            x = (width - line_width) // 2
        elif alignment == "right":
            x = width - line_width - 10
        else:
            x = 10

        for part in line:
            font = ImageFont.truetype(FONT_PATH, font_size)
            color = part["color"]
            ascent, _ = font.getmetrics()
            draw.text((x, y + max_ascent - ascent), part["text"], fill=color, font=font)
            text_width = dummy_draw.textbbox((0, 0), part["text"], font=font)[2]
            x += text_width + 5
        y += line_height + line_spacing

    image_path = os.path.join(UPLOAD_FOLDER, "text_label.png")
    image.save(image_path)
    return image_path

def apply_rotation(image_path, angle):
    if angle not in [0, 90, 180, 270]:
        logging.warning(f"Ungültiger Drehwinkel: {angle}. Keine Rotation angewendet.")
        return image_path
    with Image.open(image_path) as img:
        rotated_img = img.rotate(-angle, resample=Image.Resampling.LANCZOS, expand=True)
        rotated_path = os.path.join(UPLOAD_FOLDER, f"rotated_{os.path.basename(image_path)}")
        rotated_img.save(rotated_path)
        return rotated_path

def resize_image(image_path):
    max_width = 696
    with Image.open(image_path) as img:
        aspect_ratio = img.height / img.width
        new_height = int(max_width * aspect_ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        resized_path = os.path.join(UPLOAD_FOLDER, "resized_" + os.path.basename(image_path))
        img.save(resized_path)
        return resized_path

def send_to_printer(image_path, current_settings):
    logging.debug(f"Starte Druck für {image_path}")
    try:
        qlr = BrotherQLRaster(current_settings["printer_model"])
        qlr.exception_on_warning = True
        instructions = convert(
            qlr=qlr,
            images=[image_path],
            label=current_settings["label_size"],
            rotate="0",
            threshold=float(current_settings["threshold"]),
            dither=current_settings["dither"],
            compress=current_settings["compress"],
            red=current_settings["red"],
        )
        backend = backend_factory("network")["backend_class"](current_settings["printer_uri"])
        backend.write(instructions)
        backend.dispose()
        logging.debug("Druck erfolgreich abgeschlossen")
    except Exception as e:
        logging.error(f"Fehler beim Drucken: {e}")
        raise

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)