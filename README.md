# sysperftest

### Brief
**System performance test script**

### Usage
**Usage**: ./remoteconsole.py

### Main Menu
--------------------------------M A I N  M E N U--------------------------------

1. List and select host group [None selected means all hosts]
2. Ping test for multiple host[s]
3. Init remote ssh console for host[s] specified (once group changed)
4. YUM setup for host[s] initiated
5. Install necessary package[s]
6. Put package[s] to remote machine
7. Sub Menu for system bench test
0. Inactive mode (Send command manually)

3.14  
    -- Remove the whole directory '/tmp/sysperftest'

### Submenu
\--------------------------------------------------------------------------------  
FIO (I/O)  
    \-- \# todo <libaio not found error>
IOZONE3 (Filesystem I/O)  
    \-- <test passed>  
STREAM Benchmark (Memory)  
    \-- <test passed>  
NETPERF (Network Performance)  
    \-- <test passed>   
LMBENCH (FULL, Processor/Memory/File/Bandwidth)  
    \-- <single copy test passwd>  
UNIXBENCH (FULL)  
    \-- <system bench test passed, get run state FAILED.>  
Stress-ng (POC)  
    \-- <test passed>  
LTP (POC)  
    \--  
\---------------------------------------------------------------------------------------
l. List and select script[s] running background
r. Running state of script [True: running | False: finished]
c. Clean last results. <rm -rf /tmp/sysperftest/sysperftest_*>
f. Fetch results exist (All files those names starts with 'sysperftest_').

R. Read 5 lines of log file '/tmp/sysperftest/log/remoteconsole.log'
L. List directory '/tmp/sysperftest/'

A. Run all test and fetch the results

[None][None]>>>>

