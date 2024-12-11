from typing import TypedDict, Union

class FelizResponse(TypedDict):
	indicator: bool
	message: str
	content: Union[dict, str, list, None]