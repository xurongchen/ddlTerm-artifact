# Install ddlTerm
You can choose one of the following installation procedures.
### Based on Docker
1. Follow the [installation documents](https://docs.docker.com/get-docker/)
2. Use the file `ddlTerm.dockerfile` in `docker` to build the image
    ```sh
    docker build --no-cache -f docker/ddlterm.dockerfile -t ddltermartifact:latest docker
    ```
3. Except 2, you can download the built docker image directly. Then:
    ```
    docker load -i ddltermartifact.tar
    ```

### Based on Linux
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
