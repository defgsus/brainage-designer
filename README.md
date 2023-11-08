# BrainAGE Designer

## Installation

Install a recent version of [Docker Engine](https://docs.docker.com/engine/install/) 
or the **Docker Desktop** if you can't help it.

#### Ubuntu 18.04
```shell
mkdir tmp
cd tmp
wget https://download.docker.com/linux/ubuntu/dists/bionic/pool/stable/amd64/containerd.io_1.6.9-1_amd64.deb
wget https://download.docker.com/linux/ubuntu/dists/bionic/pool/stable/amd64/docker-ce-cli_20.10.9~3-0~ubuntu-bionic_amd64.deb
wget https://download.docker.com/linux/ubuntu/dists/bionic/pool/stable/amd64/docker-ce_20.10.9~3-0~ubuntu-bionic_amd64.deb
wget https://download.docker.com/linux/ubuntu/dists/bionic/pool/stable/amd64/docker-compose-plugin_2.6.0~ubuntu-bionic_amd64.deb

sudo dpkg -i *.deb

cd ..
rm -r tmp/
```

### run with docker compose

Copy the file [docker-compose-EXAMPLE.yml](docker-compose-EXAMPLE.yml) to `docker-compose.yml` and
replace the `<PATH-TO-...>` entries:

    <PATH-TO-DATA>:   the top-most directory where all data read and written to
    <PATH-TO-MATLAB>: the directory of the matlab (v93 / R2017) runtime
    <PATH-TO-CAT12>:  the directory of the CAT12 standalone version

```shell
docker compose build
docker compose up
```
and visit [http://localhost](http://localhost).


### run single docker images

```shell
# ./build-frontend.sh

docker build --tag brainage-designer .
docker run -ti -p 80:9009 brainage-designer
```


## development

### prepare environments

```shell
# for python the typical
virtualenv -p python3 env
source env/bin/activate
pip install -r requirements.txt

# for frontend
cd frontend
yarn
```


### run server on localhost

In project root: 
```shell
# transpile with yarn & parcel
./build-frontend.sh
# start the python server
./start-server.sh
```
and visit [http://localhost:9009](http://localhost:9009).

### run server on localhost with hot-reloading

In project root:
```shell
# start the python server
./start-server.sh
```

In another shell in `frontend` directory:
```shell
yarn start
```
and visit [http://localhost:1234](http://localhost:1234).
