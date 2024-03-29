# DynDNS updater for OVH

Dockerized client that allows maintain an OVH domain pointing to a dynamic IP.

## DockerHub image

The DynDNS image is published in DockerHub: https://hub.docker.com/repository/docker/cibrandocampo/ovh-dyndns-client

## Configuring OVH

- Step 1: Configure a DynDNS in the OVH administration panel.

- Step 2: Create a user that allows you to manage it (username and password).

Official OVH documentation: https://docs.ovh.com/gb/en/domains/hosting_dynhost/

## Build image

`docker build -t ovh-dyndns-client:stable -f Dockerfile .`


## Enviroment variables

List of custom enviroment variables

| Variable | Default value |
| ------ | ------ |
| API_PUBLIC_IP_URL | https://api.ipify.org |
| PUBLIC_IP_FILE_PATH | /tmp/current_ip |
| DOMAINS_CONFIG_FILE_PATH | /dyndns-client/config/domains.json |
| UPDATE_INTERVAL | 300 |


## Execution
Before running the container, we must create a JSON file with the domain configuration.

```json
[
    {
        "hostname": "example.es",
        "user": "example-user",
        "pass": "example-password"
    },
    {
        "hostname": "example2.es",
        "user": "example2-user",
        "pass": "example2-password"
    }
]
```
NOTE: There is an example file in /config

Next, the docker can be executed by providing the previously created file.

```sh
docker run -v path/to/domains.json:/dyndns-client/config/domains.json cibrandocampo/ovh-dyndns-client:stable
```

## Help

Send me an email (hello@cibran.es) if you need extra help.

## License

GNU GENERAL PUBLIC LICENSE