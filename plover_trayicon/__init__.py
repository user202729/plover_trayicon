from typing import Dict, Tuple, TYPE_CHECKING
import subprocess
import sys
from pathlib import Path
from plover import log
import argparse
import shlex

#from PyQt5.QtWidgets import QSystemTrayIcon, QApplication
#from PyQt5.QtGui import QIcon

if TYPE_CHECKING:
	import plover.engine


trayIcons: Dict[str, subprocess.Popen]={}

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


parser=ArgumentParser(description="Display a tray icon in the system tray.",
		add_help=False,
		#exit_on_error=False,
		)
parser.add_argument("-p", "--persistent", help="Store the change to the hard disk", action="store_true")
parser.add_argument("-t", "--title", help="Title of the icon", default="Plover")
parser.add_argument("id", help="ID of the icon")
parser.add_argument("path", help="Path to the icon. If absent, the icon will be deleted", nargs="?")

def main(engine: "plover.engine.StenoEngine", arguments_string: str)->None:
	try:
		args=parser.parse_args(shlex.split(arguments_string))
	except ValueError:
		return

	if args.path is None:
		try:
			process=trayIcons[args.id]
			sendMessage(process, b"")
			process.wait()
			del trayIcons[args.id]
		except KeyError as e:
			raise RuntimeError(f"Icon with the specified id ({args.id!r}) does not exist!") from e

		return

	try:
		process=trayIcons[args.id]
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
		trayIcons[args.id]=process
		sendMessage(process, args.title.encode('u8'))

	sendMessage(process, args.path.encode('u8'))
