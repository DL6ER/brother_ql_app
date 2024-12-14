// Initial Dark Mode setzen basierend auf den Systemeinstellungen
function setInitialMode() {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const savedMode = localStorage.getItem("darkMode");
    const mode = savedMode || (prefersDark ? "dark" : "light");
    document.body.classList.add(mode + "-mode");
}

// Dark Mode umschalten
function toggleDarkMode() {
    if (document.body.classList.contains("dark-mode")) {
        document.body.classList.remove("dark-mode");
        document.body.classList.add("light-mode");
        localStorage.setItem("darkMode", "light");
    } else {
        document.body.classList.remove("light-mode");
        document.body.classList.add("dark-mode");
        localStorage.setItem("darkMode", "dark");
    }
}

// Einstellungen aus dem Backend laden und in die Formulare einfügen
async function loadSettings() {
    try {
        const response = await fetch("/settings");
        const settings = await response.json();

        // Druckerkonfiguration
        document.getElementById("printer_uri").value = settings.printer_uri;
        document.getElementById("printer_model").value = settings.printer_model;
        document.getElementById("label_size").value = settings.label_size;

        // Druckeinstellungen
        document.getElementById("rotate").value = settings.rotate;
        document.getElementById("threshold").value = settings.threshold;
        document.getElementById("dither").value = settings.dither.toString();
        document.getElementById("compress").value = settings.compress.toString();
        document.getElementById("red").value = settings.red.toString();
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
    formData.append("compress", document.getElementById("compress").value);
    formData.append("red", document.getElementById("red").value);

    try {
        const response = await fetch("/update_settings", {
            method: "POST",
            body: formData,
        });
        const result = await response.json();
        document.getElementById("result").innerText = result.message || "Einstellungen gespeichert!";
    } catch (error) {
        console.error("Fehler beim Speichern der Einstellungen:", error);
        document.getElementById("result").innerText = "Fehler beim Speichern der Einstellungen.";
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
async function printText() {
    const textArea = document.getElementById("text");
    const text = textArea.value;

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
        document.getElementById("result").innerText = result.message || "Text wurde gedruckt!";
    } catch (error) {
        console.error("Fehler beim Drucken des Textes:", error);
        document.getElementById("result").innerText = "Fehler beim Drucken.";
    }
}

// JSON generieren und in Zwischenablage kopieren
async function generateJson() {
    const textArea = document.getElementById("text");
    const text = textArea.value;

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
        document.getElementById("result").innerText = "JSON wurde in die Zwischenablage kopiert!";
    } catch (error) {
        console.error("Fehler beim Kopieren in die Zwischenablage:", error);
        document.getElementById("result").innerText = "Fehler beim Kopieren.";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const settingsToggle = document.getElementById("settings-toggle");
    const settingsContent = document.getElementById("settings-content");

    // Check if Dark Mode is enabled in localStorage
    const isDarkMode = localStorage.getItem("darkMode") === "true";

    // Apply the initial mode
    if (isDarkMode) {
        document.body.classList.add("dark-mode");
        darkModeToggle.textContent = "☀️"; // Sun icon for light mode toggle
    }

    // Toggle Dark Mode
    darkModeToggle.addEventListener("click", () => {
        const isCurrentlyDark = document.body.classList.toggle("dark-mode");
        localStorage.setItem("darkMode", isCurrentlyDark);

        // Change the toggle icon
        darkModeToggle.textContent = isCurrentlyDark ? "☀️" : "🌙";
    });

    // Toggle Einstellungen ein- und ausklappen
    settingsToggle.addEventListener("click", () => {
        const isHidden = settingsContent.classList.contains("hidden");
        settingsContent.classList.toggle("hidden");

        // Toggle Text im Button
        settingsToggle.textContent = isHidden ? "➖" : "➕";
    });
});