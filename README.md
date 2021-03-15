# plover\_trayicon

Show an additional tray icon that can be controlled by Plover's commands.

### Usage

Add the commands in the translation part of the stroke definition.

* `{PLOVER:trayicon:icon_id /path/to/icon_file}`: Create an icon with the specified ID and icon path.
  If an icon with the specified ID already exists, its icon will be replaced.

  Note that if the path contains any spaces or backslashes, it must be properly quoted
  (for example with `'...'`, the strung will be parsed with `shlex.split`)

For more info, run `python -m plover_trayicon.help`.

Only tested on some environments.
