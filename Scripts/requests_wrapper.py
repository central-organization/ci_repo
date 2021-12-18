import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def requests_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """Wrapper for requests, used for safe http/https requests.

    Args:
        retries (int, optional): [description]. Defaults to 3.
        backoff_factor (float, optional): [description]. Defaults to 0.3.
        status_forcelist (tuple, optional): [description]. Defaults to (500, 502, 504).
        session ([type], optional): [description]. Defaults to None.

    Returns:
        session: requests.Session() object
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session