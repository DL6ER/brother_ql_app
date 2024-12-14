document.addEventListener("DOMContentLoaded", () => {
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const settingsToggle = document.getElementById("settings-toggle");
    const settingsContent = document.getElementById("settings-content");
    const saveSettingsButton = document.getElementById("save-settings");
    const generateJsonButton = document.getElementById("generate-json");

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
        const text = document.getElementById("text").value;
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

    // JSON generieren und in die Zwischenablage kopieren
    async function generateJson() {
        const text = document.getElementById("text").value;
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
            await navigator.clipboard.writeText(JSON.stringify(jsonData, null, 2));
            alert("JSON wurde in die Zwischenablage kopiert!");
        } catch (error) {
            console.error("Fehler beim Kopieren in die Zwischenablage:", error);
            alert("Fehler beim Kopieren.");
        }
    }

    // Einstellungen ein- und ausklappen
    settingsToggle.addEventListener("click", () => {
        const isHidden = settingsContent.classList.contains("hidden");
        settingsContent.classList.toggle("hidden");

        // Text im Button aktualisieren
        settingsToggle.textContent = isHidden ? "➖" : "➕";
    });

    // Initial Dark Mode setzen
    setInitialMode();

    // Dark Mode Toggle
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
});