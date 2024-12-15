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

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append({"text": "<br>", "font": None})

    def handle_data(self, data):
        font_size = settings.get("font_size", 50)
        font = ImageFont.truetype(FONT_PATH, font_size)
        self.parts.append({"text": data.strip(), "font": font})

    def handle_endtag(self, tag):
        pass

@app.route("/settings", methods=["GET"])
def get_settings():
    return jsonify(settings)

@app.route("/update_settings", methods=["POST"])
def update_settings():
    global settings
    settings.update(request.json)
    save_settings(settings)
    return jsonify({"success": True, "message": "Einstellungen gespeichert."})

@app.route("/api/text/", methods=["POST"])
def api_text():
    """
    Endpoint to print text labels. Accepts text and settings in the request JSON.
    """
    data = request.json

    # Extract text and settings from the request
    text = data.get("text", "").strip()
    api_settings = data.get("settings", {})
    local_settings = {**settings, **api_settings}  # Combine global settings with API-provided settings

    if not text:
        return jsonify({"error": "Kein Text angegeben."}), 400

    try:
        # Generate label image
        image_path = create_label_image(text, local_settings)

        # Apply rotation if specified
        rotated_path = apply_rotation(image_path, int(local_settings.get("rotate", 0)))

        # Send to printer with updated settings
        send_to_printer(rotated_path, local_settings)

        return jsonify({"success": True, "message": "Text erfolgreich gedruckt!"})
    except Exception as e:
        logging.error(f"Fehler beim Textdruck: {e}")
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

def create_label_image(html_text, local_settings):
    """
    Creates a label image from the provided HTML-like text and settings.
    """
    width = 696  # Fixed label width
    font_size = int(local_settings.get("font_size", 50))
    alignment = local_settings.get("alignment", "left")

    # Parse the HTML-like text into parts
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

    # Prepare to calculate dimensions
    dummy_image = Image.new("RGB", (width, 10), "white")
    dummy_draw = ImageDraw.Draw(dummy_image)

    total_height = 10
    line_spacing = 5
    line_metrics = []

    # Measure each line's height and width
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

    # Create the actual label image
    total_height += 10
    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)

    y = 10
    for line, max_ascent, max_descent, line_height, line_width in line_metrics:
        x = 10 if alignment == "left" else (width - line_width) // 2 if alignment == "center" else width - line_width - 10
        for part in line:
            font = ImageFont.truetype(FONT_PATH, font_size)
            draw.text((x, y + max_ascent - font.getmetrics()[0]), part["text"], fill="black", font=font)
            x += dummy_draw.textbbox((0, 0), part["text"], font=font)[2] + 5
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