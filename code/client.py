import os
import json
import logging
from connection import execute_get
from twisted.internet import task, reactor

HOST = 'https://www.ovh.com'
PATH = '/nic/update'
SYS_PARAM = 'dyndns'


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def get_public_ip():
    logging.debug("get_public_ip")
    return execute_get(os.getenv('API_PUBLIC_IP_URL', "https://api.ipify.org"))


def update_ip_file(new_ip):
    logging.debug("update_ip_file")
    with open(os.getenv('PUBLIC_IP_FILE_PATH', "/tmp/current_ip"), 'w+') as f:
        f.write(new_ip)


def read_ip_file():
    logging.debug("read_ip_file")
    if os.path.isfile(os.getenv('PUBLIC_IP_FILE_PATH', "current_ip")):
        with open(os.getenv('PUBLIC_IP_FILE_PATH', "current_ip"), 'r') as f:
            return str(f.readline())
    logging.debug("read_ip_file - Not file detected")
    return False


def read_domains_configuration():
    logging.debug("read_domains_configuration")
    if os.path.isfile(os.getenv('DOMAINS_CONFIG_FILE_PATH', "domains.json")):
        with open(os.getenv('DOMAINS_CONFIG_FILE_PATH', "domains.json"), 'r') as f:
            return json.load(f)
    logging.error("read_domains_configuration - Any configuration file detected")
    exit(-1)


def update_ip_to_ovh():
    logging.debug("update_ip_to_ovh")
    public_ip = read_ip_file()
    new_public_ip = get_public_ip()
    logging.debug(f'update_ip_to_ovh - New: {new_public_ip} OLD: {public_ip}')

    if public_ip and public_ip == new_public_ip:
        logging.debug(f'The public IP has not changed')
    else:
        logging.info(f'New public IP assigned - New: {new_public_ip} OLD: {public_ip}')
        for domain in read_domains_configuration():
            logging.debug(f'Updating ip for hostname: {domain["hostname"]}')

            url = f'{HOST}{PATH}?system={SYS_PARAM}&hostname={domain["hostname"]}&myip={new_public_ip}'
            auth = {'user': domain['user'], 'pass': domain['pass']}

            response = execute_get(url, auth)

            logging.info(f'Updated ip for hostname: {domain["hostname"]} with reponse: {response}')

        update_ip_file(new_public_ip)


task.LoopingCall(update_ip_to_ovh).start(int(os.getenv('UPDATE_INTERVAL', 300)))
reactor.run()
