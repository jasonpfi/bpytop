import os
import logging
from typing import List, Dict, Union
from distutils.util import strtobool

from pytop.const import VERSION, DEFAULT_CONF
from pytop.classes import *

errlog = logging.getLogger("ErrorLogger")

class Config:
	'''Holds all config variables and functions.

    Used for loading from and saving to disk.
    '''

	keys: List[str] = ["color_theme", "update_ms", "proc_sorting",
                       "proc_reversed", "proc_tree", "check_temp",
                       "draw_clock", "background_update", "custom_cpu_name",
                       "proc_colors", "proc_gradient", "proc_per_core", "proc_mem_bytes",
		       "disks_filter", "update_check", "log_level", "mem_graphs",
                       "show_swap", "swap_disk", "show_disks", "net_download",
                       "net_upload", "net_auto", "net_color_fixed", "show_init", "mini_mode"]

	conf_dict: Dict[str, Union[str, int, bool]] = {}
	color_theme: str = "Default"
	update_ms: int = 2000
	proc_sorting: str = "cpu lazy"
	proc_reversed: bool = False
	proc_tree: bool = False
	proc_colors: bool = True
	proc_gradient: bool = True
	proc_per_core: bool = False
	proc_mem_bytes: bool = True
	check_temp: bool = True
	draw_clock: str = "%X"
	background_update: bool = True
	custom_cpu_name: str = ""
	disks_filter: str = ""
	update_check: bool = True
	mem_graphs: bool = True
	show_swap: bool = True
	swap_disk: bool = True
	show_disks: bool = True
	net_download: str = "10M"
	net_upload: str = "10M"
	net_color_fixed: bool = False
	net_auto: bool = False
	show_init: bool = True
	mini_mode: bool = False
	log_level: str = "WARNING"

	warnings: List[str] = []
	info: List[str] = []

	sorting_options: List[str] = ["pid", "program", "arguments", "threads", "user", "memory", "cpu lazy", "cpu responsive"]
	log_levels: List[str] = ["ERROR", "WARNING", "INFO", "DEBUG"]

	changed: bool = False
	recreate: bool = False
	config_file: str = ""

	_initialized: bool = False

	def __init__(self, path: str):
		self.config_file = path
		conf: Dict[str, Union[str, int, bool]] = self.load_config()

		if not "version" in conf.keys():
			self.recreate = True
			self.info.append(f'Config file malformatted or missing, will be recreated on exit!')
		elif conf["version"] != VERSION:
			self.recreate = True
			self.info.append(f'Config file version and bpytop version missmatch, will be recreated on exit!')
		for key in self.keys:
			if key in conf.keys() and conf[key] != "_error_":
				setattr(self, key, conf[key])
			else:
				self.recreate = True
				self.conf_dict[key] = getattr(self, key)
		self._initialized = True

	def __setattr__(self, name, value):
		if self._initialized:
			object.__setattr__(self, "changed", True)
		object.__setattr__(self, name, value)
		if name not in ["_initialized", "recreate", "changed"]:
			self.conf_dict[name] = value

	def load_config(self) -> Dict[str, Union[str, int, bool]]:
		'''Load config from file, set correct types for values and return a dict'''
		new_config: Dict[str,Union[str, int, bool]] = {}
		conf_file: str = ""

		if os.path.isfile(self.config_file):
			conf_file = self.config_file
		elif os.path.isfile("/etc/bpytop.conf"):
			conf_file = "/etc/bpytop.conf"
		else:
			return new_config

		try:
			with open(conf_file, "r") as f:
				for line in f:
					line = line.strip()
					if line.startswith("#? Config"):
						new_config["version"] = line[line.find("v. ") + 3:]
					for key in self.keys:
						if line.startswith(key):
							line = line.replace(key + "=", "")
							if line.startswith('"'):
								line = line.strip('"')
							if type(getattr(self, key)) == int:
								try:
									new_config[key] = int(line)
								except ValueError:
									self.warnings.append(f'Config key "{key}" should be an integer!')
							if type(getattr(self, key)) == bool:
								try:
									new_config[key] = bool(strtobool(line))
								except ValueError:
									self.warnings.append(f'Config key "{key}" can only be True or False!')
							if type(getattr(self, key)) == str:
									new_config[key] = str(line)
		except Exception as e:
			errlog.exception(str(e))

		if "proc_sorting" in new_config and not new_config["proc_sorting"] in self.sorting_options:
			new_config["proc_sorting"] = "_error_"
			self.warnings.append(f'Config key "proc_sorted" didn\'t get an acceptable value!')
		if "log_level" in new_config and not new_config["log_level"] in self.log_levels:
			new_config["log_level"] = "_error_"
			self.warnings.append(f'Config key "log_level" didn\'t get an acceptable value!')
		if isinstance(new_config["update_ms"], int) and new_config["update_ms"] < 100:
			new_config["update_ms"] = 100
			self.warnings.append(f'Config key "update_ms" can\'t be lower than 100!')
		return new_config

	def save_config(self):
		'''Save current config to config file if difference in values or version, creates a new file if not found'''
		if not self.changed and not self.recreate: return
		try:
			with open(self.config_file, "w" if os.path.isfile(self.config_file) else "x") as f:
				f.write(DEFAULT_CONF.substitute(self.conf_dict))
		except Exception as e:
			errlog.exception(str(e))

