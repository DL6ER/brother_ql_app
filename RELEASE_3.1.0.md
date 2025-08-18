# Release 3.1.0 (2025-08-18)

## Overview

This release adds support for additional printer models and label types, enhancing the compatibility of the Brother QL Printer App with a wider range of Brother QL printers and label formats. The user interface has also been improved with dropdown selections for printer models and label types. Additionally, USB printer support has been added with automatic backend detection and better configuration documentation.

## New Features

### Additional Printer Models (contributed by DL6ER)
- Added support for QL-1100 (contributed by DL6ER)
- Added support for QL-1100NWB (contributed by DL6ER)
- Added support for QL-1115NWB (contributed by DL6ER)

### Additional Label Types (contributed by DL6ER)
- Added support for more label sizes and types (contributed by DL6ER):
  - 12+17 mm (endless)
  - 18 mm (endless)
  - 62red mm (red, endless)
  - 103 mm (endless)
  - 104 mm (endless)
  - 54x29 mm (die-cut)
  - 60x86 mm (die-cut)
  - 103x164 mm (die-cut)
  - pt12 (pTouch 12mm endless)
  - pt18 (pTouch 18mm endless)
  - pt24 (pTouch 24mm endless)
  - pt36 (pTouch 36mm endless)

### UI Improvements (contributed by DL6ER)
- Changed printer model input from text field to dropdown with all supported models
- Changed label size dropdown to include all supported label types with better descriptions
- Renamed "Label Size" to "Label Type" for clarity

### Library Updates (contributed by DL6ER)
- Updated from brother-ql 0.9.4 to brother-ql-inventree 1.3
  - This fork provides better support for newer printer models and label types
  - Includes improved detection of media and commands to list and configure settings

### USB Printer Support (contributed by DL6ER)
- Added automatic backend detection to properly handle both USB and network printers
- Improved printer service to use the appropriate backend based on the printer URI
- Disabled keep-alive functionality for USB printers where it's not needed
- Updated documentation with clear instructions for configuring USB-attached printers
- Fixed port mapping in docker-compose.yml from 5055:5000 to 5000:5000 for easier access

## Compatibility

This release is compatible with all previously supported Brother QL printer models and adds support for the QL-1100 series. All existing API endpoints and functionality continue to work as before.

## Installation

### Docker (Recommended)
```bash
docker pull ghcr.io/dodoooh/brother_ql_app:3.1.0
docker run -p 5000:5000 -v /path/to/data:/app/data --device=/dev/usb/lp0 ghcr.io/dodoooh/brother_ql_app:3.1.0
```

### Manual Installation
```bash
git clone https://github.com/dodoooh/brother_ql_app.git
cd brother_ql_app
pip install -r requirements.txt
./run_app.sh
```