import os
import time
from pathlib import Path
from typing import Union, Optional, Callable

from tqdm import tqdm

import requests


def streaming_download(
        url: str,
        filename: Union[Path, str],
        force: bool = False,
        chunk_size: int = 2^18,
        callback: Optional[Callable] = None,
        callback_interval: int = 5,
        verbose: bool = False,
):
    filename = Path(filename)
    do_download = False
    web_available = False
    if not filename.exists():
        do_download = True
        local_size = None
    else:
        local_size = filename.stat().st_size

    try:
        response = requests.get(url, stream=True, timeout=5)
        web_available = True
    except requests.ConnectionError:
        pass

    remote_size = None
    if web_available:
        try:
            remote_size = int(response.headers["Content-Length"])
        except (KeyError, ValueError):
            pass

    if remote_size is not None and local_size is not None and (remote_size != local_size):
        do_download = True

    if do_download or force:
        if not web_available:
            raise ConnectionError(f"Url can't be reached: '{url}'")

        os.makedirs(filename.parent, exist_ok=True)

        num_downloaded = 0
        last_progress_time = time.time() - callback_interval
        with open(filename, "wb") as fp:

            with tqdm(
                    total=remote_size,
                    unit_scale=True,
                    unit_divisor=1024,
                    disable=not verbose,
            ) as loop:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    fp.write(chunk)
                    chunk_length = len(chunk)
                    num_downloaded += chunk_length
                    loop.update(chunk_length)

                    if callback:
                        cur_time = time.time()
                        if cur_time - last_progress_time >= callback_interval:
                            last_progress_time = cur_time
                            callback({"size": remote_size, "downloaded": num_downloaded})
