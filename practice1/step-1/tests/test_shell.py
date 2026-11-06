"""Регрессии оболочки, XML VFS и обработчиков окна без запуска GUI."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from emulator import Shell, ShellWindow
from vfs import VFS

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


def make_shell():
    """Создать независимую оболочку на стандартной VFS."""
    return Shell(VFS(EXAMPLES / 'deep.xml'))


class ShellTests(unittest.TestCase):
    """Проверки команд и сохранения изменений только в памяти."""

    def test_ls_hides_dotfiles(self):
        """Скрытый файл отсутствует в выводе обычного ls."""
        output = make_shell().execute('ls')
        self.assertIn('readme.txt', output)
        self.assertNotIn('.hidden', output)

    def test_cd_and_quoted_head(self):
        """Относительные пути и кавычки не теряются при разборе."""
        shell = make_shell()
        self.assertEqual(shell.execute('cd /home/student/docs'), '')
        self.assertEqual(shell.execute('head -n 1 "my notes.txt"'),
                         'Заметка 1')
        shell.execute('cd ..')
        self.assertEqual(shell.cwd, '/home/student')
        shell.execute('cd')
        self.assertEqual(shell.cwd, '/')

    def test_head_default_zero_and_limit(self):
        """Количество строк соблюдается, ноль возвращает пустой вывод."""
        shell = make_shell()
        self.assertEqual(len(shell.execute('head /readme.txt').splitlines()),
                         len(shell.vfs.root['readme.txt'].splitlines()))
        self.assertEqual(shell.execute('head -n 0 /readme.txt'), '')
        self.assertEqual(shell.execute('head -n 1 /readme.txt'),
                         'Первая строка')

    def test_invalid_commands(self):
        """Ошибки аргументов возвращаются строками и не закрывают окно."""
        commands = ['unknown', 'ls /missing', 'ls / /home',
                    'cd /readme.txt', 'cd / /home', 'head', 'head -n',
                    'head -n x /readme.txt', 'head -n -1 /readme.txt',
                    'head /home', 'head /binary.bin',
                    'tree /missing', 'tree / /home',
                    'ls "незакрытая кавычка', 'exit extra']
        shell = make_shell()
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(shell.execute(command).startswith('Ошибка:'))
                self.assertFalse(shell.closed)

    def test_comments(self):
        """Комментарии пропускаются, решетка в кавычках сохраняется."""
        shell = make_shell()
        self.assertEqual(shell.execute('# comment'), '')
        self.assertEqual(shell.execute('ls # comment'), shell.execute('ls'))
        self.assertIn('путь не найден', shell.execute('ls "#name"'))

    def test_tree(self):
        """Дерево содержит вложенные имена и исключает скрытые файлы."""
        output = make_shell().execute('tree')
        self.assertIn('my notes.txt', output)
        self.assertIn('└──', output)
        self.assertNotIn('.hidden', output)

    def test_delete_only_in_memory(self):
        """Удаление не изменяет XML, повторная загрузка возвращает папку."""
        original = (EXAMPLES / 'deep.xml').read_bytes()
        shell = make_shell()
        self.assertEqual(shell.execute('rmdir /empty'), '')
        self.assertNotIn('empty', shell.vfs.root)
        self.assertIn('empty', make_shell().vfs.root)
        self.assertEqual((EXAMPLES / 'deep.xml').read_bytes(), original)

    def test_delete_protected_paths(self):
        """Корень, предки, непустые каталоги и файлы защищены."""
        shell = make_shell()
        shell.execute('cd /home/student/docs')
        for command in ['rmdir /', 'rmdir .', 'rmdir ..', 'rmdir /home',
                        'rmdir /readme.txt', 'rmdir /missing', 'rmdir',
                        'rmdir /empty /prune']:
            with self.subTest(command=command):
                self.assertTrue(shell.execute(command).startswith('Ошибка:'))

    def test_exit(self):
        """Только корректный exit устанавливает флаг завершения."""
        shell = make_shell()
        self.assertEqual(shell.execute('exit'), 'До свидания!')
        self.assertTrue(shell.closed)


class VfsTests(unittest.TestCase):
    """Проверки нормализации путей и валидации XML."""

    def test_paths(self):
        """Путь не выходит выше корня, повторные слеши допустимы."""
        vfs = make_shell().vfs
        path, _ = vfs.resolve('/../../home//student/./docs/..')
        self.assertEqual(path, '/home/student')
        path, _ = vfs.resolve('../docs/my notes.txt', '/home/student/docs')
        self.assertEqual(path, '/home/student/docs/my notes.txt')

    def test_file_not_directory(self):
        """После файла нельзя применять /, . или .. ."""
        vfs = make_shell().vfs
        for path in ['/readme.txt/', '/readme.txt/..', '/readme.txt/.']:
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, 'не каталог'):
                    vfs.resolve(path)

    def test_base64(self):
        """Двоичное содержимое XML декодируется в исходные байты."""
        _, node = make_shell().vfs.resolve('/binary.bin')
        self.assertEqual(node, bytes([0, 255, 1, 2]))

    def test_invalid_xml(self):
        """Повторные имена, кодировки и неизвестные элементы отклоняются."""
        cases = ['<bad/>', '<vfs>', '<vfs><file name=""/></vfs>',
                 '<vfs><file name="a"/><file name="a"/></vfs>',
                 '<vfs><file name="../a"/></vfs>',
                 '<vfs><file name="a" encoding="other"/></vfs>',
                 '<vfs><file name="a" encoding="base64">?</file></vfs>',
                 '<vfs><file name="a"><nested/></file></vfs>',
                 '<vfs><other name="a"/></vfs>']
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'vfs.xml'
            for text in cases:
                with self.subTest(xml=text):
                    path.write_text(text, encoding='utf-8')
                    with self.assertRaises(ValueError):
                        VFS(path)


class WindowTests(unittest.TestCase):
    """Обработчики окна проверяются с подставными виджетами."""

    @patch('emulator.tk.Entry')
    @patch('emulator.tk.Label')
    @patch('emulator.tk.Frame')
    @patch('emulator.ScrolledText')
    @patch('emulator.tk.Tk')
    def test_script_stays_open(self, root, output, frame, label, entry):
        """Окончание скрипта без exit сохраняет открытое окно."""
        shell = make_shell()
        window = ShellWindow(shell, ['ls'])
        window.next_line()
        window.next_line()
        self.assertFalse(shell.closed)
        root.return_value.destroy.assert_not_called()
        self.assertIn('ls', window.output.insert.call_args_list[0].args[1])

    @patch('emulator.tk.Entry')
    @patch('emulator.tk.Label')
    @patch('emulator.tk.Frame')
    @patch('emulator.ScrolledText')
    @patch('emulator.tk.Tk')
    def test_exit_schedules_close(self, root, output, frame, label, entry):
        """Exit из скрипта планирует закрытие окна."""
        shell = make_shell()
        window = ShellWindow(shell, ['exit'])
        window.next_line()
        self.assertTrue(shell.closed)
        calls = root.return_value.after.call_args_list
        callbacks = [call.args[1] for call in calls]
        self.assertIn(root.return_value.destroy, callbacks)
