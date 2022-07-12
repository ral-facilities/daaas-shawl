# Shawl5

Shawl5 is an interface to SLURM systems that runs as a local web application.

<img src="https://i.imgur.com/pCRFbYv.png"/>

## Installation (ubuntu 22.04)

    sudo apt install python3 python3-pip
    git clone git@github.com:dvolk/shawl5.git
    cd shawl5
    python3 -m venv env
    source env/bin/activate
    pip3 install -r requirements.txt

## Running

    python3 shawl5.py

This will open a web browser window to http://127.0.0.1:7322

## Manual

see [MANUAL.md](MANUAL.md) for more information on shawl.
