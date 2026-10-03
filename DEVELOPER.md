# VK Code Show: разработка

## Структура

- `VK-code-show.py` - тонкая корневая точка входа.
- `vk_code_show/app.py` - создание `QApplication`, русская Qt-локализация,
  глобальная тема, загрузка настроек и запуск окна.
- `vk_code_show/ui.py` - главное окно, захват клавиш, история и runtime UI scale.
- `vk_code_show/settings.py` - `settings.json`, defaults и миграции.
- `vk_code_show/ui_scale_service.py` - чистые формулы масштаба.
- `vk_code_show/ui_scale_runtime.py` и `ui_scale_overrides.py` - интеграция Qt
  screen/DPI и масштабирование QSS/layout/widget metrics.
- `Build_Tools/` - PyInstaller spec, GUI compiler и post-build перенос.
- `RUNTIME_MANIFEST.json` создается в portable-папке после сборки.
- `assets/icons/logo.png` - исходный прозрачный PNG для основной иконки,
  корневой `logo.ico` генерируется из него.

## Окружение

Все команды выполняются только через проектную `.venv`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
```

VS Code должен использовать `${workspaceFolder}\.venv\Scripts\python.exe`.

## Иконка

Основной источник иконки - `assets/icons/logo.png`. Для обновления
`logo.ico` использовать Pillow из `requirements-dev.txt` и сохранять ICO с
размерами `16, 24, 32, 48, 64, 128, 256`.

## Настройки

Runtime-настройки хранятся в `settings.json` рядом со скриптом или exe и не
коммитятся. Обязательные ключи:

- `window_pos_x`, `window_pos_y`, `window_width`, `window_height`, `maximized`;
- `ui_scale_mode`, `ui_scale_delta_percent`, `ui_scale_percent`.

Масштаб работает как автоматический расчет от `QScreen.availableGeometry()` и
`logicalDotsPerInch()` плюс ручная поправка пользователя `-50..50`.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Для smoke-проверки GUI:

```powershell
.\.venv\Scripts\python.exe .\VK-code-show.py
```

## Сборка

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe .\Build_Tools\build.py
```

`post_build.py` переносит папку portable в корень проекта и не запускает
собранный `.exe`. Он копирует `logo.ico`, `VERSION`, создает
`RUNTIME_MANIFEST.json`; пользователь запускает portable-приложение вручную.

## Release Helpers

После сборки portable-папки:

```powershell
Start-Process .\.venv\Scripts\pythonw.exe -WindowStyle Hidden -ArgumentList ".\00_CrRel.pyw"
Start-Process .\.venv\Scripts\pythonw.exe -WindowStyle Hidden -ArgumentList ".\00_Move.pyw"
```

Installer по умолчанию выбирает `D:\Apps\VK-code-show`, затем первый доступный
fixed drive кроме `C:`, затем `C:\Apps\VK-code-show`. `UsePreviousAppDir=no`.
Деинсталлятор завершает процесс приложения и удаляет `{app}` целиком.

## Release gates (0.2.0)

`Build_Tools/build.py` — единая точка CLI/GUI сборки. Проверяет `.venv`, сохраняет
настройки прошлой portable-папки в `_release_work/pre-build-settings`, удаляет
старую папку перед сборкой и задаёт минимальный PATH.
`runtime_dll_policy.py` проверяет исходные native origins до замены MSVC DLL,
затем выбирает полный комплект из установленного PySide6. EXE получает Windows
FileVersion/ProductVersion из VERSION.

`post_build.py` проверяет COLLECT-00.toc и SHA-256 корневого MSVC runtime,
выполняет smoke реального EXE с timeout 45 секунд, проверяет stdout/stderr и код
выхода, затем переносит папку и удаляет work-каталоги. Результаты остаются в
`_release_work/build-audit.json` и `frozen-smoke.json`. `RUNTIME_MANIFEST.json`
содержит SHA-256 EXE и результат frozen-проверки. Лицензии собственного кода,
Qt и Python включены в сборку.

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe .\VK-code-show.py --smoke-test .\_release_work\source-smoke.json
```

Smoke использует временные настройки и проверяет импорт Qt, перевод, иконку,
создание окна, захват V (VK 86 / scan 47), clipboard, очистку истории и рендер.
Пользовательский settings.json не меняется. Для offscreen-рендера шрифты Windows
загружаются явно.

Установщик берёт Desktop из Windows User Shell Folders с системным fallback,
сверяет VERSION исходников и portable, предлагает запуск по отмеченной галочке
`[Run]` с `skipifsilent`. Build helpers установщик не запускают.

Последний GitHub snapshot имеет orphan-историю; локальная история сохраняется.
Обычный push main может вернуть полную историю: публиковать через согласованный
orphan workflow после dry-run. Метаданные существующего релиза исправляются
отдельным PATCH без изменения tag или assets. Новый 0.2.0 до публикации локальный.

## Компилятор установщика

Для нестандартного расположения Inno Setup задайте INNO_SETUP_ISCC полным путём к ISCC.exe. Иначе используются стандартные каталоги установки и доступный компилятор из PATH.
