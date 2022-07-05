"""Web interface to SLURM."""

import datetime
import json
import logging
import pathlib
import sys
import threading
import time
import uuid
import webbrowser
import subprocess

import argh
import flask
import humanize
import paramiko
import scp
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


def slurm_state_pretty(slurm_state):
    """Pretty print the slurm state."""
    if slurm_state == "R":
        return f"<span class='w3-yellow'>{ icon_spin('spinner') }</span> Running"
    elif slurm_state == "PD":
        return f"<span class='w3-yellow'>{ icon_spin('spinner') }</span> Pending"
    elif slurm_state == "U":
        return f"<span class='w3-yellow'>{ icon_spin('cog') }</span> Uploading"
    elif slurm_state == "D":
        return f"<span class='w3-yellow'>{ icon_spin('cog') }</span> Downloading"
    elif slurm_state == "F":
        return f"<span class='w3-green'>{ icon('check-circle') }</span> Finished"
    elif slurm_state == "DLOK":
        return f"<span class='w3-green'>{ icon('check-circle') }</span> Downloaded"
    elif slurm_state == "C":
        return f"<span class='w3-red'>{ icon('exclamation-circle') }</span> Cancelled"
    elif slurm_state == "E-jobfilemissing":
        return f"<span class='w3-red'>{ icon('exclamation-circle') }</span> Error: no job file found"
    elif slurm_state == "E-sbatcherror":
        return f"<span class='w3-red'>{ icon('exclamation-circle') }</span> Error: sbatch error"
    elif slurm_state == "E-uploadfailed":
        return f"<span class='w3-red'>{ icon('exclamation-circle') }</span> Error: upload failed"
    elif slurm_state == "E-downloadfailed":
        return f"<span class='w3-red'>{ icon('exclamation-circle') }</span> Error: download failed"
    else:
        return slurm_state


def slurm_state_to_default_action(slurm_state):
    """Return array containing the default action for the given slurm state."""
    if slurm_state == "R":
        return ["cancel"]
    elif slurm_state == "PD":
        return ["cancel"]
    elif slurm_state == "F":
        # this is a state added by update_runs()
        return ["download"]
    elif slurm_state == "DLOK":
        return ["browse"]
    elif slurm_state == "E-downloadfailed":
        return ["download"]
    elif slurm_state[0:2] == "E-":
        # some error, allow deletion
        return ["remove"]
    elif slurm_state == "C":
        return ["remove"]
    else:
        return ["repeat"]


def slurm_state_to_all_actions(slurm_state):
    """Return array denoting what operations can be done in the given slurm state."""
    if slurm_state == "R":
        return ["cancel", "repeat"]
    elif slurm_state == "PD":
        return ["cancel", "repeat"]
    elif slurm_state == "F":
        # this is a state added by update_runs()
        return ["download", "remove", "repeat"]
    elif slurm_state == "DLOK":
        return ["browse", "download", "remove", "repeat"]
    elif slurm_state == "E-downloadfailed":
        return ["download", "remove", "repeat"]
    elif slurm_state == "E-sbatcherror":
        # sbatch failed, allow downloading for error logs
        return ["remove", "download", "repeat"]
    elif slurm_state[0:2] == "E-":
        # some error, allow deletion
        return ["remove", "repeat"]
    elif slurm_state == "C":
        return ["remove", "repeat"]
    else:
        return ["repeat"]


@app.context_processor
def inject_globals():
    """Make some functions available in the templates."""
    return {
        "time_now": int(time.time()),
        "nice_time": nice_time,
        "icon": icon,
        "slurm_state_pretty": slurm_state_pretty,
        "slurm_state_to_default_action": slurm_state_to_default_action,
        "slurm_state_to_all_actions": slurm_state_to_all_actions,
    }


def state_defaults():
    """Return the default/empty state."""
    return {
        "slurm_hostname": "ui1.scarf.rl.ac.uk",
        "slurm_username": "",
        "slurm_password": "",
        "runs": [],
    }


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


def connect(hostname, username, password):
    """Establish up a new SSH connection."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hostname, username=username, password=password)
    return client


def connect2():
    """Connect with saved credentials and save to global variable 'conn'."""
    global conn
    conn = connect(
        state["slurm_hostname"], state["slurm_username"], state["slurm_password"]
    )


conn = None


def conn_run(cmd):
    """Wrap exec_command so we have some debug information."""
    logging.info(f"running: {cmd}")
    return conn.exec_command(cmd)


@app.route("/")
def index():
    """Index page. Redirect to login."""
    return flask.redirect(flask.url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    global conn
    if flask.request.method == "GET":
        error = flask.request.args.get("error")
        error_msg = None
        if error == "badlogin":
            error_msg = "Authentication failed."
        if error == "badssh":
            error_msg = "Unknown SSH error."
        if error == "badsomething":
            error_msg = "Unknown error."
        return flask.render_template(
            "login.jinja2", state=state, title="Shawl login", error_msg=error_msg
        )

    elif flask.request.method == "POST":
        slurm_hostname = flask.request.form.get("slurm_hostname")
        slurm_username = flask.request.form.get("slurm_username")
        slurm_password = flask.request.form.get("slurm_password")

        state["slurm_hostname"] = slurm_hostname
        state["slurm_username"] = slurm_username
        state["slurm_password"] = slurm_password
        save_app_state()

        try:
            connect2()
        except paramiko.ssh_exception.AuthenticationException:
            logging.exception("authentication error:")
            return flask.redirect(flask.url_for("login", error="badlogin"))
        except paramiko.ssh_exception.SSHException:
            logging.exception("authentication error:")
            return flask.redirect(flask.url_for("login", error="badssh"))
        except Exception:
            logging.exception("authentication error:")
            return flask.redirect(flask.url_for("login", error="badsomething"))

        return flask.redirect(flask.url_for("runs"))


def get_remote_username():
    """Get remote username. This might be different than what we logged in with."""
    stdin, stdout, stderr = conn_run("whoami")
    my_username = stdout.read().decode().strip()
    logging.debug(my_username)
    stdin.close()
    stdout.close()
    stderr.close()
    return my_username


def get_my_remote_runs():
    """Get user's remote runs by running squeue."""
    my_username = get_remote_username()
    stdin, stdout, stderr = conn_run(f"squeue -u {my_username}")
    runs = [line.split() for line in stdout.read().decode().split("\n")]
    stdin.close()
    stdout.close()
    stderr.close()
    ret_runs = {}
    logging.debug(runs)
    for run in runs[1:-1]:  # all lines except first and last
        job_id = run[0]
        status = run[4]
        ret_runs = {job_id: {"status": status}}
    logging.debug(ret_runs)
    return ret_runs


def update_runs():
    """Synchronize local information with remote runs."""

    def skip_remote_update_status(status):
        """Return whether to update the local status with the remote status.

        We don't want to do it if the local status is Error,
        Cancelled, Uploading or Downloading.
        """
        if status[0:2] == "E-" or status in ["C", "U", "D", "DLOK"]:
            return True
        else:
            return False

    local_runs = state["runs"]  # runs we know about
    remote_runs = get_my_remote_runs()  # remote runs, pending and running
    logging.debug(remote_runs)

    for local_run in local_runs:
        remote_run = remote_runs.get(local_run["job_id"])
        if remote_run:
            local_run["status"] = remote_run["status"]
        else:
            # couldn't find it remotely, assume it's finished, unless the status
            # is E-* or C in which case keep the local state
            if not skip_remote_update_status(local_run["status"]):
                local_run["status"] = "F"

    state["runs"] = local_runs


def is_connection_active():
    """Check if paramiko connection is active."""
    if not conn or not conn.get_transport() or not conn.get_transport().is_active():
        return False
    else:
        return True


def maybe_reconnect():
    """Check if we need to reconnect to the slurm host."""
    if not is_connection_active():
        conn.close()
        logging.info("maybe_reconnect(): reconnecting")
        connect2()


@app.route("/runs")
def runs():
    """List SLURM runs and some actions."""
    logging.debug(state)
    if not conn:
        return flask.redirect(flask.url_for("login"))

    maybe_reconnect()
    update_runs()
    return flask.render_template("runs.jinja2", state=state, title="Runs")


@app.route("/run_info/<run_uuid>")
def run_info(run_uuid):
    run = get_run_by_uuid(run_uuid)
    return flask.render_template("run_info.jinja2", run=run)


def run_run(run_name, run_local_dir):
    """Run a job on slurm.

    1. Find the job file name by looking at the local run directory.
    We take the first job file found, but maybe the user should
    be prompted to select it if there are multiple or an error
    given if none are found. The assumption now is that these files
    will be prepared by experts and users will only change the input
    files. Another way to do this would be to have a central repo
    of job files and then the run dir would only contain the input
    files.

    2. Create remote run directory
    We create new uuid4 and then create the directory ~/runs/<uuid>
    on the remote end.

    3. Copy input files to remote run dir
    All the files in the local run directory are copied to the remote
    run directory.

    4. Run sbatch
    Now we run sbatch in the remote run directory, with the job file
    we found in step 1.

    TODO finish this
    """
    run_uuid = str(uuid.uuid4())
    # find the job file name
    job_files = list(pathlib.Path(run_local_dir).glob("*.job"))
    if not job_files:
        state["runs"].append(
            {
                "job_id": "",
                "run_local_dir": run_local_dir,
                "run_name": run_name,
                "run_uuid": run_uuid,
                "job_file": "Not found",
                "added": int(time.time()),
                "status": "E-jobfilemissing",
            }
        )
        save_app_state()
        return
    job_file = job_files[0].name

    # append to app state
    state["runs"].append(
        {
            "job_id": "",
            "run_local_dir": run_local_dir,
            "run_name": run_name,
            "run_uuid": run_uuid,
            "job_file": job_file,
            "added": int(time.time()),
            "status": "U",
        }
    )
    save_app_state()

    # create remote run directory
    try:
        remote_run_dir = f"runs/{run_uuid}"
        maybe_reconnect()
        conn_run(f"mkdir -p {remote_run_dir}")
        time.sleep(1)
        # copy input files to remote run dir
        files = pathlib.Path(run_local_dir).glob("**/*")
        scpconn = scp.SCPClient(conn.get_transport())
        scpconn.put(files, recursive=True, remote_path=remote_run_dir)
    except Exception:
        logging.exception("upload error:")
        update_run_by_uuid(run_uuid, {"status": "E-uploadfailed"})
        save_app_state()
        return
    # run sbatch
    # TODO check return code
    cmd = f"cd {remote_run_dir} ; sbatch {job_file}"
    stdin, stdout, stderr = conn_run(cmd)
    job_id = stdout.read()
    retcode = stdout.channel.recv_exit_status()
    if retcode != 0:
        update_run_by_uuid(run_uuid, {"status": "E-sbatcherror"})
        save_app_state()
        return

    logging.debug(job_id)
    job_id = job_id.decode().split()[-1]
    stdin.close()
    stdout.close()
    stderr.close()
    # append to app state
    update_run_by_uuid(
        run_uuid,
        {
            "job_id": job_id,
            "status": "S",
        },
    )
    save_app_state()


def get_run_by_uuid(run_uuid):
    """Get run dict by run uuid.

    Should there be an index?
    """
    for run in state["runs"]:
        if run["run_uuid"] == run_uuid:
            return run


def update_run_by_uuid(run_uuid, dic):
    """Get run dict by run uuid.

    Should there be an index?
    """
    for run in state["runs"]:
        if run["run_uuid"] == run_uuid:
            run.update(dic)


@app.route("/cancel/<run_uuid>")
def cancel(run_uuid):
    """Cancel a run that is in progress by running scancel on slurm host."""
    maybe_reconnect()
    run = get_run_by_uuid(run_uuid)
    if not run:
        return flask.redirect(flask.url_for("runs"))

    run_job_id = run.get("job_id")
    if not run_job_id:
        return flask.redirect(flask.url_for("runs"))

    conn_run(f"scancel {run_job_id}")

    run["status"] = "C"
    save_app_state()

    return flask.redirect(flask.url_for("runs"))


def download_thread(run_uuid):
    """Download run from remote."""
    run_name = get_run_by_uuid(run_uuid).get("run_name")
    remote_run_dir = f"runs/{run_uuid}"
    try:
        maybe_reconnect()
        scpconn = scp.SCPClient(conn.get_transport())
        local_path = pathlib.Path.home() / "shawl_runs" / run_name
        local_path.mkdir(exist_ok=True, parents=True)
        scpconn.get(
            remote_path=remote_run_dir, recursive=True, local_path=str(local_path)
        )
    except Exception:
        logging.exception("error occured in download:")
        update_run_by_uuid(run_uuid, {"status": "E-downloadfailed"})
        save_app_state()
        return
    update_run_by_uuid(run_uuid, {"status": "DLOK"})
    save_app_state()


@app.route("/download/<run_uuid>")
def download(run_uuid):
    """Download finished run directory by copying the remote run directory."""
    # TODO
    update_run_by_uuid(run_uuid, {"status": "D"})
    threading.Thread(target=download_thread, args=(run_uuid,)).start()
    save_app_state()
    return flask.redirect(flask.url_for("runs"))


@app.route("/documentation")
def documentation():
    """Show documentation."""
    manual_md = markdown2.markdown(
        open("MANUAL.md").read(), extras=["header-ids", "toc"]
    )
    return flask.render_template(
        "docs.jinja2", title="Documentation", manual_md=manual_md
    )


def remove_run(run_uuid):
    """Remove a run by uuid."""
    state["runs"] = [run for run in state["runs"] if run.get("run_uuid") != run_uuid]
    save_app_state()


@app.route("/remove/<run_uuid>")
def remove(run_uuid):
    """Remove job endpoint."""
    remove_run(run_uuid)
    return flask.redirect(flask.url_for("runs"))


@app.route("/new_run", methods=["GET", "POST"])
def new_run():
    """Display new run page and start new run."""
    if not conn:
        return flask.redirect(flask.url_for("login"))

    path_placeholder = pathlib.Path.home() / "my_run_files"
    run_name = flask.request.args.get("run_name")
    run_local_dir = flask.request.args.get("run_local_dir")

    if flask.request.method == "GET":
        return flask.render_template(
            "new_run.jinja2",
            title="New run",
            path_placeholder=path_placeholder,
            run_name=run_name,
            run_local_dir=run_local_dir,
        )
    elif flask.request.method == "POST":
        run_name = flask.request.form.get("run_name")
        run_local_dir = flask.request.form.get("run_local_dir")
        threading.Thread(target=run_run, args=(run_name, run_local_dir)).start()
        return flask.redirect(flask.url_for("runs"))


@app.route("/browse/<run_uuid>")
def browse(run_uuid):
    """Open file browser at downloaded files location."""
    run = get_run_by_uuid(run_uuid)

    run_dir = (
        pathlib.Path.home() / "shawl_runs" / run.get("run_name") / run.get("run_uuid")
    )
    subprocess.Popen(["thunar", run_dir])
    return flask.redirect(flask.url_for("runs"))


@app.route("/signout")
def signout():
    """Sign out by closing the connection."""
    conn.close()
    return flask.redirect(flask.url_for("login"))


@app.route("/backup")
def backup():
    """Backup shawl.json file to slurm host."""
    maybe_reconnect()
    scpconn = scp.SCPClient(conn.get_transport())
    local_conf_path = pathlib.Path().home() / "shawl.json"
    scpconn.put(local_conf_path, remote_path="~/shawl.json")
    return flask.redirect(flask.url_for("runs"))


@app.route("/restore")
def restore():
    """Restore shawl.json file from slurm host."""
    scpconn = scp.SCPClient(conn.get_transport())
    local_conf_path = pathlib.Path().home() / "shawl.json"
    scpconn.get(remote_path="shawl.json", local_path=local_conf_path)
    return flask.redirect(flask.url_for("runs"))


def update_stale_runs():
    """Go through stale runs statuses and change them."""
    for run in state["runs"]:
        if run["status"] == "D":
            run["status"] = "E-downloadfailed"
        elif run["status"] == "U":
            run["status"] = "E-uploadfailed"


def main(port=7321, open_browser=True):
    """Run flask server."""
    update_stale_runs()

    web_url = f"http://127.0.0.1:{port}"

    def open_scarf():
        """Open the web browser to the scarf url after 5 seconds."""
        time.sleep(5)
        webbrowser.open_new(web_url)

    if open_browser:
        threading.Thread(target=open_scarf).start()

    app.run(port=port)


if __name__ == "__main__":
    argh.dispatch_command(main)
