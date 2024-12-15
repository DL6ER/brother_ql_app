document.addEventListener("DOMContentLoaded", async () => {
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const languageDropdown = document.getElementById("language-dropdown");
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
    const textArea = document.getElementById("text");

    let translations = {};
    let currentLanguage = "en";

    const availableLanguages = {
        de: { name: "Deutsch", emoji: "🇨🇭" },
        en: { name: "English", emoji: "🇬🇧" },
        es: { name: "Español", emoji: "🇪🇸" },
        fr: { name: "Français", emoji: "🇫🇷" },
        nl: { name: "Nederlands", emoji: "🇳🇱" }
    };

    // Improved translation loading with error handling
    async function loadLocale(locale) {
        try {
            const response = await fetch(`/locales/${locale}.json`);
            if (!response.ok) {
                console.error(`Failed to load locale ${locale}`);
                return locale === 'en' ? {} : loadLocale('en');
            }
            return await response.json();
        } catch (error) {
            console.error(`Error loading locale ${locale}:`, error);
            return {};
        }
    }

    // Übersetzungen auf die Seite anwenden
    function applyTranslations() {
        document.querySelectorAll("[data-translate]").forEach((element) => {
            const key = element.getAttribute("data-translate");
            if (translations[key]) {
                if (element.tagName === "INPUT" && element.type === "placeholder") {
                    element.placeholder = translations[key];
                } else {
                    element.textContent = translations[key];
                }
            }
        });
    }

    // Enhanced language switching
    async function changeLanguage(newLanguage) {
        try {
            translations = await loadLocale(newLanguage);
            currentLanguage = newLanguage;
            localStorage.setItem("language", newLanguage);
            applyTranslations();
            updateLanguageDropdown();
        } catch (error) {
            console.error("Language change failed:", error);
        }
    }

    // Dropdown für Sprachauswahl aktualisieren
    function updateLanguageDropdown() {
        languageDropdown.innerHTML = '';
        
        Object.entries(availableLanguages).forEach(([code, { name, emoji }]) => {
            const option = document.createElement("option");
            option.value = code;
            option.innerHTML = `${emoji} ${name}`;
            option.selected = code === currentLanguage;
            languageDropdown.appendChild(option);
        });
    }

    // Dark Mode initialisieren
    function setInitialMode() {
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        const savedMode = localStorage.getItem("darkMode");
        const mode = savedMode || (prefersDark ? "dark" : "light");
        if (mode === "dark") {
            document.body.classList.add("dark-mode");
            darkModeToggle.textContent = "☀️";
        }
    }

    // Dark Mode umschalten
    function toggleDarkMode() {
        const isDarkMode = document.body.classList.toggle("dark-mode");
        localStorage.setItem("darkMode", isDarkMode ? "dark" : "light");
        darkModeToggle.textContent = isDarkMode ? "☀️" : "🌙";
    }

    // Schriftgröße und Textausrichtung dynamisch aktualisieren
    function updateTextAppearance() {
        const fontSize = document.getElementById("font_size").value;
        const alignment = document.getElementById("alignment").value;
        textArea.style.fontSize = `${fontSize}px`;
        textArea.style.textAlign = alignment;
    }

    // Einstellungen vom Server laden
    async function loadSettings() {
        try {
            const response = await fetch("/settings");
            if (!response.ok) throw new Error(`Settings load error: ${response.status}`);
            const settings = await response.json();
            document.getElementById("printer_uri").value = settings.printer_uri || "";
            document.getElementById("printer_model").value = settings.printer_model || "";
            document.getElementById("label_size").value = settings.label_size || "62";
            document.getElementById("font_size").value = settings.font_size || 50;
            document.getElementById("rotate").value = settings.rotate || "0";
            document.getElementById("threshold").value = settings.threshold || "70";
            document.getElementById("dither").value = settings.dither ? "true" : "false";
            document.getElementById("red").value = settings.red ? "true" : "false";
        } catch (error) {
            alert(translations.messages?.error_loading_settings || "Failed to load settings.");
        }
    }

    // Einstellungen speichern
    async function saveSettings() {
        const formData = new FormData();
        formData.append("printer_uri", document.getElementById("printer_uri").value);
        formData.append("printer_model", document.getElementById("printer_model").value);
        formData.append("label_size", document.getElementById("label_size").value);
        formData.append("font_size", document.getElementById("font_size").value);
        formData.append("rotate", document.getElementById("rotate").value);
        formData.append("threshold", document.getElementById("threshold").value);
        formData.append("dither", document.getElementById("dither").value);
        formData.append("red", document.getElementById("red").value);
        try {
            const response = await fetch("/update_settings", { method: "POST", body: formData });
            if (!response.ok) throw new Error(`Settings save error: ${response.status}`);
            alert(translations.messages?.settings_saved || "Settings saved successfully.");
        } catch (error) {
            alert(translations.messages?.error_saving_settings || "Failed to save settings.");
        }
    }

    // JSON generieren
    function generateJson() {
        const text = textArea.value.trim();
        if (!text) {
            alert(translations.messages?.error_no_text || "Please enter text.");
            return;
        }
        const jsonData = {
            text: text.replace(/\n/g, "<br>"),
            settings: {
                printer_uri: document.getElementById("printer_uri").value,
                printer_model: document.getElementById("printer_model").value,
                label_size: document.getElementById("label_size").value,
                font_size: document.getElementById("font_size").value,
                alignment: document.getElementById("alignment").value,
                rotate: document.getElementById("rotate").value,
                threshold: document.getElementById("threshold").value,
                dither: document.getElementById("dither").value === "true",
                red: document.getElementById("red").value === "true",
            },
        };
        resultContainer.textContent = JSON.stringify(jsonData, null, 2);
        resultSection.classList.remove("hidden");
    }

    // Einstellungen ein-/ausklappen
    settingsToggle.addEventListener("click", () => {
        settingsContent.classList.toggle("open");
        settingsContent.classList.toggle("hidden");
        const isOpen = settingsContent.classList.contains("open");
        settingsToggle.textContent = isOpen ? "➖" : "➕";
    });

    // Event-Listener hinzufügen
    generateJsonButton.addEventListener("click", generateJson);
    darkModeToggle.addEventListener("click", toggleDarkMode);
    languageDropdown.addEventListener("change", (e) => changeLanguage(e.target.value));
    saveSettingsButton.addEventListener("click", saveSettings);
    document.getElementById("font_size").addEventListener("input", updateTextAppearance);
    document.getElementById("alignment").addEventListener("change", updateTextAppearance);
    document.getElementById("text-form").addEventListener("reset", () => {
        resultSection.classList.add("hidden");
        resultContainer.innerText = "";
    });
    imageUpload.addEventListener("change", () => {
        const file = imageUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                imagePreview.classList.remove("hidden");
            };
            reader.readAsDataURL(file);
        } else {
            imagePreview.classList.add("hidden");
            previewImg.src = "";
        }
    });

    // Initialize language
    const browserLanguage = navigator.language.split("-")[0];
    const savedLanguage = localStorage.getItem("language");
    currentLanguage = savedLanguage || (availableLanguages[browserLanguage] ? browserLanguage : "en");

    // Initialize UI
    await changeLanguage(currentLanguage);
    updateLanguageDropdown();
    setInitialMode();
    await loadSettings();
});