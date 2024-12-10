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

document.addEventListener("DOMContentLoaded", () => {
    // Dark Mode initial setzen
    setInitialMode();

    // Dark Mode Umschalter
    document.getElementById("dark-mode-toggle").addEventListener("click", () => {
        toggleDarkMode();
    });

    // Einstellungen speichern
    document.getElementById("settings-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const response = await fetch("/update_settings", {
            method: "POST",
            body: formData,
        });
        const result = await response.json();
        document.getElementById("result").innerText = result.message || result.error;
    });

    // Text drucken
    document.getElementById("text-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = document.getElementById("text").value;
        const labelSize = document.getElementById("label_size").value;
        const fontSize = document.getElementById("font_size").value;
        const alignment = document.getElementById("alignment").value; // Ausrichtung

        const jsonData = {
            text: text,
            settings: {
                label_size: labelSize,
                font_size: fontSize,
                alignment: alignment, // Neue Einstellung für die API
            },
        };

        const response = await fetch("/api/text/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(jsonData),
        });

        const result = await response.json();
        document.getElementById("result").innerText = result.message || result.error;
    });

    // JSON generieren und in Zwischenablage kopieren
    document.getElementById("generate-json").addEventListener("click", async () => {
        const text = document.getElementById("text").value;
        const labelSize = document.getElementById("label_size").value;
        const fontSize = document.getElementById("font_size").value;
        const alignment = document.getElementById("alignment").value; // Ausrichtung

        const jsonData = {
            text: text,
            settings: {
                label_size: labelSize,
                font_size: fontSize,
                alignment: alignment, // Neue Einstellung im JSON
            },
        };

        // JSON in die Zwischenablage kopieren
        try {
            await navigator.clipboard.writeText(JSON.stringify(jsonData, null, 2));
            document.getElementById("result").innerText = "JSON wurde in die Zwischenablage kopiert!";
        } catch (err) {
            document.getElementById("result").innerText = "Fehler beim Kopieren in die Zwischenablage.";
        }

        // JSON in der Konsole anzeigen
        console.log(jsonData);
    });
});