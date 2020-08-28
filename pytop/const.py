import os
import sys
from time import time
from string import Template
from typing import List, Tuple, Dict

import psutil

VERSION = "1.0.0"

SELF_START = time()

SYSTEM: str
if "linux" in sys.platform:
    SYSTEM = "Linux"
elif "bsd" in sys.platform:
    SYSTEM = "BSD"
elif "darwin" in sys.platform:
    SYSTEM = "MacOS"
else:
    SYSTEM = "Other"

BANNER_SRC: List[Tuple[str, str, str]] = [
	("#ffa50a", "#0fd7ff", "██████╗ ██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗"),
	("#f09800", "#00bfe6", "██╔══██╗██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔═══██╗██╔══██╗"),
	("#db8b00", "#00a6c7", "██████╔╝██████╔╝ ╚████╔╝    ██║   ██║   ██║██████╔╝"),
	("#c27b00", "#008ca8", "██╔══██╗██╔═══╝   ╚██╔╝     ██║   ██║   ██║██╔═══╝ "),
	("#a86b00", "#006e85", "██████╔╝██║        ██║      ██║   ╚██████╔╝██║"),
	("#000000", "#000000", "╚═════╝ ╚═╝        ╚═╝      ╚═╝    ╚═════╝ ╚═╝"),
]

# This is the template used to create the config file
DEFAULT_CONF: Template = Template(
f'#? Config file for bpytop v. {VERSION}' +

'''
#* Color theme, looks for a .theme file in "/usr/[local/]share/bpytop/themes" and "~/.config/bpytop/themes", "Default" for builtin default theme.
#* Prefix name by a plus sign (+) for a theme located in user themes folder, i.e. color_theme="+monokai"
color_theme="$color_theme"

#* Update time in milliseconds, increases automatically if set below internal loops processing time, recommended 2000 ms or above for better sample times for graphs.
update_ms=$update_ms

#* Processes sorting, "pid" "program" "arguments" "threads" "user" "memory" "cpu lazy" "cpu responsive",
#* "cpu lazy" updates top process over time, "cpu responsive" updates top process directly.
proc_sorting="$proc_sorting"

#* Reverse sorting order, True or False.
proc_reversed=$proc_reversed

#* Show processes as a tree
proc_tree=$proc_tree

#* Use the cpu graph colors in the process list.
proc_colors=$proc_colors

#* Use a darkening gradient in the process list.
proc_gradient=$proc_gradient

#* If process cpu usage should be of the core it's running on or usage of the total available cpu power.
proc_per_core=$proc_per_core

#* Show process memory as bytes instead of percent
proc_mem_bytes=$proc_mem_bytes

#* Check cpu temperature, needs "vcgencmd" on Raspberry Pi and "osx-cpu-temp" on MacOS X.
check_temp=$check_temp

#* Draw a clock at top of screen, formatting according to strftime, empty string to disable.
draw_clock="$draw_clock"

#* Update main ui in background when menus are showing, set this to false if the menus is flickering too much for comfort.
background_update=$background_update

#* Custom cpu model name, empty string to disable.
custom_cpu_name="$custom_cpu_name"

#* Optional filter for shown disks, should be last folder in path of a mountpoint, "root" replaces "/", separate multiple values with comma.
#* Begin line with "exclude=" to change to exclude filter, oterwise defaults to "most include" filter. Example: disks_filter="exclude=boot, home"
disks_filter="$disks_filter"

#* Show graphs instead of meters for memory values.
mem_graphs=$mem_graphs

#* If swap memory should be shown in memory box.
show_swap=$show_swap

#* Show swap as a disk, ignores show_swap value above, inserts itself after first disk.
swap_disk=$swap_disk

#* If mem box should be split to also show disks info.
show_disks=$show_disks

#* Set fixed values for network graphs, default "10M" = 10 Mibibytes, possible units "K", "M", "G", append with "bit" for bits instead of bytes, i.e "100mbit"
net_download="$net_download"
net_upload="$net_upload"

#* Start in network graphs auto rescaling mode, ignores any values set above and rescales down to 10 Kibibytes at the lowest.
net_auto=$net_auto

#* If the network graphs color gradient should scale to bandwith usage or auto scale, bandwith usage is based on "net_download" and "net_upload" values
net_color_fixed=$net_color_fixed

#* Show init screen at startup, the init screen is purely cosmetical
show_init=$show_init

#* Enable check for new version from github.com/aristocratos/bpytop at start.
update_check=$update_check

#* Enable start in mini mode, can be toggled with shift+m at any time.
mini_mode=$mini_mode

#* Set loglevel for "~/.config/bpytop/error.log" levels are: "ERROR" "WARNING" "INFO" "DEBUG".
#* The level set includes all lower levels, i.e. "DEBUG" will show all logging info.
log_level=$log_level
''')

CONFIG_DIR: str = f'{os.path.expanduser("~")}/.config/bpytop'
if not os.path.isdir(CONFIG_DIR):
	try:
		os.makedirs(CONFIG_DIR)
		os.mkdir(f'{CONFIG_DIR}/themes')
	except PermissionError:
		print(f'ERROR!\nNo permission to write to "{CONFIG_DIR}" directory!')
		raise SystemExit(1)
CONFIG_FILE: str = f'{CONFIG_DIR}/bpytop.conf'

THEME_DIR: str = ""
for td in ["local/", ""]:
	if os.path.isdir(f'/usr/{td}share/bpytop/themes'):
		THEME_DIR = f'/usr/{td}share/bpytop/themes'
		break
USER_THEME_DIR: str = f'{CONFIG_DIR}/themes'

CORES: int = psutil.cpu_count(logical=False) or 1
THREADS: int = psutil.cpu_count(logical=True) or 1

THREAD_ERROR: int = 0

DEBUG = bool('--debug' in sys.argv)

DEFAULT_THEME: Dict[str, str] = {
	"main_bg" : "",
	"main_fg" : "#cc",
	"title" : "#ee",
	"hi_fg" : "#969696",
	"selected_bg" : "#7e2626",
	"selected_fg" : "#ee",
	"inactive_fg" : "#40",
	"graph_text" : "#60",
	"meter_bg" : "#40",
	"proc_misc" : "#0de756",
	"cpu_box" : "#3d7b46",
	"mem_box" : "#8a882e",
	"net_box" : "#423ba5",
	"proc_box" : "#923535",
	"div_line" : "#30",
	"temp_start" : "#4897d4",
	"temp_mid" : "#5474e8",
	"temp_end" : "#ff40b6",
	"cpu_start" : "#50f095",
	"cpu_mid" : "#f2e266",
	"cpu_end" : "#fa1e1e",
	"free_start" : "#223014",
	"free_mid" : "#b5e685",
	"free_end" : "#dcff85",
	"cached_start" : "#0b1a29",
	"cached_mid" : "#74e6fc",
	"cached_end" : "#26c5ff",
	"available_start" : "#292107",
	"available_mid" : "#ffd77a",
	"available_end" : "#ffb814",
	"used_start" : "#3b1f1c",
	"used_mid" : "#d9626d",
	"used_end" : "#ff4769",
	"download_start" : "#231a63",
	"download_mid" : "#4f43a3",
	"download_end" : "#b0a9de",
	"upload_start" : "#510554",
	"upload_mid" : "#7d4180",
	"upload_end" : "#dcafde",
	"process_start" : "#80d0a3",
	"process_mid" : "#dcd179",
	"process_end" : "#d45454",
}

MENUS: Dict[str, Dict[str, Tuple[str, ...]]] = {
	"options" : {
		"normal" : (
			"┌─┐┌─┐┌┬┐┬┌─┐┌┐┌┌─┐",
			"│ │├─┘ │ ││ ││││└─┐",
			"└─┘┴   ┴ ┴└─┘┘└┘└─┘"),
		"selected" : (
			"╔═╗╔═╗╔╦╗╦╔═╗╔╗╔╔═╗",
			"║ ║╠═╝ ║ ║║ ║║║║╚═╗",
			"╚═╝╩   ╩ ╩╚═╝╝╚╝╚═╝") },
	"help" : {
		"normal" : (
			"┬ ┬┌─┐┬  ┌─┐",
			"├─┤├┤ │  ├─┘",
			"┴ ┴└─┘┴─┘┴  "),
		"selected" : (
			"╦ ╦╔═╗╦  ╔═╗",
			"╠═╣║╣ ║  ╠═╝",
			"╩ ╩╚═╝╩═╝╩  ") },
	"quit" : {
		"normal" : (
			"┌─┐ ┬ ┬ ┬┌┬┐",
			"│─┼┐│ │ │ │ ",
			"└─┘└└─┘ ┴ ┴ "),
		"selected" : (
			"╔═╗ ╦ ╦ ╦╔╦╗ ",
			"║═╬╗║ ║ ║ ║  ",
			"╚═╝╚╚═╝ ╩ ╩  ") }
}

MENU_COLORS: Dict[str, Tuple[str, ...]] = {
	"normal" : ("#0fd7ff", "#00bfe6", "#00a6c7", "#008ca8"),
	"selected" : ("#ffa50a", "#f09800", "#db8b00", "#c27b00")
}

#? Units for floating_humanizer function
UNITS: Dict[str, Tuple[str, ...]] = {
	"bit" : ("bit", "Kib", "Mib", "Gib", "Tib", "Pib", "Eib", "Zib", "Yib", "Bib", "GEb"),
	"byte" : ("Byte", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB", "BiB", "GEB")
}

try:
	CONFIG: Config = Config(CONFIG_FILE)
	if DEBUG:
		errlog.setLevel(DEBUG)
	else:
		errlog.setLevel(getattr(logging, CONFIG.log_level))
		if CONFIG.log_level == "DEBUG": DEBUG = True
	errlog.info(f'New instance of bpytop version {VERSION} started with pid {os.getpid()}')
	errlog.info(f'Loglevel set to {"DEBUG" if DEBUG else CONFIG.log_level}')
	errlog.debug(f'Using psutil version {".".join(str(x) for x in psutil.version_info)}')
	errlog.debug(f'CMD: {" ".join(sys.argv)}')
	if CONFIG.info:
		for info in CONFIG.info:
			errlog.info(info)
		CONFIG.info = []
	if CONFIG.warnings:
		for warning in CONFIG.warnings:
			errlog.warning(warning)
		CONFIG.warnings = []
except Exception as e:
	errlog.exception(f'{e}')
	raise SystemExit(1)

