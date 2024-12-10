# Brother QL Printer App
![Docker Pulls](https://img.shields.io/docker/pulls/dodoooh/brother_ql_app)
![GitHub Release](https://img.shields.io/github/v/release/dodoooh/brother_ql_app)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/dodoooh/brother_ql_app)

![GitHub License](https://img.shields.io/github/license/dodoooh/brother_ql_app)


<br><br>
A modern web application to control Brother QL printers, allowing text and image printing with full customization options.
</div>
<br><br>

## 🍓 Features

- **Text Printing**: Print HTML-formatted text (e.g., `<b>Bold</b>` or `<span color=\"red\">Red</span>`).
- **Image Printing**: Upload and print images. (in development)
- **Custom Settings**: Adjust font size, label size, and text alignment.
- **API Support**: JSON-based API for integration with external systems.
- **Responsive Design**: Works seamlessly on desktop, tablet, and smartphone.

---

## 🚀 Installation with Docker

### Docker Compose
```yaml
services:
  brother_ql:
    image: dodoooh/brother_ql_app:latest
    container_name: brother_ql_service
    environment:
      - PRINTER_URI=tcp://192.168.1.20
      - PRINTER_MODEL=QL-800
      - LABEL_SIZE=62
    ports:
      - 5000:5000
```

### Docker Run
```bash
docker run -p 5000:5000 --env PRINTER_URI=tcp://192.168.1.20 --env PRINTER_MODEL=QL-800 --env LABEL_SIZE=62 dodoooh/brother_ql_app:latest
```

### Access the application
- Open your browser and navigate to [http://localhost:5000](http://localhost:5000)



3. **Access the application in your browser:**
   - URL: [http://localhost:5000](http://localhost:5000)

---

## 📔 API Documentation

### **POST /api/text/**
Prints text on a label.

- **Request Body (JSON):**
  ```json
  {
    "text": "This is a  <b>BOLD</b> Text.<br>The next word is <span color=\"red\">red</span>.",
    "settings": {
        "label_size": "62",
        "font_size": "10",
        "alignment": "center"
    }
}
  ```