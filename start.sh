#!/bin/bash
export QUICK2WIRE_API_HOME=~/watermon/quick2wire-python-api
export PYTHONPATH=$PYTHONPATH:$QUICK2WIRE_API_HOME

cd ~/watermon
python3 watermon.py
