"""Web interface to SLURM."""

import logging
import threading
import time
import webbrowser
import shlex
import argparse
import pathlib

import flask
import markdown2

import run_utils
import web_utils
import branding

app = flask.Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

brands = branding.load_brands()
my_brand = "default"


@app.context_processor
def inject_globals():
    """Make some functions available in the templates."""
    return {"icon": web_utils.icon}


@app.route("/")
def myapp():
    """App page."""
    brand = brands[my_brand]
    manual_html = markdown2.markdown(
        open(brand.manual_file).read(), extras=["header-ids", "toc"]
    )

    return flask.render_template(
        "app.jinja2",
        manual_html=manual_html,
        brand=brand,
    )


@app.route("/api/watch_queue", methods=["POST"])
def term_watch_queue():
    """Watch queue api endpoint."""
    hostname = flask.request.form.get("hostname")
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    ssh_cmd = "watch squeue -u $(whoami)"
    run_utils.run_term_ssh_cmd(hostname, username, password, ssh_cmd)
    return "OK"


@app.route("/api/remote_shell", methods=["POST"])
def term_remote_shell():
    """Remote shell api endpoint."""
    hostname = flask.request.form.get("hostname")
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    remote_path = flask.request.form.get("remote_path")
    run_utils.run_term_ssh(hostname, username, password, remote_path)
    return "OK"


@app.route("/api/run", methods=["POST"])
def term_run():
    """Terminal run api endpoint."""
    hostname = flask.request.form.get("hostname")
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    local_path = flask.request.form.get("local_path").strip().rstrip("/")
    remote_path = flask.request.form.get("remote_path").strip().rstrip("/")
    # Present a fzf prompt if there are > 1 job files
    # nd pipe the output (the job file the user selected) into a file named "selected"
    cmd = f"find {shlex.quote(local_path)} -name '*.job' -print0 | ./fzf --read0 --print0 -1 --margin 1,1 --padding 1,1 --header='Select job file to run' --cycle --layout reverse --preview 'less {{}}' > selected"
    logging.debug(f"cmd: {cmd}")
    run_utils.run_term_cmd(cmd)
    # Read the file "selected" to get the job file that the user selected
    # We only want the file name, not the path, and remove the newline at the end
    # read_text() seems to already strip null bytes, but is that expected?
    cont = pathlib.Path("selected").read_bytes().replace(b"\0", b"").decode()
    sel_job_file = pathlib.Path(cont).name
    logging.debug(f"sel_job_file: {sel_job_file}")
    if not sel_job_file:
        logging.warning("No job file selected. Not running any job")
        return "NO_JOB_FILE_SELECTED"
    ssh_cmd = f"cd {shlex.quote(remote_path)} ; sbatch {shlex.quote(sel_job_file)}"
    logging.debug(f"ssh_cmd: {ssh_cmd}")
    run_utils.run_term_ssh_cmd(hostname, username, password, ssh_cmd)
    return "OK"


@app.route("/api/rsync_up", methods=["POST"])
def term_rsync_up():
    """Rsync from local to remote api endpoint."""
    hostname = flask.request.form.get("hostname")
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    local_path = flask.request.form.get("local_path").strip().rstrip("/")
    remote_path = flask.request.form.get("remote_path").strip().rstrip("/")
    run_utils.run_term_rsync_up(hostname, username, password, local_path, remote_path)
    return "OK"


@app.route("/api/rsync_down", methods=["POST"])
def term_rsync_down():
    """Rsync from remote to local api endpoint."""
    hostname = flask.request.form.get("hostname")
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    local_path = flask.request.form.get("local_path").strip().rstrip("/")
    remote_path = flask.request.form.get("remote_path").strip().rstrip("/")
    run_utils.run_term_rsync_down(hostname, username, password, local_path, remote_path)
    return "OK"


@app.route("/api/filebrowser", methods=["POST"])
def filebrowser():
    """Launch filebrowser api endpoint."""
    local_path = flask.request.form.get("local_path")
    run_utils.run_filebrowser(local_path)
    return "OK"


def main():
    """Run flask server."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--no-debug", dest="debug", action="store_false")
    parser.set_defaults(debug=False)
    parser.add_argument("--host", nargs="?", default="127.0.0.1")
    parser.add_argument("--port", nargs="?", default=7322)
    parser.add_argument("--brand", nargs="?", default="default")
    args = parser.parse_args()
    print(args)

    global my_brand
    my_brand = args.brand

    def open_shawl():
        """Open the web browser to the shawl url after 3 seconds."""
        time.sleep(3)
        web_url = f"http://{args.host}:{args.port}"
        webbrowser.open_new(web_url)

    if not args.debug:
        threading.Thread(target=open_shawl).start()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
