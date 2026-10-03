<p align="center"><img src="assets/icons/logo.png" width="128" alt="VK Code Show"></p>
<h1 align="center">VK Code Show</h1>
<p align="center">Коды клавиш Windows и scan code с копированием в один клик.</p>
<p align="center"><a href="README.en.md">English</a> · <a href="https://github.com/Frommer-droid/VK-code-show/releases/latest">Последний релиз</a></p>

**Небольшая Windows-утилита для просмотра virtual-key codes активного окна.**

Приложение показывает VK-код последней нажатой клавиши, хранит короткую историю
и копирует значения в обычном виде или как `{VKC:86}`.

## Возможности

- Захват клавиш, когда окно приложения активно.
- Отображение VK, hex VK, scan code, Qt key, текста и модификаторов.
- Копирование выбранного VK, hex VK, последнего VKC token и scan code.
- Русская локализация стандартных Qt-текстов.
- Автоматический UI scale от текущего экрана/DPI и ручная поправка через
  `Масштаб интерфейса`.

## Готовое приложение

Скачайте установщик из [последнего релиза](https://github.com/Frommer-droid/VK-code-show/releases/latest),
установите приложение и нажмите клавишу в его активном окне. Для `V` появятся
VK `86`, hex `0x56` и token `{VKC:86}`. Scan code зависит от клавиатуры.
Доступ к скачиванию требует доступа к репозиторию, пока он приватный.
Python для готовой сборки не нужен.

## Требования

- Windows x64.
- Python 3.12.
- Проектная `.venv`.

## Быстрый старт

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\VK-code-show.py
```

Если `VK-code-show.py` запущен другим Python, bootstrap попробует
перезапустить приложение через `.\.venv\Scripts\python.exe`.

## Разработка

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

VS Code настроен на проектный интерпретатор в `.vscode/settings.json`.

## Сборка

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe .\Build_Tools\build.py
```

`post_build.py` переносит portable-папку `VK-code-show` в корень проекта и не
запускает собранный exe.

## Release Helpers

```powershell
Start-Process .\.venv\Scripts\pythonw.exe -WindowStyle Hidden -ArgumentList ".\00_CrRel.pyw"
Start-Process .\.venv\Scripts\pythonw.exe -WindowStyle Hidden -ArgumentList ".\00_Move.pyw"
```

`00_CrRel.pyw` создает `VK-code-show_v<VERSION>_Setup.exe` на рабочем столе Windows.
Installer по умолчанию ставит приложение в `D:\Apps\VK-code-show`, при
отсутствии подходящего диска использует fallback на `C:\Apps\VK-code-show`.

Подробности разработки и релиза описаны в [DEVELOPER.md](DEVELOPER.md).

## Ограничения и лицензия

Захват работает только при активном окне приложения; глобального перехвата нет.
Настройки хранятся рядом с программой: каталог должен быть доступен для записи.
Собственный код — [MIT](LICENSE); зависимости — [по своим лицензиям](THIRD_PARTY_NOTICES.md).
