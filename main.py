import tkinter as tk
from tkinter import filedialog
import os
import sys
import subprocess
import tempfile
import shutil
import threading
import time
import shutil

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear')

def print_logo():
    """Display the Jango ASCII logo"""
    clear_screen()
    lines = [
    "        __                       ",
    "       / /___ _____  ____ _____  ",
    "  __  / / __ `/ __ \/ __ `/ __ \ ",
    " / /_/ / /_/ / / / / /_/ / /_/ / ",
    " \____/\__,_/_/ /_/\__, /\____/  ",
    "                  /____/         "
    ]
    
    terminal_width = shutil.get_terminal_size().columns
    
    print("\n")
    for line in lines:
        print(line.center(terminal_width))
    print("\n")


def loading_spinner(stop_event, message="Processing"):
    """Display an animated loading spinner"""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\r{message}... {spinner[idx % len(spinner)]}')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(message) + 10) + '\r')
    sys.stdout.flush()


def check_sudo():
    """Check for sudo privileges and request them if not present"""
    if os.geteuid() != 0:
        print("This script requires sudo privileges.")
        print("Requesting sudo access...\n")
        args = ['sudo', sys.executable] + sys.argv
        os.execvp('sudo', args)
    else:
        print("Sudo privileges detected.\n")


def select_appimage():
    """Open file dialog to select an AppImage file"""
    root = tk.Tk()
    root.geometry("1200x800")
    root.withdraw()

    # Get the actual user's home directory (even when running with sudo)
    user = os.environ.get("SUDO_USER") or os.environ.get("USER")
    home_dir = os.path.expanduser(f"~{user}") if user else os.path.expanduser("~")

    file_path = filedialog.askopenfilename(
        title="Select an AppImage file",
        initialdir=home_dir,
        filetypes=[("AppImage files", "*.AppImage *.appimage"), ("All files", "*.*")]
    )

    if file_path:
        print(f"Selected file: {file_path}\n")
        return file_path
    else:
        print("No file selected. Exiting...")
        sys.exit(0)


def extract_icon_from_appimage(file_path, app_name, tmpdir):
    """Extract icon from AppImage and copy it to system location"""
    icon_path = ""
    
    # Make AppImage executable
    os.chmod(file_path, 0o755)
    
    # Extract the AppImage
    subprocess.run(
        [file_path, '--appimage-extract'],
        cwd=tmpdir,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    squashfs_root = os.path.join(tmpdir, 'squashfs-root')
    
    if not os.path.exists(squashfs_root):
        return None
    
    # Find the .desktop file
    desktop_file = None
    for root, dirs, files in os.walk(squashfs_root):
        for file in files:
            if file.endswith('.desktop'):
                desktop_file = os.path.join(root, file)
                break
        if desktop_file:
            break
    
    if not desktop_file or not os.path.exists(desktop_file):
        return None
    
    # Parse the .desktop file to find the icon
    with open(desktop_file, 'r') as f:
        for line in f:
            if line.startswith('Icon='):
                icon_name = line.split('=', 1)[1].strip()
                
                # Search for icon file with different extensions
                for ext in ['.png', '.svg', '.xpm', '.ico', '']:
                    # Try direct path
                    icon_file = os.path.join(squashfs_root, icon_name + ext)
                    if os.path.exists(icon_file):
                        icon_dest = f'/usr/share/icons/{app_name}{ext}'
                        shutil.copy2(icon_file, icon_dest)
                        return icon_dest
                    
                    # Try common icon directories
                    for search_dir in ['usr/share/icons', 'usr/share/pixmaps', '.']:
                        icon_search = os.path.join(squashfs_root, search_dir, icon_name + ext)
                        if os.path.exists(icon_search):
                            icon_dest = f'/usr/share/icons/{app_name}{ext}'
                            shutil.copy2(icon_search, icon_dest)
                            return icon_dest
                break
    
    return None


def create_desktop_entry(file_path, app_name):
    """Create a desktop entry for the AppImage"""
    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(
        target=loading_spinner,
        args=(stop_spinner, "Extracting AppImage")
    )
    spinner_thread.start()

    try:
        # Extract icon from AppImage
        with tempfile.TemporaryDirectory() as tmpdir:
            icon_path = extract_icon_from_appimage(file_path, app_name, tmpdir)
        
        # Fallback to AppImage path if no icon found
        if not icon_path:
            icon_path = file_path
        
        # Write the .desktop file
        desktop_path = f'/usr/share/applications/{app_name}.desktop'
        with open(desktop_path, 'w') as f:
            f.write("[Desktop Entry]\n")
            f.write(f"Name={app_name}\n")
            f.write("Comment=Installed via Jango\n")
            f.write(f"Exec={file_path} %U\n")
            f.write(f"Icon={icon_path}\n")
            f.write("Terminal=false\n")
            f.write("Type=Application\n")
            f.write("Categories=Utility;Application;\n")
        
        print(f"\n✓ Desktop file created: {desktop_path}")
        if icon_path:
            print(f"✓ Icon: {icon_path}")
        print(f"\n{app_name} has been installed successfully!\n")
        
    except PermissionError:
        print("\n✗ Permission denied. Try running with sudo.")
    except subprocess.TimeoutExpired:
        print("\n✗ Timeout while extracting AppImage.")
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
    finally:
        stop_spinner.set()
        spinner_thread.join()


def main():
    """Main application flow"""
    #monitor_terminal_resize()
    print_logo()
    check_sudo()
    print_logo()
    
    file_path = select_appimage()
    app_name = input("Enter application name: ").strip()
    
    if not app_name:
        print("Application name cannot be empty. Exiting...")
        sys.exit(1)
    
    create_desktop_entry(file_path, app_name)


if __name__ == "__main__":
    main()