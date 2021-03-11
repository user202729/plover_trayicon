from typing import Dict, Tuple, TYPE_CHECKING
import subprocess
import sys
from pathlib import Path

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

def main(engine: "plover.engine.StenoEngine", argument: str)->None:
	try:
		icon_id, filepath=argument.split(":", maxsplit=1)
	except ValueError:
		icon_id=argument
		filepath=""

	if not filepath:
		try:
			process=trayIcons[icon_id]
			sendMessage(process, b"")
			process.wait()
			del trayIcons[icon_id]
		except KeyError as e:
			raise RuntimeError(f"Icon with the specified id ({icon_id!r}) does not exist!") from e

		return

	try:
		process=trayIcons[icon_id]
	except KeyError:
		assert Path(sys.executable).stem.lower()=="python", (sys.executable, Path(sys.executable).stem)

		def run():
			import sys
			from PIL import Image
			from pystray import Icon

			icon=Icon("Plover")

			def setup(icon):
				while True:
					message_size = int.from_bytes(sys.stdin.buffer.read(8), 'little') # 8 is definitely enough
					filepath=sys.stdin.buffer.read(message_size)
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
		trayIcons[icon_id]=process

	sendMessage(process, filepath.encode('u8'))
