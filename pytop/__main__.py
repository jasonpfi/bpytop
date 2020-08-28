#!/usr/bin/env python3
# pylint: disable=not-callable, no-member
# indent = tab
# tab-size = 4

import os, sys, threading, signal, re, subprocess, logging, logging.handlers
import urllib.request
from time import time, sleep, strftime, localtime
from datetime import timedelta
from _thread import interrupt_main
from collections import defaultdict
from select import select
from distutils.util import strtobool
from string import Template
from math import ceil, floor
from random import randint
from shutil import which
from typing import List, Set, Dict, Tuple, Optional, Union, Any, Callable, ContextManager, Iterable, Type, NamedTuple

from pytop.const import *
from pytop.config import Config
from pytop.classes import *
from pytop.utils import *
from pytop.theme import Theme

errors: List[str] = []
try:
	import fcntl, termios, tty
except Exception as e:
	errors.append(f'{e}')

try:
	import psutil # type: ignore
except Exception as e:
	errors.append(f'{e}')


if errors:
	print ("ERROR!")
	for error in errors:
		print(error)
	if SYSTEM == "Other":
		print("\nUnsupported platform!\n")
	else:
		print("\nInstall required modules!\n")
	raise SystemExit(1)

#? This should use the std python module argparse
if len(sys.argv) > 1:
	for arg in sys.argv[1:]:
		if not arg in ["-m", "--mini", "-v", "--version",
                       "-h", "--help", "--debug"]:
			print(f'Unrecognized argument: {arg}\n'
				  f'Use argument -h or --help for help')
			raise SystemExit(1)

if "-h" in sys.argv or "--help" in sys.argv:
	print(f'USAGE: {sys.argv[0]} [argument]\n\n'
		  f'Arguments:\n'
		  f'    -m, --mini            Start in minimal mode without memory and net boxes\n'
		  f'    -v, --version         Show version info and exit\n'
		  f'    -h, --help            Show this help message and exit\n'
		  f'    --debug               Start with loglevel set to DEBUG overriding value set in config\n'
	)
	raise SystemExit(0)
elif "-v" in sys.argv or "--version" in sys.argv:
	print(f'bpytop version: {VERSION}\n'
		  f'psutil version: {".".join(str(x) for x in psutil.version_info)}')
	raise SystemExit(0)

if __name__ == "__main__":

	# Create the error logger
	setup_err_log()

	# Start the debug timer to start program
	if DEBUG:
		TimeIt.start("Init")

	# Initialization class
	# Used to monitor startup health
	class Init:
		running: bool = True
		initbg_colors: List[str] = []
		initbg_data: List[int]
		initbg_up: Graph
		initbg_down: Graph
		resized = False

		@staticmethod
		def fail(err):
			if CONFIG.show_init:
				Draw.buffer("+init!", f'{Mv.restore}{Symbol.fail}')
				sleep(2)
			errlog.exception(f'{err}')
			clean_quit(1, errmsg=f'Error during init! See {CONFIG_DIR}/error.log for more information.',
					   start_time=SELF_START)

		@classmethod
		def success(cls, start: bool = False):
			if not CONFIG.show_init or cls.resized:
				return

			if start:
				Draw.buffer("init", z=1)
				Draw.buffer("initbg", z=10)
				for i in range(51):
					for _ in range(2):
						cls.initbg_colors.append(Color.fg(i, i, i))
				Draw.buffer("banner", (f'{Banner.draw(Term.height // 2 - 10, center=True)}{Mv.d(1)}{Mv.l(11)}{Colors.black_bg}{Colors.default}'
						f'{Fx.b}{Fx.i}Version: {VERSION}{Fx.ui}{Fx.ub}{Term.bg}{Term.fg}{Color.fg("#50")}'), z=2)
				for _i in range(7):
					perc = f'{str(round((_i + 1) * 14 + 2)) + "%":>5}'
					Draw.buffer("+banner", f'{Mv.to(Term.height // 2 - 2 + _i, Term.width // 2 - 28)}{Fx.trans(perc)}{Symbol.v_line}')

				Draw.out("banner")
				Draw.buffer("+init!", f'{Color.fg("#cc")}{Fx.b}{Mv.to(Term.height // 2 - 2, Term.width // 2 - 21)}{Mv.save}')

				cls.initbg_data = [randint(0, 100) for _ in range(Term.width * 2)]
				cls.initbg_up = Graph(Term.width, Term.height // 2, cls.initbg_colors, cls.initbg_data, invert=True)
				cls.initbg_down = Graph(Term.width, Term.height // 2, cls.initbg_colors, cls.initbg_data, invert=False)

			if start:
				return

			cls.draw_bg(5)
			Draw.buffer("+init!", f'{Mv.restore}{Symbol.ok}\n{Mv.r(Term.width // 2 - 22)}{Mv.save}')

		@classmethod
		def draw_bg(cls, times: int = 5):
			"""Draw background """
			for _ in range(times):
				sleep(0.05)
				x = randint(0, 100)
				Draw.buffer("initbg",
							f'{Fx.ub}{Mv.to(0, 0)}{cls.initbg_up(x)}{Mv.to(Term.height // 2, 0)}{cls.initbg_down(x)}')
				Draw.out("initbg", "banner", "init")

		@classmethod
		def done(cls):
			cls.running = False
			if not CONFIG.show_init:
				return
			if cls.resized:
				Draw.now(Term.clear)
			else:
				cls.draw_bg(10)
			Draw.clear("initbg", "banner", "init", saved=True)
			if cls.resized:
				return
			del cls.initbg_up, cls.initbg_down, cls.initbg_data, cls.initbg_colors

	#? Switch to alternate screen, clear screen, hide cursor,
	#? enable mouse reporting and disable input echo
	Draw.now(Term.alt_screen, Term.clear, Term.hide_cursor, Term.mouse_on,
			 Term.title("BpyTOP"))
	Term.echo(False)
	Term.refresh(force=True)
	if CONFIG.update_check:
		UpdateChecker.run()

	#? Load theme
	if CONFIG.show_init:
		Init.success(start=True)
		Draw.buffer("+init!",
					f'{Mv.restore}{Fx.trans("Loading theme and creating colors... ")}{Mv.save}')
	try:
		theme: Theme = Theme(CONFIG.color_theme)
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Setup boxes
	if CONFIG.show_init:
		Draw.buffer("+init!",
					f'{Mv.restore}{Fx.trans("Doing some maths and drawing... ")}{Mv.save}')
	try:
		if CONFIG.check_temp:
			CpuCollector.get_sensors()
		Box.calc_sizes()
		Box.draw_bg(now=False)
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Setup signal handlers for SIGSTP, SIGCONT, SIGINT and SIGWINCH
	if CONFIG.show_init:
		Draw.buffer("+init!",
					f'{Mv.restore}{Fx.trans("Setting up signal handlers... ")}{Mv.save}')
	try:
		signal.signal(signal.SIGTSTP,  now_sleeping) #* Ctrl-Z
		signal.signal(signal.SIGCONT,  now_awake)	#* Resume
		signal.signal(signal.SIGINT,   quit_sigint)	#* Ctrl-C
		signal.signal(signal.SIGWINCH, Term.refresh) #* Terminal resized
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Start a separate thread for reading keyboard input
	if CONFIG.show_init:
		Draw.buffer("+init!",
					f'{Mv.restore}{Fx.trans("Starting input reader thread... ")}{Mv.save}')
	try:
		Key.start()
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Start a separate thread for data collection and drawing
	if CONFIG.show_init:
		Draw.buffer("+init!",
					f'{Mv.restore}{Fx.trans("Starting data collection and drawer thread... ")}{Mv.save}')
	try:
		Collector.start()
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Collect data and draw to buffer
	if CONFIG.show_init:
		Draw.buffer("+init!",
					f'{Mv.restore}{Fx.trans("Collecting data and drawing... ")}{Mv.save}')
	try:
		Collector.collect(draw_now=False)
		pass
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	#? Draw to screen
	if CONFIG.show_init:
		Draw.buffer("+init!",
					f'{Mv.restore}{Fx.trans("Finishing up... ")}{Mv.save}')
	try:
		Collector.collect_done.wait()
	except Exception as e:
		Init.fail(e)
	else:
		Init.success()

	# Finish up and draw screen
	# Stop debug timer
	Init.done()
	Term.refresh()
	Draw.out(clear=True)
	if CONFIG.draw_clock:
		Box.clock_on = True
	if DEBUG:
		TimeIt.stop("Init")

	#? Main loop ------------------------------------------------------------------------------------->

	def main():
		# This is pretty wack
		# Should be done with global "running" variable that can be set
		while not False:

			# Redraw the screen
			Term.refresh()
			Timer.stamp()

			# Process key presses before timer goes off
			# Timer is used to re-draw screen
			while Timer.not_zero():
				if Key.input_wait(Timer.left()):
					process_keys()

			# Collect all new data
			Collector.collect()

	#? Start main loop
	try:
		main()
	except Exception as e:
		errlog.exception(f'{e}')
		clean_quit(1, start_time=SELF_START)
	else:
		#? Quit cleanly even if false starts being true...
		clean_quit(start_time=SELF_START)
