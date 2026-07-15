import requests
from pathlib import Path

def download_to_local(url:str, out_path:Path,
                      parent_mkdir:bool=True):
    if not isinstance(out_path,Path):
        raise ValueError(f"{out_path}, must be a valid path object")

    if parent_mkdir:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        response_request = requests.get(url)
        response_request.raise_for_status()


        out_path.write_bytes(response_request.content)
        return True

    except requests.RequestException as e:
        print(f"failed to dwonload {url}:{e}")
        return False

