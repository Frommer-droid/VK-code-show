# Third-party components

MIT in LICENSE covers the project's own code. Dependencies retain their licenses.

- PySide6, Shiboken6 and Qt: LGPL-3.0 / GPL-3.0 / commercial licensing,
  depending on the component. This application uses QtCore, QtGui and QtWidgets
  as separate dynamic libraries; LGPL-3.0 and GPL-3.0 texts are distributed under
  `_internal/licenses/Qt`.
  Source and licensing: https://code.qt.io/pyside/pyside-setup and https://code.qt.io/qt/qtbase.
- PyInstaller: GPL-2.0-or-later with the bootloader exception permitting
  distribution of bundled applications under their own license.
- CPython: Python Software Foundation License, distributed in `_internal/licenses/Python/LICENSE.txt`.
- Microsoft Visual C++ runtime: Microsoft redistributable runtime terms.

The editable source and build instructions are provided in this repository.
Keep the dependency notices when redistributing a binary build.
