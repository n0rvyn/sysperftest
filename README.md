# sysperftest

### Brief
**Multiple Linux Hosts System Performance Test Script**   
**来点中文吧，词穷了。就是给信创项目批量测试性能用的，setup.py咱也不会写，直接手补。**  

#### 管理端环境: 
- RHEL7.9及以上（其它版本未测试，支不支持不关心）
- Python-3.6.8及以上
- Paramiko-2.x及其依赖包
#### 支持的受管主机版本：
- RHEL7/8
- UOS20 (x86_64 & arm)
- KylinV10 (x86_64 & arm)

#### 支持的测试工具：
- lmbench
- iozone3
- LTP
- netperf
- stream
- unixbench

### Usage
**Usage**: `./remoteconsole.py`
**明白人一看就懂**

### Main Menu
>--------------------------------M A I N  M E N U--------------------------------
>
>1. List and select host group \[None selected means all hosts\]
>2. Ping test for multiple host[s]
>3. Init remote ssh console for host[s] specified (once group changed)
>4. YUM setup for host[s] initiated
>5. Install necessary package[s]
>6. Put package[s] to remote machine
>7. Sub Menu for system bench test
>0. Inactive mode (Send command manually)
>
>&emsp;3.14
&emsp;&emsp;--Remove the whole directory '/tmp/sysperftest'
>

### Submenu
>\---------------------------------------------------------------------------------  
>FIO (I/O)   
>    &emsp; -- # todo \<libaio not found error\>  
>IOZONE3 (Filesystem I/O)  
    &emsp; -- \<test passed\>  
STREAM Benchmark (Memory)  
    &emsp;\-\- \<test passed\>  
>NETPERF (Network Performance)  
>    &emsp;\-\- \<test passed\>  
>LMBENCH (FULL, Processor/Memory/File/Bandwidth)  
>    &emsp;-- <single copy test passwd>  
>UNIXBENCH (FULL)   
>    &emsp;-- <system bench test passed, get run state FAILED.>   
>Stress-ng (POC)  
>    &emsp;-- <test passed>  
>LTP (POC)  
>
>\---------------------------------------------------------------------------------------  
>l. List and select script[s] running background  
>r. Running state of script [True: running | False: finished]  
>c. Clean last results. <rm -rf /tmp/sysperftest/sysperftest_*>  
>f. Fetch results exist (All files those names starts with 'sysperftest_')  
>  
>R. Read 5 lines of log file '/tmp/sysperftest/log/remoteconsole.log'  
>L. List directory '/tmp/sysperftest/'  
>  
>A. Run all test and fetch the results  
>  
>[None][None]>>>>  
  

