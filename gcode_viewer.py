import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re

# G-code parser logic
def extract_settings_from_gcode(file_path):
    sections = {
        "Temperature": {}, "Support": {}, "Filament": {}, "Extrusion Widths": {}, "Motion Settings": {},
        "Cooling": {}, "Retraction": {}, "Speed": {}, "Walls": {}, "Infill": {}, "Build Plate": {},
        "Slicer Info": {}, "Uncategorized": {}
    }

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            buffer_line = ""  # To handle fragmented lines
            for line in f:
                clean = line.strip().lstrip(';').strip()

                # Skip empty lines
                if not clean:
                    continue

                # Handle fragmented settings
                if clean.endswith("\\") or clean.endswith("="):
                    buffer_line += clean.rstrip("\\") + " "  # Remove trailing backslash and continue buffering
                    continue

                # Finalize the buffered line when a complete line is detected
                if buffer_line:
                    clean = buffer_line + clean
                    buffer_line = ""

                # Replace escaped newlines with actual newlines
                clean = clean.replace("\\n", "\n")

                # Parse settings into key-value pairs
                if '=' in clean:
                    key, val = map(str.strip, clean.split('=', 1))

                    # Categorize settings into appropriate sections based on keywords
                    if 'temperature' in key.lower() or 'bed' in key.lower():
                        sections["Temperature"][key] = val
                    elif 'support' in key.lower():
                        sections["Support"][key] = val
                    elif 'filament' in key.lower():
                        sections["Filament"][key] = val
                    elif 'extrusion' in key.lower():
                        sections["Extrusion Widths"][key] = val
                    elif 'motion' in key.lower():
                        sections["Motion Settings"][key] = val
                    elif 'cooling' in key.lower():
                        sections["Cooling"][key] = val
                    elif 'retraction' in key.lower():
                        sections["Retraction"][key] = val
                    elif 'speed' in key.lower():
                        sections["Speed"][key] = val
                    elif 'wall' in key.lower():
                        sections["Walls"][key] = val
                    elif 'infill' in key.lower():
                        sections["Infill"][key] = val
                    elif 'build plate' in key.lower():
                        sections["Build Plate"][key] = val
                    else:
                        sections["Uncategorized"][key] = val  # Default to Uncategorized

    except Exception as e:
        print(f"Parsing error: {e}")
        raise ValueError(f"Failed to parse G-code: {e}")

    return sections


# GUI logic
settings_cache = {}

def load_file():
    # Allow the user to select a G-code file
    file_path = filedialog.askopenfilename(filetypes=[("G-code Files", "*.gcode")], title="Select a G-code File")
    if not file_path:
        return  # User canceled the file dialog

    global settings_cache
    settings_cache.clear()

    # Parse the selected G-code file
    try:
        file_settings = extract_settings_from_gcode(file_path)
        settings_cache["G-code Settings"] = file_settings
        update_tabs()
    except ValueError as e:
        messagebox.showerror("Error", str(e))


def update_tabs():
    # Clear all existing tabs
    for tab in tab_control.tabs():
        tab_control.forget(tab)

    # Add tabs only for sections that have data
    for section, content in settings_cache.get("G-code Settings", {}).items():
        if content:  # Only create tabs for sections with data
            frame = ttk.Frame(tab_control)
            tab_control.add(frame, text=section)

            # Add a text widget with a scrollbar
            text_frame = tk.Frame(frame)
            text_frame.pack(expand=True, fill=tk.BOTH)

            text = tk.Text(text_frame, wrap=tk.WORD, height=30, width=90)
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)

            text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            text.insert(tk.END, f"=== {section} ===\n\n")
            for key, val in content.items():
                if '\n' in val:  # Handle multi-line values
                    text.insert(tk.END, f"- {key.replace('_', ' ').capitalize()}:\n")
                    for line in val.split('\n'):
                        text.insert(tk.END, f"  {line.strip()}\n")
                else:  # Single-line values
                    text.insert(tk.END, f"- {key.replace('_', ' ').capitalize()}: {val}\n")
            text.insert(tk.END, "\n")  # Add spacing after each section

            # Disable editing in the text widget
            text.configure(state=tk.DISABLED)


def save_to_txt():
    if not settings_cache:
        messagebox.showwarning("No Data", "Load a G-code file first.")
        return
    save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if save_path:
        with open(save_path, 'w', encoding='utf-8') as f:
            for section, content in settings_cache.get("G-code Settings", {}).items():
                if content:
                    f.write(f"\n=== {section} ===\n")
                    for key, val in content.items():
                        if '\n' in val:  # Handle multi-line values
                            f.write(f"- {key.replace('_', ' ').capitalize()}:\n")
                            for line in val.split('\n'):
                                f.write(f"  {line.strip()}\n")
                        else:
                            f.write(f"- {key.replace('_', ' ').capitalize()}: {val}\n")
        messagebox.showinfo("Saved", f"Settings exported to {save_path}")


# Main GUI setup
root = tk.Tk()
root.title("G-code Settings Viewer")
root.geometry("900x800")

frame = tk.Frame(root)
frame.pack(pady=10)

load_button = tk.Button(frame, text="Open G-code File", command=load_file)
load_button.grid(row=0, column=0, padx=5)

save_button = tk.Button(frame, text="Save as TXT", command=save_to_txt)
save_button.grid(row=0, column=1, padx=5)

tab_control = ttk.Notebook(root)
tab_control.pack(expand=1, fill="both")

root.mainloop()