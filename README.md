## What is this?
R-BoF is a python2 based script to perform Remote Buffer Overflows on 32-bit windows systems, mainly to practice and understand simple overflow concepts. \
\
It requires the usage of mona.py and Immunity Debugger, it supports ROP Chains/DEP Bypass, SEH based overflows, and Egghunting.

## How to use?
Start the vulnerable application. Once the localhost connection is estabilished, write your IP/PORT in the script and run it to send a buffer of your choice:
```
python2 stack-bof.py 
```
You can follow the instructions in the script to launch a specific type of overflow
