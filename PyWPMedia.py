import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext
import webbrowser

# Configure main extensions and patterns
MAIN_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.tif')
DEFAULT_FONT = ("Segoe UI", 10)


def is_thumbnail(filename):
    """
    Improved thumbnail detection that handles:
    - Multiple dimension patterns in filename
    - Double extensions (.jpg.webp)
    - Complex naming patterns
    - WordPress scaled images
    """
    name = os.path.splitext(filename)[0]  # Get name without primary extension
    
    # Handle double extensions
    if name.lower().endswith(('.jpg', '.jpeg', '.png')):
        name = os.path.splitext(name)[0]
    
    # Special WordPress cases
    if '-scaled' in name.lower() or '-rotated' in name.lower():
        return True
    
    # Find all dimension patterns
    matches = re.findall(r'-(\d+)x(\d+)', name)
    if not matches:
        return False
        
    # Get the last dimension pattern (most likely the thumbnail size)
    last_width, last_height = matches[-1]
    
    # Exclude cases that are likely main files
    if int(last_width) >= 1000 and int(last_height) >= 1000:
        return False
        
    return True


def get_base_name(filename):
    """
    Extract the base name by:
    - Removing all dimension patterns
    - Handling double extensions
    - Normalizing special characters
    """
    name = os.path.splitext(filename)[0]
    
    # Handle double extensions
    if name.lower().endswith(('.jpg', '.jpeg', '.png')):
        name = os.path.splitext(name)[0]
    
    # Remove ALL dimension patterns
    base_name = re.sub(r'-\d+x\d+', '', name)
    
    # Remove WordPress scaled/rotated suffixes
    base_name = re.sub(r'-(scaled|rotated)$', '', base_name, flags=re.IGNORECASE)
    
    # Normalize hyphens and underscores
    base_name = base_name.replace('_', '-')
    base_name = re.sub(r'-+', '-', base_name)  # Replace multiple hyphens with one
    base_name = base_name.rstrip('-')
    
    return base_name


def find_matching_main_files(thumbnail_base, all_files):
    """More flexible matching for complex names"""
    matching_files = []
    thumbnail_base = thumbnail_base.lower()
    
    for filename in all_files:
        if is_thumbnail(filename):
            continue
            
        # Get base name using same method
        file_base = get_base_name(filename).lower()
        
        # Flexible matching conditions
        if (file_base == thumbnail_base or
            thumbnail_base.startswith(file_base) or
            file_base.startswith(thumbnail_base) or
            file_base.replace('-', '') == thumbnail_base.replace('-', '')):
            matching_files.append(filename)
    
    return matching_files


def normalize_filenames(folder):
    """Normalize filenames before processing"""
    for filename in os.listdir(folder):
        src = os.path.join(folder, filename)
        if not os.path.isfile(src):
            continue
            
        # Fix common issues
        new_name = filename
        new_name = new_name.replace('--', '-')
        new_name = re.sub(r'-+', '-', new_name)
        new_name = new_name.replace('_.', '.')
        
        if new_name != filename:
            dst = os.path.join(folder, new_name)
            try:
                os.rename(src, dst)
            except Exception as e:
                continue


def delete_thumbnails_in_folder(folder_path, log_callback):
    """Delete thumbnails in a folder with improved matching"""
    deleted, failed = 0, 0
    
    try:
        normalize_filenames(folder_path)
        all_files = [f for f in os.listdir(folder_path) 
                    if os.path.isfile(os.path.join(folder_path, f))]
    except Exception as e:
        log_callback(f"Error reading folder {folder_path}: {e}")
        return deleted, failed
    
    if not all_files:
        return deleted, failed
    
    # Filter to only image files
    image_files = [f for f in all_files 
                  if f.lower().endswith(tuple(ext.lower() for ext in MAIN_EXTENSIONS))]
    
    thumbnail_files = [f for f in image_files if is_thumbnail(f)]
    
    if thumbnail_files:
        log_callback(f"\nProcessing folder: {folder_path}")
        log_callback(f"Found {len(thumbnail_files)} potential thumbnails")
    
    for thumbnail in thumbnail_files:
        full_path = os.path.join(folder_path, thumbnail)
        thumbnail_base = get_base_name(thumbnail)
        
        # Find matching main files
        matching_mains = find_matching_main_files(thumbnail_base, image_files)
        
        if matching_mains:
            try:
                os.remove(full_path)
                deleted += 1
                log_callback(f"  ✔ Deleted: {thumbnail} (matches: {', '.join(matching_mains)})")
            except Exception as e:
                failed += 1
                log_callback(f"  ✖ Failed to delete {thumbnail}: {e}")
        else:
            log_callback(f"  ? Skipped: {thumbnail} (no matching main file found)")
    
    return deleted, failed


def delete_thumbnails(root_folder, log_callback):
    """Recursively delete thumbnails with progress tracking"""
    total_deleted, total_failed = 0, 0
    folders_processed = 0
    
    log_callback(f"\n=== STARTING CLEANUP ===")
    log_callback(f"Root folder: {root_folder}")
    
    for root, dirs, files in os.walk(root_folder):
        deleted, failed = delete_thumbnails_in_folder(root, log_callback)
        total_deleted += deleted
        total_failed += failed
        
        if deleted > 0 or failed > 0:
            folders_processed += 1
    
    log_callback(f"\n=== SUMMARY ===")
    log_callback(f"Folders processed: {folders_processed}")
    log_callback(f"Total deleted: {total_deleted}")
    log_callback(f"Total failed: {total_failed}")
    log_callback("="*40)


def move_remaining_files(source, dest, log_callback):
    """Move non-thumbnail files with conflict handling"""
    copied, skipped, failed = 0, 0, 0
    
    try:
        os.makedirs(dest, exist_ok=True)
    except Exception as e:
        log_callback(f"Error creating destination folder: {e}")
        return

    for root, _, files in os.walk(source):
        for file in files:
            if is_thumbnail(file):
                continue

            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest, file)

            if os.path.exists(dest_file):
                skipped += 1
                log_callback(f"Skipped (exists): {file}")
                continue

            try:
                shutil.copy2(src_file, dest_file)
                copied += 1
                log_callback(f"Copied: {file}")
            except Exception as e:
                failed += 1
                log_callback(f"Failed to copy {file}: {e}")

    log_callback(f"\nCopy complete. Copied: {copied}, Skipped: {skipped}, Failed: {failed}")


class MediaCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WordPress Media Cleaner - DotNet Guide")
        self.root.geometry("900x650")
        self.root.minsize(700, 500)
        self.root.configure(padx=10, pady=10)
        
        try:
            self.root.option_add("*Font", DEFAULT_FONT)
        except:
            self.root.option_add("*Font", ("Arial", 10))

        self.create_widgets()

    def create_widgets(self):
        # Source folder selection
        tk.Label(self.root, text="Media Folder:").grid(row=0, column=0, sticky="w")
        self.source_entry = tk.Entry(self.root, width=70)
        self.source_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        tk.Button(self.root, text="Browse", command=self.browse_source).grid(row=0, column=2)
        tk.Button(self.root, text="🔍 Preview", command=self.preview_cleanup).grid(row=0, column=3, padx=5)

        # Log area
        self.log_text = scrolledtext.ScrolledText(self.root, width=100, height=25, wrap=tk.WORD)
        self.log_text.grid(row=1, column=0, columnspan=4, pady=10, sticky="nsew")

        # Action buttons
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=2, column=0, columnspan=4, pady=5, sticky="ew")
        
        tk.Button(button_frame, text="🧹 Clean Thumbnails", command=self.clean_thumbnails).pack(side="left", padx=5)
        tk.Button(button_frame, text="📂 Move Remaining Files", command=self.move_files).pack(side="left", padx=5)
        tk.Button(button_frame, text="🗑️ Clear Log", command=self.clear_log).pack(side="left", padx=5)

        # Footer with separate links
        footer_frame = tk.Frame(self.root)
        footer_frame.grid(row=3, column=0, columnspan=4, pady=10, sticky="ew")
        
        tk.Label(footer_frame, text="🔗").pack(side="left")
        
        dotnet_link = tk.Label(footer_frame, text="dotnet.guide", fg="blue", cursor="hand2")
        dotnet_link.pack(side="left")
        dotnet_link.bind("<Button-1>", lambda e: webbrowser.open("https://dotnet.guide"))
        
        tk.Label(footer_frame, text="|").pack(side="left", padx=5)
        
        yt_link = tk.Label(footer_frame, text="YouTube: @PRBHindi", fg="blue", cursor="hand2")
        yt_link.pack(side="left")
        yt_link.bind("<Button-1>", lambda e: webbrowser.open("https://youtube.com/@PRBHindi"))

        # Configure resizing
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, folder)

    def preview_cleanup(self):
        """Preview mode with enhanced detection"""
        folder = self.source_entry.get()
        if not os.path.isdir(folder):
            self.log("Invalid folder selected.")
            return
            
        self.log("\n=== PREVIEW MODE ===\n")
        self.log("Analyzing files (NO changes will be made)...\n")
        
        total_files = total_images = total_mains = total_thumbs = 0
        would_delete = would_skip = folders_with_thumbs = 0
        
        for root, _, files in os.walk(folder):
            all_files = [f for f in files if os.path.isfile(os.path.join(root, f))]
            if not all_files:
                continue
                
            total_files += len(all_files)
            image_files = [f for f in all_files if f.lower().endswith(tuple(ext.lower() for ext in MAIN_EXTENSIONS))]
            total_images += len(image_files)
            
            thumb_files = [f for f in image_files if is_thumbnail(f)]
            if not thumb_files:
                continue
                
            folders_with_thumbs += 1
            total_thumbs += len(thumb_files)
            total_mains += len(image_files) - len(thumb_files)
            
            self.log(f"Folder: {root}")
            self.log(f"  Images: {len(image_files)} (Main: {len(image_files)-len(thumb_files)}, Thumbs: {len(thumb_files)})")
            
            # Show sample of thumbnails
            for thumb in thumb_files[:3]:  # Show first 3 as examples
                base = get_base_name(thumb)
                mains = find_matching_main_files(base, image_files)
                if mains:
                    would_delete += 1
                    self.log(f"    Would DELETE: {thumb}")
                else:
                    would_skip += 1
                    self.log(f"    Would KEEP: {thumb} (no match)")
            
            if len(thumb_files) > 3:
                self.log(f"    ...and {len(thumb_files)-3} more thumbnails")
            
            self.log("")
        
        self.log("\n=== PREVIEW SUMMARY ===")
        self.log(f"Folders scanned: {folders_with_thumbs}")
        self.log(f"Total files: {total_files}")
        self.log(f"Image files: {total_images} (Main: {total_mains}, Thumbs: {total_thumbs})")
        self.log(f"Would delete: {would_delete} thumbnails")
        self.log(f"Would keep: {would_skip} thumbnails")
        self.log("======================\n")

    def clean_thumbnails(self):
        folder = self.source_entry.get()
        if os.path.isdir(folder):
            self.log("\nStarting thumbnail cleanup...")
            delete_thumbnails(folder, self.log)
        else:
            self.log("Invalid folder selected.")

    def move_files(self):
        source = self.source_entry.get()
        if not os.path.isdir(source):
            self.log("Invalid source folder.")
            return
            
        dest = filedialog.askdirectory(title="Select Destination Folder")
        if dest:
            try:
                if os.path.commonpath([os.path.abspath(source), os.path.abspath(dest)]) == os.path.abspath(source):
                    self.log("Error: Destination cannot be inside source.")
                    return
            except ValueError:
                pass
                
            self.log(f"\nMoving files from {source} to {dest}...")
            move_remaining_files(source, dest, self.log)


if __name__ == "__main__":
    root = tk.Tk()
    app = MediaCleanerGUI(root)
    root.mainloop()