"""Учебный эмулятор UNIX-оболочки, вариант 7. Python 3.10+."""
import argparse
import getpass
import json
import shlex
import socket
import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class Shell:
    def __init__(self):
        self.cwd = '/'
        self.closed = False

    def execute(self, line):
        try:
            words = shlex.split(line, comments=True)
            if not words:
                return ''
            command, *args = words
            if command == 'exit':
                if args:
                    raise ValueError('exit: аргументы не поддерживаются')
                self.closed = True
                return 'До свидания!'
            if command in ('ls', 'cd'):
                return f'{command}: {json.dumps(args, ensure_ascii=False)}'
            raise ValueError(f'{command}: команда не найдена')
        except ValueError as error:
            return f'Ошибка: {error}'


def run_gui(shell, startup=()):
    root = tk.Tk()
    identity = f'{getpass.getuser()}@{socket.gethostname()}'
    root.title(f'Эмулятор - [{identity}]')
    root.geometry('900x600')
    output = ScrolledText(root, bg='#18202b', fg='#e0e8ef', font=('Courier', 13))
    output.pack(fill='both', expand=True)
    output.configure(state='disabled')
    bottom = tk.Frame(root)
    bottom.pack(fill='x')
    prompt = tk.Label(bottom)
    prompt.pack(side='left')
    entry = tk.Entry(bottom, font=('Courier', 13))
    entry.pack(side='left', fill='x', expand=True)
    history = []
    position = [0]

    def write(text):
        output.configure(state='normal')
        output.insert('end', text + '\n')
        output.see('end')
        output.configure(state='disabled')

    def update_prompt():
        prompt.configure(text=f'{identity}:{shell.cwd}$ ')

    def submit(line):
        write(f'{identity}:{shell.cwd}$ {line}')
        answer = shell.execute(line)
        if answer:
            write(answer)
        update_prompt()
        if shell.closed:
            root.after(300, root.destroy)

    def enter(event=None):
        line = entry.get()
        entry.delete(0, 'end')
        history.append(line)
        position[0] = len(history)
        submit(line)

    def navigate(delta):
        position[0] = max(0, min(len(history), position[0] + delta))
        entry.delete(0, 'end')
        if position[0] < len(history):
            entry.insert(0, history[position[0]])
        return 'break'

    entry.bind('<Return>', enter)
    entry.bind('<Up>', lambda e: navigate(-1))
    entry.bind('<Down>', lambda e: navigate(1))
    update_prompt()
    entry.focus_set()
    pending = iter(startup)

    def next_line():
        if shell.closed:
            return
        try:
            submit(next(pending))
            root.after(100, next_line)
        except StopIteration:
            pass
    root.after(100, next_line)
    root.mainloop()


def main():
    run_gui(Shell())


if __name__ == '__main__':
    main()
