"""Explicit-action confirmation dialogs, with Cancel as the safe default."""
import tkinter as tk
from tkinter import ttk


def confirm_action(parent, title, message, action='Apagar temporários'):
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.configure(bg='#152238')
    dialog.resizable(False, False)
    dialog.transient(parent)
    accepted = False
    tk.Label(dialog, text=title, bg='#152238', fg='#f0f5fd',
             font=('Segoe UI', 16, 'bold'), anchor='w').pack(fill='x', padx=24, pady=(22, 12))
    tk.Label(dialog, text=message, bg='#152238', fg='#c7d3e5', font=('Segoe UI', 11),
             wraplength=530, justify='left').pack(fill='x', padx=24, pady=(0, 20))
    actions = tk.Frame(dialog, bg='#152238')
    actions.pack(fill='x', padx=24, pady=(0, 22))
    def choose(value):
        nonlocal accepted
        accepted = value
        dialog.destroy()
    cancel = tk.Button(actions, text='Cancelar', command=lambda: choose(False),
                       bg='#293b54', fg='white', font=('Segoe UI', 11),
                       relief='flat', padx=20, pady=10)
    cancel.pack(side='left')
    tk.Button(actions, text=action, command=lambda: choose(True),
              bg='#b34243' if action == 'Apagar temporários' else '#167f78',
              fg='white', font=('Segoe UI', 11, 'bold'), relief='flat',
              padx=20, pady=10).pack(side='right', padx=(30, 0))
    dialog.protocol('WM_DELETE_WINDOW', lambda: choose(False))
    dialog.bind('<Escape>', lambda event: choose(False))
    dialog.bind('<Return>', lambda event: dialog.focus_get().invoke()
                if isinstance(dialog.focus_get(), tk.Button) else None)
    dialog.update_idletasks()
    width, height = max(580, dialog.winfo_reqwidth()), dialog.winfo_reqheight()
    if parent.winfo_viewable():
        x = max(0, parent.winfo_rootx() + (parent.winfo_width() - width) // 2)
        y = max(0, parent.winfo_rooty() + (parent.winfo_height() - height) // 2)
    else:
        x = max(0, (parent.winfo_screenwidth() - width) // 2)
        y = max(0, (parent.winfo_screenheight() - height) // 2)
    dialog.geometry(f'{width}x{height}+{x}+{y}')
    dialog.grab_set()
    cancel.focus_set()
    parent.wait_window(dialog)
    return accepted
