"""XML VFS: каталоги — dict, файлы — bytes; исходный файл только читается."""
import base64
import binascii
import xml.etree.ElementTree as ET


class VFS:
    def __init__(self, filename):
        try:
            document = ET.parse(filename).getroot()
            if document.tag != 'vfs':
                raise ValueError('корневой элемент должен быть <vfs>')
            self.root = self._directory(document)
        except (ET.ParseError, binascii.Error) as error:
            raise ValueError(f'Некорректная VFS: {error}') from error

    def _directory(self, element):
        children = {}
        for child in element:
            name = child.get('name', '')
            if not name or '/' in name or name in ('.', '..') or '\x00' in name or name in children:
                raise ValueError(f'Некорректное или повторное имя: {name!r}')
            if child.tag == 'directory':
                children[name] = self._directory(child)
            elif child.tag == 'file':
                encoding = child.get('encoding', 'utf-8')
                if len(child):
                    raise ValueError('Файл не может содержать XML-элементы')
                if encoding == 'base64':
                    children[name] = base64.b64decode(''.join((child.text or '').split()), validate=True)
                elif encoding == 'utf-8':
                    children[name] = (child.text or '').encode('utf-8')
                else:
                    raise ValueError(f'Неизвестная кодировка: {encoding}')
            else:
                raise ValueError(f'Неизвестный XML-элемент: {child.tag}')
        return children

    def resolve(self, path, cwd='/'):
        parts = [] if path.startswith('/') else cwd.strip('/').split('/') if cwd != '/' else []
        node = self.root
        for part in parts:
            node = node[part]
        for part in path.split('/'):
            if not part:
                continue
            if not isinstance(node, dict):
                raise ValueError(f'{path}: не каталог')
            if part == '.':
                continue
            if part == '..':
                if parts:
                    parts.pop()
                node = self.root
                for ancestor in parts:
                    node = node[ancestor]
                continue
            if part not in node:
                raise ValueError(f'{path}: путь не найден')
            node = node[part]
            parts.append(part)
        if path.endswith('/') and not isinstance(node, dict):
            raise ValueError(f'{path}: не каталог')
        return '/' + '/'.join(parts), node
