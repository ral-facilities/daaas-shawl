"""Web interface to SLURM."""

import datetime
import json
import logging
import pathlib
import sys
import threading
import time
import webbrowser
import subprocess
import shlex
import os

import argh
import flask
import humanize
import markdown2

app = flask.Flask(__name__)

logging.basicConfig(level=logging.DEBUG)


@app.errorhandler(500)
def page500(error):
    """Error page for code 500."""
    return flask.render_template("500.jinja2")


@app.route("/errortest")
def errortest():
    """Endpoint to view the error page."""
    return flask.render_template("500.jinja2")


def icon(name):
    """Return string for template fontawesome icons.

    example: icon('trash')
    """
    return f'<i class="fa fa-{name} fa-fw"></i>'


def icon_spin(name):
    """Return string for template fontawesome icons and spin it.

    example: icon_spin('cog')
    """
    return f'<i class="fa fa-{name} fa-spin fa-fw"></i>'


def nice_duration(t):
    """Return a nicer representation of how long something took."""
    return humanize.naturaldelta(datetime.timedelta(seconds=t)).capitalize()


def nice_time(time_now, t2):
    """Return a nicer representation of how long ago something occured."""
    return humanize.naturaltime(
        datetime.timedelta(seconds=(time_now - t2))
    ).capitalize()


@app.context_processor
def inject_globals():
    """Make some functions available in the templates."""
    return {
        "time_now": int(time.time()),
        "nice_time": nice_time,
        "icon": icon,
    }


def state_defaults():
    """Return the default/empty state."""
    return {
        "slurm_hostname": "ui1.scarf.rl.ac.uk",
        "slurm_username": "",
        "slurm_password": "",
    }


def run_cmd(hostname, username, password, ssh_cmd):
    """Run command remotely, opening a local terminal."""
    ssh_cmd = "watch squeue -u $(whoami)"
    term = "xfce4-terminal"
    term_cmd = f"sshpass -p {shlex.quote(password)} ssh -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {shlex.quote(username)}@{shlex.quote(hostname)} {shlex.quote('TERM=xterm-256color ' + ssh_cmd)} && read -n 1 -p 'Command finished. Press any key to continue.'"
    print(term_cmd)
    subprocess.Popen([term, "-e", term_cmd])


def run_rsync_send(hostname, username, password, local_path, remote_path):
    """Run command remotely, opening a local terminal."""
    term_cmd = f"sshpass -p {shlex.quote(password)} rsync -e 'ssh -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' {shlex.quote(local_path)} -aXxv {shlex.quote(username)}@{shlex.quote(hostname)}:{shlex.quote(remote_path)} && read -n 1 -p 'Command finished. Press any key to continue.'"
    print(cmd)
    subprocess.Popen(["xterm", "-e", term_cmd])


def load_app_state():
    """Load application config/state."""
    global state
    if not state_file.is_file():
        return
    try:
        with open(state_file) as f:
            state = json.loads(f.read())
    except Exception:
        logging.exception(
            f"An error occured while reading {state_file}. Please contact your system administrator."
        )
        sys.exit(1)


def save_app_state():
    """Save application config/state."""
    global state
    try:
        with open(state_file, "w") as f:
            f.write(json.dumps(state, indent=4))
    except Exception:
        logging.exception(
            f"An error occured while writing {state_file}. Please contact your system administrator."
        )
        sys.exit(1)


state_file = pathlib.Path.home() / "shawl.json"

state = state_defaults()

load_app_state()


@app.route("/")
def index():
    """Index page. Redirect to login."""
    return flask.render_template("page.jinja2")


@app.route("/documentation")
def documentation():
    """Show documentation."""
    manual_md = markdown2.markdown(
        open("MANUAL.md").read(), extras=["header-ids", "toc"]
    )
    return flask.render_template(
        "docs.jinja2", title="Documentation", manual_md=manual_md
    )


def main(port=7322, open_browser=True):
    """Run flask server."""

    web_url = f"http://127.0.0.1:{port}"

    def is_shawl_running():
        """Check if app is running or if we need to start it.

        Making some assumptions where about where it's installed to narrow down
        the grep. An alternative would be to rename main.py to something more
        unique.
        """
        try:
            procs = (
                subprocess.check_output(
                    "ps axwf | grep /opt/shawl5/main.py | grep -v grep", shell=True
                )
                .decode()
                .strip()
                .split("\n")
            )
            if len(procs) == 1:
                # no other shawl process is running
                return False
            else:
                return True
        except subprocess.CalledProcessError:
            logging.exception("is_shawl_running error:")
            return False

    def open_shawl():
        """Open the web browser to the scarf url after 3 seconds."""
        time.sleep(3)
        webbrowser.open_new(web_url)

    if open_browser:
        threading.Thread(target=open_shawl).start()

    if not is_shawl_running():
        logging.info("starting web server.")
        app.run(port=port)
    else:
        logging.info("shawl is already running.")


if __name__ == "__main__":
    argh.dispatch_command(main)
