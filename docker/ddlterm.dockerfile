FROM ubuntu:20.04

# MONO Environment
WORKDIR /root

RUN apt update && apt -y upgrade && DEBIAN_FRONTEND="noninteractive" apt install -y gnupg ca-certificates

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF

RUN echo "deb https://download.mono-project.com/repo/ubuntu stable-focal main" | tee /etc/apt/sources.list.d/mono-official-stable.list

RUN apt update && DEBIAN_FRONTEND="noninteractive" apt install -y mono-devel

# GCC/G++ && Python3 Environment && Development Tools
RUN DEBIAN_FRONTEND="noninteractive" apt install -y gcc g++ make python3 python3-pip ssh git zip

# Pull the ddlTerm
WORKDIR /root

RUN pip install pandas scipy sklearn antlr4-python3-runtime xlsxwriter

RUN git clone https://github.com/xurongchen/ddlTerm-artifact.git ddlTerm && rm -rf ddlTerm/.git && rm -rf ddlTerm/docker
# PROXY for github
# RUN ALL_PROXY="socks5h://166.111.82.55:1081" git clone https://github.com/xurongchen/ddlTerm-artifact.git ddlTerm && rm -rf ddlTerm/.git && rm -rf ddlTerm/docker

WORKDIR /root/ddlTerm/

# Build the ddlTerm
WORKDIR /root/ddlTerm/ice/popl16_artifact/Boogie/Source

RUN msbuild Boogie.sln

WORKDIR /root/ddlTerm/ice/popl16_artifact/C50

RUN make clean; make all

RUN cp /root/ddlTerm/ice/popl16_artifact/C50/c5.0.* /root/ddlTerm/ice/popl16_artifact/Boogie/Binaries/

WORKDIR /root

ARG Z3_Link=https://github.com/Z3Prover/z3/releases/download/z3-4.8.9/z3-4.8.9-x64-ubuntu-16.04.zip

ARG Z3_Download_Name=z3-4.8.9-x64-ubuntu-16.04

RUN wget -O z3.zip ${Z3_Link} && unzip z3.zip
# PROXY for github
# RUN ALL_PROXY=socks5h://166.111.82.55:1081 wget -O z3.zip ${Z3_Link} && unzip z3.zip

RUN cp /root/${Z3_Download_Name}/bin/z3 /root/ddlTerm/ice/popl16_artifact/Boogie/Binaries/z3.exe

WORKDIR /root
