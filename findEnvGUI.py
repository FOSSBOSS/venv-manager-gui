#!/usr/bin/env python3
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil
import shlex
import json

# sudo apt install python3-full


# Global dictionary to hold environment name -> path
environments = {}

# Log file to store discovered virtual environments (in JSON format)
LOG_FILE = os.path.join(os.getcwd(), "venv_log.json")

# Define the base directory to search for virtual environments (customize as needed)
DEFAULT_ENV_DIR = os.path.expanduser("~/virtualenvs")

def is_valid_env(env_path):
    """Check if a directory looks like a virtual environment by verifying if an activation script exists."""
    if sys.platform.startswith("win"):
        activate = os.path.join(env_path, "Scripts", "activate.bat")
    else:
        activate = os.path.join(env_path, "bin", "activate")
    return os.path.isfile(activate)

def scan_env_directory(directory):
    """Scan a directory for valid virtual environments."""
    found = {}
    if not os.path.isdir(directory):
        return found
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path) and is_valid_env(full_path):
            found[entry] = full_path
    return found

def search_system_for_envs():
    """Search the system using `locate` for pyvenv.cfg files to locate virtual environments."""
    if shutil.which("locate") is None:
        messagebox.showerror("Error", "The 'locate' command was not found in your PATH. Please ensure it is installed and available.")
        return {}

    try:
        output = subprocess.check_output(["locate", "pyvenv.cfg"], universal_newlines=True)
    except Exception as e:
        messagebox.showerror("Error", f"Error executing locate command: {e}")
        return {}

    found_envs = {}
    for line in output.strip().splitlines():
        cfg_path = line.strip()
        # The virtual environment's root is the directory containing pyvenv.cfg
        env_dir = os.path.dirname(cfg_path)
        if is_valid_env(env_dir):
            env_name = os.path.basename(env_dir)
            found_envs[env_name] = env_dir
    return found_envs

def launch_terminal_with_env(env_path):
    """
    Launch a new terminal window (Linux only) that changes directory into the virtual environment folder
    and echoes a message instructing the user to manually activate the environment.
    """
    if not os.path.isdir(env_path):
        messagebox.showerror("Error", f"Environment folder not found: {env_path}")
        return

    # Build a bash command that:
    # 1. Changes directory to the virtual environment folder.
    # 2. Echoes a reminder message.
    # 3. Starts an interactive bash shell.
    bash_command = (
        f'cd {shlex.quote(env_path)} && '
        f'echo "To activate the virtual environment, run: source ./bin/activate" && '
        f'exec bash -i'
    )

    # Check for mate-terminal first, then fallback to other terminal emulators.
    if shutil.which("mate-terminal"):
        terminal_cmd = ["mate-terminal", "--", "bash", "-c", bash_command]
    elif shutil.which("gnome-terminal"):
        terminal_cmd = ["gnome-terminal", "--", "bash", "-c", bash_command]
    elif shutil.which("konsole"):
        terminal_cmd = ["konsole", "-e", "bash", "-c", bash_command]
    elif shutil.which("x-terminal-emulator"):
        terminal_cmd = ["x-terminal-emulator", "-e", "bash", "-c", bash_command]
    else:
        terminal_cmd = ["xterm", "-e", "bash", "-c", bash_command]

    try:
        subprocess.Popen(terminal_cmd)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch terminal: {e}")


def get_installed_packages(env_path):
    """Return the list of installed packages in the virtual environment."""
    if sys.platform.startswith("win"):
        python_exe = os.path.join(env_path, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(env_path, "bin", "python")
    if not os.path.isfile(python_exe):
        return ["Python executable not found."]
    try:
        output = subprocess.check_output([python_exe, "-m", "pip", "freeze"], universal_newlines=True)
        packages = output.strip().splitlines()
        if not packages:
            return ["No packages found."]
        return packages
    except Exception as e:
        return [f"Error retrieving packages: {e}"]

def load_logged_envs():
    """Load known virtual environments from the log file."""
    if os.path.isfile(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
            return data  # Should be a dict of {env_name: env_path}
        except Exception as e:
            messagebox.showwarning("Warning", f"Error reading log file: {e}")
            return {}
    return {}

def save_logged_envs(envs):
    """Save known virtual environments to the log file."""
    try:
        with open(LOG_FILE, "w") as f:
            json.dump(envs, f, indent=4)
    except Exception as e:
        messagebox.showwarning("Warning", f"Error writing log file: {e}")

class EnvManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Virtual Environment Manager")
        self.geometry("750x500")
        self.create_widgets()
        self.load_default_envs()
        self.load_logged_envs_from_file()

    def create_widgets(self):
        # Left frame: List of environments and buttons
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        ttk.Label(left_frame, text="Virtual Environments").pack()
        
        self.env_listbox = tk.Listbox(left_frame, width=30)
        self.env_listbox.pack(fill=tk.BOTH, expand=True)
        self.env_listbox.bind("<<ListboxSelect>>", self.on_env_select)
        
        # Replace "Add Env Folder" with "Make Env"
        ttk.Button(left_frame, text="Make Env", command=self.make_env).pack(pady=5)
        ttk.Button(left_frame, text="Refresh", command=self.refresh_env_list).pack(pady=5)
        ttk.Button(left_frame, text="Launch Terminal", command=self.launch_selected_env).pack(pady=5)
        ttk.Button(left_frame, text="Search System", command=self.search_system_envs).pack(pady=5)
        
        # Right frame: Details (path and packages)
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(right_frame, text="Environment Details").pack(anchor=tk.W)
        
        self.details_text = tk.Text(right_frame, wrap=tk.NONE)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
    def load_default_envs(self):
        global environments
        new_envs = scan_env_directory(DEFAULT_ENV_DIR)
        environments.update(new_envs)
        self.refresh_env_list()
        
    def load_logged_envs_from_file(self):
        """Load previously logged environments from the log file and update the list."""
        global environments
        logged_envs = load_logged_envs()
        if logged_envs:
            environments.update(logged_envs)
            self.refresh_env_list()
        
    def refresh_env_list(self):
        self.env_listbox.delete(0, tk.END)
        for name in sorted(environments.keys()):
            self.env_listbox.insert(tk.END, name)
        
    def make_env(self):
        """Open a window to create a new virtual environment."""
        new_win = tk.Toplevel(self)
        new_win.title("Create New Virtual Environment")
        new_win.grab_set()  # Make this window modal
        
        ttk.Label(new_win, text="Enter new environment name:").pack(padx=10, pady=5)
        name_entry = ttk.Entry(new_win)
        name_entry.pack(padx=10, pady=5)
        
        def create_env():
            env_name = name_entry.get().strip()
            if not env_name:
                messagebox.showwarning("Warning", "Please enter a valid environment name.")
                return
            
            home_dir = os.path.expanduser("~")
            env_path = os.path.join(home_dir, env_name)
            
            if os.path.exists(env_path):
                messagebox.showwarning("Warning", "An environment with that name already exists!")
                return
            
            # Create the virtual environment using Python's venv module.
            try:
                subprocess.check_call([sys.executable, "-m", "venv", env_path])
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to create virtual environment: {e}")
                return
            
            # Add the new environment to our list and log.
            global environments
            environments[env_name] = env_path
            self.refresh_env_list()
            save_logged_envs(environments)
            
            new_win.destroy()
            # Launch terminal to activate the new virtual environment.
            launch_terminal_with_env(env_path)
        
        ttk.Button(new_win, text="Create", command=create_env).pack(padx=10, pady=10)
        
    def search_system_envs(self):
        """Search the entire system for virtual environments using the locate command."""
        new_envs = search_system_for_envs()
        if not new_envs:
            messagebox.showinfo("No Environments", "No virtual environments found via system search.")
            return
        environments.update(new_envs)
        self.refresh_env_list()
        # Save discovered environments to the log file
        save_logged_envs(environments)
        messagebox.showinfo("Search Complete", f"Found {len(new_envs)} environment(s).")
        
    def on_env_select(self, event):
        selection = self.env_listbox.curselection()
        if not selection:
            return
        env_name = self.env_listbox.get(selection[0])
        env_path = environments.get(env_name)
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, f"Name: {env_name}\n")
        self.details_text.insert(tk.END, f"Path: {env_path}\n\n")
        self.details_text.insert(tk.END, "Installed Packages:\n")
        packages = get_installed_packages(env_path)
        for pkg in packages:
            self.details_text.insert(tk.END, f"  {pkg}\n")
        
    def launch_selected_env(self):
        selection = self.env_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a virtual environment first.")
            return
        env_name = self.env_listbox.get(selection[0])
        env_path = environments.get(env_name)
        launch_terminal_with_env(env_path)

if __name__ == "__main__":
    app = EnvManagerGUI()
    app.mainloop()
