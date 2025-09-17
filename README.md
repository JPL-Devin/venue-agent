# Ingenium Venue Server (Refactored by Using FastAPI)

## For developers

For development, you need to run VenueServer web application.
It is assumed that REDIS service is already running.

### Set Up Python Virtual Environment

Run the following script to set up a Python virtual environment as `venv3`. 

The script will also generate an NGINX configuration file (`nginx.conf`) from a template (`nginx.conf.template`). 
You do not need to run nginx for local development.

The set up script takes a file (e.g., `config/europa_dev_envs.sh`) that contains a few environment variables. You will need to update
the environment variables according to your environment.

On a Europa WSTS:
```
$ ./setup_venueserver.sh -f config/europa_dev_envs.sh
```

On a Psyche WSTS:
```
$ ./setup_venueserver.sh -f config/psyche_dev_envs.sh
```

### REDIS

The assumption is that REDIS is running. If not, consult project GDS team to set up REDIS.
To check if REDIS is running:

```
$ ps -ealf | grep redis-server
```

### Start VenueServer

The start up shell script takes the port number and environment variable files as inputs. 
In the example below, VenueServer listens to port 19443.  NGINX will map port 9443 to this port.

You can run multiple instances of VenueServer with different ports such as 19444 (2nd instance) and 19445 (3rd instance).

```
$ ./start_venueserver.sh -p 19443 -f config/europa_dev_envs.sh
```

VenueServer will be accessible from `http://localhost:19443/api/v3/health`

### NGINX (optional)

NGINX is optional for development.
#### Start/Stop NGINX 
`setup_venueserver.sh` script generates nginx configuration file for the GDS host.
The nginx configuration file is set up to serve up to 3 instances of VenueServer on ports 19443, 19444, and 19445.
A single instance of NGINX serves mutliple instances of Venue Server.

#### Start NGINX

```
$ ./start_nginx.sh start
```

VenueServer will be accessible from `https://<hostname>.jpl.nasa.gov:9443/api/v3/health`

#### Stop NGINX
```
$ ./start_nginx.sh stop
```

#### Reload NGINX Configuration
```
$ ./start_nginx.sh reload
```


## Deployment Guide

This is a guide for GDS team who need to set up deployment scripts (example: Puppet scripts) of VenueServer.

### Step 1: Download this repository

Checkout `r14_2_0` tag of the repo.

For Europa:

```
/opt/local/ingenium/venueserver/R14.2.0
```


For Psyche:

```
/opt/ingenium/<hostname>/r14_2_0
```

### Step 2: Clone Ingenium MTAK GitHub repository

The repository is here: https://github.jpl.nasa.gov/Ingenium/mtak

Europa clones `8.x/python` directory into this directory

```
/opt/local/ingenium/venueserver/R14.2.0
```


Psyche clones the full repository into this directory

```
/opt/ingenium/mtak/r14_2_0
```

### Step 3: Define Environment Variables

A number of environment variables are used for set up and starting VenueServer. Note that the values of 
some of the environment variables will vary depending on GDS hosts.

The list of environment variables can be found in:

- Europa: `config/europa_dev_envs.sh`
- Psyche: `config/psyche_dev_envs.sh`

GDS team will need to create a deployment script that will create a file that defines the environment variables.
The below guide assumes that `venueserver_envs.sh` is created in the directory of the VenueServer source code.

- Europa: `/opt/local/ingenium/venueserver/R14.2.0/venueserver_envs.sh`
- Psyche: `/opt/ingenium/<hostname>/r14_2_0/venueserver_envs.sh`


Below is a summary of the environment variables and example values.

Note that `ING_LOG_DIR` needs to be parameterized by using `$USER` so that each VenueServer instance can have its own log file.

| Env variable            | Description                       | Europa Example                             | Psyche Example                                             |
|-------------------------|-----------------------------------|--------------------------------------------|------------------------------------------------------------|
| ING_VENUE_DIR           | directory of VenueServer code     | `/opt/local/ingenium/venueserver/R14.2.0`  | `/opt/ingenium/<hostname>/r14_2_0`                         |
| ING_MTAK_DIR            | directory of Ingenium MTAK        | `/opt/local/ingenium/python/R14.2.0`       | `/opt/ingenium/mtak/r14_2_0/r8.x/python`                   |
| ING_LOG_DIR             | directory of VenueServer log file | `/home/$USER/ingenium/eurcits207/logs`     | `/opt/ingenium/users/$USER/ingenium/psychedevit3/logs`     |
| CUSTOM_SCRIPT_BASE_DIR  | root directory of custom scripts  | `/proj/europa/sit`                         | `/teamtools/ingenium`                                      |
| LAD_HOST                | GLAD host                         | `somehost.jpl.nasa.gov`                    | `somehost.jpl.nasa.gov`                                |
| LAD_PORT                | GLAD port                         | 8887                                       | 8887                                                       |
| LAD_HTTPS               | true if GLAD uses HTTPS           | false                                      | true                                                       |
| BUS_1553_LOGFILE_PATH   | directory of 1553 Bus logs        | Not used by Europa                         | `/var/ammos/archive/$YYYY/$DOY/sse/$GDS_HOSTNAME/session_*/$USER/wsts-gds.results/psyche_*`    |
| LOGFILE_1553_DICTIONARY_FILE_PATH | Path to the 1553 dictionary file     | Not used by Europa  | `/gds/psyche/dictionary/psyche1553/current`    |
| IRIG_SOURCE | true if IRIG is used     | false  | false    |
| CHILL_GDS | directory of AMPCS     | `/ammos/ampcs/mpcs/eurc/current`  | `/ammos/ampcs/mpcs/psyche/current`    |
| PATH | Updated path     | `$CHILL_GDS/bin:$CHILL_GDS/bin/tools:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin`  | `$CHILL_GDS/bin:$CHILL_GDS/bin/tools:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin`    |
| GDS_JAVA_OPTS | AMPCS options     | `-DGdsUserConfigDir=$ING_VENUE_DIR/config/gds_config`  | `-DGdsUserConfigDir=$ING_VENUE_DIR/config/gds_config`    |

### Step 4: Create a Python Virtual Environment and Generate a NGINX configuration file

Run the set up script with the environment variables from Step 3. 

$ ./setup_venueserver.sh -f venueserver_envs.sh

- A Python virtual environment will be created as `venv3`
- nginx configuration will be created as `nginx.conf`

### Step 5: Create NGINX Service

Create an NGINX systemctl service. A single instance of NGINX will serve multiple instances of VenueServer.

NGINX service will run as the primary Ingenium user (`eurc-ing` or `psycheing`) by running the command below.

| systemctl definition      |  Instruction                |
|---------------------------|-----------------------------|
| User account              | `eurc-ing` or `psycheing`   |
| Start command             | ./start_nginx.sh start      |
| Stop command              | ./start_nginx.sh stop       |


### Step 6: Create Redis Service

Create an REDIS systemctl service. It is recommended using REDIS installed at the system level. 
REDIS version 5 or later should work.
A single instance of REDIS will serve multiple instances of VenueServer.

| systemctl definition      |  Instruction                                   |
|---------------------------|------------------------------------------------|
| User account              | Use the default defined by the REDIS distribution  |
| Start command             | Use the default defined by the REDIS distribution  |
| Stop command              | Use the default defined by the REDIS distribution  |


### Step 7: Create VenueServer Services

Create a VenueServer systemctl service. 

If multiple instances of VenueServer are running for a Venue, set up multiple systemctl services that run as different Ingenium application accounts. Each instance will use a different port (19443, 19444 or 19445).

#### The first instance of Venue Server

| systemctl definition      |  Instruction                                               |
|---------------------------|------------------------------------------------------------|
| User account              | `eurc-ing` or `psycheing`                                  |
| Start command             | ./start_venueserver.sh -f venueserver_envs.sh -p 19443     |
| Stop command              | SEND SIGINT                                                |
| health check              | https://fullhostname:9443/api/v3/health                        |

#### The second instance of Venue Server

| systemctl definition      |  Instruction                                               |
|---------------------------|------------------------------------------------------------|
| User account              | `eurc-ing2` or `psycheing2`                                  |
| Start command             | ./start_venueserver.sh -f venueserver_envs.sh -p 19444     |
| Stop command              | SEND SIGINT                                                |
| health check              | https://fullhostname:9444/api/v3/health                        |

### Step 8: Start services

- Start NGINX service
- Start REDIS service
- Start VenueServer service #1
- Start VenueServer service #2 (when applicable)
- Start VenueServer service #3 (when applicable)


### Step 9 (Optional): Set up Log Rotation of NGINX

NGINX does not have a native way to rotate logs.

This needs to be done through `logrotate` that can be set by GDS teams.

See this [article](https://www.digitalocean.com/community/tutorials/how-to-configure-logging-and-log-rotation-in-nginx-on-an-ubuntu-vps#log-rotation-with-logrotate)
 

