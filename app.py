from flask import Flask, request, render_template, jsonify
from PIL import Image, ImageDraw, ImageFont
from html.parser import HTMLParser
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends import backend_factory
import os
import json

app = Flask(__name__)

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

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

settings = load_settings()

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
    settings["red"] = request.form.get("red", "true").lower() == "true"
    save_settings(settings)
    return jsonify({"success": True, "message": "Einstellungen gespeichert."})

@app.route("/api/text/", methods=["POST"])
def api_text():
    data = request.json
    text = data.get("text", "").strip()
    alignment = data.get("settings", {}).get("alignment", settings["alignment"])
    font_size = int(data.get("settings", {}).get("font_size", settings["font_size"]))

    if not text:
        return jsonify({"error": "Kein Text angegeben."}), 400

    try:
        image_path = create_label_image(text, font_size, alignment)
        send_to_printer(image_path)
        return jsonify({"success": True, "message": "Text erfolgreich gedruckt!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_label_image(text, font_size, alignment):
    width = 696
    height = 200
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, font_size)
    text_width, text_height = draw.textsize(text, font=font)

    if alignment == "center":
        x = (width - text_width) // 2
    elif alignment == "right":
        x = width - text_width - 10
    else:
        x = 10
    y = (height - text_height) // 2

    draw.text((x, y), text, fill="black", font=font)
    image_path = os.path.join(UPLOAD_FOLDER, "text_label.png")
    image.save(image_path)
    return image_path

@app.route("/api/image/", methods=["POST"])
def print_image():
    if "image" not in request.files:
        return jsonify({"error": "Kein Bild hochgeladen."}), 400

    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "Kein Bild ausgewählt."}), 400

    try:
        image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
        image_file.save(image_path)
        resized_path = resize_image(image_path)
        send_to_printer(resized_path)
        return jsonify({"success": True, "message": "Bild erfolgreich gedruckt!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def resize_image(image_path):
    max_width = 696
    with Image.open(image_path) as img:
        aspect_ratio = img.height / img.width
        new_height = int(max_width * aspect_ratio)
        img = img.resize((max_width, new_height), Image.ANTIALIAS)
        resized_path = os.path.join(UPLOAD_FOLDER, "resized_" + os.path.basename(image_path))
        img.save(resized_path)
        return resized_path

def send_to_printer(image_path):
    qlr = BrotherQLRaster(settings["printer_model"])
    qlr.exception_on_warning = True
    instructions = convert(
        qlr=qlr,
        images=[image_path],
        label=settings["label_size"],
        rotate=settings["rotate"],
        threshold=settings["threshold"],
        dither=settings["dither"],
        compress=settings["compress"],
        red=settings["red"],
    )
    backend = backend_factory("network")["backend_class"](settings["printer_uri"])
    backend.write(instructions)
    backend.dispose()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)