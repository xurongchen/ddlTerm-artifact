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
  * `IceTerm.py`: The main entrance
  * `Logger.py`: A simple logger
  * `BG0Checker/`: A simple checker to check whether the learned bound is always greater than or equals to 0.
  * `BMCFinder/`: A bounded-model-checking based error finder
  * `BoogieAST/`: An AST parser for boogie language, which is based on Antlr4.
  * `CBChecker/`: A simple checker to check the loop bound when it is a constant value.
  * `ErrorFinder/`: An analyzer to transform ICE dataset to an error trace for invalid loop bounds. 
  * `IceCaller/`: A safety checker caller for ICE.
  * `MLearner/`: A loop bound learner, including simple, conjunctive, and lexicographic loop bound.
  * `RandTester/`: A component for rand or mutation tests.
  * `StateTrans/`: A data structure to record the program states transitions during the loop iteration.
* `docker/` includes a docker file to build the docker image
* `experiments/` includes benchmarks and necessary scripts for running experiments
* `ice/` includes an open source safety validator `ICE-DT` (we made some modification)

## Where is the result
### Run with Linux
Please update the configuration XML file in `experiment/scripts/configurations` before the experiments.
```xml
<!-- A path to output result directory -->
<Log_Dir>/my/path/to/log</Log_Dir>
```
The directory `/my/path/to/log` will include a Excel file with all the results inside.
### Run with Docker
Start the docker image with the path of log directory on your **host machine**. (replace `/path/to/a/directory/to/save/the/result`)
```sh
docker run -it -v /path/to/a/directory/to/save/the/result:/log --tmpfs /tmpfs --cpus=1 ddltermartifact:latest
```
The directory `/path/to/a/directory/to/save/the/result` will include a Excel file with all the results inside.

### Result Example
`LeNLeMixed_TO60_Standard202108251055_MAIN.xlsx` is an example.
* Column `Task` is the task name; column `Result` reports the result; 
* Column `RoB` reports the bound learning rounds; 
* Column `RoI_Total` reports the invariant learning rounds in total; 
* Column `RoI_Max` reports maximum value of the invariant learning rounds during the bound learning; 
* Column `T_Total` reports the total time; 
* Columns `ToT_Total` and `ToT_Max` report the total and maximum time on testing, respectively; 
* Columns `ToB_Total` and `ToB_Max` report the total and maximum time on bound learning, respectively; 
* Columns `ToI_Total` and `ToI_Max` report the total and maximum time on invariant learning, respectively; 
* Columns `ToC_Total` and `ToC_Max` report the total and maximum time on constant loop bound checking, respectively; 
* Columns `ToM_Total` and `ToM_Max` report the total and maximum time on the quick bound checking (based on BMC), respectively;
* Columns `FinalInv` and `FindBound` report the final loop invariant and loop bounds. 
* Columns `SizeC` and `SizeBpl` report the C and Boogie file size. 
* Columns `RoB:ICE`, `RoB:BMC`, and `RoB:CBC` report the total call times of ICE loop invariant learner, the quick bound checking (based on BMC) and the constant bound checker, respectively.
