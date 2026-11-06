"""Эмулятор оболочки ОС. Вариант №7."""
import argparse
import getpass
import shlex
import socket
import tkinter as tk
from pathlib import Path
from tkinter.scrolledtext import ScrolledText
from vfs import VFS

MAX_PATH_ARGS = 1
FILE_ARG_COUNT = 1
HEAD_OPTION_ARGS = 2
DEFAULT_HEAD_LINES = 10
MIN_HEAD_LINES = 0
STARTUP_DELAY_MS = 2000
COMMAND_DELAY_MS = 150
CLOSE_DELAY_MS = 300
ERROR_EXIT_CODE = 2


def visible_names(directory):
    """Вернуть отсортированные имена без скрытых объектов."""
    return [name for name in sorted(directory) if not name.startswith('.')]


def head_arguments(args):
    """Разобрать необязательный параметр -n и путь файла."""
    count = DEFAULT_HEAD_LINES
    if args and args[0] == '-n':
        if len(args) < HEAD_OPTION_ARGS:
            raise ValueError('head: после -n требуется число')
        try:
            count = int(args[1])
        except ValueError as error:
            message = 'head: количество строк должно быть целым числом'
            raise ValueError(message) from error
        if count < MIN_HEAD_LINES:
            message = 'head: количество строк не может быть отрицательным'
            raise ValueError(message)
        args = args[HEAD_OPTION_ARGS:]
    if len(args) != FILE_ARG_COUNT:
        raise ValueError('head: ожидается один файл; head [-n N] файл')
    return count, args[0]


class Shell:
    """Оболочка, выполняющая команды над виртуальной файловой системой."""

    def __init__(self, vfs):
        """Начать работу в виртуальном корне."""
        self.vfs = vfs
        self.cwd = '/'
        self.closed = False

    def execute(self, line):
        """Разобрать строку с кавычками и выполнить команду."""
        try:
            words = shlex.split(line, comments=True)
            if not words:
                return ''
            command, *args = words
            commands = {'ls': self.ls, 'cd': self.cd, 'head': self.head,
                        'tree': self.tree, 'rmdir': self.rmdir,
                        'exit': self.exit}
            if command not in commands:
                raise ValueError(f'{command}: команда не найдена')
            return commands[command](args)
        except ValueError as error:
            return f'Ошибка: {error}'

    def ls(self, args):
        """Показать содержимое каталога или имя файла."""
        if len(args) > MAX_PATH_ARGS:
            raise ValueError('ls: ожидается не более одного пути')
        path, node = self.vfs.resolve(args[0] if args else '.', self.cwd)
        if isinstance(node, dict):
            return '\n'.join(visible_names(node))
        return path.rsplit('/', 1)[-1]

    def cd(self, args):
        """Сменить текущий каталог, без аргумента перейти в корень."""
        if len(args) > MAX_PATH_ARGS:
            raise ValueError('cd: ожидается не более одного пути')
        path, node = self.vfs.resolve(args[0] if args else '/', self.cwd)
        if not isinstance(node, dict):
            raise ValueError(f'{path}: не каталог')
        self.cwd = path
        return ''

    def head(self, args):
        """Прочитать первые строки текстового файла UTF-8."""
        count, filename = head_arguments(args)
        _, node = self.vfs.resolve(filename, self.cwd)
        if isinstance(node, dict):
            raise ValueError(f'{filename}: это каталог')
        try:
            text = node.decode('utf-8')
        except UnicodeDecodeError as error:
            message = f'{filename}: двоичный файл, ожидается UTF-8'
            raise ValueError(message) from error
        return '\n'.join(text.splitlines()[:count])

    def tree(self, args):
        """Рекурсивно вывести дерево без скрытых объектов."""
        if len(args) > MAX_PATH_ARGS:
            raise ValueError('tree: ожидается не более одного пути')
        path, node = self.vfs.resolve(args[0] if args else '.', self.cwd)
        lines = [path]

        def walk(directory, prefix):
            """Добавить один уровень дерева к строкам результата."""
            if not isinstance(directory, dict):
                return
            names = visible_names(directory)
            for index, name in enumerate(names):
                last = index == len(names) - 1
                branch = '└── ' if last else '├── '
                lines.append(prefix + branch + name)
                padding = '    ' if last else '│   '
                walk(directory[name], prefix + padding)

        walk(node, '')
        return '\n'.join(lines)

    def rmdir(self, args):
        """Удалить пустой каталог, защищая корень и текущий путь."""
        if len(args) != FILE_ARG_COUNT:
            raise ValueError('rmdir: ожидается один путь')
        path, node = self.vfs.resolve(args[0], self.cwd)
        if path == '/':
            raise ValueError('rmdir: нельзя удалить корень')
        if self.cwd == path or self.cwd.startswith(path + '/'):
            message = 'rmdir: нельзя удалить текущий каталог или его предка'
            raise ValueError(message)
        if not isinstance(node, dict):
            raise ValueError(f'{path}: не каталог')
        if node:
            raise ValueError(f'{path}: каталог не пуст')
        parent, _, name = path.rpartition('/')
        _, directory = self.vfs.resolve(parent or '/')
        del directory[name]
        return ''

    def exit(self, args):
        """Запросить закрытие окна оболочки."""
        if args:
            raise ValueError('exit: аргументы не поддерживаются')
        self.closed = True
        return 'До свидания!'


class ShellWindow:
    """Окно Tkinter и последовательное выполнение стартового скрипта."""

    def __init__(self, shell, startup):
        """Создать виджеты и привязать обработчики ввода."""
        self.shell = shell
        self.pending = iter(startup)
        self.root = tk.Tk()
        self.identity = f'{getpass.getuser()}@{socket.gethostname()}'
        self.root.title(f'Эмулятор - [{self.identity}]')
        self.root.geometry('900x600')
        self._build_widgets()
        self.entry.bind('<Return>', self.enter)
        self.entry.focus_set()
        self.root.after(STARTUP_DELAY_MS, self.next_line)

    def invitation(self):
        """Сформировать приглашение с текущим виртуальным путем."""
        return f'{self.identity}:{self.shell.cwd}$ '

    def _build_widgets(self):
        """Создать область вывода, приглашение и поле ввода."""
        self.output = ScrolledText(
            self.root, font=('Courier', 13), state='disabled')
        self.output.pack(fill='both', expand=True)
        bottom = tk.Frame(self.root)
        bottom.pack(fill='x')
        self.prompt = tk.Label(bottom, text=self.invitation())
        self.prompt.pack(side='left')
        self.entry = tk.Entry(bottom, font=('Courier', 13))
        self.entry.pack(side='left', fill='x', expand=True)

    def submit(self, line):
        """Выполнить команду и дописать результат в область вывода."""
        invitation = self.invitation()
        result = self.shell.execute(line)
        self.output.configure(state='normal')
        self.output.insert('end', invitation + line + '\n')
        if result:
            self.output.insert('end', result + '\n')
        self.output.see('end')
        self.output.configure(state='disabled')
        self.prompt.configure(text=self.invitation())
        if self.shell.closed:
            self.root.after(CLOSE_DELAY_MS, self.root.destroy)

    def enter(self, event=None):
        """Обработать Enter и очистить поле ввода."""
        line = self.entry.get()
        self.entry.delete(0, 'end')
        self.submit(line)

    def next_line(self):
        """Выполнить следующую строку стартового скрипта."""
        if self.shell.closed:
            return
        try:
            self.submit(next(self.pending))
            self.root.after(COMMAND_DELAY_MS, self.next_line)
        except StopIteration:
            pass


def run_gui(shell, startup):
    """Запустить цикл событий графической оболочки."""
    window = ShellWindow(shell, startup)
    window.root.mainloop()


def main():
    """Загрузить VFS, стартовый скрипт и открыть окно."""
    parser = argparse.ArgumentParser(description=__doc__)
    default_vfs = Path(__file__).parent / 'examples/deep.xml'
    parser.add_argument('--vfs', type=Path, default=default_vfs)
    parser.add_argument('--script', type=Path,
                        help='Путь к стартовому скрипту UTF-8')
    options = parser.parse_args()
    print(f'VFS: {options.vfs.resolve()}\nСтартовый скрипт: {options.script}')
    try:
        shell = Shell(VFS(options.vfs))
        startup = []
        if options.script:
            startup = options.script.read_text(encoding='utf-8').splitlines()
    except (OSError, ValueError) as error:
        parser.exit(ERROR_EXIT_CODE, f'Ошибка запуска: {error}\n')
    run_gui(shell, startup)


if __name__ == '__main__':
    main()
