import yaml
import configparser

def read_yaml(fn: str) -> dict:
	"""
	This is the helper function that reads the config yaml
	file and returns a config dictionary
	- Input:
		fn: filename
	- Returns:
		dict: a config dictionary
	"""
	try:
		with open(fn, 'r', encoding="utf-8") as file:
			# The FullLoader parameter handles the conversion from YAML
			# scalar values to Python the dictionary format
			config_yaml = yaml.load(file, Loader=yaml.FullLoader)
			return {"indicator": True, "message": "Load a yaml file successfully", "content":config_yaml}
	except Exception as e:
		return {"indicator": False, "message": str(e)}

def write_yaml(fn: str, content: dict, sort_keys=True) -> dict:
	"""
	This is the helper function that writes to the config yaml and 
	returns the status indicating whether the operation is successful or not.
	- Input:
		* fn: filename
		* content: resulting yaml to be added 
	- Returns:
		A dictionary containing the following keys
		* indicator: True, False whether the operation is completed
		* message: message of operation
	"""
	indicator = True
	message = "Write to yaml successful"
	try:
		with open(fn, "w") as file:
			yaml.dump(content, file, allow_unicode = True, sort_keys=sort_keys)
	except Exception as e:
		indicator = False
		message = str(e) 
	
	return {"indicator":indicator, "message":message}

def read_ini(fn: str) -> dict:
	"""
	This is the helper function that reads the config ini
	Parameters:
		fn: filename
	Returns:
		A dictionary containing the following keys
		* indicator: True, False whether the operation is completed
		* message: message of operation
	"""
	try:
		config_ini = configparser.ConfigParser()
		config_ini.read(fn)
		return {"indicator": True, "message": "Load an ini file successfully", "content": config_ini}
	except Exception as e:
		return {"indicator": False, "message": str(e)}