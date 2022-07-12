"""Utility commands for running stuff in a terminal."""

import subprocess
import shlex
import logging

logging.basicConfig(level=logging.DEBUG)

term = "xterm"


def run_term_ssh_cmd(hostname, username, password, ssh_cmd):
    """Run command remotely, opening a local terminal."""
    term_cmd = f"sshpass -p {shlex.quote(password)} ssh -t -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {shlex.quote(username)}@{shlex.quote(hostname)} {shlex.quote(ssh_cmd)} ; read -n 1 -p 'Command finished. Press any key to continue.'"
    logging.info(term_cmd)
    subprocess.Popen([term, "-e", term_cmd])


def run_term_ssh(hostname, username, password, remote_path):
    """Run command remotely, opening a local terminal."""
    cmd = f"cd {shlex.quote(remote_path)}; bash --login"
    term_cmd = f"sshpass -p {shlex.quote(password)} ssh -t -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {shlex.quote(username)}@{shlex.quote(hostname)} {shlex.quote(cmd)}"
    logging.info(term_cmd)
    subprocess.Popen([term, "-e", term_cmd])


def run_term_rsync_up(hostname, username, password, local_path, remote_path):
    """Run command remotely, opening a local terminal."""
    term_cmd = f"sshpass -p {shlex.quote(password)} rsync -e 'ssh -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' {shlex.quote(local_path)}/ -aXxv {shlex.quote(username)}@{shlex.quote(hostname)}:{shlex.quote(remote_path)} ; read -n 1 -p 'Command finished. Press any key to continue.'"
    logging.info(term_cmd)
    subprocess.Popen([term, "-e", term_cmd])


def run_term_rsync_down(hostname, username, password, local_path, remote_path):
    """Run command remotely, opening a local terminal."""
    term_cmd = f"sshpass -p {shlex.quote(password)} rsync -e 'ssh -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' -aXxv {shlex.quote(username)}@{shlex.quote(hostname)}:{shlex.quote(remote_path)}/ {shlex.quote(local_path)} ; read -n 1 -p 'Command finished. Press any key to continue.'"
    logging.info(term_cmd)
    subprocess.Popen([term, "-e", term_cmd])


def run_filebrowser(local_path):
    """Run command remotely, opening a local terminal."""
    subprocess.Popen(["thunar", local_path])
