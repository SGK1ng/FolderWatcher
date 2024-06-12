import os
import json
import mimetypes
import time
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tempfile
from snapshot import create_snapshot, save_snapshot, load_snapshot
from compare import compare_directories, get_file_attributes, calculate_file_hash, list_ads_files
from about import about_fw

class Window:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Watcher")
        self.root.geometry('800x450')
        self.root.resizable(width=True, height=True)
        self.root.configure(bg='white')

        self.init_variables()
        self.load_translations(self.language.get())
        self.create_widgets()
        self.create_menu()
        self.setup_traces()

    def init_variables(self):
        self.use_ads = tk.BooleanVar(value=False)
        self.show_size = tk.BooleanVar(value=True)
        self.show_type = tk.BooleanVar(value=True)
        self.show_attributes = tk.BooleanVar(value=True)
        self.show_last_modified = tk.BooleanVar(value=True)
        self.show_hash = tk.BooleanVar(value=False)
        self.last_directory1 = tk.StringVar()
        self.last_directory2 = tk.StringVar()
        self.directory_label1 = tk.StringVar(value="Directory 1")
        self.directory_label2 = tk.StringVar(value="Directory 2")
        self.language = tk.StringVar(value="English")
        self.snapshot = None
        self.target_treeview = None
        self.translations = {}
        self.available_languages = self.load_available_languages()

    def load_available_languages(self):
        languages = {}
        translation_files = [
            f for f in os.listdir(os.path.dirname(__file__))
            if f.startswith('translations_') and f.endswith('.json')
        ]
        for file in translation_files:
            lang_code = file.split('_')[1].split('.')[0]
            languages[lang_code.capitalize()] = file
        return languages

    def load_translations(self, language):
        filename = self.available_languages.get(language.lower().capitalize())
        if filename:
            filepath = os.path.join(os.path.dirname(__file__), filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    self.translations = json.load(file)
            except FileNotFoundError:
                messagebox.showerror("Error", f"Translation file {filename} not found.")
                self.translations = {}

    def translate(self, text):
        return self.translations.get(text, text)

    def create_snapshot_action(self, directory_var):
        if directory_var.get():
            snapshot_zip = create_snapshot(directory_var.get(), self.use_ads.get())
            snapshot_file = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("Zip files", "*.zip")]
            )
            if snapshot_file:
                save_snapshot(snapshot_zip, snapshot_file)
                messagebox.showinfo("Snapshot Created", "Snapshot has been successfully created and saved.")
        else:
            messagebox.showerror(self.translate("No Directory Selected"), self.translate("Please select a directory first."))

    def load_snapshot_action(self, target_treeview):
        snapshot_file = filedialog.askopenfilename(
            filetypes=[("Zip files", "*.zip")]
        )
        if snapshot_file:
            target_directory = tempfile.mkdtemp()
            load_snapshot(snapshot_file, target_directory)
            self.list_files(target_treeview, target_directory)
            
            if target_treeview == self.file_tree1:
                self.last_directory1.set(target_directory)
            elif target_treeview == self.file_tree2:
                self.last_directory2.set(target_directory)

    def update_comparison_results(self, only_in1_files, only_in2_files, modified_files, only_in1_dirs, only_in2_dirs, size_diff_dirs):
        self.list_files(self.file_tree1, self.last_directory1.get())
        for child in self.file_tree1.get_children():
            item = self.file_tree1.item(child)
            filename = item['values'][0]
            self.apply_cell_tags(self.file_tree1, child, filename, modified_files, is_first_tree=True)
            
        self.list_files(self.file_tree2, self.last_directory2.get())
        for child in self.file_tree2.get_children():
            item = self.file_tree2.item(child)
            filename = item['values'][0]
            self.apply_cell_tags(self.file_tree2, child, filename, modified_files, is_first_tree=False)

        self.define_cell_tags(self.file_tree1)
        self.define_cell_tags(self.file_tree2)

    def apply_cell_tags(self, treeview, item_id, filename, modified_files, is_first_tree):
        if filename in modified_files:
            file_info = modified_files[filename]
            values = list(treeview.item(item_id)['values'])
            
            for i, col in enumerate(treeview['columns']):
                if col == self.translate("Size") and file_info['size']:
                    values[i] = f'**{values[i]}**'
                    treeview.tag_configure('size_modified', background='lightgreen')
                if col == self.translate("Attributes") and file_info['attributes']:
                    values[i] = f'**{values[i]}**'
                    treeview.tag_configure('attributes_modified', background='lightblue')
                if col == self.translate("Last Modified") and file_info['last_modified']:
                    values[i] = f'**{values[i]}**'
                    treeview.tag_configure('last_modified', background='lightpink')
                if col == self.translate("Hash") and file_info['hash']:
                    values[i] = f'**{values[i]}**'
                    treeview.tag_configure('hash_modified', background='lightyellow')

            treeview.item(item_id, values=values, tags='highlighted')

    def define_cell_tags(self, treeview):
        treeview.tag_configure('highlighted', background='lightgreen')
        treeview.tag_configure('size_modified', background='lightgreen')
        treeview.tag_configure('attributes_modified', background='lightblue')
        treeview.tag_configure('last_modified', background='lightpink')
        treeview.tag_configure('hash_modified', background='lightyellow')

    def get_tags(self, filename, primary_files, secondary_files, modified_files):
        tags = ()
        if filename in primary_files:
            tags = ('deleted',)
        elif filename in secondary_files:
            tags = ('new',)
        elif filename in modified_files:
            file_info = modified_files[filename]
            if file_info['size']:
                tags += ('modified',)
            if file_info['attributes']:
                tags += ('attributes_modified',)
            if file_info['last_modified']:
                tags += ('last_modified',)
            if file_info['hash']:
                tags += ('hash_modified',)
        return tags

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label=self.translate("About Folder Watcher"), command=self.btn_about_fw)
        menubar.add_cascade(label=self.translate("About"), menu=filemenu)

        language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.translate("Language"), menu=language_menu)

        for lang in self.available_languages.keys():
            language_menu.add_command(label=lang, command=lambda l=lang: self.update_language(l))

    def btn_about_fw(self):
        about_fw(self.root, self.language, self.translations)

    def update_language(self, lang):
        self.language.set(lang)
        self.load_translations(lang)
        self.update_display()

    def create_widgets(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        style = ttk.Style()
        style.configure('Custom.TButton', font=('Helvetica', 14))
        style.configure('Custom.TLabel', font=('Helvetica', 14))

        self.create_directory_widgets()
        self.create_checkboxes()
        self.setup_treeview()
        
        self.compare_btn = ttk.Button(self.root, text=self.translate("Compare"), command=self.btn1_click, style='Custom.TButton', takefocus=0)
        self.compare_btn.grid(row=3, column=1, columnspan=2, sticky='ew', padx=5, pady=(5, 0))

    def create_directory_widgets(self):
        frame1 = ttk.Frame(self.root)
        frame1.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        frame1.grid_columnconfigure(0, weight=1)
        snapshot_frame1 = tk.Frame(frame1, bg='white')
        snapshot_frame1.grid(row=0, column=0, columnspan=2, sticky='ew')
        self.create_snapshot_btn1 = ttk.Button(snapshot_frame1, text=self.translate("Create Snapshot"), command=lambda: self.create_snapshot_action(self.last_directory1), style='Custom.TButton', takefocus=0)
        self.create_snapshot_btn1.grid(row=0, column=0, sticky='ew', padx=5)
        self.load_snapshot_btn1 = ttk.Button(snapshot_frame1, text=self.translate("Load Snapshot"), command=lambda: self.load_snapshot_action(self.file_tree1), style='Custom.TButton', takefocus=0)
        self.load_snapshot_btn1.grid(row=0, column=1, sticky='ew', padx=5)
        self.directory1_entry = ttk.Entry(frame1, textvariable=self.last_directory1)
        self.directory1_entry.grid(row=1, column=0, sticky='ew')
        self.directory1_entry.bind('<Return>', lambda event: self.update_directory(self.file_tree1, self.last_directory1.get()))
        self.directory1_button = ttk.Button(frame1, text='...', command=lambda: self.select_directory(True), width=2, style='Custom.TButton', takefocus=0)
        self.directory1_button.grid(row=1, column=1)

        frame2 = ttk.Frame(self.root)
        frame2.grid(row=0, column=2, sticky='ew', padx=5, pady=5)
        frame2.grid_columnconfigure(0, weight=1)
        snapshot_frame2 = tk.Frame(frame2, bg='white')
        snapshot_frame2.grid(row=0, column=0, columnspan=2, sticky='ew')
        self.create_snapshot_btn2 = ttk.Button(snapshot_frame2, text=self.translate("Create Snapshot"), command=lambda: self.create_snapshot_action(self.last_directory2), style='Custom.TButton', takefocus=0)
        self.create_snapshot_btn2.grid(row=0, column=0, sticky='ew', padx=5)
        self.load_snapshot_btn2 = ttk.Button(snapshot_frame2, text=self.translate("Load Snapshot"), command=lambda: self.load_snapshot_action(self.file_tree2), style='Custom.TButton', takefocus=0)
        self.load_snapshot_btn2.grid(row=0, column=1, sticky='ew', padx=5)
        self.directory2_entry = ttk.Entry(frame2, textvariable=self.last_directory2)
        self.directory2_entry.grid(row=1, column=0, sticky='ew')
        self.directory2_entry.bind('<Return>', lambda event: self.update_directory(self.file_tree2, self.last_directory2.get()))
        self.directory2_button = ttk.Button(frame2, text='...', command=lambda: self.select_directory(False), width=2, style='Custom.TButton', takefocus=0)
        self.directory2_button.grid(row=1, column=1)

    def create_checkboxes(self):
        checkbox_frame = tk.Frame(self.root, background='white')
        checkbox_frame.grid(row=1, column=1, columnspan=2, sticky='w', pady=5)

        self.show_size_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Size"), variable=self.show_size, background='white', takefocus=0)
        self.show_size_btn.pack(side=tk.LEFT, padx=5)
        self.show_type_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Type"), variable=self.show_type, background='white', takefocus=0)
        self.show_type_btn.pack(side=tk.LEFT, padx=5)
        self.show_attributes_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Attributes"), variable=self.show_attributes, background='white', takefocus=0)
        self.show_attributes_btn.pack(side=tk.LEFT, padx=5)
        self.show_last_modified_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Last Modified"), variable=self.show_last_modified, background='white', takefocus=0)
        self.show_last_modified_btn.pack(side=tk.LEFT, padx=5)
        
        self.show_hash_btn = tk.Checkbutton(checkbox_frame, text=self.translate("Show Hash"), variable=self.show_hash, background='white', takefocus=0)
        self.show_hash_btn.pack(side=tk.LEFT, padx=5)

        self.ads_check = tk.Checkbutton(checkbox_frame, text=self.translate("Ads"), variable=self.use_ads, background='white', takefocus=0)
        self.ads_check.pack(side=tk.LEFT, padx=5)

    def update_directory(self, treeview, directory):
        if os.path.isdir(directory):
            self.list_files(treeview, directory)
        else:
            messagebox.showerror(self.translate("Error"), self.translate("Invalid directory path"))

    def setup_treeview(self):
        self.columns = [
            self.translate("File Name"),
            self.translate("Size"),
            self.translate("Type"),
            self.translate("Attributes"),
            self.translate("Last Modified"),
            self.translate("Hash")
        ]
        self.file_tree1 = ttk.Treeview(self.root, columns=self.columns, show="headings")
        self.file_tree2 = ttk.Treeview(self.root, columns=self.columns, show="headings")
        self.update_column_visibility()
        self.file_tree1.grid(row=2, column=1, sticky='nsew', padx=5, pady=5)
        self.file_tree2.grid(row=2, column=2, sticky='nsew', padx=5, pady=5)

        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(1, weight=0)

    def select_directory(self, is_first):
        directory = filedialog.askdirectory()
        if directory:
            if is_first:
                self.last_directory1.set(directory)
                self.list_files(self.file_tree1, directory)
            else:
                self.last_directory2.set(directory)
                self.list_files(self.file_tree2, directory)

    def list_files(self, treeview, directory):
        treeview.delete(*treeview.get_children())
        if directory:
            for item in os.scandir(directory):
                if self.use_ads.get() and not item.is_dir():
                    ads_files = list_ads_files(item.path)
                    for ads_file, size in ads_files:
                        self.insert_file_item(treeview, ads_file, size, "ADS")
                if item.is_dir():
                    folder_size = self.calculate_folder_size(item.path)
                    self.insert_file_item(treeview, item, folder_size, "Folder")
                else:
                    file_size = os.path.getsize(item.path)
                    self.insert_file_item(treeview, item, file_size, "File")

    def calculate_folder_size(self, folder):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def get_formated_size(self, size):
        if size == 0:
            return '0 B'
        
        size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        formatted_size = round(size / p, 2)
        
        return f'{formatted_size} {size_name[i]}'

    def insert_file_item(self, treeview, item, item_size=None, item_type=""):
        if isinstance(item, os.DirEntry):
            display_text = item.name
            item_path = item.path
            if item.is_dir():
                size_text = self.get_formated_size(item_size) if item_size is not None else ""
                type_text = self.translate("Folder")
            else:
                size_text = self.get_formated_size(item_size) if item_size is not None else ""
                mime_type, _ = mimetypes.guess_type(item_path)
                type_text = self.get_file_description(mime_type)
            attributes_text = get_file_attributes(item_path)
            last_modified_text = self.get_last_modified(item_path)
            hash_text = calculate_file_hash(item_path) if self.show_hash else ""
        else:
            full_path = item
            if ':' in full_path:
                main_file_path, ads_stream = full_path.rsplit(':', 1)
                main_file_name = os.path.basename(main_file_path)
                display_text = f"{main_file_name}:{ads_stream}"
                size_text = self.get_formated_size(item_size) if item_size is not None else ""
                type_text = "ADS File"
                attributes_text = ""
                last_modified_text = ""
                hash_text = ""

        values = [display_text, size_text, type_text, attributes_text, last_modified_text, hash_text]
        tags = ()
        if 'ADS' in item_type:
            tags = ('ads_file_pre',)
        treeview.insert("", 'end', values=values, tags=tags)

    def get_file_description(self, mime_type):
        descriptions = {
            'image': self.translate("Image"),
            'audio': self.translate("Audio"),
            'video': self.translate("Video"),
            'application/pdf': self.translate("PDF Document"),
            'application/msword': self.translate("Word Document"),
            'application/vnd.ms-excel': self.translate("Excel Spreadsheet"),
            'application/vnd.ms-powerpoint': self.translate("PowerPoint Presentation"),
            'application/zip': self.translate("ZIP Archive"),
            'application/x-rar-compressed': self.translate("RAR Archive"),
            'application/gzip': self.translate("GZip Archive"),
            'application/x-7z-compressed': self.translate("7z Archive"),
            'application': self.translate("Application"),
            'text': self.translate("Document")
        }
        for key, value in descriptions.items():
            if mime_type and key in mime_type:
                return value
        return self.translate("Unknown")

    def get_last_modified(self, path):
        last_modified_timestamp = os.path.getmtime(path)
        last_modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_timestamp))
        return last_modified_time

    def update_column_visibility(self):
        columns_to_display = [self.translate("File Name")]
        if self.show_size.get():
            columns_to_display.append(self.translate("Size"))
        if self.show_type.get():
            columns_to_display.append(self.translate("Type"))
        if self.show_attributes.get():
            columns_to_display.append(self.translate("Attributes"))
        if self.show_last_modified.get():
            columns_to_display.append(self.translate("Last Modified"))
        if self.show_hash.get():
            columns_to_display.append(self.translate("Hash"))

        for tree in [self.file_tree1, self.file_tree2]:
            tree["columns"] = columns_to_display
            for col in columns_to_display:
                tree.heading(col, text=col)
                tree.column(col, width=100, minwidth=25, stretch=tk.YES)

            current_columns = set(tree["columns"])
            for col in list(current_columns):
                if col not in columns_to_display:
                    tree.column(col, width=0, minwidth=0, stretch=tk.NO)

            if tree == self.file_tree1 and self.last_directory1.get():
                self.list_files(self.file_tree1, self.last_directory1.get())
            elif tree == self.file_tree2 and self.last_directory2.get():
                self.list_files(self.file_tree2, self.last_directory2.get())

    def setup_traces(self):
        self.show_size.trace_add('write', lambda *args: self.update_column_visibility())
        self.show_type.trace_add('write', lambda *args: self.update_column_visibility())
        self.show_attributes.trace_add('write', lambda *args: self.update_column_visibility())
        self.show_last_modified.trace_add('write', lambda *args: self.update_column_visibility())
        self.show_hash.trace_add('write', lambda *args: self.update_column_visibility())
        self.language.trace_add('write', lambda *args: self.update_display())
        self.use_ads.trace_add('write', lambda *args: self.update_display())

    def update_display(self):
        self.compare_btn.config(text=self.translate("Compare"))
        self.ads_check.config(text=self.translate("Ads"))
        self.create_snapshot_btn1.config(text=self.translate("Create Snapshot"))
        self.load_snapshot_btn1.config(text=self.translate("Load Snapshot"))
        self.create_snapshot_btn2.config(text=self.translate("Create Snapshot"))
        self.load_snapshot_btn2.config(text=self.translate("Load Snapshot"))
        self.show_size_btn.config(text=self.translate("Show Size"))
        self.show_type_btn.config(text=self.translate("Show Type"))
        self.show_attributes_btn.config(text=self.translate("Show Attributes"))
        self.show_last_modified_btn.config(text=self.translate("Show Last Modified"))
        self.show_hash_btn.config(text=self.translate("Show Hash"))

        self.create_menu()
        self.update_column_visibility()

    def btn1_click(self):
        if self.last_directory1.get() or self.last_directory2.get():
            size_diff_files, only_in1_files, only_in2_files, only_in1_dirs, only_in2_dirs, size_diff_dirs = compare_directories(
                self.last_directory1.get(), self.last_directory2.get())
            self.update_comparison_results(only_in1_files, only_in2_files, size_diff_files, only_in1_dirs, only_in2_dirs, size_diff_dirs)
        else:
            messagebox.showinfo(self.translate("Error"), self.translate("At least one directory must be selected before comparing"))

if __name__ == "__main__":
    root = tk.Tk()
    app = Window(root)
    root.mainloop()