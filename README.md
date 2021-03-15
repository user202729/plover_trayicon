# plover\_trayicon

Show an additional tray icon that can be controlled by Plover's commands.

### Usage

Add the commands in the translation part of the stroke definition.

* `{plover:trayicon:icon_id /path/to/icon_file}`: Create an icon with the specified ID and icon path.
  If an icon with the specified ID already exists, its icon will be replaced.
  The icon ID must not contain `:`.

  Note that if the path contains any spaces or backslashes, it must be properly quoted
  (for example with `'...'`, the strung will be parsed with `shlex.split`)
* `{plover:trayicon:icon_id}`: Delete the icon with the specified `icon_id`.

TODO more documentation.

In older Plover versions, it may be necessary to type `plover` in uppercase.

Only tested on some environments.
