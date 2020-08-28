import subprocess
import re
import os
import logging
from typing import List
import signal

import psutil

from pytop.const import SYSTEM, CONFIG
from pytop.classes import *

errlog = logging.getLogger("ErrorLogger")

def get_cpu_name() -> str:
	'''Fetch a suitable CPU identifier from the CPU model name string'''

	name: str = ""
	nlist: List = []
	command: str = ""
	cmd_out: str = ""
	rem_line: str = ""
	if SYSTEM == "Linux":
		command = "cat /proc/cpuinfo"
		rem_line = "model name"
	elif SYSTEM == "MacOS":
		command ="sysctl -n machdep.cpu.brand_string"
	elif SYSTEM == "BSD":
		command ="sysctl hw.model"
		rem_line = "hw.model"

	try:
		cmd_out = subprocess.check_output("LANG=C " + command, shell=True, universal_newlines=True)
	except:
		pass
	if rem_line:
		for line in cmd_out.split("\n"):
			if rem_line in line:
				name = re.sub( ".*" + rem_line + ".*:", "", line,1).lstrip()
	else:
		name = cmd_out

	nlist = name.split(" ")

	if "Xeon" in name and "CPU" in name:
		name = nlist[nlist.index("CPU")+1]
	elif "Ryzen" in name:
		name = " ".join(nlist[nlist.index("Ryzen"):nlist.index("Ryzen")+3])
	elif "CPU" in name and not nlist[0] == "CPU":
		name = nlist[nlist.index("CPU")-1]

	return name

def create_box(x: int = 0, y: int = 0, width: int = 0, height: int = 0,
               title: str = "", title2: str = "", line_color: Color = None,
               title_color: Color = None, fill: bool = True, box = None,
               theme = None) -> str:

	'''Create a box from a box object or by given arguments'''

	out: str = f'{Term.fg}{Term.bg}'
	if not line_color:
		line_color = theme.div_line
	if not title_color:
		title_color = theme.title

	#* Get values from box class if given
	if box:
		x = box.x
		y = box.y
		width = box.width
		height =box.height
		title = box.name
	hlines: Tuple[int, int] = (y, y + height - 1)

	out += f'{line_color}'

	#* Draw all horizontal lines
	for hpos in hlines:
		out += f'{Mv.to(hpos, x)}{Symbol.h_line * (width - 1)}'

	#* Draw all vertical lines and fill if enabled
	for hpos in range(hlines[0]+1, hlines[1]):
		out += f'{Mv.to(hpos, x)}{Symbol.v_line}{" " * (width-2) if fill else Mv.r(width-2)}{Symbol.v_line}'

	#* Draw corners
	out += f'{Mv.to(y, x)}{Symbol.left_up}\
	{Mv.to(y, x + width - 1)}{Symbol.right_up}\
	{Mv.to(y + height - 1, x)}{Symbol.left_down}\
	{Mv.to(y + height - 1, x + width - 1)}{Symbol.right_down}'

	#* Draw titles if enabled
	if title:
		out += f'{Mv.to(y, x + 2)}{Symbol.title_left}{title_color}{Fx.b}{title}{Fx.ub}{line_color}{Symbol.title_right}'
	if title2:
		out += f'{Mv.to(hlines[1], x + 2)}{Symbol.title_left}{title_color}{Fx.b}{title2}{Fx.ub}{line_color}{Symbol.title_right}'

	return f'{out}{Term.fg}{Mv.to(y + 1, x + 1)}'

def now_sleeping(signum, frame):
	"""Reset terminal settings and stop background input read before putting to sleep"""
	Key.stop()
	Collector.stop()
	Draw.now(Term.clear, Term.normal_screen, Term.show_cursor, Term.mouse_off, Term.mouse_direct_off, Term.title())
	Term.echo(True)
	os.kill(os.getpid(), signal.SIGSTOP)

def now_awake(signum, frame):
	"""Set terminal settings and restart background input read"""
	Draw.now(Term.alt_screen, Term.clear, Term.hide_cursor, Term.mouse_on, Term.title("BpyTOP"))
	Term.echo(False)
	Key.start()
	Term.refresh()
	Box.calc_sizes()
	Box.draw_bg()
	Collector.start()

	#Draw.out()

def quit_sigint(signum, frame):
	"""SIGINT redirection to clean_quit()"""
	clean_quit()

def clean_quit(errcode: int = 0, errmsg: str = "", thread: bool = False,
			   start_time: int = 0):
	"""Stop background input read, save current config and reset terminal settings before quitting"""

	global THREAD_ERROR
	if thread:
		THREAD_ERROR = errcode
		interrupt_main()
		return

	if THREAD_ERROR:
		errcode = THREAD_ERROR

	Key.stop()
	Collector.stop()

	if not errcode:
		CONFIG.save_config()

	Draw.now(Term.clear, Term.normal_screen, Term.show_cursor, Term.mouse_off, Term.mouse_direct_off, Term.title())
	Term.echo(True)

	if errcode == 0:
		errlog.info(f'Exiting. Runtime {timedelta(seconds=round(time() - start_time, 0))} \n')
	else:
		errlog.warning(f'Exiting with errorcode ({errcode}). Runtime {timedelta(seconds=round(time() - start_time, 0))} \n')
		if not errmsg: errmsg = f'Bpytop exited with errorcode ({errcode}). See {CONFIG_DIR}/error.log for more information!'
	if errmsg:
		print(errmsg)

	raise SystemExit(errcode)

def floating_humanizer(value: Union[float, int], bit: bool = False, per_second: bool = False, start: int = 0, short: bool = False) -> str:
	'''Scales up in steps of 1024 to highest possible unit and returns string with unit suffixed

    * bit=True or defaults to bytes
	* start=int to set 1024 multiplier starting unit
	* short=True always returns 0 decimals and shortens unit to 1 character
	'''

	out: str = ""
	unit: Tuple[str, ...] = UNITS["bit"] if bit else UNITS["byte"]
	selector: int = start if start else 0
	mult: int = 8 if bit else 1
	if value <= 0: value = 0

	if isinstance(value, float):
		value = round(value * 100 * mult)
	elif value > 0:
		value *= 100 * mult
	else:
		value = 0

	while len(f'{value}') > 5 and value >= 102400:
		value >>= 10
		if value < 100:
			out = f'{value}'
			break
		selector += 1
	else:
		if len(f'{value}') < 5 and len(f'{value}') >= 2 and selector > 0:
			decimals = 5 - len(f'{value}')
			out = f'{value}'[:-2] + "." + f'{value}'[-decimals:]
		elif len(f'{value}') >= 2:
			out = f'{value}'[:-2]
		else:
			out = f'{value}'

	if short:
		out = out.split(".")[0]
		if len(out) > 3:
			out = f'{int(out[0]) + 1}'
			selector += 1
	out += f'{"" if short else " "}{unit[selector][0] if short else unit[selector]}'
	if per_second: out += "ps" if bit else "/s"

	return out

def units_to_bytes(value: str) -> int:
	if not value: return 0
	out: int = 0
	mult: int = 0
	bit: bool = False
	value_i: int = 0
	units: Dict[str, int] = {"k" : 1, "m" : 2, "g" : 3}
	try:
		if value.lower().endswith("s"):
			value = value[:-1]
		if value.lower().endswith("bit"):
			bit = True
			value = value[:-3]
		elif value.lower().endswith("byte"):
			value = value[:-4]

		if value[-1].lower() in units:
			mult = units[value[-1].lower()]
			value = value[:-1]

		if "." in value and value.replace(".", "").isdigit():
			if mult > 0:
				value_i = round(float(value) * 1024)
				mult -= 1
			else:
				value_i = round(float(value))
		elif value.isdigit():
			value_i = int(value)

		if bit:
			value_i = round(value_i / 8)
		out = int(value_i) << (10 * mult)
	except ValueError:
		out = 0
	return out

def process_keys():
	mouse_pos: Tuple[int, int] = (0, 0)
	filtered: bool = False
	while Key.has_key():
		key = Key.get()
		if key in ["mouse_scroll_up", "mouse_scroll_down", "mouse_click"]:
			mouse_pos = Key.get_mouse()
			if mouse_pos[0] >= ProcBox.x and mouse_pos[1] >= ProcBox.current_y + 1 and mouse_pos[1] < ProcBox.current_y + ProcBox.current_h - 1:
				pass
			elif key == "mouse_click":
				key = "mouse_unselect"
			else:
				key = "_null"

		if ProcBox.filtering:
			if key in ["enter", "mouse_click", "mouse_unselect"]:
				ProcBox.filtering = False
				Collector.collect(ProcCollector, redraw=True, only_draw=True)
				continue
			elif key in ["escape", "delete"]:
				ProcCollector.search_filter = ""
				ProcBox.filtering = False
			elif len(key) == 1:
				ProcCollector.search_filter += key
			elif key == "backspace" and len(ProcCollector.search_filter) > 0:
				ProcCollector.search_filter = ProcCollector.search_filter[:-1]
			else:
				continue
			Collector.collect(ProcCollector, proc_interrupt=True, redraw=True)
			if filtered: Collector.collect_done.wait(0.1)
			filtered = True
			continue


		if key == "_null":
			continue
		elif key == "q":
			clean_quit()
		elif key == "+" and CONFIG.update_ms + 100 <= 86399900:
			CONFIG.update_ms += 100
			Box.draw_update_ms()
		elif key == "-" and CONFIG.update_ms - 100 >= 100:
			CONFIG.update_ms -= 100
			Box.draw_update_ms()
		elif key in ["b", "n"]:
			NetCollector.switch(key)
		elif key in ["M", "escape"]:
			Menu.main()
		elif key in ["o", "f2"]:
			Menu.options()
		elif key in ["h", "f1"]:
			Menu.help()
		elif key == "z":
			NetCollector.reset = not NetCollector.reset
			Collector.collect(NetCollector, redraw=True)
		elif key == "a":
			NetCollector.auto_min = not NetCollector.auto_min
			NetCollector.net_min = {"download" : -1, "upload" : -1}
			Collector.collect(NetCollector, redraw=True)
		elif key in ["left", "right"]:
			ProcCollector.sorting(key)
		elif key == " " and CONFIG.proc_tree and ProcBox.selected > 0:
			if ProcBox.selected_pid in ProcCollector.collapsed:
				ProcCollector.collapsed[ProcBox.selected_pid] = not ProcCollector.collapsed[ProcBox.selected_pid]
			Collector.collect(ProcCollector, interrupt=True, redraw=True)
		elif key == "e":
			CONFIG.proc_tree = not CONFIG.proc_tree
			Collector.collect(ProcCollector, interrupt=True, redraw=True)
		elif key == "r":
			CONFIG.proc_reversed = not CONFIG.proc_reversed
			Collector.collect(ProcCollector, interrupt=True, redraw=True)
		# elif key == "C":
		# 	CONFIG.proc_colors = not CONFIG.proc_colors
		# 	Collector.collect(ProcCollector, redraw=True, only_draw=True)
		# elif key == "G":
		# 	CONFIG.proc_gradient = not CONFIG.proc_gradient
		# 	Collector.collect(ProcCollector, redraw=True, only_draw=True)
		elif key == "c":
			CONFIG.proc_per_core = not CONFIG.proc_per_core
			Collector.collect(ProcCollector, interrupt=True, redraw=True)
		elif key == "g":
			CONFIG.mem_graphs = not CONFIG.mem_graphs
			Collector.collect(MemCollector, interrupt=True, redraw=True)
		elif key == "s":
			CONFIG.swap_disk = not CONFIG.swap_disk
			Collector.collect(MemCollector, interrupt=True, redraw=True)
		elif key == "f":
			ProcBox.filtering = True
			if not ProcCollector.search_filter: ProcBox.start = 0
			Collector.collect(ProcCollector, redraw=True, only_draw=True)
		elif key == "m":
			Box.mini_mode = not Box.mini_mode
			Draw.clear(saved=True)
			Term.refresh(force=True)
		elif key.lower() in ["t", "k", "i"] and (ProcBox.selected > 0 or ProcCollector.detailed):
			pid: int = ProcBox.selected_pid if ProcBox.selected > 0 else ProcCollector.detailed_pid # type: ignore
			if psutil.pid_exists(pid):
				if key == "t": sig = signal.SIGTERM
				elif key == "k": sig = signal.SIGKILL
				elif key == "i": sig = signal.SIGINT
				try:
					os.kill(pid, sig)
				except Exception as e:
					errlog.error(f'Exception when sending signal {sig} to pid {pid}')
					errlog.exception(f'{e}')
		elif key == "delete" and ProcCollector.search_filter:
			ProcCollector.search_filter = ""
			Collector.collect(ProcCollector, proc_interrupt=True, redraw=True)
		elif key == "enter":
			if ProcBox.selected > 0 and ProcCollector.detailed_pid != ProcBox.selected_pid and psutil.pid_exists(ProcBox.selected_pid):
				ProcCollector.detailed = True
				ProcBox.last_selection = ProcBox.selected
				ProcBox.selected = 0
				ProcCollector.detailed_pid = ProcBox.selected_pid
				ProcBox.resized = True
			elif ProcCollector.detailed:
				ProcBox.selected = ProcBox.last_selection
				ProcBox.last_selection = 0
				ProcCollector.detailed = False
				ProcCollector.detailed_pid = None
				ProcBox.resized = True
			else:
				continue
			ProcCollector.details = {}
			ProcCollector.details_cpu = []
			ProcCollector.details_mem = []
			Graphs.detailed_cpu = NotImplemented
			Graphs.detailed_mem = NotImplemented
			Collector.collect(ProcCollector, proc_interrupt=True, redraw=True)

		elif key in ["up", "down", "mouse_scroll_up", "mouse_scroll_down", "page_up", "page_down", "home", "end", "mouse_click", "mouse_unselect"]:
			ProcBox.selector(key, mouse_pos)

def setup_err_log():
	"""Used to set up basic error logger."""
	try:
		# Basic error log
		errlog = logging.getLogger("ErrorLogger")
		errlog.setLevel(logging.DEBUG)

		# Rotating file handler to capture log files
		eh = logging.handlers.RotatingFileHandler(f'{CONFIG_DIR}/error.log', maxBytes=1048576, backupCount=4)
		eh.setLevel(logging.DEBUG)
		eh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s: %(message)s", datefmt="%d/%m/%y (%X)"))
		errlog.addHandler(eh)

	# File Write permission error
	except PermissionError:
		print(f'ERROR!\nNo permission to write to "{CONFIG_DIR}" directory!')
		raise SystemExit(1)


