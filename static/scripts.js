document.addEventListener("DOMContentLoaded", () => {
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const settingsToggle = document.getElementById("settings-toggle");
    const settingsContent = document.getElementById("settings-content");
    const saveSettingsButton = document.getElementById("save-settings");
    const generateJsonButton = document.getElementById("generate-json");
    const copyToClipboardButton = document.getElementById("copy-to-clipboard");
    const resultSection = document.getElementById("result-section");
    const resultContainer = document.getElementById("result");
    const imageForm = document.getElementById("image-form");
    const imageUpload = document.getElementById("image-upload");
    const imagePreview = document.getElementById("image-preview");
    const previewImg = document.getElementById("preview-img");

    // Initial Dark Mode setzen basierend auf Systemeinstellungen oder localStorage
    function setInitialMode() {
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        const savedMode = localStorage.getItem("darkMode");
        const mode = savedMode || (prefersDark ? "dark" : "light");
        if (mode === "dark") {
            document.body.classList.add("dark-mode");
            darkModeToggle.textContent = "☀️";
        }
    }

    // Dark Mode umschalten und speichern
    function toggleDarkMode() {
        const isDarkMode = document.body.classList.toggle("dark-mode");
        localStorage.setItem("darkMode", isDarkMode);
        darkModeToggle.textContent = isDarkMode ? "☀️" : "🌙";
    }

    // Einstellungen aus dem Backend laden und in die Formulare einfügen
    async function loadSettings() {
        try {
            const response = await fetch("/settings");
            const settings = await response.json();

            // Druckerkonfiguration
            document.getElementById("printer_uri").value = settings.printer_uri || "";
            document.getElementById("printer_model").value = settings.printer_model || "";
            document.getElementById("label_size").value = settings.label_size || "62";

            // Druckeinstellungen
            document.getElementById("font_size").value = settings.font_size || 50;
            document.getElementById("rotate").value = settings.rotate || "0";
            document.getElementById("threshold").value = settings.threshold || "70";
            document.getElementById("dither").value = settings.dither ? "true" : "false";
            document.getElementById("red").value = settings.red ? "true" : "false";
        } catch (error) {
            console.error("Fehler beim Laden der Einstellungen:", error);
        }
    }

    // Einstellungen speichern
    async function saveSettings() {
        const formData = new FormData();

        // Druckerkonfiguration
        formData.append("printer_uri", document.getElementById("printer_uri").value);
        formData.append("printer_model", document.getElementById("printer_model").value);
        formData.append("label_size", document.getElementById("label_size").value);

        // Druckeinstellungen
        formData.append("font_size", document.getElementById("font_size").value);
        formData.append("rotate", document.getElementById("rotate").value);
        formData.append("threshold", document.getElementById("threshold").value);
        formData.append("dither", document.getElementById("dither").value);
        formData.append("red", document.getElementById("red").value);

        try {
            const response = await fetch("/update_settings", {
                method: "POST",
                body: formData,
            });
            const result = await response.json();
            alert(result.message || "Einstellungen gespeichert!");
        } catch (error) {
            console.error("Fehler beim Speichern der Einstellungen:", error);
            alert("Fehler beim Speichern der Einstellungen.");
        }
    }

    // Schriftgröße und Ausrichtung live anwenden
    function updateTextAppearance() {
        const textArea = document.getElementById("text");
        const fontSize = document.getElementById("font_size").value;
        const alignment = document.getElementById("alignment").value;

        textArea.style.fontSize = `${fontSize}px`;
        textArea.style.textAlign = alignment;
    }

    // Text drucken
    async function printText(event) {
        event.preventDefault(); // Verhindert das Neuladen der Seite
        const textArea = document.getElementById("text");
        const text = textArea.value.replace(/\n/g, "<br>"); // Ersetzt Zeilenumbrüche durch <br>
        const fontSize = document.getElementById("font_size").value;
        const alignment = document.getElementById("alignment").value;

        const jsonData = {
            text: text,
            settings: {
                font_size: fontSize,
                alignment: alignment,
            },
        };

        try {
            const response = await fetch("/api/text/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(jsonData),
            });
            const result = await response.json();
            alert(result.message || "Text wurde gedruckt!");
        } catch (error) {
            console.error("Fehler beim Drucken des Textes:", error);
            alert("Fehler beim Drucken.");
        }
    }

    // JSON generieren und anzeigen
    function generateJson() {
        const textArea = document.getElementById("text");
        const text = textArea.value.replace(/\n/g, "<br>"); // Zeilenumbrüche in <br> umwandeln
        const fontSize = document.getElementById("font_size").value;
        const alignment = document.getElementById("alignment").value;

        const jsonData = {
            text: text,
            settings: {
                font_size: fontSize,
                alignment: alignment,
            },
        };

        // JSON als String formatieren
        const jsonString = JSON.stringify(jsonData, null, 2);

        // JSON im Ergebnisbereich anzeigen
        resultContainer.innerText = jsonString;
        resultContainer.style.whiteSpace = "pre-wrap"; // Zeilenumbrüche sichtbar machen
        resultSection.classList.remove("hidden"); // Ergebnisbereich sichtbar machen
    }

    // JSON in die Zwischenablage kopieren
    function copyToClipboard() {
        const jsonString = resultContainer.innerText;
        navigator.clipboard.writeText(jsonString)
            .then(() => alert("JSON wurde in die Zwischenablage kopiert!"))
            .catch((error) => alert("Fehler beim Kopieren in die Zwischenablage."));
    }

    // Bildvorschau
    imageUpload.addEventListener("change", () => {
        const file = imageUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                imagePreview.classList.remove("hidden");
            };
            reader.readAsDataURL(file);
        }
    });

    // Bild drucken
    imageForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData();
        const file = imageUpload.files[0];
        if (!file) {
            alert("Bitte wählen Sie ein Bild aus!");
            return;
        }

        formData.append("image", file);

        try {
            const response = await fetch("/api/image/", {
                method: "POST",
                body: formData,
            });
            const result = await response.json();
            alert(result.message || "Bild wurde gedruckt!");
        } catch (error) {
            console.error("Fehler beim Drucken des Bildes:", error);
            alert("Fehler beim Drucken.");
        }
    });

    // Einstellungen ein- und ausklappen
    settingsToggle.addEventListener("click", () => {
        const isHidden = settingsContent.classList.contains("hidden");
        settingsContent.classList.toggle("hidden");

        // Text im Button aktualisieren
        settingsToggle.textContent = isHidden ? "➕" : "➖";
    });

    // Initial Dark Mode setzen
    setInitialMode();
    darkModeToggle.addEventListener("click", toggleDarkMode);

    // Einstellungen laden
    loadSettings();

    // Einstellungen speichern
    saveSettingsButton.addEventListener("click", saveSettings);

    // Schriftgröße und Ausrichtung live anwenden
    document.getElementById("font_size").addEventListener("input", updateTextAppearance);
    document.getElementById("alignment").addEventListener("change", updateTextAppearance);

    // Text drucken
    document.getElementById("text-form").addEventListener("submit", printText);

    // JSON generieren
    generateJsonButton.addEventListener("click", generateJson);

    // JSON in die Zwischenablage kopieren
    copyToClipboardButton.addEventListener("click", copyToClipboard);
});