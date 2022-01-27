# ddlTerm
ddlTerm is a data-driven loop termination analysis tool

## Install 
### Docker
1. Follow the [installation documents](https://docs.docker.com/get-docker/)
2. Use the file `ddlTerm.dockerfile` in `docker` to build the image
    ```sh
    docker build --no-cache -f docker/ddlterm.dockerfile -t ddltermartifact:latest docker
    ```
3. Except 2, you can download the built docker image directly. Then:
    ```
    docker load -i ddltermartifact.tar
    ```

### Linux
*We tested the following procedure on Ubuntu 18.04.*
1. Install the [Mono environment](https://www.mono-project.com/download/stable/#download-lin)

2. Install `python3`, `gcc/g++`, `make` and the necessary pip packages
    ```sh
    apt install -y gcc g++ make python3 python3-pip
    pip install pandas scipy sklearn antlr4-python3-runtime xlsxwriter
    ```

3. Build `Boogie` in `ice/popl16_artifact/Boogie/Source`
    ```sh
    msbuild Boogie.sln
    ```

4. Build `C5.0` in `ice/popl16_artifact/C50`
    ```sh
    make clean; make all
    ```
* Then, copy all generated `c5.0.*` into `ice/popl16_artifact/Boogie/Binaries`

6. Download `z3 4.8.9` from [Github](https://github.com/Z3Prover/z3/releases/download/z3-4.8.9/z3-4.8.9-x64-ubuntu-16.04.zip)
   
* Unzip the zip file, copy the inside `bin/z3` into `ice/popl16_artifact/Boogie/Binaries` and rename it to `z3.exe`

## Run Experiments
### Docker
1. Start the docker image (replace `/path/to/a/directory/to/save/the/result`)
    ```sh
    docker run -it -v /path/to/a/directory/to/save/the/result:/log --tmpfs /tmpfs --cpus=1 ddltermartifact:latest
    ```
2. Run the experiments (e.g. the main experiment in our paper)
    ```sh
    cd ddlTerm
    python3 experiment/scripts/RunTasks.py experiment/scripts/configurations/ExpMain/LeNLeMixed_Standard.xml
    ```

### Linux
1. Please update the configuration XML file in `experiment/scripts/configurations` before the experiments.
    ```xml
    <!-- A path to tmp directory -->
    <Tmp>/tmpfs</Tmp>
    <!-- A path to output result directory -->
    <Log_Dir>/log</Log_Dir>
    ```
2. Run the experiments (e.g. the main experiment in our paper)
    ```sh
    cd ddlTerm
    python3 experiment/scripts/RunTasks.py experiment/scripts/configurations/ExpMain/LeNLeMixed_Standard.xml
    ```

### For a precise result, we suggest:
* using [tmpfs](https://man7.org/linux/man-pages/man5/tmpfs.5.html) to reduce the time of IO. (By default, tmpfs has been used in docker running)
* updating the timeout setting in configuration XML files according to performance of your machine.
* setting the cpu limit to one core using [cgroup](https://man7.org/linux/man-pages/man7/cgroups.7.html). (By default, cpu limit has been used in docker running)

## Baseline in Our Paper
If you want to make a comparative experiment, please follow the install instruments for our baseline tools.

* [AProVE](https://aprove.informatik.rwth-aachen.de/)

* [Ultimate Automizer](https://monteverdi.informatik.uni-freiburg.de/tomcat/Website/?ui=tool&tool=automizer)

* [MuVal](https://zenodo.org/record/4747775#.YTMryHUzaV4)

* [FreqTerm](https://github.com/grigoryfedyukovich/aeval/tree/term)

* **Remember** to set the cpu limit to one core using [cgroup](https://man7.org/linux/man-pages/man7/cgroups.7.html) or by the parameter `--cpus` if using `docker`.

* The [benchmarks](https://github.com/grigoryfedyukovich/aeval/tree/term) locate in `experiment/benchmarks`.
    * C-style can be used for `AProVE`, `Ultimate Automizer` and `MuVal`.
    * Horn-style can be used for `FreqTerm`.

* We provide some useful scripts in `experiment/baseline.scripts` to run the experiments for `AProVE`, `Ultimate Automizer` and `FreqTerm`. 
  You can modify the path in the scripts to run these tools. We hope these scripts are useful for you.

## File Structure
* `code/` contains all source codes of loop bound generation
* `docker/` includes a docker file to build the docker image
* `experiments/` includes benchmarks and necessary scripts for running experiments
* `ice/` includes an open source safety validator `ICE-DT` (we made some modification)