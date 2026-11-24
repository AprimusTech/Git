"""Integrated Tkinter dashboard for WhatsApp incoming messages and AI drafts.
The GUI never sends messages. The monitor is a separate read-only process.
"""
import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from config import CONTACTS_PATH, DB_PATH
from database import (initialize_database, upsert_contact, log_message, queue_draft,
                      get_recent_drafts, get_app_state)
from ai_engine import generate_reply

BASE = Path(__file__).resolve().parent
MONITOR_SCRIPT = BASE / 'whatsapp_draft_monitor.py'


class AgentDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('WhatsApp Personal AI Agent — Integrated Draft Dashboard')
        self.geometry('1180x790')
        self.minsize(980, 680)
        initialize_database()
        self.monitor_process = None
        self.contacts = self.load_config()
        self.sync_contacts()
        self._build_ui()
        self.refresh_contacts()
        self.refresh_history()
        self.refresh_status()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def load_config(self):
        if not CONTACTS_PATH.exists():
            CONTACTS_PATH.write_text('{}', encoding='utf-8')
        return json.loads(CONTACTS_PATH.read_text(encoding='utf-8'))

    def sync_contacts(self):
        for phone, contact in self.contacts.items():
            normalized = ''.join(ch for ch in phone if ch.isdigit())
            if normalized:
                upsert_contact({'phone': normalized, **contact})

    def _build_ui(self):
        header = ttk.Frame(self, padding=(16, 12)); header.pack(fill='x')
        ttk.Label(header, text='Personal WhatsApp AI Agent', font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        ttk.Label(header, text='Read-only WhatsApp monitoring • AI drafts • Manual review only',
                  foreground='#27733b').pack(anchor='w', pady=(3, 0))
        monitor_bar = ttk.Frame(self, padding=(16, 4)); monitor_bar.pack(fill='x')
        self.monitor_status = tk.StringVar(value='Monitor: checking...')
        ttk.Label(monitor_bar, textvariable=self.monitor_status).pack(side='left')
        ttk.Button(monitor_bar, text='Start WhatsApp Monitor', command=self.start_monitor).pack(side='right', padx=4)
        ttk.Button(monitor_bar, text='Stop Monitor', command=self.stop_monitor).pack(side='right', padx=4)
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill='both', expand=True, padx=14, pady=10)
        self.contact_tab = ttk.Frame(self.tabs, padding=12)
        self.draft_tab = ttk.Frame(self.tabs, padding=12)
        self.queue_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.contact_tab, text='Contacts & Rules')
        self.tabs.add(self.draft_tab, text='Generate Draft')
        self.tabs.add(self.queue_tab, text='Live Draft Inbox')
        self._build_contacts_tab(); self._build_draft_tab(); self._build_queue_tab()

    def _build_contacts_tab(self):
        pane = ttk.Frame(self.contact_tab); pane.pack(fill='both', expand=True)
        left = ttk.Frame(pane); left.pack(side='left', fill='y', padx=(0, 12))
        ttk.Label(left, text='Configured contacts').pack(anchor='w')
        self.contact_list = tk.Listbox(left, width=34, height=22, exportselection=False)
        self.contact_list.pack(fill='y', pady=6)
        self.contact_list.bind('<<ListboxSelect>>', self.load_selected_contact)
        ttk.Button(left, text='Reload contacts', command=self.reload_contacts).pack(fill='x')
        right = ttk.Frame(pane); right.pack(side='left', fill='both', expand=True)
        self.phone_var = tk.StringVar(); self.name_var = tk.StringVar()
        self.enabled_var = tk.BooleanVar(value=False)
        self.style_var = tk.StringVar(value='Natural Hinglish, short and friendly')
        for label, var in [('Phone (country code + number)', self.phone_var),
                           ('WhatsApp chat display name (must match)', self.name_var),
                           ('Reply style', self.style_var)]:
            ttk.Label(right, text=label).pack(anchor='w', pady=(7, 2))
            ttk.Entry(right, textvariable=var).pack(fill='x')
        ttk.Checkbutton(right, text='Enable AI for this contact (whitelist)',
                        variable=self.enabled_var).pack(anchor='w', pady=8)
        ttk.Label(right, text='Contact-specific instructions').pack(anchor='w', pady=(6, 2))
        self.instructions = tk.Text(right, height=7, wrap='word'); self.instructions.pack(fill='x')
        btns = ttk.Frame(right); btns.pack(fill='x', pady=10)
        ttk.Button(btns, text='Save contact', command=self.save_contact).pack(side='left')
        ttk.Button(btns, text='Clear form', command=self.clear_contact_form).pack(side='left', padx=8)
        ttk.Label(right, text='Important: exact chat-name matching is intentional to prevent drafting for the wrong person.').pack(anchor='w', pady=8)

    def _build_draft_tab(self):
        f = self.draft_tab
        ttk.Label(f, text='Select enabled contact').pack(anchor='w')
        self.draft_contact = ttk.Combobox(f, state='readonly', width=65)
        self.draft_contact.pack(anchor='w', pady=6)
        ttk.Label(f, text='Incoming message').pack(anchor='w', pady=(6, 2))
        self.incoming = tk.Text(f, height=5, wrap='word'); self.incoming.pack(fill='x')
        ttk.Button(f, text='Generate AI draft', command=self.make_draft).pack(anchor='w', pady=10)
        self.status_var = tk.StringVar(value='Ready. Select a contact and enter a message.')
        ttk.Label(f, textvariable=self.status_var).pack(anchor='w')
        ttk.Label(f, text='Generated draft (not sent)').pack(anchor='w', pady=(8, 2))
        self.draft_output = tk.Text(f, height=9, wrap='word'); self.draft_output.pack(fill='both', expand=True)
        ttk.Button(f, text='Copy draft', command=self.copy_draft).pack(anchor='e', pady=6)

    def _build_queue_tab(self):
        top = ttk.Frame(self.queue_tab); top.pack(fill='x', pady=(0, 8))
        ttk.Label(top, text='Drafts generated by WhatsApp Monitor and manual generation (latest first).').pack(side='left')
        ttk.Button(top, text='Refresh now', command=self.refresh_history).pack(side='right')
        columns = ('time', 'contact', 'incoming', 'draft', 'status')
        self.queue_tree = ttk.Treeview(self.queue_tab, columns=columns, show='headings', height=15)
        for col, title, width in [('time', 'Created', 130), ('contact', 'Contact', 130),
                                  ('incoming', 'Incoming message', 300), ('draft', 'AI draft', 430),
                                  ('status', 'Status', 90)]:
            self.queue_tree.heading(col, text=title); self.queue_tree.column(col, width=width, anchor='w')
        self.queue_tree.pack(fill='both', expand=True)
        self.queue_tree.bind('<<TreeviewSelect>>', self.show_selected_draft)
        ttk.Label(self.queue_tab, text='Selected draft preview').pack(anchor='w', pady=(8, 2))
        self.history_preview = tk.Text(self.queue_tab, height=5, wrap='word', state='disabled')
        self.history_preview.pack(fill='x')
        actions = ttk.Frame(self.queue_tab); actions.pack(fill='x', pady=6)
        ttk.Button(actions, text='Copy selected draft', command=self.copy_selected_draft).pack(side='right')
        self.history_rows = {}

    def reload_contacts(self):
        try:
            self.contacts = self.load_config(); self.sync_contacts(); self.refresh_contacts()
        except Exception as exc:
            messagebox.showerror('Contacts error', str(exc))

    def refresh_contacts(self):
        self.contact_list.delete(0, tk.END)
        for phone, c in self.contacts.items():
            flag = 'ON' if c.get('enabled') else 'OFF'
            self.contact_list.insert(tk.END, f"[{flag}] {c.get('name', '(unnamed)')} — {phone}")
        enabled = [f"{c.get('name') or phone} ({phone})" for phone, c in self.contacts.items() if c.get('enabled')]
        self.draft_contact['values'] = enabled
        if enabled and not self.draft_contact.get(): self.draft_contact.current(0)

    def load_selected_contact(self, _event=None):
        selection = self.contact_list.curselection()
        if not selection: return
        phone = list(self.contacts.keys())[selection[0]]; c = self.contacts[phone]
        self.phone_var.set(phone); self.name_var.set(c.get('name', ''))
        self.enabled_var.set(bool(c.get('enabled', False))); self.style_var.set(c.get('style', ''))
        self.instructions.delete('1.0', tk.END); self.instructions.insert('1.0', c.get('instructions', ''))

    def save_contact(self):
        phone = ''.join(ch for ch in self.phone_var.get() if ch.isdigit())
        name = self.name_var.get().strip()
        if len(phone) < 8 or not name:
            messagebox.showwarning('Invalid contact', 'Enter a valid phone number and exact WhatsApp chat display name.'); return
        self.contacts[phone] = {'name': name, 'enabled': self.enabled_var.get(), 'auto_reply': False,
            'style': self.style_var.get().strip(), 'instructions': self.instructions.get('1.0', tk.END).strip()}
        CONTACTS_PATH.write_text(json.dumps(self.contacts, indent=2, ensure_ascii=False), encoding='utf-8')
        self.sync_contacts(); self.refresh_contacts()
        messagebox.showinfo('Saved', 'Contact settings saved. Automatic sending remains disabled.')

    def clear_contact_form(self):
        self.phone_var.set(''); self.name_var.set(''); self.enabled_var.set(False)
        self.style_var.set('Natural Hinglish, short and friendly'); self.instructions.delete('1.0', tk.END)

    def make_draft(self):
        selected = self.draft_contact.get().strip(); incoming = self.incoming.get('1.0', tk.END).strip()
        if not selected or not incoming:
            messagebox.showwarning('Missing information', 'Choose a contact and enter an incoming message.'); return
        phone = selected[selected.rfind('(') + 1:selected.rfind(')')]
        self.status_var.set('Generating draft...'); self.update_idletasks()
        try:
            incoming_id = log_message(phone, 'incoming', incoming, status='manual_input')
            draft = generate_reply(phone, incoming)
            log_message(phone, 'draft', draft, status='generated_manual')
            queue_draft(phone, incoming_id, draft)
            self.draft_output.delete('1.0', tk.END); self.draft_output.insert('1.0', draft)
            self.status_var.set('Draft generated. Nothing has been sent.')
            self.refresh_history()
        except Exception as exc:
            self.status_var.set('Draft generation failed.'); messagebox.showerror('Draft generation failed', str(exc))

    def copy_draft(self):
        text = self.draft_output.get('1.0', tk.END).strip()
        if text:
            self.clipboard_clear(); self.clipboard_append(text); self.status_var.set('Draft copied to clipboard.')

    def refresh_history(self):
        selected = self.queue_tree.selection()
        for item in self.queue_tree.get_children(): self.queue_tree.delete(item)
        self.history_rows = {}
        for row in get_recent_drafts(300):
            key = str(row['queue_id']); self.history_rows[key] = row
            self.queue_tree.insert('', 'end', iid=key, values=(row['created_at'], row['display_name'] or row['phone'],
                (row['incoming'] or '')[:180], (row['draft'] or '')[:180], row['status']))
        for item in selected:
            if self.queue_tree.exists(item): self.queue_tree.selection_set(item)

    def show_selected_draft(self, _event=None):
        selection = self.queue_tree.selection()
        if not selection: return
        row = self.history_rows.get(selection[0])
        if not row: return
        content = f"INCOMING MESSAGE\n{row['incoming'] or ''}\n\nAI DRAFT — NOT SENT\n{row['draft']}"
        self.history_preview.configure(state='normal'); self.history_preview.delete('1.0', tk.END)
        self.history_preview.insert('1.0', content); self.history_preview.configure(state='disabled')

    def copy_selected_draft(self):
        selection = self.queue_tree.selection()
        if not selection: return
        row = self.history_rows.get(selection[0])
        if row:
            self.clipboard_clear(); self.clipboard_append(row['draft'] or '')

    def start_monitor(self):
        if self.monitor_process and self.monitor_process.poll() is None:
            messagebox.showinfo('Monitor', 'Monitor is already running.'); return
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_CONSOLE
            self.monitor_process = subprocess.Popen([sys.executable, str(MONITOR_SCRIPT)],
                cwd=str(BASE), creationflags=creationflags)
        else:
            self.monitor_process = subprocess.Popen([sys.executable, str(MONITOR_SCRIPT)], cwd=str(BASE))
        self.monitor_status.set('Monitor: starting — WhatsApp browser will open')

    def stop_monitor(self):
        if self.monitor_process and self.monitor_process.poll() is None:
            self.monitor_process.terminate(); self.monitor_status.set('Monitor: stop requested')
        else:
            self.monitor_status.set('Monitor: not running (or started outside this GUI)')

    def refresh_status(self):
        status = get_app_state('monitor_status', 'not started')
        error = get_app_state('last_monitor_error', '')
        self.monitor_status.set(f'Monitor: {status}' + (f' | Last error: {error[:100]}' if error and status.startswith('error') else ''))
        self.refresh_history()
        self.after(2500, self.refresh_status)

    def on_close(self):
        if self.monitor_process and self.monitor_process.poll() is None:
            if messagebox.askyesno('Exit', 'Stop the WhatsApp monitor and close the dashboard?'):
                self.monitor_process.terminate()
            else:
                return
        self.destroy()


if __name__ == '__main__':
    AgentDashboard().mainloop()
