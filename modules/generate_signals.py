import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import paramiko
import threading
import os
import re


class SignalGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CME Signal Generator")
        self.root.geometry("750x600")
        self.root.configure(bg="#1e1e2e")
        
        # ЏгвЁ Є д ©« ¬
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.session_file = os.path.join(self.script_dir, 'last_session.json')
        
        # ‘вЁ«Ё
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TLabel', background='#1e1e2e', foreground='#cdd6f4', font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=10)
        self.style.configure('TFrame', background='#1e1e2e')
        self.style.map('TButton',
                       background=[('active', '#89b4fa'), ('!active', '#45475a')],
                       foreground=[('active', '#1e1e2e'), ('!active', '#cdd6f4')])
        
        # ‡ Јаг§Є  ­ бва®ҐЄ Ё Ї®б«Ґ¤­Ґ© бҐббЁЁ
        self.settings = self.load_settings()
        self.last_session = self.load_last_session()
        
        # Ћб­®ў­®© даҐ©¬
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ‡ Ј®«®ў®Є
        title_label = tk.Label(main_frame, text="? CME Signal Generator", 
                               font=('Segoe UI', 18, 'bold'), 
                               bg='#1e1e2e', fg='#f9e2af')
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(main_frame, text="ѓҐ­Ґа жЁп бЁЈ­ «®ў б  ўв®¬ вЁзҐбЄЁ¬ ЇаЁ¬Ґ­Ґ­ЁҐ¬ Є®­дЁЈ®ў", 
                                  font=('Segoe UI', 9), 
                                  bg='#1e1e2e', fg='#6c7086')
        subtitle_label.pack(pady=(0, 20))
        
        # ”аҐ©¬ ¤«п ¤ в
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=10)
        
        # Ќ з «м­ п ¤ в 
        start_label = ttk.Label(date_frame, text="Ќ з «м­ п ¤ в :")
        start_label.grid(row=0, column=0, padx=(0, 10), pady=5, sticky='e')
        
        self.start_date = DateEntry(date_frame, width=15, 
                                     background='#45475a', foreground='#cdd6f4',
                                     borderwidth=2, date_pattern='yyyy-mm-dd',
                                     font=('Segoe UI', 10))
        self.start_date.grid(row=0, column=1, pady=5, sticky='w')
        
        # Љ®­Ґз­ п ¤ в 
        end_label = ttk.Label(date_frame, text="Љ®­Ґз­ п ¤ в :")
        end_label.grid(row=1, column=0, padx=(0, 10), pady=5, sticky='e')
        
        self.end_date = DateEntry(date_frame, width=15,
                                   background='#45475a', foreground='#cdd6f4',
                                   borderwidth=2, date_pattern='yyyy-mm-dd',
                                   font=('Segoe UI', 10))
        self.end_date.grid(row=1, column=1, pady=5, sticky='w')
        
        # ЏаЁ¬Ґ­пҐ¬ б®еа ­с­­лҐ ¤ вл
        self.apply_saved_dates()
        
        # –Ґ­ваЁа®ў ­ЁҐ даҐ©¬  ¤ в
        date_frame.columnconfigure(0, weight=1)
        date_frame.columnconfigure(2, weight=1)
        
        # ”аҐ©¬ ¤«п зҐЄЎ®Єб®ў
        self.style.configure('TCheckbutton', background='#1e1e2e', foreground='#cdd6f4', 
                            font=('Segoe UI', 9))
        self.style.map('TCheckbutton',
                      background=[('active', '#1e1e2e')],
                      foreground=[('active', '#cdd6f4')])
        
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.pack(fill=tk.X, pady=10)
        
        checkbox_label = tk.Label(checkbox_frame, text="ќв Їл ўлЇ®«­Ґ­Ёп:", 
                                  font=('Segoe UI', 10, 'bold'),
                                  bg='#1e1e2e', fg='#cdd6f4')
        checkbox_label.pack(anchor='w')
        
        # ЏҐаҐ¬Ґ­­лҐ ¤«п зҐЄЎ®Єб®ў
        self.run_features_calculator = tk.BooleanVar(value=True)
        self.run_rscript = tk.BooleanVar(value=True)
        self.run_signal_processing = tk.BooleanVar(value=True)
        self.run_cleanup = tk.BooleanVar(value=True)
        
        # ‡ Јаг¦ Ґ¬ б®еа ­с­­лҐ §­ зҐ­Ёп
        self.apply_saved_checkboxes()
        
        cb1 = ttk.Checkbutton(checkbox_frame, text="‡ ЇгбЄ FeaturesCalculator", 
                              variable=self.run_features_calculator)
        cb1.pack(anchor='w', padx=20)
        
        cb2 = ttk.Checkbutton(checkbox_frame, text="‡ ЇгбЄ R бЄаЁЇв ", 
                              variable=self.run_rscript)
        cb2.pack(anchor='w', padx=20)
        
        cb3 = ttk.Checkbutton(checkbox_frame, text="ЋЎа Ў®вЄ  д ©«®ў Ё а бЄЁ¤лў ­ЁҐ Ї® Ї ЇЄ ¬", 
                              variable=self.run_signal_processing)
        cb3.pack(anchor='w', padx=20)
        
        cb4 = ttk.Checkbutton(checkbox_frame, text="“¤ «Ґ­ЁҐ temp Ї Ї®Є", 
                              variable=self.run_cleanup)
        cb4.pack(anchor='w', padx=20)
        
        # ”аҐ©¬ ¤«п Є­®Ї®Є
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10)
        
        # Љ­®ЇЄ  § ЇгбЄ 
        self.run_button = tk.Button(buttons_frame, text="? ‡ ЇгбвЁвм ЈҐ­Ґа жЁо бЁЈ­ «®ў",
                                     font=('Segoe UI', 11, 'bold'),
                                     bg='#f9e2af', fg='#1e1e2e',
                                     activebackground='#f5c2e7', activeforeground='#1e1e2e',
                                     relief=tk.FLAT, padx=20, pady=10,
                                     cursor='hand2',
                                     command=self.start_generation)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        # Љ­®ЇЄ  ЇаҐ®Ўа §®ў ­Ёп д ©« 
        self.convert_button = tk.Button(buttons_frame, text="?? ЏаҐ®Ўа §®ў вм д ©«",
                                         font=('Segoe UI', 11, 'bold'),
                                         bg='#89b4fa', fg='#1e1e2e',
                                         activebackground='#b4befe', activeforeground='#1e1e2e',
                                         relief=tk.FLAT, padx=20, pady=10,
                                         cursor='hand2',
                                         command=self.open_file_browser)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        # ‚Є« ¤ЄЁ ¤«п «®Ј®ў
        self.style.configure('TNotebook', background='#1e1e2e')
        self.style.configure('TNotebook.Tab', background='#45475a', foreground='#cdd6f4', 
                            font=('Segoe UI', 9, 'bold'), padding=[10, 5])
        self.style.map('TNotebook.Tab',
                      background=[('selected', '#89b4fa')],
                      foreground=[('selected', '#1e1e2e')])
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # ‚Є« ¤Є  1: Ћб­®ў­®© «®Ј
        main_log_frame = ttk.Frame(notebook)
        notebook.add(main_log_frame, text='?? Ћб­®ў­®© «®Ј')
        
        self.log_text = scrolledtext.ScrolledText(main_log_frame, 
                                                   height=18, 
                                                   font=('Consolas', 9),
                                                   bg='#11111b', fg='#cdd6f4',
                                                   insertbackground='#cdd6f4',
                                                   relief=tk.FLAT,
                                                   wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ‚Є« ¤Є  2: Џ®«­л© «®Ј ўлзЁб«Ґ­Ё©
        fc_log_frame = ttk.Frame(notebook)
        notebook.add(fc_log_frame, text='?? Џ®«­л© «®Ј ўлзЁб«Ґ­Ё©')
        
        self.fc_log_text = scrolledtext.ScrolledText(fc_log_frame, 
                                                      height=18, 
                                                      font=('Consolas', 9),
                                                      bg='#11111b', fg='#a6adc8',
                                                      insertbackground='#cdd6f4',
                                                      relief=tk.FLAT,
                                                      wrap=tk.WORD)
        self.fc_log_text.pack(fill=tk.BOTH, expand=True)
        
        # ’ҐЈЁ ¤«п ®б­®ў­®Ј® «®Ј 
        self.log_text.tag_configure('error', foreground='#f38ba8')
        self.log_text.tag_configure('success', foreground='#a6e3a1')
        self.log_text.tag_configure('info', foreground='#89b4fa')
        self.log_text.tag_configure('warning', foreground='#f9e2af')
        self.log_text.tag_configure('interval', foreground='#cba6f7')
        
        # ’ҐЈЁ ¤«п «®Ј  FeaturesCalculator
        self.fc_log_text.tag_configure('error', foreground='#f38ba8')
        self.fc_log_text.tag_configure('info', foreground='#89b4fa')
        
        self.log("Приложение запущено. Выберите даты и нажмите 'Запустить'.", "info")
    
    def load_settings(self):
        """‡ Јаг§Є  ­ бва®ҐЄ Ё§ settings.json"""
        settings_path = os.path.join(self.script_dir, 'settings.json')
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {}
    
    def load_last_session(self):
        """‡ Јаг§Є  ¤ ­­ле Ї®б«Ґ¤­Ґ© бҐббЁЁ"""
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def save_last_session(self, start_date, end_date):
        """‘®еа ­Ґ­ЁҐ ¤ в Ё б®бв®п­Ёп зҐЄЎ®Єб®ў Ї®б«Ґ¤­Ґ© бҐббЁЁ"""
        session_data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'run_features_calculator': self.run_features_calculator.get(),
            'run_rscript': self.run_rscript.get(),
            'run_signal_processing': self.run_signal_processing.get(),
            'run_cleanup': self.run_cleanup.get()
        }
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            self.log(f"Не удалось сохранить сессию: {e}", "warning")
    
    def apply_saved_dates(self):
        """ЏаЁ¬Ґ­Ґ­ЁҐ б®еа ­с­­ле ¤ в Є Ї®«п¬ ўў®¤ """
        if self.last_session:
            try:
                if 'start_date' in self.last_session:
                    start = datetime.strptime(self.last_session['start_date'], '%Y-%m-%d').date()
                    self.start_date.set_date(start)
                if 'end_date' in self.last_session:
                    end = datetime.strptime(self.last_session['end_date'], '%Y-%m-%d').date()
                    self.end_date.set_date(end)
            except Exception:
                pass  # …б«Ё ¤ вл ­ҐЄ®ааҐЄв­лҐ, ЁбЇ®«м§гҐ¬ вҐЄгйго ¤ вг
    
    def apply_saved_checkboxes(self):
        """ЏаЁ¬Ґ­Ґ­ЁҐ б®еа ­с­­ле б®бв®п­Ё© зҐЄЎ®Єб®ў"""
        if self.last_session:
            if 'run_features_calculator' in self.last_session:
                self.run_features_calculator.set(self.last_session['run_features_calculator'])
            if 'run_rscript' in self.last_session:
                self.run_rscript.set(self.last_session['run_rscript'])
            if 'run_signal_processing' in self.last_session:
                self.run_signal_processing.set(self.last_session['run_signal_processing'])
            if 'run_cleanup' in self.last_session:
                self.run_cleanup.set(self.last_session['run_cleanup'])
    
    def log(self, message, tag=None):
        """„®Ў ў«Ґ­ЁҐ б®®ЎйҐ­Ёп ў ®б­®ў­®© «®Ј"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.configure(state='normal')
        if tag:
            self.log_text.insert(tk.END, formatted_message, tag)
        else:
            self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        self.root.update_idletasks()
    
    def log_fc(self, message, tag=None):
        """„®Ў ў«Ґ­ЁҐ б®®ЎйҐ­Ёп ў «®Ј FeaturesCalculator"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.fc_log_text.configure(state='normal')
        if tag:
            self.fc_log_text.insert(tk.END, formatted_message, tag)
        else:
            self.fc_log_text.insert(tk.END, formatted_message)
        self.fc_log_text.see(tk.END)
        self.fc_log_text.configure(state='disabled')
        self.root.update_idletasks()
    
    def open_file_browser(self):
        """ЋвЄалвЁҐ д ©«®ў®Ј® Ўа г§Ґа  ¤«п ўлЎ®а  д ©«  ­  бҐаўҐаҐ"""
        # Џа®ўҐаЄ  ­ бва®ҐЄ
        if not self.settings:
            self.log("Ошибка: Не удалось загрузить settings.json", "error")
            return
        
        ssh_username = self.settings.get('SSH_USERNAME')
        ssh_key_path = self.settings.get('SSH_KEY_PATH')
        remote_host = self.settings.get('REMOTE_HOST')
        signal_folder = self.settings.get('SIGNAL_FOLDER', '').rstrip('/')
        
        if not all([ssh_username, ssh_key_path, remote_host, signal_folder]):
            self.log("Ошибка: Не все параметры указаны в settings.json", "error")
            return
        
        # ‘®§¤ с¬ ®Є­® Ўа г§Ґа 
        browser = tk.Toplevel(self.root)
        browser.title("‚лЎ®а д ©«  ­  бҐаўҐаҐ")
        browser.geometry("600x500")
        browser.configure(bg="#1e1e2e")
        browser.transient(self.root)
        browser.grab_set()
        
        # ’ҐЄгйЁ© Їгвм
        current_path = tk.StringVar(value=signal_folder)
        
        # ”аҐ©¬ ¤«п ЇгвЁ
        path_frame = ttk.Frame(browser)
        path_frame.pack(fill=tk.X, padx=10, pady=10)
        
        path_label = tk.Label(path_frame, text="Џгвм:", bg='#1e1e2e', fg='#cdd6f4', font=('Segoe UI', 10))
        path_label.pack(side=tk.LEFT)
        
        path_entry = tk.Entry(path_frame, textvariable=current_path, font=('Consolas', 10),
                             bg='#45475a', fg='#cdd6f4', insertbackground='#cdd6f4', relief=tk.FLAT)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # ‘ЇЁб®Є д ©«®ў
        list_frame = ttk.Frame(browser)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        file_listbox = tk.Listbox(list_frame, font=('Consolas', 10),
                                   bg='#11111b', fg='#cdd6f4',
                                   selectbackground='#89b4fa', selectforeground='#1e1e2e',
                                   relief=tk.FLAT, yscrollcommand=scrollbar.set)
        file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=file_listbox.yview)
        
        # ‚лЎа ­­л© д ©«
        selected_file = tk.StringVar()
        
        selected_label = tk.Label(browser, textvariable=selected_file, 
                                  bg='#1e1e2e', fg='#a6e3a1', font=('Segoe UI', 9))
        selected_label.pack(pady=5)
        
        def load_files(path):
            """‡ Јаг§Є  бЇЁбЄ  д ©«®ў б бҐаўҐа """
            file_listbox.delete(0, tk.END)
            selected_file.set("")
            
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                private_key = paramiko.Ed25519Key.from_private_key_file(ssh_key_path)
                ssh.connect(hostname=remote_host, username=ssh_username, pkey=private_key, timeout=10)
                
                # Џ®«гз Ґ¬ бЇЁб®Є д ©«®ў Ё Ї Ї®Є
                cmd = f"ls -la {path} 2>/dev/null | tail -n +2"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                output = stdout.read().decode('utf-8')
                ssh.close()
                
                # „®Ў ў«пҐ¬ ".." ¤«п ЇҐаҐе®¤  ўўҐае
                if path != '/':
                    file_listbox.insert(tk.END, "?? ..")
                
                for line in output.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 9:
                        name = ' '.join(parts[8:])
                        if name in ['.', '..']:
                            continue
                        if line.startswith('d'):
                            file_listbox.insert(tk.END, f"?? {name}")
                        else:
                            file_listbox.insert(tk.END, f"?? {name}")
                
            except Exception as e:
                file_listbox.insert(tk.END, f"ЋиЁЎЄ : {str(e)}")
        
        def on_double_click(event):
            """ЋЎа Ў®вЄ  ¤ў®©­®Ј® Є«ЁЄ """
            selection = file_listbox.curselection()
            if not selection:
                return
            
            item = file_listbox.get(selection[0])
            name = item[2:].strip()  # “ЎЁа Ґ¬ ЁЄ®­Єг
            
            if item.startswith("??"):
                # ќв® Ї ЇЄ  - ЇҐаҐе®¤Ё¬ ў ­Ґс
                if name == "..":
                    new_path = '/'.join(current_path.get().rstrip('/').split('/')[:-1])
                    if not new_path:
                        new_path = '/'
                else:
                    new_path = f"{current_path.get().rstrip('/')}/{name}"
                current_path.set(new_path)
                load_files(new_path)
            else:
                # ќв® д ©« - ўлЎЁа Ґ¬ ҐЈ®
                on_select(None)
        
        def on_select(event):
            """ЋЎа Ў®вЄ  ўлЎ®а  д ©« """
            selection = file_listbox.curselection()
            if not selection:
                return
            
            item = file_listbox.get(selection[0])
            if item.startswith("??"):
                name = item[2:].strip()
                full_path = f"{current_path.get().rstrip('/')}/{name}"
                selected_file.set(f"‚лЎа ­: {full_path}")
        
        file_listbox.bind('<Double-1>', on_double_click)
        file_listbox.bind('<<ListboxSelect>>', on_select)
        
        def go_to_path():
            """ЏҐаҐе®¤ Ї® ўўҐ¤с­­®¬г ЇгвЁ"""
            load_files(current_path.get())
        
        go_button = tk.Button(path_frame, text="", font=('Segoe UI', 10, 'bold'),
                             bg='#45475a', fg='#cdd6f4', relief=tk.FLAT,
                             command=go_to_path)
        go_button.pack(side=tk.LEFT)
        
        # Љ­®ЇЄЁ
        buttons_frame = ttk.Frame(browser)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def convert_selected():
            """ЏаҐ®Ўа §®ў ­ЁҐ ўлЎа ­­®Ј® д ©« """
            if not selected_file.get():
                return
            
            file_path = selected_file.get().replace("‚лЎа ­: ", "")
            browser.destroy()
            
            # ‡ ЇгбЄ Ґ¬ ЇаҐ®Ўа §®ў ­ЁҐ ў ®в¤Ґ«м­®¬ Ї®в®ЄҐ
            thread = threading.Thread(target=lambda: self.convert_file(file_path), daemon=True)
            thread.start()
        
        convert_btn = tk.Button(buttons_frame, text="? ЏаҐ®Ўа §®ў вм",
                                font=('Segoe UI', 10, 'bold'),
                                bg='#a6e3a1', fg='#1e1e2e',
                                relief=tk.FLAT, padx=15, pady=5,
                                command=convert_selected)
        convert_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = tk.Button(buttons_frame, text="? Ћв¬Ґ­ ",
                               font=('Segoe UI', 10, 'bold'),
                               bg='#f38ba8', fg='#1e1e2e',
                               relief=tk.FLAT, padx=15, pady=5,
                               command=browser.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # ‡ Јаг¦ Ґ¬ ­ з «м­го Ї ЇЄг
        load_files(signal_folder)
    
    def convert_file(self, file_path):
        """ЏаҐ®Ўа §®ў ­ЁҐ д ©«  ­  бҐаўҐаҐ зҐаҐ§ бҐаўҐа­л© бЄаЁЇв"""
        self.log(f"\n{'='*50}", 'info')
        self.log(f"Преобразование файла: {file_path}", "warning")
        
        ssh_username = self.settings.get('SSH_USERNAME')
        ssh_key_path = self.settings.get('SSH_KEY_PATH')
        remote_host = self.settings.get('REMOTE_HOST')
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            private_key = paramiko.Ed25519Key.from_private_key_file(ssh_key_path)
            ssh.connect(hostname=remote_host, username=ssh_username, pkey=private_key, timeout=30)
            
            self.log("SSH Ї®¤Є«озҐ­ЁҐ гбв ­®ў«Ґ­®", 'success')
            
            # ‡ Јаг¦ Ґ¬ бҐаўҐа­л© бЄаЁЇв
            sftp = ssh.open_sftp()
            remote_script_path = self.upload_server_script(sftp, ssh_username)
            sftp.close()
            self.log(f"Скрипт загружен: {remote_script_path}", "info")
            
            # ‡ ЇгбЄ Ґ¬ бҐаўҐа­л© бЄаЁЇв б Ї а ¬Ґва®¬ --convert
            cmd = f"python3 {remote_script_path} --convert '{file_path}'"
            self.log(f"Запуск: {cmd}", "info")
            
            stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
            
            # —Ёв Ґ¬ ўлў®¤
            while True:
                line = stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("DONE:"):
                    self.log(f"✓ {line.replace('DONE:', '').strip()}", 'success')
                elif line.startswith("ERROR:"):
                    self.log(f"✗ {line}", 'error')
                elif line.startswith("INFO:"):
                    self.log(f"  {line.replace('INFO:', '').strip()}", 'info')
            
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8')
                if error_output:
                    self.log(f"Stderr: {error_output}", 'error')
            
            ssh.close()
            self.log("SSH соединение закрыто", "info")
            
        except Exception as e:
            self.log(f"Ошибка: {str(e)}", "error")
    
    def start_generation(self):
        """‡ ЇгбЄ ЈҐ­Ґа жЁЁ ў ®в¤Ґ«м­®¬ Ї®в®ЄҐ"""
        self.run_button.configure(state='disabled', bg='#6c7086')
        thread = threading.Thread(target=self.generate_signals, daemon=True)
        thread.start()
    
    def parse_config_filename(self, filename):
        """Џ абЁ­Ј ¤ вл Ё§ Ё¬Ґ­Ё д ©«  д®а¬ в  dd-mm-yyyy.json"""
        match = re.match(r'(\d{2})-(\d{2})-(\d{4})\.json', filename)
        if match:
            day, month, year = match.groups()
            return datetime(int(year), int(month), int(day)).date()
        return None
    
    def get_config_files_list(self, ssh, config_history_path):
        """Џ®«гзҐ­ЁҐ бЇЁбЄ  д ©«®ў Є®­дЁЈ®ў б ¤ в ¬Ё"""
        stdin, stdout, stderr = ssh.exec_command(f"ls -1 {config_history_path}")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            return []
        
        files = stdout.read().decode('utf-8').strip().split('\n')
        config_files = []
        
        for f in files:
            f = f.strip()
            if f:
                date = self.parse_config_filename(f)
                if date:
                    config_files.append((date, f))
        
        # ‘®авЁа®ўЄ  Ї® ¤ вҐ
        config_files.sort(key=lambda x: x[0])
        return config_files
    
    def split_interval_by_configs(self, start_date, end_date, config_files):
        """ђ §ЎЁҐ­ЁҐ Ё­вҐаў «  ­  Ї®¤-Ё­вҐаў «л б®Ј« б­® д ©« ¬ Є®­дЁЈ®ў"""
        intervals = []
        
        # Ќ е®¤Ё¬ д ©«, Є®в®ал© ЇаЁ¬Ґ­пҐвбп Є start_date
        # ќв® д ©« б ¬ ЄбЁ¬ «м­®© ¤ в®© <= start_date
        applicable_config = None
        for config_date, config_file in config_files:
            if config_date <= start_date:
                applicable_config = (config_date, config_file)
            else:
                break
        
        if applicable_config is None:
            # ЌҐв Ї®¤е®¤пйҐЈ® Є®­дЁЈ 
            return []
        
        current_start = start_date
        current_config = applicable_config
        
        # Џа®е®¤Ё¬ Ї® ўбҐ¬ Є®­дЁЈ ¬ Ї®б«Ґ applicable_config
        for i, (config_date, config_file) in enumerate(config_files):
            if config_date <= current_config[0]:
                continue
            
            if config_date > end_date:
                # ќв®в Є®­дЁЈ §  ЇаҐ¤Ґ« ¬Ё ­ иҐЈ® Ё­вҐаў « 
                break
            
            # €­вҐаў « ®в current_start ¤® (config_date - 1 ¤Ґ­м)
            interval_end = config_date - timedelta(days=1)
            if interval_end >= current_start:
                intervals.append({
                    'start': current_start,
                    'end': interval_end,
                    'config_file': current_config[1]
                })
            
            # ЏҐаҐе®¤Ё¬ Є б«Ґ¤гойҐ¬г Ё­вҐаў «г
            current_start = config_date
            current_config = (config_date, config_file)
        
        # „®Ў ў«пҐ¬ Ї®б«Ґ¤­Ё© Ё­вҐаў « ¤® end_date
        if current_start <= end_date:
            intervals.append({
                'start': current_start,
                'end': end_date,
                'config_file': current_config[1]
            })
        
        return intervals
    
    def read_remote_file(self, ssh, path):
        """—вҐ­ЁҐ д ©«  ­  г¤ «с­­®¬ е®бвҐ"""
        stdin, stdout, stderr = ssh.exec_command(f"cat {path}")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode('utf-8')
            raise Exception(f"ЋиЁЎЄ  звҐ­Ёп {path}: {error}")
        return stdout.read().decode('utf-8')
    
    def clean_json_string(self, json_str):
        """ЋзЁбвЄ  JSON ®в Є®¬¬Ґ­в аЁҐў, trailing commas Ё гЇа ў«пойЁе бЁ¬ў®«®ў"""
        # “¤ «пҐ¬ гЇа ў«пойЁҐ бЁ¬ў®«л (Єа®¬Ґ \n, \r, \t)
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)
        # ‡ ¬Ґ­пҐ¬ \r\n Ё \r ­  \n
        json_str = json_str.replace('\r\n', '\n').replace('\r', '\n')
        # “¤ «пҐ¬ ®¤­®бва®з­лҐ Є®¬¬Ґ­в аЁЁ // ... (­® ­Ґ ў­гваЁ бва®Є)
        json_str = re.sub(r'(?<!:)//.*?(?=\n|$)', '', json_str)
        # “¤ «пҐ¬ ¬­®Ј®бва®з­лҐ Є®¬¬Ґ­в аЁЁ /* ... */
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        # “¤ «пҐ¬ trailing commas ЇҐаҐ¤ } Ё«Ё ]
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        return json_str
    
    def parse_json_safe(self, json_str):
        """ЃҐ§®Ї б­л© Ї абЁ­Ј JSON б ®зЁбвЄ®©"""
        cleaned = self.clean_json_string(json_str)
        return json.loads(cleaned)
    
    def write_remote_file(self, ssh, path, content):
        """‡ ЇЁбм д ©«  ­  г¤ «с­­®¬ е®бвҐ"""
        # ќЄа ­ЁагҐ¬ ®¤Ё­ а­лҐ Є ўлзЄЁ ў Є®­вҐ­вҐ
        escaped_content = content.replace("'", "'\"'\"'")
        cmd = f"echo '{escaped_content}' > {path}"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode('utf-8')
            raise Exception(f"ЋиЁЎЄ  § ЇЁбЁ {path}: {error}")
    
    def write_remote_file_sftp(self, sftp, path, content):
        """‡ ЇЁбм д ©«  зҐаҐ§ SFTP"""
        with sftp.file(path, 'w') as f:
            f.write(content)
    
    def upload_server_script(self, sftp, ssh_username):
        """‡ Јаг§Є  бҐаўҐа­®Ј® бЄаЁЇв  ­  бҐаўҐа"""
        server_script_path = os.path.join(self.script_dir, 'process_signals_server.py')
        remote_dir = f"/home/{ssh_username}/PythonScripts"
        remote_path = f"{remote_dir}/process_signals_server.py"
        
        # —Ёв Ґ¬ «®Є «м­л© бЄаЁЇв
        with open(server_script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # ‘®§¤ с¬ Ї ЇЄг Ё § ЇЁблў Ґ¬ бЄаЁЇв
        try:
            sftp.mkdir(remote_dir)
        except IOError:
            pass  # Џ ЇЄ  г¦Ґ бгйҐбвўгҐв
        
        self.write_remote_file_sftp(sftp, remote_path, script_content)
        return remote_path
    
    def process_signal_files(self, ssh, sftp, signal_folder, config_history_path, ssh_username):
        """ЋЎа Ў®вЄ  д ©«®ў бЁЈ­ «®ў зҐаҐ§ бҐаўҐа­л© бЄаЁЇв"""
        # ‡ Јаг¦ Ґ¬ бҐаўҐа­л© бЄаЁЇв
        self.log("Загрузка серверного скрипта...", "info")
        remote_script_path = self.upload_server_script(sftp, ssh_username)
        self.log(f"✓ Скрипт загружен: {remote_script_path}", "success")
        
        # ‡ ЇгбЄ Ґ¬ бҐаўҐа­л© бЄаЁЇв
        cmd = f"python3 {remote_script_path} {signal_folder} {config_history_path}"
        self.log(f"Запуск: {cmd}", "info")
        
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        
        # —Ёв Ґ¬ ўлў®¤ Ё «®ЈЁагҐ¬
        self.log_fc("=== ‡ ЇгбЄ бҐаўҐа­®Ј® бЄаЁЇв  ®Ўа Ў®вЄЁ бЁЈ­ «®ў ===", 'info')
        
        while True:
            line = stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            
            self.log_fc(line)
            
            # Џ абЁ¬ ўлў®¤ ¤«п ®б­®ў­®Ј® «®Ј 
            if line.startswith("PROGRESS:"):
                # PROGRESS: 5/40
                progress_part = line.replace("PROGRESS:", "").strip()
                self.log(f"  ✓ Обработано файлов: {progress_part}", "info")
            elif line.startswith("DONE:"):
                self.log(f"  ✓ {line.replace('DONE:', '')}", 'success')
            elif line.startswith("ERROR:"):
                self.log(f"  ⚠ {line}", "warning")
            elif line.startswith("INFO:"):
                self.log(f"  • {line.replace('INFO:', '')}", 'info')
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            error_output = stderr.read().decode('utf-8')
            self.log(f"‘ҐаўҐа­л© бЄаЁЇв § ўҐаиЁ«бп б ®иЁЎЄ®© (Є®¤ {exit_status})", 'error')
            if error_output:
                self.log(f"Stderr: {error_output}", 'error')
        else:
            self.log("? ЋЎа Ў®вЄ  д ©«®ў бЁЈ­ «®ў § ўҐаиҐ­ ", 'success')
    
    def generate_signals(self):
        """Ћб­®ў­ п «®ЈЁЄ  ЈҐ­Ґа жЁЁ бЁЈ­ «®ў"""
        try:
            start = self.start_date.get_date()
            end = self.end_date.get_date()
            
            # ‘®еа ­пҐ¬ ¤ вл ¤«п б«Ґ¤гойҐЈ® § ЇгбЄ 
            self.save_last_session(start, end)
            
            self.log(f"‚лЎа ­­л© ЇҐаЁ®¤: {start} - {end}", 'info')
            
            # Џа®ўҐаЄ  ­ бва®ҐЄ
            if not self.settings:
                self.log("Ошибка: Не удалось загрузить settings.json", "error")
                return
            
            ssh_username = self.settings.get('SSH_USERNAME')
            ssh_key_path = self.settings.get('SSH_KEY_PATH')
            remote_host = self.settings.get('REMOTE_HOST')
            signal_folder = self.settings.get('SIGNAL_FOLDER')
            
            if not all([ssh_username, ssh_key_path, remote_host, signal_folder]):
                self.log("Ошибка: Не все параметры указаны в settings.json", "error")
                return
            
            self.log(f"Џ®¤Є«озҐ­ЁҐ Є {remote_host} Є Є {ssh_username}...")
            
            # SSH Ї®¤Є«озҐ­ЁҐ
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                # ‡ Јаг§Є  ЇаЁў в­®Ј® Є«оз 
                private_key = paramiko.Ed25519Key.from_private_key_file(ssh_key_path)
                
                ssh.connect(
                    hostname=remote_host,
                    username=ssh_username,
                    pkey=private_key,
                    timeout=30
                )
                
                self.log("SSH Ї®¤Є«озҐ­ЁҐ гбв ­®ў«Ґ­®!", 'success')
                
                # ЋвЄалў Ґ¬ SFTP ¤«п § ЇЁбЁ д ©«®ў
                sftp = ssh.open_sftp()
                
                # ЏгвЁ
                config_history_path = f"{signal_folder.rstrip('/')}/ConfigHistory"
                dest_backup_path = f"/home/{ssh_username}/CMESignals/ConfigHistory"
                base_config_path = f"/home/{ssh_username}/build/FeaturesCalculator/Configs/Cme/Features/Local"
                
                instruments_path = f"{base_config_path}/Instruments.json"
                config_cme_local_path = f"{base_config_path}/ConfigCmeLocal.json"
                signal_printer_path = f"{base_config_path}/SignalPrinter.json"
                features_calculator_path = f"/home/{ssh_username}/build/FeaturesCalculator/RelCmeLocal/FeaturesCalculator"
                
                # 1. ЃнЄ Ї ConfigHistory
                self.log("‘®§¤ ­ЁҐ ЎнЄ Ї  ConfigHistory...", 'info')
                mkdir_cmd = f"mkdir -p {dest_backup_path}"
                ssh.exec_command(mkdir_cmd)
                
                copy_cmd = f"cp -r {config_history_path}/* {dest_backup_path}/ 2>/dev/null || true"
                stdin, stdout, stderr = ssh.exec_command(copy_cmd)
                stdout.channel.recv_exit_status()
                self.log("ЃнЄ Ї ConfigHistory ўлЇ®«­Ґ­", 'success')
                
                # 2. Џ®«гзҐ­ЁҐ бЇЁбЄ  д ©«®ў Є®­дЁЈ®ў
                self.log("Џ®«гзҐ­ЁҐ бЇЁбЄ  д ©«®ў Є®­дЁЈга жЁЁ...", 'info')
                config_files = self.get_config_files_list(ssh, config_history_path)
                
                if not config_files:
                    self.log("ЌҐ ­ ©¤Ґ­® д ©«®ў Є®­дЁЈга жЁЁ ў ConfigHistory", 'error')
                    return
                
                self.log(f"Ќ ©¤Ґ­® {len(config_files)} д ©«®ў Є®­дЁЈга жЁЁ:", 'info')
                for cfg_date, cfg_file in config_files:
                    self.log(f"   {cfg_file} ({cfg_date})")
                
                # 3. ђ §ЎЁҐ­ЁҐ Ё­вҐаў « 
                intervals = self.split_interval_by_configs(start, end, config_files)
                
                # 4. ЋЎа Ў®вЄ  Є ¦¤®Ј® Ё­вҐаў «  (Ґб«Ё ўЄ«озс­ FeaturesCalculator)
                if self.run_features_calculator.get():
                    if not intervals:
                        if start > end:
                            self.log(f"?? Ќ з «м­ п ¤ в  ({start}) > Є®­Ґз­®© ({end}). FeaturesCalculator ­Ґ Ўг¤Ґв § ЇгйҐ­.", 'warning')
                        else:
                            self.log("?? ЌҐ г¤ «®бм а §ЎЁвм Ё­вҐаў «. ЌҐв Ї®¤е®¤пйЁе Є®­дЁЈ®ў. FeaturesCalculator ­Ґ Ўг¤Ґв § ЇгйҐ­.", 'warning')
                    else:
                        self.log(f"\n€­вҐаў « а §ЎЁв ­  {len(intervals)} з бвҐ©:", 'warning')
                        for i, interval in enumerate(intervals, 1):
                            self.log(f"  {i}. {interval['start']} - {interval['end']}  {interval['config_file']}", 'interval')
                    
                    for i, interval in enumerate(intervals, 1):
                        self.log(f"\n{'='*50}", 'info')
                        self.log(f"ЋЎа Ў®вЄ  Ё­вҐаў «  {i}/{len(intervals)}", 'warning')
                        self.log(f"ЏҐаЁ®¤: {interval['start']} - {interval['end']}", 'interval')
                        self.log(f"Љ®­дЁЈ: {interval['config_file']}", 'interval')
                        
                        # 4.1. —Ёв Ґ¬ Ё ¬®¤ЁдЁжЁагҐ¬ Instruments.json
                        config_file_path = f"{config_history_path}/{interval['config_file']}"
                        self.log(f"‡ Јаг§Є  Є®­дЁЈ : {config_file_path}")
                        
                        config_content = self.read_remote_file(ssh, config_file_path)
                        config_json = self.parse_json_safe(config_content)
                        
                        # ђҐЄгабЁў­ п § ¬Ґ­  ўбҐе SharedFeedMode ­  'Local'
                        def replace_feed_mode(obj):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    if key == 'SharedFeedMode':
                                        obj[key] = 'Local'
                                    else:
                                        replace_feed_mode(value)
                            elif isinstance(obj, list):
                                for item in obj:
                                    replace_feed_mode(item)
                        
                        replace_feed_mode(config_json)
                        modified_config = config_json
                        
                        instruments_content = json.dumps(modified_config, indent=2)
                        self.write_remote_file_sftp(sftp, instruments_path, instruments_content)
                        self.log(f"? ‡ ЇЁб ­ Instruments.json (SharedFeedMode: Local)", 'success')
                        
                        # 4.2. ЋЎ­®ў«пҐ¬ ConfigCmeLocal.json
                        self.log("ЋЎ­®ў«Ґ­ЁҐ ConfigCmeLocal.json...", "info")
                        cme_local_content = self.read_remote_file(ssh, config_cme_local_path)
                        cme_local_json = self.parse_json_safe(cme_local_content)
                        
                        # ”®а¬ вЁагҐ¬ ¤ вл Є Є yyyy-mm-dd:yyyy-mm-dd
                        date_range = f"{interval['start'].strftime('%Y-%m-%d')}:{interval['end'].strftime('%Y-%m-%d')}"
                        
                        if 'ManyDatesConfig' in cme_local_json:
                            cme_local_json['ManyDatesConfig']['Dates'] = [date_range]
                        else:
                            cme_local_json['ManyDatesConfig'] = {
                                'CoresCount': 5,
                                'Dates': [date_range]
                            }
                        
                        cme_local_content = json.dumps(cme_local_json, indent=2)
                        self.write_remote_file_sftp(sftp, config_cme_local_path, cme_local_content)
                        self.log(f"? ‡ ЇЁб ­ ConfigCmeLocal.json (Dates: {date_range})", 'success')
                        
                        # 4.3. ЋЎ­®ў«пҐ¬ SignalPrinter.json
                        self.log("ЋЎ­®ў«Ґ­ЁҐ SignalPrinter.json...", "info")
                        signal_printer_content = self.read_remote_file(ssh, signal_printer_path)
                        signal_printer_json = self.parse_json_safe(signal_printer_content)
                        
                        signal_printer_json['FolderWithSignal'] = f"{signal_folder.rstrip('/')}/temp"
                        signal_printer_json['FileNameSuffix'] = '_signal'
                        
                        signal_printer_content = json.dumps(signal_printer_json, indent=2)
                        self.write_remote_file_sftp(sftp, signal_printer_path, signal_printer_content)
                        self.log(f"? ‡ ЇЁб ­ SignalPrinter.json", 'success')
                        
                        # 4.4. ‡ ЇгбЄ FeaturesCalculator
                        self.log(f"‡ ЇгбЄ FeaturesCalculator ¤«п Ё­вҐаў «  {interval['start']} - {interval['end']}...", 'warning')
                        
                        # ‡ ЇгбЄ Ґ¬ Ё§ ¤ЁаҐЄв®аЁЁ, Ј¤Ґ ­ е®¤Ёвбп ЁбЇ®«­пҐ¬л© д ©«
                        features_calculator_dir = f"/home/{ssh_username}/build/FeaturesCalculator/RelCmeLocal"
                        run_cmd = f"cd {features_calculator_dir} && ./FeaturesCalculator"
                        stdin, stdout, stderr = ssh.exec_command(run_cmd, get_pty=True)
                        
                        # ”Ё«мвагҐ¬лҐ Ї®¤бва®ЄЁ (бЇ ¬ ®в FeaturesCalculator)
                        filter_patterns = [
                            'LvlImpliedCrossReal',
                            'Clock MANUAL OVERRIDE',
                            'Cannot find date for last mid manager',
                            '#STDOFF',
                            'Cannot find expression file',
                            'RunCmeOneDay',
                            'Complete init one_feed_processors',
                            'Start read local dump',
                            'Gap in  snap',
                            'GAP in online feed',
                            'All instrument snap completed',
                            'All data snap completed',
                            'LvlCme.',
                            'Change IsOnline',
                        ]
                        
                        # Џ ввҐа­ ¤«п Ё§ў«ҐзҐ­Ёп Їа®ЈаҐбб 
                        progress_pattern = re.compile(r'GetNextNewMessage.*?(\d+\.\d+)%')
                        last_progress = None
                        
                        # ‹®ЈЁагҐ¬ ­ з «® ў Ї®«­л© «®Ј
                        self.log_fc(f"=== ‡ ЇгбЄ FeaturesCalculator ¤«п {interval['start']} - {interval['end']} ===", 'info')
                        
                        # —Ёв Ґ¬ ўлў®¤ Ї®бва®з­®
                        while True:
                            line = stdout.readline()
                            if not line:
                                break
                            line = line.strip()
                            if line:
                                # ‚бҐЈ¤  ЇЁиҐ¬ ў Ї®«­л© «®Ј FeaturesCalculator
                                self.log_fc(line)
                                
                                # Џа®ЇгбЄ Ґ¬ бва®ЄЁ б дЁ«мвагҐ¬л¬Ё Ї ввҐа­ ¬Ё ¤«п ®б­®ў­®Ј® «®Ј 
                                if any(pattern in line for pattern in filter_patterns):
                                    continue
                                
                                # ЋЎа Ў®вЄ  бва®Є б Їа®ЈаҐбб®¬
                                progress_match = progress_pattern.search(line)
                                if progress_match:
                                    progress = progress_match.group(1)
                                    # Џ®Є §лў Ґ¬ Їа®ЈаҐбб в®«мЄ® Ґб«Ё Ё§¬Ґ­Ё«бп ­  5% Ё«Ё Ў®«ҐҐ
                                    progress_int = int(float(progress))
                                    if last_progress is None or progress_int >= last_progress + 5 or progress_int == 100:
                                        self.log(f"  ✓ Обработано: {progress}%", "info")
                                        last_progress = progress_int
                                    continue
                                
                                self.log(f"  > {line}")
                        
                        exit_status = stdout.channel.recv_exit_status()
                        
                        if exit_status != 0:
                            error_output = stderr.read().decode('utf-8')
                            self.log(f"FeaturesCalculator § ўҐаиЁ«бп б ®иЁЎЄ®© (Є®¤ {exit_status})", 'error')
                            if error_output:
                                self.log(f"Stderr: {error_output}", 'error')
                        else:
                            self.log(f"? FeaturesCalculator § ўҐаис­ гбЇҐи­®", 'success')
                        
                        self.log(f"€­вҐаў « {i} ®Ўа Ў®в ­!", 'success')
                    
                    self.log(f"\n{'='*50}", 'info')
                    self.log("‚бҐ Ё­вҐаў «л ®Ўа Ў®в ­л гбЇҐи­®!", 'success')
                    self.log(f"‚бҐЈ® Ё­вҐаў «®ў: {len(intervals)}", 'info')
                else:
                    self.log("?? FeaturesCalculator Їа®ЇгйҐ­ (®вЄ«озс­ ў ­ бва®©Є е)", 'warning')
                
                # 5. ‡ ЇгбЄ R бЄаЁЇв  ¤«п ®Ўа Ў®вЄЁ бЁЈ­ «®ў
                if self.run_rscript.get():
                    rscript_path = self.settings.get('RSCRIPT_PATH')
                    if rscript_path:
                        self.log(f"\n{'='*50}", 'info')
                        self.log("‡ ЇгбЄ R бЄаЁЇв  ¤«п ®Ўа Ў®вЄЁ бЁЈ­ «®ў...", 'warning')
                        
                        input_folder = f"{signal_folder.rstrip('/')}/temp"
                        output_folder = f"{signal_folder.rstrip('/')}/temp_moment_fixed"
                        
                        rscript_cmd = f"Rscript {rscript_path} {input_folder} {output_folder}"
                        self.log(f"Љ®¬ ­¤ : {rscript_cmd}", 'info')
                        
                        stdin, stdout, stderr = ssh.exec_command(rscript_cmd, get_pty=True)
                        
                        # ‹®ЈЁагҐ¬ ўлў®¤ R бЄаЁЇв  (в®«мЄ® ў® ўв®аго ўЄ« ¤Єг)
                        self.log_fc(f"=== ‡ ЇгбЄ R бЄаЁЇв  ===", 'info')
                        while True:
                            line = stdout.readline()
                            if not line:
                                break
                            line = line.strip()
                            if line:
                                self.log_fc(line)
                        
                        exit_status = stdout.channel.recv_exit_status()
                        
                        if exit_status != 0:
                            error_output = stderr.read().decode('utf-8')
                            self.log(f"R бЄаЁЇв § ўҐаиЁ«бп б ®иЁЎЄ®© (Є®¤ {exit_status})", 'error')
                            if error_output:
                                self.log(f"Stderr: {error_output}", 'error')
                        else:
                            self.log(f"? R бЄаЁЇв § ўҐаис­ гбЇҐи­®", 'success')
                    else:
                        self.log("?? RSCRIPT_PATH ­Ґ гЄ § ­ ў settings.json", 'warning')
                else:
                    self.log("?? R бЄаЁЇв Їа®ЇгйҐ­ (®вЄ«озс­ ў ­ бва®©Є е)", 'warning')
                
                # 6. ЋЎа Ў®вЄ  д ©«®ў бЁЈ­ «®ў
                if self.run_signal_processing.get():
                    self.log(f"\n{'='*50}", 'info')
                    self.log("ЋЎа Ў®вЄ  д ©«®ў бЁЈ­ «®ў...", 'warning')
                    self.process_signal_files(ssh, sftp, signal_folder, config_history_path, ssh_username)
                else:
                    self.log("?? ЋЎа Ў®вЄ  д ©«®ў Їа®ЇгйҐ­  (®вЄ«озҐ­  ў ­ бва®©Є е)", 'warning')
                
                # 7. “¤ «Ґ­ЁҐ ўаҐ¬Ґ­­ле Ї Ї®Є
                if self.run_cleanup.get():
                    self.log(f"\n{'='*50}", 'info')
                    self.log("“¤ «Ґ­ЁҐ ўаҐ¬Ґ­­ле Ї Ї®Є...", 'info')
                    temp_path = f"{signal_folder.rstrip('/')}/temp"
                    temp_fixed_path = f"{signal_folder.rstrip('/')}/temp_moment_fixed"
                    
                    ssh.exec_command(f"rm -rf {temp_path}")
                    ssh.exec_command(f"rm -rf {temp_fixed_path}")
                    self.log(f"? “¤ «Ґ­л: temp, temp_moment_fixed", 'success')
                else:
                    self.log("?? “¤ «Ґ­ЁҐ temp Ї Ї®Є Їа®ЇгйҐ­® (®вЄ«озҐ­® ў ­ бва®©Є е)", 'warning')
                
                sftp.close()
                self.log(f"\n{'='*50}", 'info')
                self.log("?? ѓҐ­Ґа жЁп бЁЈ­ «®ў Ї®«­®бвмо § ўҐаиҐ­ !", 'success')
                
            except paramiko.AuthenticationException:
                self.log("ЋиЁЎЄ   гвҐ­вЁдЁЄ жЁЁ SSH. Џа®ўҐамвҐ Є«оз.", 'error')
            except paramiko.SSHException as e:
                self.log(f"SSH ®иЁЎЄ : {str(e)}", 'error')
            except FileNotFoundError:
                self.log(f"SSH Є«оз ­Ґ ­ ©¤Ґ­: {ssh_key_path}", 'error')
            except json.JSONDecodeError as e:
                self.log(f"ЋиЁЎЄ  Ї абЁ­Ј  JSON: {str(e)}", 'error')
            except Exception as e:
                self.log(f"Ошибка: {str(e)}", "error")
            finally:
                ssh.close()
                self.log("SSH б®Ґ¤Ё­Ґ­ЁҐ § Єалв®.")
                
        except Exception as e:
            self.log(f"Ошибка: {str(e)}", "error")
        finally:
            # ђ §Ў«®ЄЁа®ўЄ  Є­®ЇЄЁ
            self.root.after(0, lambda: self.run_button.configure(state='normal', bg='#f9e2af'))


def main():
    root = tk.Tk()
    app = SignalGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""generate_signals_class"""


# API class for programmatic access (non-GUI)
class GenerateSignals:
    """API wrapper for signal generation without GUI"""
    
    def __init__(self, settings: dict):
        self.settings = settings
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self._log_callback = None
        self._log_fc_callback = None
    
    def log(self, message: str, level: str = "info"):
        """Log message via callback or print"""
        import datetime as dt
        timestamp = dt.datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        
        
        if self._log_callback:
            self._log_callback(formatted_message, level)
        else:
            print(formatted_message)
    
    def log_fc(self, message: str):
        """Log FeaturesCalculator output via callback or print"""
        import datetime as dt
        timestamp = dt.datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        
        if self._log_fc_callback:
            self._log_fc_callback(formatted_message)
        elif self._log_callback:
            self._log_callback(formatted_message, "info")
        else:
            print(formatted_message)
    
    def parse_date_flexible(self, date_str: str) -> datetime:
        """Parse date from various formats"""
        formats = [
            "%d.%m.%Y",  # DD.MM.YYYY
            "%Y-%m-%d",  # YYYY-MM-DD
            "%d/%m/%Y",  # DD/MM/YYYY
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {date_str}")
    
    def _get_config_files_list(self, ssh, config_history_path: str) -> list:
        """Get list of config files from ConfigHistory"""
        try:
            stdin, stdout, stderr = ssh.exec_command(f"ls -1 {config_history_path}")
            files = stdout.read().decode('utf-8').strip().split('\n')
            
            config_files = []
            for f in files:
                if f.endswith('.json'):
                    try:
                        # Parse DD-MM-YYYY.json format
                        match = re.match(r'(\d{2})-(\d{2})-(\d{4})\.json', f)
                        if match:
                            day, month, year = match.groups()
                            date = datetime(int(year), int(month), int(day))
                            config_files.append((date, f))
                        else:
                            config_files.append((None, f))
                    except ValueError:
                        config_files.append((None, f))
            
            config_files.sort(key=lambda x: x[0] if x[0] else datetime.min)
            return config_files
        except Exception as e:
            self.log(f"ЋиЁЎЄ  Ї®«гзҐ­Ёп бЇЁбЄ  Є®­дЁЈ®ў: {e}", "error")
            return []
    
    def _read_remote_file(self, ssh, path: str) -> str:
        """Read file from remote host"""
        stdin, stdout, stderr = ssh.exec_command(f"cat {path}")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode('utf-8')
            raise Exception(f"Error reading {path}: {error}")
        return stdout.read().decode('utf-8')
    
    def _write_remote_file_sftp(self, sftp, path: str, content: str):
        """Write file via SFTP"""
        with sftp.file(path, 'w') as f:
            f.write(content)
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON from comments and trailing commas"""
        import re
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)
        json_str = json_str.replace('\r\n', '\n').replace('\r', '\n')
        json_str = re.sub(r'(?<!:)//.*?(?=\n|$)', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        return json_str
    
    def _parse_json_safe(self, json_str: str) -> dict:
        """Safe JSON parsing with cleanup"""
        cleaned = self._clean_json_string(json_str)
        return json.loads(cleaned)
    
    def _split_interval_by_configs(self, start_date, end_date, config_files):
        """Split interval into sub-intervals according to config files"""
        intervals = []
        
        applicable_config = None
        for config_date, config_file in config_files:
            if config_date and config_date <= start_date:
                applicable_config = (config_date, config_file)
            else:
                break
        
        if applicable_config is None:
            return []
        
        current_start = start_date
        current_config = applicable_config
        
        for i, (config_date, config_file) in enumerate(config_files):
            if config_date is None:
                continue
            if config_date <= current_config[0]:
                continue
            
            if config_date > end_date:
                break
            
            interval_end = config_date - timedelta(days=1)
            if interval_end >= current_start:
                intervals.append({
                    'start': current_start,
                    'end': interval_end,
                    'config_file': current_config[1]
                })
            
            current_start = config_date
            current_config = (config_date, config_file)
        
        if current_start <= end_date:
            intervals.append({
                'start': current_start,
                'end': end_date,
                'config_file': current_config[1]
            })
        
        return intervals
    
    def _upload_server_script(self, sftp, ssh_username: str) -> str:
        """Upload server script to remote host"""
        server_script_path = os.path.join(self.script_dir, 'process_signals_server.py')
        remote_dir = f"/home/{ssh_username}/PythonScripts"
        remote_path = f"{remote_dir}/process_signals_server.py"
        
        with open(server_script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        try:
            sftp.mkdir(remote_dir)
        except IOError:
            pass
        
        self._write_remote_file_sftp(sftp, remote_path, script_content)
        return remote_path
    
    def _process_signal_files(self, ssh, sftp, signal_folder: str, config_history_path: str, ssh_username: str):
        """Process signal files via server script"""
        self.log("‡ Јаг§Є  бҐаўҐа­®Ј® бЄаЁЇв ...", "info")
        remote_script_path = self._upload_server_script(sftp, ssh_username)
        self.log(f"? ‘ЄаЁЇв § Јаг¦Ґ­: {remote_script_path}", "success")
        
        cmd = f"python3 {remote_script_path} {signal_folder} {config_history_path}"
        self.log(f"‡ ЇгбЄ: {cmd}", "info")
        
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        
        while True:
            line = stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("PROGRESS:"):
                progress_part = line.replace("PROGRESS:", "").strip()
                self.log(f"  ✓ Обработано файлов: {progress_part}", "info")
            elif line.startswith("DONE:"):
                self.log(f"  {line.replace('DONE:', '?')}", "success")
            elif line.startswith("ERROR:"):
                self.log(f"  ⚠ {line}", "warning")
            elif line.startswith("INFO:"):
                self.log(f"  {line.replace('INFO:', '??')}", "info")
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            error_output = stderr.read().decode('utf-8')
            self.log(f"‘ҐаўҐа­л© бЄаЁЇв § ўҐаиЁ«бп б ®иЁЎЄ®© (Є®¤ {exit_status})", "error")
            if error_output:
                self.log(f"Stderr: {error_output}", "error")
        else:
            self.log("? ЋЎа Ў®вЄ  д ©«®ў бЁЈ­ «®ў § ўҐаиҐ­ ", "success")
    
    def generate(
        self,
        start_date: str,
        end_date: str,
        run_features_calculator: bool = True,
        run_rscript: bool = True,
        run_signal_processing: bool = True,
        run_cleanup: bool = True,
        log_callback=None,
        log_fc_callback=None
    ) -> dict:
        """
        Generate signals for date range
        
        Args:
            start_date: Start date (DD.MM.YYYY or YYYY-MM-DD)
            end_date: End date (DD.MM.YYYY or YYYY-MM-DD)
            run_features_calculator: Run FeaturesCalculator
            run_rscript: Run R script
            run_signal_processing: Process signals
            run_cleanup: Cleanup temp files
            log_callback: Callback function(message, level)
            log_fc_callback: Callback function for FeaturesCalculator output(message)
        
        Returns:
            dict with status and message
        """
        self._log_callback = log_callback
        self._log_fc_callback = log_fc_callback
        
        try:
            start = self.parse_date_flexible(start_date)
            end = self.parse_date_flexible(end_date)
            
            self.log("=" * 50, "info")
            self.log(f"‚лЎа ­­л© ЇҐаЁ®¤: {start.date()} - {end.date()}", "info")
            self.log("=" * 50, "info")
            
            if not self.settings:
                self.log("ЋиЁЎЄ : ЌҐ г¤ «®бм § Јаг§Ёвм settings.json", "error")
                return {"status": "error", "message": "Settings not loaded"}
            
            ssh_username = self.settings.get('SSH_USERNAME')
            ssh_key_path = self.settings.get('SSH_KEY_PATH')
            remote_host = self.settings.get('REMOTE_HOST')
            signal_folder = self.settings.get('SIGNAL_FOLDER', '').rstrip('/')
            
            if not all([ssh_username, ssh_key_path, remote_host, signal_folder]):
                self.log("ЋиЁЎЄ : ЌҐ ўбҐ Ї а ¬Ґвал гЄ § ­л ў settings.json", "error")
                return {"status": "error", "message": "Missing SSH settings"}
            
            self.log(f"Џ®¤Є«озҐ­ЁҐ Є {remote_host} Є Є {ssh_username}...", "info")
            
            import paramiko
            import re
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                private_key = paramiko.Ed25519Key.from_private_key_file(ssh_key_path)
                ssh.connect(hostname=remote_host, username=ssh_username, pkey=private_key, timeout=30)
                self.log("SSH Ї®¤Є«озҐ­ЁҐ гбв ­®ў«Ґ­®!", "success")
                
                sftp = ssh.open_sftp()
                
                config_history_path = f"{signal_folder}/ConfigHistory"
                dest_backup_path = f"/home/{ssh_username}/CMESignals/ConfigHistory"
                base_config_path = f"/home/{ssh_username}/build/FeaturesCalculator/Configs/Cme/Features/Local"
                
                # 1. Backup ConfigHistory
                self.log("‘®§¤ ­ЁҐ ЎнЄ Ї  ConfigHistory...", "info")
                ssh.exec_command(f"mkdir -p {dest_backup_path}")
                ssh.exec_command(f"cp -r {config_history_path}/* {dest_backup_path}/ 2>/dev/null || true")
                self.log("ЃнЄ Ї ConfigHistory ўлЇ®«­Ґ­", "success")
                
                # 2. Get config files list
                self.log("Џ®«гзҐ­ЁҐ бЇЁбЄ  д ©«®ў Є®­дЁЈга жЁЁ...", "info")
                config_files = self._get_config_files_list(ssh, config_history_path)
                
                if not config_files:
                    self.log("ЌҐ ­ ©¤Ґ­® д ©«®ў Є®­дЁЈга жЁЁ ў ConfigHistory", "error")
                    return {"status": "error", "message": "No config files found"}
                else:
                    self.log(f"Ќ ©¤Ґ­® {len(config_files)} д ©«®ў Є®­дЁЈга жЁЁ:", "info")
                    for config_date, config_file in config_files:
                        if config_date:
                            self.log(f"   {config_file} ({config_date.date()})")
                
                # 3. Run FeaturesCalculator
                if run_features_calculator:
                    intervals = self._split_interval_by_configs(start, end, config_files)
                    
                    if not intervals:
                        self.log("?? ЌҐ г¤ «®бм а §ЎЁвм Ё­вҐаў «. ЌҐв Ї®¤е®¤пйЁе Є®­дЁЈ®ў. FeaturesCalculator ­Ґ Ўг¤Ґв § ЇгйҐ­.", "warning")
                    else:
                        self.log(f"\n€­вҐаў « а §ЎЁв ­  {len(intervals)} з бвҐ©:", "warning")
                        for i, interval in enumerate(intervals, 1):
                            self.log(f"  {i}. {interval['start'].date()} - {interval['end'].date()}  {interval['config_file']}", "interval")
                        
                        instruments_path = f"{base_config_path}/Instruments.json"
                        config_cme_local_path = f"{base_config_path}/ConfigCmeLocal.json"
                        signal_printer_path = f"{base_config_path}/SignalPrinter.json"
                        
                        for i, interval in enumerate(intervals, 1):
                            self.log("=" * 50, "info")
                            self.log(f"ЋЎа Ў®вЄ  Ё­вҐаў «  {i}/{len(intervals)}", "warning")
                            self.log(f"ЏҐаЁ®¤: {interval['start'].date()} - {interval['end'].date()}", "interval")
                            self.log(f"Љ®­дЁЈ: {interval['config_file']}", "interval")
                            
                            # ‡ Јаг§Є  Є®­дЁЈга жЁЁ
                            config_file_path = f"{config_history_path}/{interval['config_file']}"
                            self.log(f"‡ Јаг§Є  Є®­дЁЈ : {config_file_path}", "info")
                            
                            # Update Instruments.json
                            config_file_path = f"{config_history_path}/{interval['config_file']}"
                            config_content = self._read_remote_file(ssh, config_file_path)
                            config_json = self._parse_json_safe(config_content)
                            
                            def replace_feed_mode(obj):
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if key == 'SharedFeedMode':
                                            obj[key] = 'Local'
                                        else:
                                            replace_feed_mode(value)
                                elif isinstance(obj, list):
                                    for item in obj:
                                        replace_feed_mode(item)
                            
                            replace_feed_mode(config_json)
                            instruments_content = json.dumps(config_json, indent=2)
                            self._write_remote_file_sftp(sftp, instruments_path, instruments_content)
                            self.log("? ‡ ЇЁб ­ Instruments.json (SharedFeedMode: Local)", "success")
                            
                            # Update ConfigCmeLocal.json
                            self.log("ЋЎ­®ў«Ґ­ЁҐ ConfigCmeLocal.json...")
                            cme_local_content = self._read_remote_file(ssh, config_cme_local_path)
                            cme_local_json = self._parse_json_safe(cme_local_content)
                            
                            date_range = f"{interval['start'].strftime('%Y-%m-%d')}:{interval['end'].strftime('%Y-%m-%d')}"
                            
                            if 'ManyDatesConfig' in cme_local_json:
                                cme_local_json['ManyDatesConfig']['Dates'] = [date_range]
                            else:
                                cme_local_json['ManyDatesConfig'] = {'CoresCount': 5, 'Dates': [date_range]}
                            
                            cme_local_content = json.dumps(cme_local_json, indent=2)
                            self._write_remote_file_sftp(sftp, config_cme_local_path, cme_local_content)
                            self.log(f"? ‡ ЇЁб ­ ConfigCmeLocal.json (Dates: {date_range})", "success")
                            
                            # Update SignalPrinter.json
                            self.log("ЋЎ­®ў«Ґ­ЁҐ SignalPrinter.json...")
                            signal_printer_content = self._read_remote_file(ssh, signal_printer_path)
                            signal_printer_json = self._parse_json_safe(signal_printer_content)
                            
                            signal_printer_json['FolderWithSignal'] = f"{signal_folder}/temp"
                            signal_printer_json['FileNameSuffix'] = '_signal'
                            
                            signal_printer_content = json.dumps(signal_printer_json, indent=2)
                            self._write_remote_file_sftp(sftp, signal_printer_path, signal_printer_content)
                            self.log("? ‡ ЇЁб ­ SignalPrinter.json", "success")
                            
                            # Run FeaturesCalculator
                            self.log(f"‡ ЇгбЄ FeaturesCalculator ¤«п Ё­вҐаў «  {interval['start'].date()} - {interval['end'].date()}...", "warning")
                            features_calculator_dir = f"/home/{ssh_username}/build/FeaturesCalculator/RelCmeLocal"
                            run_cmd = f"cd {features_calculator_dir} && ./FeaturesCalculator"
                            stdin, stdout, stderr = ssh.exec_command(run_cmd, get_pty=True)
                            
                            filter_patterns = [
                                'LvlImpliedCrossReal', 'Clock MANUAL OVERRIDE',
                                'Cannot find date for last mid manager', '#STDOFF',
                                'Cannot find expression file', 'RunCmeOneDay',
                                'Complete init one_feed_processors', 'Start read local dump',
                                'Gap in  snap', 'GAP in online feed',
                                'All instrument snap completed', 'All data snap completed',
                                'LvlCme.', 'Change IsOnline',
                            ]
                            
                            progress_pattern = re.compile(r'GetNextNewMessage.*?(\d+\.\d+)%')
                            last_progress = None
                            
                            while True:
                                line = stdout.readline()
                                if not line:
                                    break
                                line = line.strip()
                                if line:
                                    if any(pattern in line for pattern in filter_patterns):
                                        continue
                                    
                                    progress_match = progress_pattern.search(line)
                                    if progress_match:
                                        progress = progress_match.group(1)
                                        progress_int = int(float(progress))
                                        if last_progress is None or progress_int >= last_progress + 5 or progress_int == 100:
                                            self.log(f"  ✓ Обработано: {progress}%", "info")
                                            last_progress = progress_int
                                        continue
                                    
                                    self.log_fc(line)
                            
                            exit_status = stdout.channel.recv_exit_status()
                            
                            if exit_status != 0:
                                error_output = stderr.read().decode('utf-8')
                                self.log(f"FeaturesCalculator § ўҐаиЁ«бп б ®иЁЎЄ®© (Є®¤ {exit_status})", "error")
                                if error_output:
                                    self.log(f"Stderr: {error_output}", "error")
                            else:
                                self.log("? FeaturesCalculator § ўҐаис­ гбЇҐи­®", "success")
                        
                        self.log("‚бҐ Ё­вҐаў «л ®Ўа Ў®в ­л гбЇҐи­®!", "success")
                        self.log(f"‚бҐЈ® Ё­вҐаў «®ў: {len(intervals)}", "info")
                else:
                    self.log("?? FeaturesCalculator Їа®ЇгйҐ­ (®вЄ«озс­ ў ­ бва®©Є е)", "warning")
                
                # 4. Run R script
                if run_rscript:
                    rscript_path = self.settings.get('RSCRIPT_PATH')
                    if rscript_path:
                        self.log("=" * 50, "info")
                        self.log("‡ ЇгбЄ R бЄаЁЇв  ¤«п ®Ўа Ў®вЄЁ бЁЈ­ «®ў...", "warning")
                        
                        input_folder = f"{signal_folder}/temp"
                        output_folder = f"{signal_folder}/temp_moment_fixed"
                        
                        rscript_cmd = f"Rscript {rscript_path} {input_folder} {output_folder}"
                        self.log(f"Љ®¬ ­¤ : {rscript_cmd}", "info")
                        
                        stdin, stdout, stderr = ssh.exec_command(rscript_cmd, get_pty=True)
                        
                        while True:
                            line = stdout.readline()
                            if not line:
                                break
                            line = line.strip()
                            if line:
                                self.log(f"  {line}")
                        
                        exit_status = stdout.channel.recv_exit_status()
                        
                        if exit_status != 0:
                            error_output = stderr.read().decode('utf-8')
                            self.log(f"R бЄаЁЇв § ўҐаиЁ«бп б ®иЁЎЄ®© (Є®¤ {exit_status})", "error")
                            if error_output:
                                self.log(f"Stderr: {error_output}", "error")
                        else:
                            self.log("? R бЄаЁЇв § ўҐаис­ гбЇҐи­®", "success")
                    else:
                        self.log("?? RSCRIPT_PATH ­Ґ гЄ § ­ ў settings.json", "warning")
                else:
                    self.log("?? R бЄаЁЇв Їа®ЇгйҐ­ (®вЄ«озс­ ў ­ бва®©Є е)", "warning")
                
                # 5. Process signals
                if run_signal_processing:
                    self.log("=" * 50, "info")
                    self.log("ЋЎа Ў®вЄ  д ©«®ў бЁЈ­ «®ў...", "warning")
                    self._process_signal_files(ssh, sftp, signal_folder, config_history_path, ssh_username)
                else:
                    self.log("?? ЋЎа Ў®вЄ  д ©«®ў Їа®ЇгйҐ­  (®вЄ«озҐ­  ў ­ бва®©Є е)", "warning")
                
                # 6. Cleanup
                if run_cleanup:
                    self.log("=" * 50, "info")
                    self.log("“¤ «Ґ­ЁҐ ўаҐ¬Ґ­­ле Ї Ї®Є...", "info")
                    temp_path = f"{signal_folder}/temp"
                    temp_fixed_path = f"{signal_folder}/temp_moment_fixed"
                    
                    ssh.exec_command(f"rm -rf {temp_path}")
                    ssh.exec_command(f"rm -rf {temp_fixed_path}")
                    self.log("? “¤ «Ґ­л: temp, temp_moment_fixed", "success")
                else:
                    self.log("?? “¤ «Ґ­ЁҐ temp Ї Ї®Є Їа®ЇгйҐ­® (®вЄ«озҐ­® ў ­ бва®©Є е)", "warning")
                
                sftp.close()
                ssh.close()
                
                self.log("=" * 50, "info")
                self.log("?? ѓҐ­Ґа жЁп бЁЈ­ «®ў Ї®«­®бвмо § ўҐаиҐ­ !", "success")
                return {
                    "status": "success",
                    "message": f"Generated signals for {start.date()} - {end.date()}",
                    "config_files": len(config_files) if config_files else 0
                }
                
            except paramiko.AuthenticationException:
                self.log("ЋиЁЎЄ   гвҐ­вЁдЁЄ жЁЁ SSH. Џа®ўҐамвҐ Є«оз.", "error")
                return {"status": "error", "message": "SSH authentication failed"}
            except paramiko.SSHException as e:
                self.log(f"SSH ®иЁЎЄ : {e}", "error")
                return {"status": "error", "message": f"SSH error: {e}"}
            except Exception as e:
                self.log(f"ЋиЁЎЄ : {e}", "error")
                return {"status": "error", "message": f"Connection error: {e}"}
                
        except ValueError as e:
            self.log(f"Date parsing error: {e}", "error")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            self.log(f"Unexpected error: {e}", "error")
            return {"status": "error", "message": str(e)}
