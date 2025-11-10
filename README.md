# Jango

A simple tool to create desktop entries for AppImage files on Linux with automatic icon extraction.

## Features

- Extracts AppImage contents to find icons
- Automatically creates desktop entries with proper icons
- Loading spinner while processing
- Automatic sudo privilege management

## Requirements

- Python 3.6+
- Linux operating system
- Sudo privileges

## Installation

### Clone the repository
```bash
git clone https://github.com/Dy1ngRat/jango.git
cd jango
```

### Install dependencies
```bash
pip install -r requirements.txt
```

## Building

To build the executable from source:

```bash
pyinstaller --onefile --name Jango --clean main.py
```

The executable will be created in the `dist/` directory.

## Usage

Run the built executable with sudo privileges:

```bash
sudo ./dist/Jango
```

The application will:
1. Request sudo privileges if not already running as root
2. Display a loading spinner while extracting the AppImage
3. Extract and copy the icon from the AppImage
4. Create a desktop entry in `/usr/share/applications/`

## How It Works

1. The script extracts the AppImage using `--appimage-extract`
2. Searches for the `.desktop` file inside the extracted contents
3. Finds and copies the icon to `/usr/share/icons/`
4. Creates a new desktop entry file for easy application access

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Repository

https://github.com/Dy1ngRat/jango