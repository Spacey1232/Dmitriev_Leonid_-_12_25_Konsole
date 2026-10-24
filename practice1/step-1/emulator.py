"""Учебный эмулятор UNIX-оболочки, вариант 7. Python 3.10+."""
import argparse
import getpass
import json
import shlex
import socket
from pathlib import Path
from vfs import VFS
import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class Shell:
    def __init__(self, vfs=None):
        self.vfs = vfs
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
            if command in ('ls', 'cd', 'head', 'tree'):
                return self.dispatch(command, args)
            raise ValueError(f'{command}: команда не найдена')
        except ValueError as error:
            return f'Ошибка: {error}'

    def dispatch(self, command, args):
        show_hidden = False
        count = 10
        if command in ('ls', 'tree') and args and args[0] == '-a':
            show_hidden = True
            args = args[1:]
        if command == 'head' and args and args[0] == '-n':
            if len(args) < 2:
                raise ValueError('head: после -n требуется число')
            try:
                count = int(args[1])
            except ValueError:
                raise ValueError('head: количество строк должно быть целым числом')
            if count < 0:
                raise ValueError('head: количество строк не может быть отрицательным')
            args = args[2:]
        if args and args[0] == '--':
            args = args[1:]
        elif args and args[0].startswith('-'):
            raise ValueError(f'{command}: неизвестный параметр {args[0]}')
        if command in ('cd', 'tree') and len(args) > 1:
            raise ValueError(f'{command}: слишком много аргументов')
        if command == 'head' and not args:
            raise ValueError('head: требуется имя файла')
        if command == 'cd':
            path, node = self.vfs.resolve(args[0] if args else '/', self.cwd)
            if not isinstance(node, dict):
                raise ValueError(f'{path}: не каталог')
            self.cwd = path
            return ''
        results = []
        for operand in args or ['.']:
            path, node = self.vfs.resolve(operand, self.cwd)
            if command == 'head':
                if isinstance(node, dict):
                    raise ValueError(f'{operand}: это каталог')
                try:
                    result = ''.join(node.decode('utf-8').splitlines(keepends=True)[:count]).rstrip('\n')
                except UnicodeDecodeError:
                    raise ValueError(f'{operand}: двоичный файл, ожидается UTF-8')
            elif command == 'ls':
                result = '\n'.join(name for name in sorted(node) if show_hidden or not name.startswith('.')) if isinstance(node, dict) else path.rsplit('/', 1)[-1]
            else:
                lines = [path]
                def walk(current, prefix=''):
                    if not isinstance(current, dict):
                        return
                    names = [n for n in sorted(current) if show_hidden or not n.startswith('.')]
                    for i, name in enumerate(names):
                        last = i == len(names) - 1
                        lines.append(prefix + ('└── ' if last else '├── ') + name)
                        walk(current[name], prefix + ('    ' if last else '│   '))
                walk(node)
                result = '\n'.join(lines)
            results.append((f'==> {operand} <==\n' if len(args) > 1 else '') + result)
        return '\n'.join(results)


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vfs', type=Path, default=Path(__file__).parent / 'examples/deep.xml')
    parser.add_argument('--script', type=Path, help='Стартовый скрипт UTF-8; комментарии #')
    parser.add_argument('--headless', action='store_true', help='Выполнить скрипт без GUI')
    options = parser.parse_args()
    print(f'VFS: {options.vfs.resolve()}\nScript: {options.script}\nHeadless: {options.headless}')
    try:
        startup = options.script.read_text(encoding='utf-8').splitlines() if options.script else []
        shell = Shell(VFS(options.vfs))
    except (OSError, ValueError) as error:
        parser.exit(2, f'Ошибка запуска: {error}\n')
    if options.headless:
        for line in startup:
            print(f'{shell.cwd}$ {line}')
            result = shell.execute(line)
            if result:
                print(result)
            if shell.closed:
                break
    else:
        run_gui(shell, startup)


if __name__ == '__main__':
    main()
