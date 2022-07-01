## Shawl

Shawl is a web application that runs locally (on your PC, or on your virtual machine) and allows you to start and organize SLURM runs.

## How to start a new run

### Prepare data

To use Shawl, your input data and the SLURM job file should be in a single directory

For example:

    /home/dv/stuff/code/Shawl/demo_inputs
    ├── namd.job
    ├── 04.restart.coor
    ├── 04.restart.vel
    ├── 04.restart.xsc
    ├── dppc-p1.conf
    ├── ionized.pdb
    ├── ionized.psf
    ├── par_all36_prot.prm
    ├── par_all27_prot_na.prm
    └── par_all36_lipid.prm

You should only have 1 job file per directory.

### Run Shawl

When this directory is prepared, please start Shawl, which will open to the sign in page.

Enter your SLURM system hostname (login node), and your SLURM system username and password (for SCARF this will be your fed id and password)

Once you have successfully signed in, you will be at the dashboard page. If you
haven't run anything yet, the list of runs will be empty.

To start a new run, click the New run button.

On the new run page, enter a run name (it cannot contain forward slashes "/").

Next, enter the directory path that you prepared above.

Click Submit to start the run.

You will be redirected back to the dashboard, where you can view the status of the run.

Once the run reached the finished state, you can click the download button on the right side of the list. Your files will be downloaded to:

    ~/shawl_runs/<your run name>/<run uuid>

## Run states

This is an explanation of the states available on the dashboard:

- Uploading - shawl is uploading your files to the login node.
- Pending - Your run has been queued on the SLURM system.
- Running - Your run is running on the SLURM system.
- Cancelled - This run has been cancelled, hopefully by you.
- Finished - Your run has succeeded and the files can be downloaded.

## Error states

The following errors can occour:

- Error: no job file found

This means that the input directory does not have a job file. To fix this, add a SLURM job file to the input directory and start a new run.

- Error: sbatch error

This means that an error occured on the SLURM system when submitting the job. You have have a mistake in your job file, or there may be a problem on the SLURM system. Try again and contact support if the problem persists.

- Error: upload failed

This means that shawl could not upload the input directory to the SLURM login node. This may be because of a transient problem with your internet connection or there is a problem on the login node (for example, out of disk space).

- Error: download failed

This means that shawl could not download the results directory from the SLURM login node to your home directory. This may be because of a transient problem with your internet connect or you may have run out of disk space locally.

## Moving runs to a different machine

Shawl keeps the information on runs on your local machine, and thus if you run it on a different machine you won't have the runs available.

If you want to move it, you can copy the file ~/shawl.json.

## Support and feedback

Please email support-email-here if you encounter any problems, or if you have any questions or suggestions.
