import logging
from requests import get
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException


def execute_get(url, auth=False):
    logging.debug("execute_get")
    try:

        if not auth:
            return get(url).content.decode('utf8')

        return get(url, auth=HTTPBasicAuth(auth['user'], auth['pass'])).content.decode('utf8')

    except HTTPError as errh:
        logging.error("execute_get - HTTP error: " + str(errh))
        exit(-1)
    except ConnectionError as errc:
        logging.error("execute_get - Connection error: " + str(errc))
        exit(-1)
    except Timeout as errt:
        logging.error("execute_get - Timeout error: " + str(errt))
        exit(-1)
    except RequestException as err:
        logging.error("execute_get - Unknown error: " + str(err))
        exit(-1)
