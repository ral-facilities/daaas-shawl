namdCmd       ='singularity exec /home/mw1075744/maksims/alcnr/singularity/md.sif mpirun --host localhost:28 -np 16 namd2'

projectDir = '/home/mw1075744/namd_prod_demo'
// fromFilePairs returns key, pair
moleculeFiles = Channel.fromFilePairs("ionized.{psf,pdb}", flat:true)
// fromPath returns list from glob
restartFiles  = Channel.fromPath("$projectDir/04.restart.*").buffer(size:3)
confFiles     = Channel.fromPath("$projectDir/*.conf")
prmFiles      = Channel.fromPath("$projectDir/reference_data/*.prm").buffer(size:3)

process namd_production {
    publishDir 'results', mode: 'copy'

    input:
        set id, file(psf), file(pdb) from moleculeFiles
        file '*' from restartFiles
	file('dppc-p1.conf') from confFiles
	file '*' from prmFiles

    output:
        set id, file('prod01.dcd'), file('prod01.restart.coor'), file('prod01.restart.vel'), file('prod01.restart.xsc')  into outputTraj

    """
    echo "Running NAMD ..."
    ${namdCmd} dppc-p1.conf
    """
}
