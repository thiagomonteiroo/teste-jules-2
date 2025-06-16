import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageGrab
import os
import tempfile

class ImageResizerApp:
    def __init__(self, master):
        self.master = master
        master.title("Image Resizer")

        # Instance variables to store state
        self.resized_images_data = []
        self.resize_errors = []
        self.temp_files = [] # To keep track of temporary files from clipboard paste

        # --- Input Frame for Width and Height ---
        input_frame = ttk.Frame(master, padding="10")
        input_frame.pack(fill=tk.X)

        width_label = ttk.Label(input_frame, text="Width:")
        width_label.pack(side=tk.LEFT, padx=5, pady=5)
        self.width_entry = ttk.Entry(input_frame, width=10)
        self.width_entry.pack(side=tk.LEFT, padx=5, pady=5)

        height_label = ttk.Label(input_frame, text="Height:")
        height_label.pack(side=tk.LEFT, padx=5, pady=5)
        self.height_entry = ttk.Entry(input_frame, width=10)
        self.height_entry.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Frame for Image Selection ---
        selection_frame = ttk.Frame(master, padding="10")
        selection_frame.pack(fill=tk.BOTH, expand=True)

        # Image Listbox
        self.image_listbox = tk.Listbox(selection_frame)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar for Listbox
        listbox_scrollbar = ttk.Scrollbar(selection_frame, orient=tk.VERTICAL, command=self.image_listbox.yview)
        listbox_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.image_listbox.config(yscrollcommand=listbox_scrollbar.set)

        # Drag and Drop Setup
        self.image_listbox.drop_target_register(DND_FILES)
        self.image_listbox.dnd_bind('<<DropEnter>>', self.drop_enter)
        self.image_listbox.dnd_bind('<<DropLeave>>', self.drop_leave)
        self.image_listbox.dnd_bind('<<DropPosition>>', self.drop_position)
        self.image_listbox.dnd_bind('<<Drop>>', self.drop_files)

        # Buttons Frame (for select, paste)
        buttons_sub_frame = ttk.Frame(selection_frame)
        buttons_sub_frame.pack(fill=tk.Y, side=tk.LEFT, padx=5)

        # Select Images Button
        select_button = ttk.Button(buttons_sub_frame, text="Select Images", command=self.select_images)
        select_button.pack(pady=5, fill=tk.X)

        # Paste from Clipboard Button
        paste_button = ttk.Button(buttons_sub_frame, text="Paste from Clipboard", command=self.paste_from_clipboard)
        paste_button.pack(pady=5, fill=tk.X)

        # --- Action Frame (Resize Button) ---
        action_frame = ttk.Frame(master, padding="10")
        action_frame.pack(fill=tk.X)

        resize_button = ttk.Button(action_frame, text="Resize and Save Images", command=self.process_and_save_images)
        resize_button.pack(pady=5)

        # Cleanup temp files on exit
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    # --- Drag and Drop Event Handlers ---
    def drop_enter(self, event):
        event.widget.focus_force()
        return event.action

    def drop_leave(self, event):
        return event.action

    def drop_position(self, event):
        return event.action

    def drop_files(self, event):
        if event.data:
            filepaths = self.master.tk.splitlist(event.data)
            for filepath in filepaths:
                if filepath.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    if filepath not in self.image_listbox.get(0, tk.END):
                        self.image_listbox.insert(tk.END, filepath)
                else:
                    print(f"Skipping non-image file (drag-drop): {filepath}") # User feedback via status bar/log later
        return event.action

    # --- Button Command Methods ---
    def select_images(self):
        filepaths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.webp"), ("All files", "*.*"))
        )
        if filepaths:
            for filepath in filepaths:
                if filepath not in self.image_listbox.get(0, tk.END):
                    self.image_listbox.insert(tk.END, filepath)

    def paste_from_clipboard(self):
        try:
            image = ImageGrab.grabclipboard()
            if image:
                temp_filename = tempfile.NamedTemporaryFile(delete=False, suffix=".png", prefix="pasted_").name
                self.temp_files.append(temp_filename) # Keep track for cleanup

                if image.mode != 'RGB': # Ensure compatibility for saving as PNG
                    image = image.convert('RGB')
                image.save(temp_filename, "PNG")

                if temp_filename not in self.image_listbox.get(0, tk.END):
                    self.image_listbox.insert(tk.END, temp_filename)
                else:
                    messagebox.showinfo("Info", "Image already in list.") # Should be rare with temp names
            else:
                messagebox.showinfo("Info", "No image found on clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not paste image from clipboard: {e}")
            print(f"Clipboard error: {e}") # For debugging

    # --- Core Logic: Image Resizing and Saving ---
    def process_and_save_images(self):
        self.resized_images_data.clear()
        self.resize_errors.clear()

        try:
            width_str = self.width_entry.get()
            height_str = self.height_entry.get()
            if not width_str or not height_str:
                messagebox.showerror("Error", "Please enter both width and height.")
                return
            width = int(width_str)
            height = int(height_str)
            if width <= 0 or height <= 0:
                messagebox.showerror("Error", "Width and height must be positive integers.")
                return
        except ValueError:
            messagebox.showerror("Error", "Width and height must be valid integers.")
            return

        selected_files = self.image_listbox.get(0, tk.END)
        if not selected_files:
            messagebox.showerror("Error", "No images selected to resize.")
            return

        supported_extensions = (".jpg", ".jpeg", ".png", ".webp")

        for filepath in selected_files:
            filename = os.path.basename(filepath)
            try:
                if not filepath.lower().endswith(supported_extensions):
                    # Specific Portuguese error message for unsupported file format
                    self.resize_errors.append(f"Erro: O arquivo {filename} não é um formato de imagem suportado.")
                    continue

                img = Image.open(filepath)
                original_format = img.format or 'PNG' # Default to PNG if format is None (e.g. for pasted images)

                # Handle RGBA to RGB conversion for JPEG if needed
                if original_format.upper() == 'JPEG' and img.mode == 'RGBA':
                    img = img.convert('RGB')

                resized_img = img.resize((width, height), Image.Resampling.LANCZOS) # Using LANCZOS for better quality

                self.resized_images_data.append({
                    'original_path': filepath, # For determining output directory
                    'filename': filename,
                    'resized_image': resized_img,
                    'original_format': original_format.upper()
                })
            except FileNotFoundError:
                self.resize_errors.append(f"Error: File not found '{filename}'.")
            except Exception as e:
                self.resize_errors.append(f"Error processing '{filename}': {e}")

        # Proceed to save if there are images processed
        if self.resized_images_data:
            self._save_processed_images(selected_files[0]) # Pass first path for output dir context

        # Display errors, if any
        if self.resize_errors:
            error_message = "\n".join(self.resize_errors)
            # Determine title and icon based on whether there were also successes
            if self.resized_images_data: # Some successes, some errors
                messagebox.showwarning("Operação Concluída com Avisos", f"Algumas imagens processadas, mas com erros:\n\n{error_message}")
            else: # No successes, only errors
                messagebox.showerror("Falha na Operação", f"Nenhuma imagem foi processada com sucesso:\n\n{error_message}")
            print("Resize/Save errors:\n", error_message) # Also print to console
        elif self.resized_images_data: # Only show success if no errors at all and some images were processed
             messagebox.showinfo("Sucesso", f"Imagens redimensionadas e salvas com sucesso!") # Specific Portuguese success message
        elif not selected_files: # Handled earlier, but as a fallback
            pass # No files selected, message already shown
        else: # No images were processed (e.g. all were unsupported) and no specific errors were caught other than unsupported
            # This case should be covered by resize_errors not being empty if all files were unsupported
            # If selected_files is not empty, but resized_images_data is empty and resize_errors is empty, it's an edge case.
            # However, the current logic means resize_errors would contain the "unsupported format" messages.
            pass # All feedback handled.

        # Clear data for the next run only after all operations including error reporting
        # self.resized_images_data.clear()
        # self.resize_errors.clear() # Errors are shown, so can be cleared


    def _save_processed_images(self, first_image_path_context):
        if not self.resized_images_data:
            return

        try:
            # Determine output directory based on the context of the first image (or a default if needed)
            base_dir = os.path.dirname(first_image_path_context)
            # Check if first_image_path_context is a temp file. If so, save to user's Desktop or Documents.
            if first_image_path_context in self.temp_files:
                # Try Desktop, then Documents, then current working directory as fallback
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                documents_path = os.path.join(os.path.expanduser("~"), "Documents")
                if os.path.isdir(desktop_path):
                    base_dir = desktop_path
                elif os.path.isdir(documents_path):
                    base_dir = documents_path
                else:
                    base_dir = os.getcwd() # Fallback to current working directory

            output_dir = os.path.join(base_dir, "OUTPUT_IMAGES_Resized")
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            self.resize_errors.append(f"Error creating output directory '{output_dir}': {e}")
            messagebox.showerror("Save Error", f"Could not create output directory: {output_dir}\n{e}")
            return

        successfully_saved_count = 0
        for item in self.resized_images_data:
            original_filename_base, original_filename_ext = os.path.splitext(item['filename'])
            # For temporary pasted files, their 'filename' might be like 'pasted_XXXX.png'
            # We want the output to be more descriptive if possible, or just use this name.

            save_format = item['original_format'] # Already uppercased

            # Determine output extension
            if save_format == 'JPEG':
                output_extension = ".jpg"
            elif save_format == 'PNG':
                output_extension = ".png"
            elif save_format == 'WEBP':
                output_extension = ".webp"
            else: # Default to PNG for unknown or problematic formats
                save_format = 'PNG'
                output_extension = ".png"

            # Construct final filename, ensuring it doesn't clash if original was e.g. .jpeg but we save as .jpg
            output_filename_base = original_filename_base
            output_filepath = os.path.join(output_dir, output_filename_base + output_extension)

            # Handle potential filename clashes by appending a number
            counter = 1
            while os.path.exists(output_filepath):
                output_filepath = os.path.join(output_dir, f"{output_filename_base}_{counter}{output_extension}")
                counter += 1

            try:
                # Ensure image mode is compatible with save format (e.g., RGB for JPEG)
                current_image = item['resized_image']
                if save_format == 'JPEG' and current_image.mode not in ('RGB', 'L'): # L is grayscale
                    current_image = current_image.convert('RGB')

                current_image.save(output_filepath, format=save_format)
                successfully_saved_count += 1
            except Exception as e:
                self.resize_errors.append(f"Erro ao salvar '{item['filename']}' como '{os.path.basename(output_filepath)}': {e}")

        # Feedback is now primarily handled by the calling function (process_and_save_images)
        # This function's role is just to save the files it's given.
        # The successfully_saved_count could be returned if more granular feedback from saving itself is needed.

    def on_closing(self):
        # Clean up temporary files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                print(f"Error cleaning up temp file {temp_file}: {e}")
        self.master.destroy()

if __name__ == '__main__':
    # Use TkinterDnD.Tk for the main window to enable drag & drop
    root = TkinterDnD.Tk()
    app = ImageResizerApp(root)
    root.mainloop()
