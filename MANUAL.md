#### Premise

Shawl is a web application that runs locally (on your PC, or on your virtual machine) and provides a simple interface to SLURM.

#### How to start a new run

##### Step 1: Prepare data

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

You can have more than 1 job file per directory. The job files should have a ".job" file extension.

##### Step 2: Fill in the settings

On the right side of the screen, please fill in your SLURM system credentials and the local run path (the directory you prepared above), and the remote run path (the path on the SLURM system where the files will be copied to).

##### Step 3: Upload data

You can now click the "Sync local to remote" button on the right side of the screen. This will open a terminal, which will copy the your local run path to the remote run path. Once it is finished you can close the terminal window.

##### Step 4: Start the job

Once the upload is finished, you can click the "Submit job" button to submit your job to the SLURM system.

If your input directory contains more than one job file, the terminal will ask you to select one. Press enter to select a job file to run or close the window to not run any. You can only select and run one file at a time.

Once the job is submitted, you can close the terminal window.

##### Step 5: Watch queue

You can optionally watch the queue by clicking the "Watch queue" button. This will open a terminal window which shows the status of the job.

##### Step 6: Download results

Once the run is finished, you can download the results by clicking "Sync remote to local". This will download the the remote run path to the local run path specified in the settings on the left.

##### Step 7: Open in file browser

You can optionally browse your files by clicking the "Open file browser" button. This opens a graphical file browser in the local run directory.

#### Other stuff you can do

##### See job logs as it is running

When a job is running, you can watch the output by clicking **Open remote shell** and then running a command such as `tail`:

    tail -f youroutputfile.log

SLURM won't log the program output to a file by default. You will have to configure that in the job file, for example:

    #SBATCH -o dppc.log
    #SBATCH -e dppc.err

##### Cancel a running job

You can cancel a job by clicking **Open remote shell**, and running:

    scancel <jobid>

You can get the job ID from the watch squeue window.

##### Open a terminal in the local run directory

To open a terminal in the local run directory, click **Open file browser**, then right click in the application between the files (i.e. the space between the file icons), then select **Open Terminal Here**

#### Support and feedback

Please email support-email-here if you encounter any problems, or if you have any questions or suggestions.
