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

        // Allgemeine Einstellungen
        document.getElementById("label_size").value = settings.label_size;
        document.getElementById("font_size").value = settings.font_size;
        document.getElementById("alignment").value = settings.alignment;

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
    
    // Allgemeine Einstellungen
    formData.append("label_size", document.getElementById("label_size").value);
    formData.append("font_size", document.getElementById("font_size").value);
    formData.append("alignment", document.getElementById("alignment").value);

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
        document.getElementById("result").innerText = result.message || result.error;
    } catch (error) {
        console.error("Fehler beim Speichern der Einstellungen:", error);
        document.getElementById("result").innerText = "Fehler beim Speichern der Einstellungen.";
    }
}

// Text drucken
async function printText() {
    const text = document.getElementById("text").value;

    // Aktuelle Einstellungen holen
    const labelSize = document.getElementById("label_size").value;
    const fontSize = document.getElementById("font_size").value;
    const alignment = document.getElementById("alignment").value;

    const rotate = document.getElementById("rotate").value;
    const threshold = document.getElementById("threshold").value;
    const dither = document.getElementById("dither").value === "true";
    const compress = document.getElementById("compress").value === "true";
    const red = document.getElementById("red").value === "true";

    const jsonData = {
        text: text,
        settings: {
            label_size: labelSize,
            font_size: fontSize,
            alignment: alignment,
            rotate: rotate,
            threshold: parseFloat(threshold),
            dither: dither,
            compress: compress,
            red: red,
        },
    };

    try {
        const response = await fetch("/api/text/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(jsonData),
        });
        const result = await response.json();
        document.getElementById("result").innerText = result.message || result.error;
    } catch (error) {
        console.error("Fehler beim Drucken des Textes:", error);
        document.getElementById("result").innerText = "Fehler beim Drucken.";
    }
}

// JSON generieren und in Zwischenablage kopieren
async function generateJson() {
    const text = document.getElementById("text").value;

    // Aktuelle Einstellungen holen
    const labelSize = document.getElementById("label_size").value;
    const fontSize = document.getElementById("font_size").value;
    const alignment = document.getElementById("alignment").value;

    const rotate = document.getElementById("rotate").value;
    const threshold = document.getElementById("threshold").value;
    const dither = document.getElementById("dither").value === "true";
    const compress = document.getElementById("compress").value === "true";
    const red = document.getElementById("red").value === "true";

    const jsonData = {
        text: text,
        settings: {
            label_size: labelSize,
            font_size: fontSize,
            alignment: alignment,
            rotate: rotate,
            threshold: parseFloat(threshold),
            dither: dither,
            compress: compress,
            red: red,
        },
    };

    // JSON in die Zwischenablage kopieren
    try {
        await navigator.clipboard.writeText(JSON.stringify(jsonData, null, 2));
        document.getElementById("result").innerText = "JSON wurde in die Zwischenablage kopiert!";
    } catch (err) {
        console.error("Fehler beim Kopieren in die Zwischenablage:", err);
        document.getElementById("result").innerText = "Fehler beim Kopieren in die Zwischenablage.";
    }
}

// Event-Listener
document.addEventListener("DOMContentLoaded", () => {
    // Dark Mode initial setzen
    setInitialMode();

    // Dark Mode Umschalter
    document.getElementById("dark-mode-toggle").addEventListener("click", () => {
        toggleDarkMode();
    });

    // Einstellungen laden
    loadSettings();

    // Einstellungen speichern
    document.getElementById("save-settings").addEventListener("click", (e) => {
        e.preventDefault();
        saveSettings();
    });

    // Text drucken
    document.getElementById("text-form").addEventListener("submit", (e) => {
        e.preventDefault();
        printText();
    });

    // JSON generieren
    document.getElementById("generate-json").addEventListener("click", () => {
        generateJson();
    });
});