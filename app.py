import os
import json
import logging
from flask import Flask, request, render_template, jsonify, redirect, url_for, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from html.parser import HTMLParser
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends import backend_factory

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

logging.basicConfig(level=logging.DEBUG)

def load_settings():
    if os.path.exists(SETTINGS_FILE) and os.path.isfile(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

settings = load_settings()

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append("<br>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_endtag(self, tag):
        pass

@app.route("/")
def index():
    """
    Renders the main page of the Web-GUI.
    """
    return render_template("index.html", settings=settings)

@app.route("/settings", methods=["GET"])
def get_settings():
    """
    Returns current settings in JSON format.
    """
    return jsonify(settings)

@app.route("/update_settings", methods=["POST"])
def update_settings():
    """
    Updates settings from the Web-GUI form and saves them.
    """
    global settings
    for key in DEFAULT_SETTINGS.keys():
        if key in request.form:
            value = request.form[key]
            if isinstance(DEFAULT_SETTINGS[key], bool):
                settings[key] = value.lower() == "true"
            elif isinstance(DEFAULT_SETTINGS[key], int):
                settings[key] = int(value)
            elif isinstance(DEFAULT_SETTINGS[key], float):
                settings[key] = float(value)
            else:
                settings[key] = value
    save_settings(settings)
    return redirect(url_for("index"))

@app.route("/api/text/", methods=["POST"])
def api_text():
    data = request.get_json()
    if not data or "text" not in data or "settings" not in data:
        logging.error("No text or settings provided")
        return jsonify({"error": "No text or settings provided"}), 400

    text = data["text"]
    settings = load_settings()
    received_settings = data["settings"]
    local_settings = {
        "printer_uri": received_settings.get("printer_uri", settings["printer_uri"]),
        "printer_model": received_settings.get("printer_model", settings["printer_model"]),
        "label_size": received_settings.get("label_size", settings["label_size"]),
        "font_size": float(received_settings.get("font_size", settings["font_size"])),
        "alignment": received_settings.get("alignment", settings["alignment"]),
        "rotate": int(received_settings.get("rotate", settings["rotate"])),
        "threshold": float(received_settings.get("threshold", settings["threshold"])),
        "dither": received_settings.get("dither", settings["dither"]),
        "red": received_settings.get("red", settings["red"]),
        "compress": received_settings.get("compress", settings["compress"]),
    }

    try:
        logging.info("Received text: %s", text)
        logging.info("Using settings: %s", local_settings)
        image_path = create_label_image(text, local_settings)
        logging.info("Image created at: %s", image_path)
        if local_settings["rotate"] != "0":
            image_path = apply_rotation(image_path, int(local_settings["rotate"]))
            logging.info("Image rotated to: %s", image_path)
        send_to_printer(image_path, local_settings)
        logging.info("Text printed successfully")
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error printing text: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/image/", methods=["POST"])
def print_image():
    """
    Endpoint to print images. Accepts an uploaded image and settings via request.
    """
    if "image" not in request.files:
        return jsonify({"error": "Kein Bild hochgeladen."}), 400

    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "Kein Bild ausgewählt."}), 400

    try:
        # Parse optional settings from request
        api_settings = json.loads(request.form.get("settings", "{}"))
        local_settings = {**settings, **api_settings}  # Combine global settings with API-provided settings

        # Save the uploaded image
        image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
        image_file.save(image_path)

        # Resize the image to fit label width
        resized_path = resize_image(image_path)

        # Apply rotation if specified
        rotated_path = apply_rotation(resized_path, int(local_settings.get("rotate", 0)))

        # Send to printer with updated settings
        send_to_printer(rotated_path, local_settings)

        return jsonify({"success": True, "message": "Bild erfolgreich gedruckt!"})
    except Exception as e:
        logging.error(f"Fehler beim Bilddruck: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/locales/<path:filename>')
def serve_locale(filename):
    return send_from_directory('locales', filename)

def create_label_image(html_text, local_settings):
    width = 696  # Fixed label width
    font_size = int(local_settings.get("font_size", 50))
    alignment = local_settings.get("alignment", "left")

    parser = TextParser()
    parser.feed(html_text)

    lines = []
    current_line = []
    for part in parser.parts:
        if part == "<br>":
            lines.append("".join(current_line))
            current_line = []
        else:
            current_line.append(part)
    if current_line:
        lines.append("".join(current_line))

    dummy_image = Image.new("RGB", (width, 10), "white")
    dummy_draw = ImageDraw.Draw(dummy_image)

    total_height = 10
    line_spacing = 5
    line_metrics = []

    for line in lines:
        font = ImageFont.truetype(FONT_PATH, font_size)
        bbox = dummy_draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        max_ascent, max_descent = font.getmetrics()
        total_height += line_height + line_spacing
        line_metrics.append((line, max_ascent, max_descent, line_height, line_width))

    total_height += 10
    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)

    y = 10
    for line_text, max_ascent, max_descent, line_height, line_width in line_metrics:
        if alignment == "center":
            x = (width - line_width) // 2
        elif alignment == "right":
            x = width - line_width - 10
        else:
            x = 10
        draw.text((x, y), line_text, font=font, fill="black")
        y += line_height + line_spacing

    image_path = os.path.join(UPLOAD_FOLDER, "text_label.png")
    image.save(image_path)
    return image_path

def apply_rotation(image_path, angle):
    """
    Applies rotation to the label image.
    """
    with Image.open(image_path) as img:
        rotated_img = img.rotate(-angle, resample=Image.Resampling.LANCZOS, expand=True)
        rotated_path = os.path.join(UPLOAD_FOLDER, f"rotated_{os.path.basename(image_path)}")
        rotated_img.save(rotated_path)
        return rotated_path

def resize_image(image_path):
    """
    Resizes an uploaded image to fit the label width.
    """
    max_width = 696
    with Image.open(image_path) as img:
        aspect_ratio = img.height / img.width
        new_height = int(max_width * aspect_ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        resized_path = os.path.join(UPLOAD_FOLDER, "resized_" + os.path.basename(image_path))
        img.save(resized_path)
        return resized_path

def send_to_printer(image_path, local_settings):
    """
    Sends the label image to the printer with the provided settings.
    """
    try:
        qlr = BrotherQLRaster(local_settings["printer_model"])
        qlr.exception_on_warning = True
        instructions = convert(
            qlr=qlr,
            images=[image_path],
            label=local_settings["label_size"],
            rotate=local_settings["rotate"],
            threshold=float(local_settings["threshold"]),
            dither=local_settings["dither"],
            compress=local_settings["compress"],
            red=local_settings["red"],
        )
        backend = backend_factory("network")["backend_class"](local_settings["printer_uri"])
        backend.write(instructions)
        backend.dispose()
    except Exception as e:
        logging.error(f"Fehler beim Drucken: {e}")
        raise

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)