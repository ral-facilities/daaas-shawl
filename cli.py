import subprocess
import shlex
import logging
import time
import json
import pathlib
import sys

import argh

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# generic ssh utils


def run_ssh_cmd_with_output(hostname, username, password, ssh_cmd):
    logging.debug(f"running on {hostname}: {ssh_cmd}")
    term_cmd = f"sshpass -p {shlex.quote(password)} ssh -q -t -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {shlex.quote(username)}@{shlex.quote(hostname)} {shlex.quote(ssh_cmd)}"
    return subprocess.check_output(shlex.split(term_cmd))


def run_rsync_up(hostname, username, password, local_path, remote_path):
    logging.debug(f"uploading to {hostname}: {local_path} to {remote_path}")
    """Run command remotely, opening a local terminal."""
    term_cmd = f"sshpass -p {shlex.quote(password)} rsync -e 'ssh -q -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' --stats --progress {shlex.quote(local_path)}/ -axv {shlex.quote(username)}@{shlex.quote(hostname)}:{shlex.quote(remote_path)}"
    subprocess.check_output(shlex.split(term_cmd))


def run_rsync_down(hostname, username, password, local_path, remote_path):
    logging.debug(f"downloading from {hostname}: {remote_path} to {local_path}")
    """Run command remotely, opening a local terminal."""
    term_cmd = f"sshpass -p {shlex.quote(password)} rsync -e 'ssh -q -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' -axv --stats --progress {shlex.quote(username)}@{shlex.quote(hostname)}:{shlex.quote(remote_path)}/ {shlex.quote(local_path)}"
    subprocess.check_output(shlex.split(term_cmd))


# slurm model


def slurm_upload(hostname, username, password, local_path, remote_path):
    local_path = local_path.strip().rstrip("/")
    remote_path = remote_path.strip().rstrip("/")
    run_rsync_up(hostname, username, password, local_path, remote_path)


def slurm_run(hostname, username, password, remote_path):
    ssh_cmd = f"cd {shlex.quote(remote_path)} ; sbatch $(find . -name '*.job')"
    return (
        run_ssh_cmd_with_output(hostname, username, password, ssh_cmd)
        .decode()
        .strip()
        .split(" ")[3]
    )


def slurm_download(hostname, username, password, local_path, remote_path):
    local_path = local_path.strip().rstrip("/")
    remote_path = remote_path.strip().rstrip("/")
    run_rsync_down(hostname, username, password, local_path, remote_path)


def slurm_wait_for_job(
    hostname, username, password, job_id, sleep_time=60, failure_retries=1440
):
    while True:
        ssh_cmd = f"squeue -u $(whoami) | {{ grep {job_id} || true; }}"
        try:
            out = run_ssh_cmd_with_output(
                hostname, username, password, ssh_cmd
            ).decode()
            logging.debug(f'squeue grep: "{out.strip()}"')
            if not out:
                break
            failure_retries = 1440
        except Exception as e:
            logging.error(f"fail: {e}")
            if failure_retries <= 0:
                break
            else:
                failure_retries = failure_retries - 1
        logging.debug(f"sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)


# slurm view

config_path = pathlib.Path.home() / "shawl-cli.json"


def fill_array(arr, size, elem):
    while len(arr) < size:
        arr.append(elem)


def configure():
    cmd = (
        'zenity --forms --title="Configure Shawl CLI"'
        ' --text="Please enter the details of the SLURM cluster you will be using"'
        ' --text="You can leave some of this empty and then specify it dynamically"'
        ' --separator="\n"'
        ' --add-entry="SLURM Hostname"'
        ' --add-entry="SLURM Username"'
        ' --add-entry="Password"'
        ' --add-entry="Local path"'
        ' --add-entry="Remote path"'
    )
    vals = subprocess.check_output(shlex.split(cmd)).decode().split()
    fill_array(vals, 5, "")
    hostname, username, password, local_path, remote_path = vals
    with open(pathlib.Path.home() / "shawl-cli.json", "w") as f:
        json.dump(
            {
                "hostname": hostname,
                "username": username,
                "password": password,
                "local_path": local_path,
                "remote_path": remote_path,
            },
            f,
        )


def run(hostname="", username="", password="", local_path="", remote_path=""):
    config = dict()
    try:
        with open(config_path) as f:
            config = json.load(f)
    except:
        logging.warning(f"couldn't open {config_path}")
    if not hostname:
        hostname = config.get("hostname")
    if not username:
        username = config.get("username")
    if not password:
        password = config.get("password")
    if not local_path:
        local_path = config.get("local_path")
    if not remote_path:
        remote_path = config.get("remote_path")
    if not (hostname and username and password and local_path and remote_path):
        logging.error(
            f"Please specifiy the hostname, username, password, local_path and remote_path either as a command-line argument or in the config file ({config_path})"
        )
        sys.exit(1)
    run_bare(hostname, username, password, local_path, remote_path)


def run_bare(hostname, username, password, local_path, remote_path):
    logging.info("uploading files")
    slurm_upload(hostname, username, password, local_path, remote_path)

    logging.info("running job")
    job_id = slurm_run(hostname, username, password, remote_path)
    logging.info(f"job id is {job_id}")

    logging.info("waiting for job to finish")
    slurm_wait_for_job(hostname, username, password, job_id)

    logging.info("downloading files")
    slurm_download(hostname, username, password, local_path, remote_path)


if __name__ == "__main__":
    argh.dispatch_commands([configure, run, run_bare])
