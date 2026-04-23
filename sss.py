

import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class StructureChecker:
    """Класс для проверки структуры проекта."""

    def __init__(self, root_path: Path, show_hidden: bool = False, max_depth: int = 5):
        self.root_path = root_path.resolve()
        self.show_hidden = show_hidden
        self.max_depth = max_depth
        self.structure_lines: List[str] = []

        # Стандартные директории для игнорирования
        self.ignore_dirs = {
            '__pycache__', '.git', '.pytest_cache', '.ruff_cache',
            'mypy_cache', '.idea', '.vscode', '.mypy_cache',
            'node_modules', '.venv', 'venv', 'env', 'virtualenv',
            'logs', 'staticfiles', '__pycache__'
        }

        # Стандартные файлы для игнорирования
        self.ignore_files = {
            '.DS_Store', 'Thumbs.db', 'desktop.ini', 'db.sqlite3',
            'poetry.lock', '.coverage', '.coveragerc'
        }

        # Расширения бинарных файлов (не показываем содержимое)
        self.binary_extensions = {
            '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.pdf', '.zip', '.tar', '.gz',
            '.lock', '.db'
        }

    def should_ignore_dir(self, dir_path: Path) -> bool:
        """Проверяет, нужно ли игнорировать директорию."""
        dir_name = dir_path.name

        # Игнорируем системные и служебные директории
        if dir_name in self.ignore_dirs:
            return True

        # Игнорируем скрытые директории (если не включен показ скрытых)
        if not self.show_hidden and dir_name.startswith('.'):
            return True

        return False

    def should_ignore_file(self, file_path: Path) -> bool:
        """Проверяет, нужно ли игнорировать файл."""
        file_name = file_path.name

        # Игнорируем служебные файлы
        if file_name in self.ignore_files:
            return True

        # Игнорируем скрытые файлы (если не включен показ скрытых)
        if not self.show_hidden and file_name.startswith('.'):
            return True

        # Игнорируем файлы с определенными расширениями
        if file_path.suffix in self.binary_extensions:
            return True

        return False

    def format_size(self, size: int) -> str:
        """Форматирует размер файла."""
        if size == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def get_file_icon(self, file_path: Path) -> str:
        """Возвращает иконку для файла на основе расширения."""
        suffix = file_path.suffix.lower()
        file_name_lower = file_path.name.lower()

        # Специальные файлы
        if file_name_lower == 'makefile':
            return '🔨'
        if file_name_lower == 'dockerfile':
            return '🐳'
        if file_name_lower == '.env':
            return '🔐'
        if file_name_lower == '.gitignore':
            return '🙈'
        if file_name_lower == 'manage.py':
            return '🎮'

        # Расширения
        icons = {
            '.py': '🐍',
            '.js': '📜',
            '.ts': '📘',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.yaml': '⚙️',
            '.yml': '⚙️',
            '.toml': '🔧',
            '.md': '📝',
            '.txt': '📄',
            '.ini': '⚙️',
            '.conf': '⚙️',
            '.sh': '🐚',
            '.bat': '💻',
            '.ps1': '💻',
            '.sql': '🗄️',
        }

        return icons.get(suffix, '📄')

    def get_dir_icon(self, dir_path: Path) -> str:
        """Возвращает иконку для директории."""
        dir_name = dir_path.name.lower()

        special_dirs = {
            'src': '📂',
            'apps': '📦',
            'tests': '🧪',
            'static': '🎨',
            'media': '🖼️',
            'templates': '📑',
            'docs': '📚',
            'scripts': '🔧',
            'config': '⚙️',
            'database': '🗄️',
        }

        return special_dirs.get(dir_name, '📁')

    def collect_structure(self, path: Optional[Path] = None, prefix: str = "",
                          level: int = 0):
        """Рекурсивный сбор актуальной структуры проекта."""
        if path is None:
            path = self.root_path
            # Показываем корневую директорию
            root_icon = self.get_dir_icon(path)
            self.structure_lines.append(f"{root_icon} {path.name}/")
            prefix = "    "
            level = 0

        # Проверяем максимальную глубину
        if level >= self.max_depth:
            if any(path.iterdir()):
                self.structure_lines.append(f"{prefix}    ... (еще содержимое)")
            return

        try:
            # Получаем все элементы в директории
            items = []
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    if not self.should_ignore_dir(item):
                        items.append(item)
                else:  # файл
                    if not self.should_ignore_file(item):
                        items.append(item)

            # Обрабатываем каждый элемент
            for i, item in enumerate(items):
                is_last_item = (i == len(items) - 1)
                connector = "└── " if is_last_item else "├── "

                if item.is_dir():
                    # Отображаем директорию
                    dir_icon = self.get_dir_icon(item)
                    self.structure_lines.append(f"{prefix}{connector}{dir_icon} {item.name}/")

                    # Рекурсивно обрабатываем поддиректорию
                    next_prefix = prefix + ("    " if is_last_item else "│   ")
                    self.collect_structure(item, next_prefix, level + 1)
                else:
                    # Отображаем файл с размером и иконкой
                    try:
                        size = item.stat().st_size
                        size_str = self.format_size(size)
                        file_icon = self.get_file_icon(item)
                        self.structure_lines.append(f"{prefix}{connector}{file_icon} {item.name} ({size_str})")
                    except (PermissionError, OSError):
                        self.structure_lines.append(f"{prefix}{connector}🔒 {item.name} (доступ запрещен)")

        except PermissionError:
            self.structure_lines.append(f"{prefix}    ⚠️ Нет доступа к директории")

    def count_items(self) -> Dict[str, int]:
        """Подсчитывает количество файлов и директорий в структуре."""
        files_count = 0
        dirs_count = 0

        for line in self.structure_lines:
            # Строки директорий (заканчиваются на / и содержат иконку)
            if line.strip().endswith('/') and not line.strip().endswith(')/'):
                dirs_count += 1
            # Строки файлов (содержат размер в скобках)
            elif ' (' in line and line.strip().endswith(')'):
                files_count += 1

        return {'files': files_count, 'dirs': dirs_count}

    def save_to_file(self, output_file: Path):
        """Сохраняет структуру в файл."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("STRUCTURE OF PROJECT\n")
            f.write(f"Path: {self.root_path}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Show hidden: {'Yes' if self.show_hidden else 'No'}\n")
            f.write(f"Max depth: {self.max_depth}\n")
            f.write("=" * 80 + "\n\n")
            f.write("\n".join(self.structure_lines))
            f.write("\n\n" + "=" * 80 + "\n")

            stats = self.count_items()
            f.write("STATISTICS:\n")
            f.write(f"  Directories: {stats['dirs']}\n")
            f.write(f"  Files: {stats['files']}\n")
            f.write(f"  Total: {stats['dirs'] + stats['files']}\n")
            f.write("=" * 80 + "\n")

    def print_structure(self, max_lines: int = 100):
        """Выводит структуру в консоль."""
        print("\n".join(self.structure_lines[:max_lines]))
        if len(self.structure_lines) > max_lines:
            print(f"\n... and {len(self.structure_lines) - max_lines} more lines")


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(description='Project Structure Analysis')
    parser.add_argument('path', nargs='?', default='.',
                        help='Path to project (default: current directory)')
    parser.add_argument('--hidden', action='store_true',
                        help='Show hidden files and directories')
    parser.add_argument('--depth', type=int, default=4,
                        help='Maximum depth (default: 4)')
    parser.add_argument('--output', '-o', type=str, default='project_structure.txt',
                        help='Output file name (default: project_structure.txt)')

    args = parser.parse_args()

    # Определяем путь к проекту
    project_path = Path(args.path).resolve()

    if not project_path.exists():
        print(f"Error: Path {project_path} does not exist!")
        return

    print("=" * 60)
    print("Project Structure Analysis")
    print("=" * 60)
    print(f"Path: {project_path}")
    print(f"Settings: depth={args.depth}, hidden={'Yes' if args.hidden else 'No'}")
    print("=" * 60)
    print()

    # Собираем структуру
    checker = StructureChecker(project_path, show_hidden=args.hidden, max_depth=args.depth)
    checker.collect_structure()

    # Выводим структуру
    checker.print_structure()

    # Сохраняем в файл
    output_file = project_path / args.output
    checker.save_to_file(output_file)
    print(f"\n[OK] Full structure saved to: {output_file}")

    # Статистика
    stats = checker.count_items()
    print("\n" + "=" * 60)
    print("STATISTICS:")
    print(f"  Directories: {stats['dirs']}")
    print(f"  Files: {stats['files']}")
    print(f"  Total: {stats['dirs'] + stats['files']}")
    print("=" * 60)


if __name__ == '__main__':
    main()