from typing import Dict, Tuple, TYPE_CHECKING, NamedTuple
import subprocess
import sys
import json
from pathlib import Path
from plover import log
import argparse
import shlex
from plover.oslayer.config import CONFIG_DIR

#from PyQt5.QtWidgets import QSystemTrayIcon, QApplication
#from PyQt5.QtGui import QIcon

if TYPE_CHECKING:
	import plover.engine

def sendMessage(process: subprocess.Popen, message: bytes):
	# might raise BlockingIOError if the subprocess misbehave
	assert process.stdin is not None
	process.stdin.write(len(message).to_bytes(8, "little"))
	process.stdin.write(message)
	process.stdin.flush()


class ArgumentParser(argparse.ArgumentParser):
	def error(self, message):
		log.error(message)
		raise ValueError

#	def exit(self, status=0, message=None):
#		log.debug(f"statuscode={status}")
#		log.error(message)
#		raise ValueError


SAVE_FILE_PATH=Path(CONFIG_DIR)/"plover_trayicon_state.json"


class Icon(NamedTuple):
	process: subprocess.Popen
	title: str
	path: str


trayIcons: Dict[str, Icon]={}


parser=ArgumentParser(description="Display a tray icon in the system tray.",
		add_help=False,
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		#exit_on_error=False,
		)
parser.add_argument("-e", "--temporary", help="Do not store the change to the hard disk this time. "
		"Note that the next time the plugin is called without this flag, the change will be stored."
		, action="store_true")
parser.add_argument("-t", "--title", help="Title of the icon.", default="Plover")
parser.add_argument("id", help="ID of the icon. Each icon should have a different ID.")
parser.add_argument("path", help="Path to the icon. If absent, the icon will be deleted.", nargs="?")


def deleteTrayIcon(icon_id: str)->None:
	# might raise KeyError if the icon is not found
	process, title, path=trayIcons[icon_id]
	sendMessage(process, b"")
	process.wait()
	del trayIcons[icon_id]


def addTrayIcon(icon_id: str, title: str, path: str)->None:
	try:
		process, old_title, old_path=trayIcons[icon_id]
		title=old_title # TODO
		log.info("Cannot change title of existing icon")
	except KeyError:
		assert Path(sys.executable).stem.lower()=="python", (sys.executable, Path(sys.executable).stem)

		# This function must not take any arguments or access any variables in the upper scopes.
		# In fact, it's not called at all; rather its source code is passed to the subprocess
		def run():
			import sys
			from PIL import Image
			from pystray import Icon

			def read_message()->bytes:
				message_size = int.from_bytes(sys.stdin.buffer.read(8), 'little') # 8 is definitely enough
				return sys.stdin.buffer.read(message_size)

			icon=Icon(read_message().decode('u8'))

			def setup(icon):
				while True:
					filepath=read_message()
					if not filepath:
						icon.stop()
						break
					icon.icon=Image.open(filepath.decode('u8'))
					icon.visible=True

			icon.run(setup=setup)

		import inspect
		lines=inspect.getsource(run).splitlines()
		assert lines[0].lstrip().startswith('def')
		indentation = len(lines[1])-len(lines[1].lstrip())
		code="\n".join(line[indentation:] for line in lines[1:])

		process=subprocess.Popen((sys.executable, "-c", code),
				stdin=subprocess.PIPE,
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL,
				)
		sendMessage(process, title.encode('u8'))
		trayIcons[icon_id]=Icon(process, title, "")

	try:
		sendMessage(process, path.encode('u8'))
		trayIcons[icon_id]=Icon(process, title, path)
	except: # there should not be anything happen, but just in case
		deleteTrayIcon(icon_id)
		raise


def savePersistentIcons()->None:
	json.dump({
		icon_id: (icon.title, icon.path)
		for icon_id, icon in trayIcons.items()
		}, SAVE_FILE_PATH.open("w"), ensure_ascii=False, indent=0)


def initialLoadPersistentIcons()->None:
	try:
		content=json.load(SAVE_FILE_PATH.open("r"))
		if not isinstance(content, dict):
			raise TypeError
		for icon_id, (title, path) in content.items():
			if not isinstance(icon_id, str) or not isinstance(title, str) or not isinstance(path, str):
				raise TypeError
	except FileNotFoundError:
		return
	except (json.JSONDecodeError, ValueError, TypeError):
		log.error(f"Save file at {SAVE_FILE_PATH} is corrupted")
		return

	for icon_id, (title, path) in content.items():
		addTrayIcon(icon_id, title, path)
initialLoadPersistentIcons()


def main(engine: "plover.engine.StenoEngine", arguments_string: str)->None:
	try:
		args=parser.parse_args(shlex.split(arguments_string))
	except ValueError:
		return

	if args.path is None:
		try:
			deleteTrayIcon(args.id)
		except KeyError as e:
			raise RuntimeError(f"Icon with the specified id ({args.id!r}) does not exist!") from e
		if not args.temporary: savePersistentIcons()
		return

	addTrayIcon(args.id, args.title, args.path)
	if not args.temporary: savePersistentIcons()
