import random

import redgifs as rg

from src.pipeline import MyPipeline
from src.retry import retry_with_backoff

_api = None


def _get_api() -> rg.API:
    """Get or create the RedGifs API instance."""
    global _api
    if _api is None:
        _api = rg.API()
        _api.login()
    return _api


def close_api():
    """Close the API connection."""
    global _api
    if _api is not None:
        _api.close()
        _api = None


@retry_with_backoff(max_retries=3, base_delay=2.0)
def _fetch_redgifs(args: dict, pipeline) -> list:
    """Fetch videos from RedGifs API."""
    api = _get_api()

    tag = args["redgifs"]["tags"]
    sort = args["redgifs"]["sort"]

    page = random.randint(1, 3)

    order = getattr(rg.Order, sort.upper(), rg.Order.TRENDING)

    response = api.search(tag, order=order, count=40, page=page)

    if not response.gifs:
        raise ValueError(f"No results found for tag: {tag}")

    return response.gifs


def redgifs(pipeline: MyPipeline = None, args: dict = None) -> dict:
    """Fetch a video from RedGifs and add it to the pipeline."""
    gifs = _fetch_redgifs(args, pipeline)

    api = _get_api()
    selected_gif = None

    for gif in gifs:
        if gif.urls.hd is None:
            continue
        filename = gif.urls.hd.split("/")[-1].split("?")[0]
        if args.get("unique_posts") and pipeline.check_post_history(filename):
            continue
        selected_gif = gif
        break

    if selected_gif is None:
        raise ValueError(f"All {len(gifs)} videos from RedGifs are already in history")

    filename = selected_gif.urls.hd.split("/")[-1].split("?")[0]

    api.download(selected_gif.urls.hd, filename)

    pipeline.add_media("video", filename)
    args.setdefault("_add_to_history", []).append(filename)
    return args


if __name__ == "__main__":
    try:
        test_dict = {
            "type": "video",
            "redgifs": {"tags": "women", "sort": "trending"},
            "unique_posts": False,
        }

        class MockPipeline:
            def __init__(self):
                self._history = set()

            def check_post_history(self, fn):
                return fn in self._history

            def add_media(self, t, p):
                print(f"Added media: {t} - {p}")

        result = redgifs(MockPipeline(), test_dict)
        print(f"Success: {result.get('_add_to_history', [])}")
    finally:
        close_api()
