"""XML VFS: каталоги хранятся как dict, файлы как bytes."""
import base64
import binascii
import xml.etree.ElementTree as element_tree


def validate_name(name, children):
    """Отклонить пустые, повторные и недопустимые имена."""
    invalid = (not name, '/' in name, name in ('.', '..'),
               '\x00' in name, name in children)
    if any(invalid):
        raise ValueError(f'Некорректное или повторное имя: {name!r}')


def file_content(element):
    """Преобразовать текст или base64 в байтовое содержимое файла."""
    if len(element):
        raise ValueError('Файл не может содержать XML-элементы')
    encoding = element.get('encoding', 'utf-8')
    text = element.text or ''
    if encoding == 'base64':
        return base64.b64decode(''.join(text.split()), validate=True)
    if encoding == 'utf-8':
        return text.encode('utf-8')
    raise ValueError(f'Неизвестная кодировка: {encoding}')


class VFS:
    """Файловая система в памяти, загруженная из XML."""

    def __init__(self, filename):
        """Прочитать XML и проверить корневой элемент."""
        try:
            document = element_tree.parse(filename).getroot()
            if document.tag != 'vfs':
                raise ValueError('корневой элемент должен быть <vfs>')
            self.root = self._directory(document)
        except (element_tree.ParseError, binascii.Error) as error:
            raise ValueError(f'Некорректная VFS: {error}') from error

    def _directory(self, element):
        """Рекурсивно загрузить дочерние объекты каталога."""
        children = {}
        for child in element:
            name = child.get('name', '')
            validate_name(name, children)
            children[name] = self._load_node(child)
        return children

    def _load_node(self, element):
        """Выбрать обработчик файла или вложенного каталога."""
        if element.tag == 'directory':
            return self._directory(element)
        if element.tag == 'file':
            return file_content(element)
        raise ValueError(f'Неизвестный XML-элемент: {element.tag}')

    def _node_at(self, parts):
        """Найти узел по уже нормализованным компонентам пути."""
        node = self.root
        for part in parts:
            node = node[part]
        return node

    def _step(self, node, parts, part, path):
        """Обработать компоненту пути и обновить список каталогов."""
        if not isinstance(node, dict):
            raise ValueError(f'{path}: не каталог')
        if part == '.':
            return node
        if part == '..':
            if parts:
                parts.pop()
            return self._node_at(parts)
        if part not in node:
            raise ValueError(f'{path}: путь не найден')
        parts.append(part)
        return node[part]

    def resolve(self, path, cwd='/'):
        """Разрешить абсолютный или относительный путь с . и .. ."""
        parts = []
        if not path.startswith('/'):
            parts = [part for part in cwd.split('/') if part]
        node = self._node_at(parts)
        for part in path.split('/'):
            if part:
                node = self._step(node, parts, part, path)
        if path.endswith('/') and not isinstance(node, dict):
            raise ValueError(f'{path}: не каталог')
        return '/' + '/'.join(parts), node
