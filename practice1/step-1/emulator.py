"""Эмулятор оболочки ОС. Вариант №7."""
import argparse
import getpass
import shlex
import socket
import tkinter as tk
from pathlib import Path
from tkinter.scrolledtext import ScrolledText
from vfs import VFS


class Shell:
    def __init__(self, vfs):
        self.vfs = vfs
        self.cwd = '/'
        self.closed = False

    def execute(self, line):
        try:
            words = shlex.split(line, comments=True)
            if not words:
                return ''
            command, *args = words
            commands = {'ls': self.ls, 'cd': self.cd, 'head': self.head,
                        'tree': self.tree, 'rmdir': self.rmdir, 'exit': self.exit}
            if command not in commands:
                raise ValueError(f'{command}: команда не найдена')
            return commands[command](args)
        except ValueError as error:
            return f'Ошибка: {error}'

    def ls(self, args):
        if len(args) > 1:
            raise ValueError('ls: ожидается не более одного пути')
        path, node = self.vfs.resolve(args[0] if args else '.', self.cwd)
        if isinstance(node, dict):
            return '\n'.join(name for name in sorted(node) if not name.startswith('.'))
        return path.rsplit('/', 1)[-1]

    def cd(self, args):
        if len(args) > 1:
            raise ValueError('cd: ожидается не более одного пути')
        path, node = self.vfs.resolve(args[0] if args else '/', self.cwd)
        if not isinstance(node, dict):
            raise ValueError(f'{path}: не каталог')
        self.cwd = path
        return ''

    def head(self, args):
        count = 10
        if args and args[0] == '-n':
            if len(args) < 2:
                raise ValueError('head: после -n требуется число')
            try:
                count = int(args[1])
            except ValueError:
                raise ValueError('head: количество строк должно быть целым числом')
            if count < 0:
                raise ValueError('head: количество строк не может быть отрицательным')
            args = args[2:]
        if len(args) != 1:
            raise ValueError('head: ожидается один файл; формат: head [-n N] файл')
        _, node = self.vfs.resolve(args[0], self.cwd)
        if isinstance(node, dict):
            raise ValueError(f'{args[0]}: это каталог')
        try:
            text = node.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError(f'{args[0]}: двоичный файл, ожидается UTF-8')
        return '\n'.join(text.splitlines()[:count])

    def tree(self, args):
        if len(args) > 1:
            raise ValueError('tree: ожидается не более одного пути')
        path, node = self.vfs.resolve(args[0] if args else '.', self.cwd)
        lines = [path]

        def walk(directory, prefix):
            if not isinstance(directory, dict):
                return
            names = [name for name in sorted(directory) if not name.startswith('.')]
            for index, name in enumerate(names):
                last = index == len(names) - 1
                lines.append(prefix + ('└── ' if last else '├── ') + name)
                walk(directory[name], prefix + ('    ' if last else '│   '))

        walk(node, '')
        return '\n'.join(lines)

    def rmdir(self, args):
        if len(args) != 1:
            raise ValueError('rmdir: ожидается один путь')
        path, node = self.vfs.resolve(args[0], self.cwd)
        if path == '/':
            raise ValueError('rmdir: нельзя удалить корень')
        if self.cwd == path or self.cwd.startswith(path + '/'):
            raise ValueError('rmdir: нельзя удалить текущий каталог или его предка')
        if not isinstance(node, dict):
            raise ValueError(f'{path}: не каталог')
        if node:
            raise ValueError(f'{path}: каталог не пуст')
        parent, _, name = path.rpartition('/')
        _, directory = self.vfs.resolve(parent or '/')
        del directory[name]
        return ''

    def exit(self, args):
        if args:
            raise ValueError('exit: аргументы не поддерживаются')
        self.closed = True
        return 'До свидания!'


def run_gui(shell, startup):
    root = tk.Tk()
    identity = f'{getpass.getuser()}@{socket.gethostname()}'
    root.title(f'Эмулятор - [{identity}]')
    root.geometry('900x600')
    output = ScrolledText(root, font=('Courier', 13), state='disabled')
    output.pack(fill='both', expand=True)
    bottom = tk.Frame(root)
    bottom.pack(fill='x')
    prompt = tk.Label(bottom, text=f'{identity}:{shell.cwd}$ ')
    prompt.pack(side='left')
    entry = tk.Entry(bottom, font=('Courier', 13))
    entry.pack(side='left', fill='x', expand=True)

    def submit(line):
        invitation = f'{identity}:{shell.cwd}$ '
        result = shell.execute(line)
        output.configure(state='normal')
        output.insert('end', invitation + line + '\n')
        if result:
            output.insert('end', result + '\n')
        output.see('end')
        output.configure(state='disabled')
        prompt.configure(text=f'{identity}:{shell.cwd}$ ')
        if shell.closed:
            root.after(300, root.destroy)

    def enter(event=None):
        line = entry.get()
        entry.delete(0, 'end')
        submit(line)

    pending = iter(startup)

    def next_line():
        if shell.closed:
            return
        try:
            submit(next(pending))
            root.after(150, next_line)
        except StopIteration:
            pass

    entry.bind('<Return>', enter)
    entry.focus_set()
    root.after(150, next_line)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vfs', type=Path, default=Path(__file__).parent / 'examples/deep.xml')
    parser.add_argument('--script', type=Path, help='Путь к стартовому скрипту UTF-8')
    options = parser.parse_args()
    print(f'VFS: {options.vfs.resolve()}\nСтартовый скрипт: {options.script}')
    try:
        shell = Shell(VFS(options.vfs))
        startup = options.script.read_text(encoding='utf-8').splitlines() if options.script else []
    except (OSError, ValueError) as error:
        parser.exit(2, f'Ошибка запуска: {error}\n')
    run_gui(shell, startup)


if __name__ == '__main__':
    main()
