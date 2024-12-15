# Brother QL Printer App
![Docker Pulls](https://img.shields.io/docker/pulls/dodoooh/brother_ql_app)
![GitHub Release](https://img.shields.io/github/v/release/dodoooh/brother_ql_app)
![GitHub Issues](https://img.shields.io/github/issues/dodoooh/brother_ql_app)
<br>

A modern web application to control Brother QL printers, enabling customizable text and image printing with ease.

<br>

## 🚀 Features

- **🖋 Text Printing**: Easily print HTML-formatted text, such as `<b>Bold</b>` or `<span color="red">Red</span>`, for precise label designs.

- **🖼 Image Printing**: Upload and print images effortlessly to create visually appealing labels.

- **⚙️ Custom Settings**: Fine-tune font size, label size, and text alignment to match your specific needs.

- **🔗 API Support**: Seamlessly integrate with external systems like Home Assistant ❤️ via a JSON-based API.

- **🖨 Multiple Printer Support**: Control multiple printers simultaneously via the API, enabling the use of different label sizes and configurations for various tasks.

- **📱 Responsive Design**: Enjoy a smooth user experience on desktop, tablet, and smartphone devices.

- **🌍 Multilanguage Support**: Available in multiple languages! Contribute by adding new translations or improving existing ones via a pull request. *(Corrections or additions in any language are greatly appreciated!)*

---

## 🐳 Installation with Docker

### Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
services:
  brother_ql:
    image: dodoooh/brother_ql_app:latest
    container_name: brother_ql_service
    ports:
      - \"5000:5000\"
    restart: unless-stopped
    volumes:
      - ./settings.json:/app/settings.json
```

Start the service:

```bash
docker-compose up -d
```

### Using Docker Run

Run the application with:

```bash
docker run -d \\
  -p 5000:5000 \\
  --name brother_ql_service \\
  dodoooh/brother_ql_app:latest
```

### Access the Application

Open your browser and navigate to [http://localhost:5000](http://localhost:5000)

---

## 📔 API Documentation

Here are all the possible settings you can use:

| **Setting**      | **Type**    | **Description**                                                                 | **Optional**                              |
|------------------|-------------|---------------------------------------------------------------------------------|------------------------------------------|
| **printer_uri**  | String      | **Printer URI** (e.g., `"tcp://192.168.1.100"`)                                 | **No**, if not configured globally       |
| **printer_model**| String      | **Printer Model** (e.g., `"QL-800"`)                                            | **No**, if not configured globally       |
| **label_size**   | String      | **Label Size** (e.g., `"62"`)                                                   | **No**, if not configured globally       |
| **font_size**    | Integer     | Font size                                                                       | Yes                                      |
| **alignment**    | String      | Text alignment (`"left"`, `"center"`, `"right"`)                               | Yes                                      |
| **rotate**       | Integer     | Rotation angle in degrees                                                       | Yes                                      |
| **threshold**    | Float       | Threshold value for image processing                                            | Yes                                      |
| **dither**       | Boolean     | Enable dithering (`true` or `false`)                                            | Yes                                      |
| **compress**     | Boolean     | Enable compression (`true` or `false`)                                          | Yes                                      |
| **red**          | Boolean     | Use red ink (`true` or `false`)                                                 | Yes                                      |

---

**Note**: The settings `printer_uri`, `printer_model`, and `label_size` are **required** if not configured globally via `settings.json`. All other settings are optional and will override the global settings when specified.

## 📤 Example API Usage

### **Text Printing**

Use the `/api/text/` endpoint to print formatted text.

```python
import requests

url = 'http://localhost:5000/api/text/'
payload = {
    "text": "Hello World!\nThis is a test print.",
    "settings": {
        "printer_uri": "tcp://192.168.1.100",   # optional, if not globally configured
        "printer_model": "QL-800",              # optional, if not globally configured
        "label_size": "62",                     # optional, if not globally configured
        "font_size": 40,                        # optional
        "alignment": "center",                  # optional
        "rotate": 90,                           # optional
        "threshold": 80.0,                      # optional
        "dither": True,                         # optional
        "compress": True,                       # optional
        "red": False                            # optional
    }
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.json())
```

---

### **Image Printing**

Use the `/api/image/` endpoint to upload and print an image.

```python
import requests
import json

url = 'http://localhost:5000/api/image/'
image_path = '/path/to/image.jpg'  # Replace with the path to your image
settings = {
    "printer_uri": "tcp://192.168.1.100",   # optional, if not globally configured
    "printer_model": "QL-800",              # optional, if not globally configured
    "label_size": "62",                     # optional, if not globally configured
    "rotate": 180,                          # optional
    "threshold": 75.0,                      # optional
    "dither": False,                        # optional
    "compress": False,                      # optional
    "red": True                             # optional
}

with open(image_path, 'rb') as img_file:
    files = {
        'image': img_file
    }
    data = {
        'settings': json.dumps(settings)  # optional
    }
    response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.json())
```

---

**Note**: Replace the `printer_uri`, `printer_model`, and other optional parameters as needed to suit your configuration. The endpoints provide JSON responses with the status of the operation.

---

## 📝 License

This project is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International Public License](LICENSE).

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for more information.

---

**Enjoy using the Brother QL Printer App! If you encounter any issues or have suggestions for improvements, feel free to reach out through our [GitHub Issues](https://github.com/dodoooh/brother_ql_app/issues).**