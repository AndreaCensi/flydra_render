#!/bin/bash

prefix=/home/andrea/svn/snp_env/
rfsee_dir=/home/andrea/svn/snp_env/src/snp/snp-a/rfsee

source $prefix/environment.sh

# /home/andrea/PY_flydra/bin/python /home/andrea/svn/snp.git/snp-a/snp_simulate_slave.py
export MPLCONFIGDIR=$rfsee_dir
export DISPLAY=:0

$prefix/deploy/bin/python $rfsee_dir/rfsee_server.py 2>> $rfsee_dir/rfsee.stderr
