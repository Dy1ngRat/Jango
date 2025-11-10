import tkinter as tk
from tkinter import filedialog, ttk
import os
import sys
import subprocess
import tempfile
import shutil
import threading
import time

def logo():
    os.system('clear');
    print("")
    print("")
    print("")
    print("░░░░░██╗░█████╗░███╗░░██╗░██████╗░░█████╗░")
    print("░░░░░██║██╔══██╗████╗░██║██╔════╝░██╔══██╗")
    print("░░░░░██║███████║██╔██╗██║██║░░██╗░██║░░██║")
    print("██╗░░██║██╔══██║██║╚████║██║░░╚██╗██║░░██║")
    print("╚█████╔╝██║░░██║██║░╚███║╚██████╔╝╚█████╔╝")
    print("░╚════╝░╚═╝░░╚═╝╚═╝░░╚══╝░╚═════╝░░╚════╝░")
    print("")
    print("")
    print("")    

def loading_spinner(stop_event, message="Processing"):
    """Display a loading spinner animation"""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\r{message}... {spinner[idx % len(spinner)]}')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(message) + 10) + '\r')
    sys.stdout.flush()

def needs_sudo():
    """Check for sudo privileges and request them if not present"""
    if os.geteuid() != 0:
        print("This script requires sudo privileges.")
        print("Requesting sudo access...")
        # Re-run the script with sudo
        args = ['sudo', sys.executable] + sys.argv
        os.execvp('sudo', args)
    else:
        print("Sudo privileges detected.")

def select_file():
    root = tk.Tk()
    root.geometry("1200x800+2000+100") 
    root.withdraw()  # Hide the root window

    # Figure out the actual user's home directory
    user = os.environ.get("SUDO_USER") or os.environ.get("USER")
    home_dir = os.path.expanduser(f"~{user}") if user else os.path.expanduser("~")

    global file_path
    file_path = filedialog.askopenfilename(
        title="Select an AppImage file",
        initialdir=home_dir,
        filetypes=[("AppImage files", "*.appimage"), ("Other types", "*.*")]
    )

    if file_path:
        print(f"Selected file: {file_path}")
    else:
        print("No file selected.")

def write_desktop(file_path, name):

    # Start loading spinner
    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=loading_spinner, args=(stop_spinner, "Extracting AppImage"))
    spinner_thread.start()

    try:
        icon_path = ""
        
        # Method 1: Extract icon from AppImage
        # AppImages can be mounted to extract their contents
        with tempfile.TemporaryDirectory() as tmpdir:
            # Make AppImage executable
            os.chmod(file_path, 0o755)
            
            # Extract the AppImage
            extract_result = subprocess.run(
                [file_path, '--appimage-extract'],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            squashfs_root = os.path.join(tmpdir, 'squashfs-root')
            
            if os.path.exists(squashfs_root):
                # Look for .desktop file in extracted contents
                desktop_file = None
                for root, dirs, files in os.walk(squashfs_root):
                    for file in files:
                        if file.endswith('.desktop'):
                            desktop_file = os.path.join(root, file)
                            break
                    if desktop_file:
                        break
                
                # Parse the .desktop file to find the icon
                if desktop_file and os.path.exists(desktop_file):
                    with open(desktop_file, 'r') as f:
                        for line in f:
                            if line.startswith('Icon='):
                                icon_name = line.split('=', 1)[1].strip()
                                
                                # Look for the icon file
                                for ext in ['.png', '.svg', '.xpm', '.ico']:
                                    icon_file = os.path.join(squashfs_root, icon_name + ext)
                                    if os.path.exists(icon_file):
                                        # Copy icon to a permanent location
                                        icon_dest = f'/usr/share/icons/{name}{ext}'
                                        shutil.copy2(icon_file, icon_dest)
                                        icon_path = icon_dest
                                        break
                                    
                                    # Try finding icon in common locations
                                    for search_dir in ['usr/share/icons', 'usr/share/pixmaps', '.']:
                                        icon_search = os.path.join(squashfs_root, search_dir, icon_name + ext)
                                        if os.path.exists(icon_search):
                                            icon_dest = f'/usr/share/icons/{name}{ext}'
                                            shutil.copy2(icon_search, icon_dest)
                                            icon_path = icon_dest
                                            break
                                    
                                    if icon_path:
                                        break
                                break
        
        # If no icon found, use a default or the AppImage path itself
        if not icon_path:
            icon_path = file_path  # Some systems can extract icon from AppImage directly
        
        # Write the .desktop file
        desktop_path = f'/usr/share/applications/{name}.desktop'
        with open(desktop_path, 'w') as file:
            file.write("[Desktop Entry]\n")
            file.write(f"Name={name}\n")
            file.write("Comment=This is my application\n")
            file.write(f"Exec={file_path} %U\n")
            file.write(f"Icon={icon_path}\n")
            file.write("Terminal=false\n")
            file.write("Type=Application\n")
            file.write("Categories=Utility;Application;\n")
        
        print(f"\nDesktop file written successfully to {desktop_path}")
        if icon_path:
            print(f"Icon: {icon_path}")
        
    except PermissionError:
        print("Permission denied. Try running with sudo.")
    except subprocess.TimeoutExpired:
        print("Timeout while extracting AppImage.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Stop the loading spinner
        stop_spinner.set()
        spinner_thread.join()

if __name__ == "__main__":
    logo()

    needs_sudo()

    logo()

    select_file()
    
    if hasattr(file_path, 'decode'): # encoding shit
        file_path = file_path.decode('utf-8')
    
    name = input("Enter name of program: ")
    write_desktop(file_path, name)