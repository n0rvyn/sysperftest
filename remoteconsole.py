#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020-2021 by ZHANG ZHIJIE.
# All rights reserved.

# Last Modified Time: 11/28/21 20:47
# Author: ZHANG ZHIJIE
# Email: beyan@beyan.me
# File Name: sysPerfTest.py
# Tools: PyCharm

"""
---Short description of this Python module---

"""
import os
import subprocess
import random
import time
import threading
import sys
from sshconsole import sshconsole
from sshconsole import busybox
import tarfile

"""
Remote SSH console and Multiple threading remote machine system performance test console.

history:
    v2.0.3  Add     'run_all_script one by one method'
    v2.0.4  Modify  'read_grouped_console' method, None group no longer initiated once and once
            Modify  'rm_tmp_home_all' method, return {hostname: True|False} rather than {hostname: ''}
    v2.0.5  Modify  'when init ssh console, only fetch OS info and hostname;
                    'in case of unsupported command prevent ssh connection.'
"""

# define a parameter to store the start time
# for naming the log files
_DATETIME = time.strftime("%y%m%d%H%M")

# path and name definition for local host
# define the parameter of the HOME directory
_HOME = os.path.abspath(os.path.dirname(__file__))
# the directory for test tools, compressed packages
_PKG_PATH = os.path.join(_HOME, 'packages')
# define the temp directory
_TMP_PATH = os.path.join(_HOME, 'tmp')
# if not the temp directory exist, create one
# define directory for storing log locally
_LOG_PATH = os.path.join(_HOME, 'log')
_LOG_FILE_PATH = os.path.join(_LOG_PATH, 'sysperftest.log')
# define the directory to store configuration files
_CONFIG_PATH = os.path.join(_HOME, 'config')
# define the path of the configuration file
_CONFIG_FILE_PATH = os.path.join(_CONFIG_PATH, 'hosts.conf')
# define the location of scripts
_BIN_PATH = os.path.join(_HOME, 'bin')
# define the directory on local host to store results from kind of tools
_PKG_RESULTS_ORIGIN_PATH = os.path.join(_HOME, 'results/original')
# define the directory to store results after organised.
_PKG_RESULTS_EXL_PATH = os.path.join(_HOME, 'results/original')

try:
    # check if the directory defined above exist
    _ = [os.makedirs(f) for f in [_TMP_PATH, _LOG_PATH, _PKG_RESULTS_EXL_PATH, _PKG_RESULTS_ORIGIN_PATH]]
except FileExistsError:
    pass


# Define a list for storing required packages' name
_REQUIRED_PKGS = ['unzip', 'tar', 'make', 'python3', 'lsof', 'bzip2', 'libtirpc-devel', 'libaio-devel',
                  'lksctp-tools', 'psmisc', 'net-tools', 'net-snmp', 'gcc', 'perl', 'autoconf', 'nfs-utils',
                  'wget', 'gcc', 'rpcbind', 'libtirpc', 'gcc-gfortran', 'fio', 'sysstat', 'nmap-ncat']

# define the default media URL of rhel-based system
# URL suffix format: _BASEURL/os_id/arch/os_version_id
#                    _BASEURL/rhel/x86_64/7.9
#                    _BASEURL/uos/arm/20
_BASEURL = 'http://172.16.10.250:8080/'


"""
define the parameters for REMOTE hosts.
"""
# the home directory execute command on the remote machine, always be: /tmp/sysperftest/
_REMOTE_HOME = os.path.join('/tmp', os.path.basename(os.path.abspath(os.path.dirname(__file__))).split('-')[0])
# define the directory to store startup scripts
_REMOTE_BIN_PATH = os.path.join(_REMOTE_HOME, 'bin')
# define the package directory on remote host
_REMOTE_PKG_PATH = os.path.join(_REMOTE_HOME, 'packages')
# define the log directory on remote host
# record running state of each script
_REMOTE_LOG_PATH = os.path.join(_REMOTE_HOME, 'log')
# define the directory of results on remote host


# read value for key from
def _ReadKeyValue(keyword, val_is_int=False, val_is_bool=False, val_is_list=False):
    return busybox.ReadKeyValue(keyword=keyword,
                                configfile=_CONFIG_FILE_PATH,
                                val_is_bool=val_is_bool,
                                val_is_int=val_is_int,
                                val_is_list=val_is_list)


_read_baseurl = _ReadKeyValue('baseurl')
_BASEURL = _read_baseurl if _read_baseurl else _BASEURL


class SysPerfTest(sshconsole.SshConsole):
    def __init__(self, hostname=None, port=22, username=None, password=None, dis_log=False, retry=3, timeout=3):
        """
        add later.
        todo auto reconnect when socket been broken.
        """
        self.hostname = hostname if hostname is not None else ''
        self.port = port
        self.username = username if username is not None else 'root'
        self.password = input(f'Input Password ({self.hostname}): ') if password is None else password
        self.timeout = timeout
        self.logfile = _LOG_FILE_PATH
        # self.logger_name = f'{__class__.__name__}_{self.hostname}'
        sshconsole.SshConsole.__init__(self, dis_log=dis_log, log_path=self.logfile)

        self.node_name = None
        self.os_id, self.os_version_id, self.arch = None, None, None
        self.no_cpus, self.cpu_model_name = None, None
        self.total_mem_mib, self.total_swap_mib = 0, 0
        self.no_disks, self.disks_name, self.disks_size = 0, None, None
        self.initiated = self.init_connect()

    def init_connect(self):
        self.ssh_connect(hostname=self.hostname, port=self.port, username=self.username,
                         password=self.password, timeout=self.timeout)

        try:
            # define hostname of machine
            self.node_name = self.fetch_output_str('hostname')
            # define OS id, version & arch
            self.os_id, self.os_version_id, self.arch = self.fetch_os_info()
            if self.os_version_id == 'uos':
                self.os_id, self.os_version_id = self.os_version_id, self.os_id

            """
            # define number of cpus, type of cpu and cpu frequencies
            self.no_cpus, self.cpu_model_name = self.fetch_cpu_info()
            # define total memory in Mib, total swap size in Mib
            self.total_mem_mib, self.total_swap_mib = self.fetch_mem_info()
            # define disks information parameters
            self.no_disks, self.disks_name, self.disks_size = self.fetch_disks_info()
            """

            return True
        except TypeError as error:
            self._colorlog(error, 'critical')
            # uncommitted the line followed will break the loop of init multiple console
            # todo also exit within threading.Thread target
            # exit(-1)
            return False
        except ValueError as error:
            self._colorlog(error, 'error')
            return False

    def fetch_hostname(self):
        """
        return: hostname of the machine
        """
        self.hostname = self.fetch_output_str('hostname')
        return self.hostname

    def fetch_os_info(self):
        """
        return: (rhel, 7.6, x86_64)
        """
        os_info_cmd = """cat /etc/os-release | grep -wE "ID|VERSION_ID" | awk -F'"' '{print $2}'; uname -p"""
        try:
            return tuple(i.strip('\n') for i in (self.fetch_output_list(os_info_cmd)))
        except TypeError as error:
            self._colorlog(error, 'error')

    def fetch_cpu_info(self):
        """
        return: ('1', 'Intel(R) Core(TM) i5-8259U CPU @ 2.30GHz', '2304.000')
        """
        # cpu_info_cmd = """lscpu | grep -E "^CPU...:|Model name:|CPU MHz:" | awk -F':' '{print $2}' | sed 's/  //g' """
        cpu_info_cmd = """lscpu | grep -E "^CPU...:|Model name:" | awk -F':' '{print $2}' | sed 's/  //g'"""
        try:
            return tuple(i.strip('\n').strip() for i in (self.fetch_output_list(cpu_info_cmd)))
        except TypeError as error:
            self._colorlog(error, 'error')

    def fetch_mem_info(self):
        """
        return: ('216', '767')
        """
        mem_info_cmd = """free -m | grep -E "Mem|Swap" | awk '{print $2}'"""
        try:
            return tuple(i.strip('\n') for i in (self.fetch_output_list(mem_info_cmd)))
        except TypeError as error:
            self._colorlog(error, 'error')

    def fetch_disks_info(self):
        disk_name_cmd = """lsblk | grep -vE "├|─|NAME" | awk '{print $1}'"""
        disk_size_cmd = """lsblk | grep -vE "├|─|NAME" | awk '{print $4}'"""
        disk_num_cmd = """lsblk | grep -vE "├|─|NAME" | wc -l"""
        no_disks = self.fetch_output_str(disk_num_cmd)
        disks_name = tuple(i.strip('\n') for i in (self.fetch_output_list(disk_name_cmd)))
        disks_size = tuple(i.strip('\n') for i in (self.fetch_output_list(disk_size_cmd)))
        return no_disks, disks_name, disks_size

    def rhel_based_setup_yum(self, os_id=None, baseurl=None, arch=None, os_version_id=None):
        os_id = self.os_id if os_id is None else os_id
        os_version_id = self.os_version_id if os_version_id is None else os_version_id
        arch = self.arch if arch is None else arch

        baseurl = _BASEURL if baseurl is None else baseurl

        try:
            if os_version_id.startswith('7') or os_version_id == 'V10' or arch == 'aarch64':
                yum_config = (f'[{os_id}]',
                              f'name = {os_id.upper()} Yum Repo for SysPerf test',
                              f'baseurl = {baseurl}/{os_id}/{arch}/{os_version_id}',
                              'enable = 1',
                              'gpgcheck = 0\n'
                              )
            elif os_version_id.startswith('8') or os_version_id in ['V10', '20']:
                yum_config = (f'[{os_id}-BaseOS]',
                              f'name = {os_id.upper()} Base OS Yum Repo for SysPerf test',
                              f'baseurl = {baseurl}/{os_id}/{arch}/{os_version_id}/BaseOS',
                              'enable = 1',
                              'gpgcheck = 0',
                              '',
                              f'[{os_id}-AppStream]',
                              f'name = {os_id.upper()} App Stream Yum Repo for SysPerf test',
                              f'baseurl = {baseurl}/{os_id}/{arch}/{os_version_id}/AppStream',
                              'enable = 1',
                              'gpgcheck = 0',
                              '')
            else:
                self._colorlog(f'[{os_id}-{arch}-{os_version_id}] OS not supported!', 'error')
                return False
        except AttributeError as error:
            # todo with ssh_console() return True or False, no need to except AttributeError any more?
            self._colorlog(error, 'error')
            return False

        _tmp_yum = os.path.join(_TMP_PATH, f'yum_tmp_{self.hostname}.repo')
        _remote_yum_path = '/etc/yum.repos.d/sysperftest.repo'
        with open(_tmp_yum, 'w') as f:
            f.writelines('\n'.join(yum_config))

        # todo backup exist YUM configuration generally
        self.fetch_output_str('mv /etc/yum.repos.d/kylin_x86_64.repo /etc/yum.repos.d/kylin_x86_64.repo.bak')
        try:
            self.sftp_put(_tmp_yum, _remote_yum_path)
        except OSError as e:
            return False
        return self.fetch_return_stat('yum clean all && yum install -y tar')

    def put_pkgs(self, clean=True):
        f = self.exec_command(f'rm -rf {_REMOTE_PKG_PATH}') if clean is True else ''
        return self.sftp_put_dir(_PKG_PATH, _REMOTE_HOME)

    def put_bin(self, clean=True):
        f = self.exec_command(f'rm -rf {_REMOTE_BIN_PATH}') if clean is True else ''
        return self.sftp_put_dir(_BIN_PATH, _REMOTE_HOME)

    def send_script_bg(self, script_name, local_dir_path=None, remote_dir_path=None):
        # send script to remote machine and running background
        _script_name = script_name
        # _interval = interval
        _local_dir_path = local_dir_path if local_dir_path is not None else _BIN_PATH
        _remote_dir_path = _REMOTE_BIN_PATH if remote_dir_path is None else remote_dir_path
        _local_path = os.path.join(_local_dir_path, _script_name)
        _remote_path = os.path.join(_remote_dir_path, _script_name)
        return self.script_run_bg(_local_path, _remote_path, _REMOTE_LOG_PATH)
        # self.script_run_bg(_local_path, _remote_path)

    def is_script_run(self, script_name=None):
        return self.bg_proc_run_stat(script_name) if script_name is not None else 'Unknown'

    def send_script_bg_wait_done(self, script_name, interval=6):
        self.send_script_bg(script_name=script_name)
        while True:
            time.sleep(interval)
            if not self.is_script_run(script_name=script_name):
                return True

    def inst_pkgs_need(self) -> dict:
        return {pkg: self.fetch_return_stat(f'yum install -y {pkg}') for pkg in _REQUIRED_PKGS}

    def _pack_results(self):
        _host_mark = self.hostname.replace('.', '')
        _pkg_name = f'{_DATETIME}_{_host_mark}_sysperftest.tar'
        self.fetch_output_str(f'cd {_REMOTE_HOME} && tar -cvf {_pkg_name} sysperftest_*')
        return _pkg_name

    def fetch_results(self) -> bool:
        _pkg_name = self._pack_results()
        _local_path = os.path.join(_PKG_RESULTS_EXL_PATH, _pkg_name)
        self.sftp_get(os.path.join(_REMOTE_HOME, _pkg_name), _local_path)
        return True if os.path.isfile(_local_path) else False

    def clean_last_results(self):
        return self.fetch_return_stat(f'rm -rf {_REMOTE_HOME}/sysperftest_*')

    def nmon_setup(self):
        pass

    def nmon_fetch_simple(self):
        pass


class MultiRemoteConsole(object):
    def __init__(self):
        self.hosts = {}
        # self.consoles = []
        self.console_grouped = {}
        self.consoles_all = []
        self._return = []

    def _read_hosts(self, config_file=None) -> dict:
        _config_file = config_file if config_file is not None else _CONFIG_FILE_PATH
        try:
            with open(_config_file, 'r+') as f:
                group_index = ''
                for line in [i.strip('\n').strip() for i in f.readlines()]:
                    if line.startswith('#') or not line:
                        continue
                    if line.startswith('['):
                        group_name = line.strip('[').strip(']')
                        group_index = group_name
                        self.hosts.update({group_name: []})
                        continue
                    try:
                        # (hostname, vendor, username, password, port)
                        self.hosts[group_index].append(
                            tuple([key_value.split('=')[-1].strip('"').strip("'")
                                                              for key_value in [i.strip()
                                                                                for i in line.split(',')]]))
                    except KeyError:
                        continue
                    except ValueError:
                        continue
                    except TypeError:
                        continue
        except FileNotFoundError as e:
            print(e)
        return self.hosts

    def ping_hosts(self, group_name=None):
        _return = {}

        def multi_ping(hostname=None, port=None):
            # todo try int(port) except ValueError -> test connection with 'ping'
            # todo replace (ssh) open as ssh_open with replace(')', '_') strip('(')
            try:
                _ping_cmd = f'ping -c1 -W1 {hostname}' if port is None else f'nc -v -z -w1 {hostname} {int(port)}'
            except ValueError:
                _ping_cmd = f'ping -c1 -W1 {hostname}'

            _ping_return = str(subprocess.getstatusoutput(_ping_cmd)[0]).replace('0', 'OK').replace('1', 'FAILED')
            return _return.update({hostname: _ping_return}) if hostname is not None else None

        _hosts = []
        # read hosts for all or group name specified
        # (hostname, vendor, username, password, port)
        try:
            [_hosts.extend(_host) for _host in self._read_hosts().values()] if group_name is None else [_hosts.extend(self._read_hosts()[group_name])]
        except KeyError:
            return None

        try:
            thread = [threading.Thread(target=multi_ping, args=(_hostname, _attr[-1])) for _hostname, *_attr in _hosts]
        except IndexError:
            print('Host configuration line error found!')
            return _return
        [t.start() for t in thread]
        [t.join() for t in thread]

        """
        # print the output to display
        _to_prt = [f'{_hostname:<15s}:{str(_result):<10}' for _hostname, _result in _return.items()]
        # i+1 for avoid list[0] taken the whole 1st line
        _to_prt = [f'{_to_prt[i-1]}\n' if (i % 3) == 0 else f'{_to_prt[i-1]}' for i in range(1, len(_to_prt)+1)]
        print(''.join(_to_prt))
        """
        print(self.dict_dis_format(_return, 15, 10, 3))
        return _return

    @staticmethod
    def dict_dis_format(source_dict: dict, key_len=15, value_len=0, num_dis_per_line=2, new_line=False):
        """
        format dict parameter to displayable strings
        such as:
            {'hostname1': 'ok', 'hostname2': 'failed', 'hostname3': 'ok', 'hostname4': 'ok'} ->
            hostname1  : ok  hostname2:  failed
            hostname3  : ok  hostname4:  ok
        """
        # todo ignore the empty lines
        new_line = '\n' if new_line else ''
        # print the output to display
        # _ = [f'{key:<{key_len}s}:{new_line}{str(value):<{value_len}}' for key, value in source_dict.items()]
        # display with color 'gray'
        _ = [f'\033[0;37m{key:<{key_len}s}\033[0m:{new_line}{str(value):<{value_len}}' for key, value in source_dict.items()]
        # i+1 for avoid list[0] taken the whole 1st line
        return f'{new_line}'.join([f'{_[i - 1]}\n' if 0 == (i % num_dis_per_line) else f'{_[i - 1]}' for i in range(1, len(_) + 1)])

    def list_groups(self):
        self._read_hosts()
        return list(key for key in self._read_hosts().keys())

    def init_multi_consoles(self, group_name=None):
        print('-' * 32, 'init ssh console', '-' * 32, sep='')
        _console_list = []
        _hosts = []
        _init_results = {}

        def init_ssh(_hostname, _vendor=None, _username=None, _password=None, _port=None):
            _vendor = '' if _vendor is None else _vendor
            _username = 'root' if _username is None else _username
            _password = '' if _password is None else _password
            # todo handle host detail line without password specified
            # error raised: Oops, unhandled type 3 ('unimplemented')
            _password = input(f'Password ({_hostname}): ') if '' == _password else _password
            try:
                _port = 22 if _port is None else int(_port)
            except ValueError:
                _port = 22

            _ssh_console = SysPerfTest(hostname=_hostname, username=_username, password=_password, port=int(_port))
            # only append successfully initiated console
            if _ssh_console.initiated:
                _console_list.append(_ssh_console)
            _node_name = _ssh_console.node_name if _ssh_console.node_name else 'Unknown(init failed)'
            _init_results.update({_hostname: _node_name})
            # print(f'{_hostname:<15s}: {_node_name}')

        try:
            [_hosts.extend(_host) for _host in self._read_hosts().values()] if group_name is None else [_hosts.extend(self._read_hosts()[group_name])]
        except KeyError:
            return None

        try:
            thread = [threading.Thread(target=init_ssh, args=(hostname, *attr, )) for hostname, *attr in _hosts]
            [t.start() for t in thread]
            [t.join() for t in thread]
        except ValueError:
            pass

        # self.consoles = _console_list
        # [self.consoles_all.append(consl) if consl not in self.consoles_all else None for consl in _console_list]
        self.consoles_all = _console_list if group_name is None else self.consoles_all

        # append console objects list as the value of key 'group_name' of the dict self.console_grouped
        self.console_grouped.update({group_name: _console_list}) if group_name is not None else None

        # print init results to display
        print(self.dict_dis_format(_init_results, 15, 25, 2))
        print('-'*30, 'ssh client init done', '-'*30, sep='')
        return _console_list

    def read_grouped_console(self, group_name=None):
        try:
            _console_list = self.console_grouped[group_name]
        # group_name not been initiated or group_name is None
        except KeyError:
            _console_list = self.init_multi_consoles(group_name) if group_name is not None else self.consoles_all
            # if _console_list empty, reinit console list for group None
            _console_list = _console_list if _console_list else self.init_multi_consoles()

        return _console_list

    def setup_yum(self, group_name=None):
        # _ = [consl.init_connect() for consl in self.init_multi_consoles(group_name)]
        # _ = [consl.os_id for consl in self.init_multi_consoles(group_name)]
        _results = {}
        #
        # once group changed, self.consoles not empty, the values may be beyond to another group
        # _console_list = self.consoles if self.consoles else self.init_multi_consoles(group_name)
        _console_list = self.read_grouped_console(group_name)

        # define a method as the target of threading, to print messages wanted to display
        def setup_yum_target(ssh_console: SysPerfTest):
            _results.update({ssh_console.hostname: ssh_console.rhel_based_setup_yum()})
            # print(f'{ssh_console.hostname:<15s}: {ssh_console.rhel_based_setup_yum()}')

        thread = [threading.Thread(target=setup_yum_target, args=(consl, )) for consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        print(self.dict_dis_format(_results, 15, 6, 3))

    def inst_necessary_pkgs(self, group_name=None):
        # _console_list = self.consoles if self.consoles else self.init_multi_consoles(group_name)
        _console_list = self.read_grouped_console(group_name)

        def inst_pkg_target(ssh_console: SysPerfTest):
            # print(f'{ssh_console.hostname:<15s}: {ssh_console.inst_pkgs_need()}')
            print(f'\n{ssh_console.hostname}: \n{self.dict_dis_format(ssh_console.inst_pkgs_need(), 15, 8, 3)}')

        # thread = [threading.Thread(target=inst_pkg_target, args=(consl,)) for consl in self.consoles]
        thread = [threading.Thread(target=inst_pkg_target, args=(consl,)) for consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]

    def send_command_to_hosts(self, command: str, group_name=None):
        _result = {}
        # _hosts = []
        # if self.consoles is empty, multiple init console with method: self.init_multi_console(group_name)
        # _console_list = self.consoles if self.consoles else self.init_multi_consoles(group_name)
        _console_list = self.read_grouped_console(group_name)

        def send_cmd_target(ssh_console: SysPerfTest):
            _result.update({ssh_console.hostname: ssh_console.fetch_output_str(command)})

        thread = [threading.Thread(target=send_cmd_target, args=(consl, )) for consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        print(self.dict_dis_format(_result, 15, 60, 1, True))

    def send_pkgs(self, group_name=None):
        _results = {}
        _console_list = self.read_grouped_console(group_name)

        def send_pkgs_target(ssh_console: SysPerfTest):
            _results.update({ssh_console.hostname: ssh_console.put_pkgs()})

        thread = [threading.Thread(target=send_pkgs_target, args=(consl, )) for consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        print(self.dict_dis_format(_results, 15, 8, 3))

    def run_script_bg(self, group_name=None, script_name=None):
        """
        wait: set to 'True' waiting for script executing to be finished.
        """
        _result = {}
        _script_name = script_name if script_name is not None else ''

        _console_list = self.read_grouped_console(group_name)

        def run_bg_target(_ssh_console: SysPerfTest, _script_name):
            _result.update({_ssh_console.hostname: str(_ssh_console.send_script_bg(_script_name)).replace('0', 'OK')})

        thread = [threading.Thread(target=run_bg_target, args=(_consl, _script_name, )) for _consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        print(self.dict_dis_format(_result, 15, 8, 3))

    def is_script_running(self, group_name=None, script_name=None):
        _results = {}
        _script_name = script_name if script_name is not None else ''

        _console_list = self.read_grouped_console(group_name)

        def is_script_running_target(_ssh_console: SysPerfTest, _script_name):
            _results.update({_ssh_console.hostname: _ssh_console.is_script_run(_script_name)})

        thread = [threading.Thread(target=is_script_running_target, args=(_consl, _script_name,)) for _consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        print(self.dict_dis_format(_results, 15, 8, 3))

    def list_scripts(self):
        _script_list = [f for f in os.listdir(_BIN_PATH)]
        _ = {str(i): _script_list[i] for i in range(len(_script_list))}
        # print([f'{i}: {_script_list[i]}' for i in range(len(_script_list))])
        print(self.dict_dis_format(_, 2, 18, 4))
        try:
            _return = _script_list[int(input('Select one of the index: '))]
        except ValueError:
            _return = None
        return _return

    def run_all_scripts(self, group_name=None):
        print('\nClean last results: ')
        print('-'*80)
        self.clean_last_results(group_name)

        print('\nRemove expired packages and scripts: ')
        print('-'*80)
        self.rm_tmp_home_all(group_name)

        print('\nSend the latest packages to remote machine: ')
        print('-'*80)
        self.send_pkgs(group_name)

        print('\nRun all scripts: ')
        print('-'*80)
        _result = {}
        _console_list = self.read_grouped_console(group_name)
        _scripts_list = [f for f in os.listdir(_BIN_PATH)]

        def run_bg_wait_target(_ssh_console: SysPerfTest, _scripts_list: list):
            _result.update({_ssh_console.hostname: [(s, _ssh_console.send_script_bg_wait_done(s)) for s in _scripts_list]})

        thread = [threading.Thread(target=run_bg_wait_target, args=(_consl, _scripts_list,)) for _consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        # todo format output of script's name & run state
        print(self.dict_dis_format(_result, 15, 60, 1, True))
        print('Fetch results from multiple machines: ')
        self.fetch_results(group_name)

    def fetch_results(self, group_name=None):
        _results = {}
        _console_list = self.read_grouped_console(group_name)

        def fetch_results_target(_ssh_console: SysPerfTest):
            _results.update({_ssh_console.hostname: _ssh_console.fetch_results()})

        thread = [threading.Thread(target=fetch_results_target, args=(_consl,)) for _consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        print(self.dict_dis_format(_results, 15, 8, 3))

    def clean_last_results(self, group_name=None):
        _results = {}
        _console_list = self.read_grouped_console(group_name)

        def clean_target(_ssh_console: SysPerfTest):
            _results.update({_ssh_console.hostname: _ssh_console.clean_last_results()})

        thread = [threading.Thread(target=clean_target, args=(_consl, )) for _consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        print(self.dict_dis_format(_results, 15, 8, 3))

    def rm_tmp_home_all(self, group_name=None):
        # return self.send_command_to_hosts('rm -rf /tmp/sysperftest', group_name=group_name)
        rm_cmd = """rm -rf /tmp/sysperftest"""
        _results = {}
        _console_list = self.read_grouped_console(group_name)

        def rm_all_target(_ssh_console: SysPerfTest):
            _results.update({_ssh_console.hostname: _ssh_console.fetch_return_stat(rm_cmd)})

        thread = [threading.Thread(target=rm_all_target, args=(_consl,)) for _consl in _console_list]
        [t.start() for t in thread]
        [t.join() for t in thread]
        print(self.dict_dis_format(_results, 15, 8, 3))

    def read_log_lines(self, group_name=None):
        return self.send_command_to_hosts('tail -5 /tmp/sysperftest/log/remoteconsole.log', group_name=group_name)

    def list_remote_home(self, group_name=None):
        return self.send_command_to_hosts('ls -l /tmp/sysperftest/', group_name=group_name)


MENU = """
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
"""

RUN_SUB_MENU = """
---------------------------------------------------------------------------------------
FIO (I/O)                       
    -- # todo <libaio not found error>
IOZONE3 (Filesystem I/O)        
    -- <test passed>
STREAM Benchmark (Memory)       
    -- <test passed>
NETPERF (Network Performance)   
    -- <test passed>
LMBENCH (FULL, Processor/Memory/File/Bandwidth)  
    -- <single copy test passwd>
UNIXBENCH (FULL)                
    -- <system bench test passed, get run state FAILED.>
Stress-ng (POC)                 
    -- <test passed>
LTP (POC)
    -- 
---------------------------------------------------------------------------------------
l. List and select script[s] running background
r. Running state of script [True: running | False: finished]
c. Clean last results. <rm -rf /tmp/sysperftest/sysperftest_*>
f. Fetch results exist (All files those names starts with 'sysperftest_').

R. Read 5 lines of log file '/tmp/sysperftest/log/remoteconsole.log'
L. List directory '/tmp/sysperftest/'

A. Run all test and fetch the results
"""

PROMPT = '>> '
SUB_PROMPT = '>>>> '

if __name__ == '__main__':
    multi_consl = MultiRemoteConsole()
    group_selected = None
    script_running = None
    quit_code = ['q', 'exit', 'quit']
    print('-' * 32, 'M A I N  M E N U', '-' * 32, sep='')
    print(MENU)
    while True:
        while True:
            answer = input(f'[{group_selected}][{script_running}]>> ').strip()
            if answer:
                break
        loop_started = time.perf_counter()

        # show main menu
        if answer.lower() in ['m', 'p', 'menu', 'ls']:
            print('-' * 32, 'M A I N  M E N U', '-' * 32, sep='')
            print(MENU)
            continue
        # quit when met 'q', 'Q', 'quit', 'exit' ...
        if answer.lower() in quit_code:
            print('Exit as your wish.')
            exit(0)
        # list group names
        if answer.startswith('1'):
            grp_list = multi_consl.list_groups()
            print('-'*80)
            [print(f'{i}: {grp_list[i]}') for i in range(len(grp_list))]
            try:
                group_selected = grp_list[int(input('\nSelect index above(99 for all): '))]
            except ValueError:
                continue
            except IndexError:
                group_selected = None
            print(f'[{group_selected}] selected.')
            continue
        # multiple ping test
        elif answer.startswith('2'):
            print('\nhost group: ', group_selected)
            print('-'*80)
            multi_consl.ping_hosts(group_selected)

        # init ssh client
        elif answer == '3':
            print('\nhost group: ', group_selected)
            print('-' * 80)
            multi_consl.init_multi_consoles(group_selected)
        # setup yum
        elif answer == '4':
            print('\nhost group: ', group_selected)
            print('-' * 80)
            multi_consl.setup_yum(group_selected)
        # install packages
        elif answer.startswith('5'):
            print('\nhost group: ', group_selected)
            print('-' * 80)
            multi_consl.inst_necessary_pkgs(group_selected)
        # clean tmp and send packages
        elif answer.startswith('6'):
            print('\nhost group: ', group_selected)
            print('-' * 80)
            multi_consl.send_pkgs(group_selected)
        #
        # sub menu for running system bench tools
        #
        elif answer.lower() in ['7', 's']:
            print(RUN_SUB_MENU)
            while True:
                # print(RUN_SUB_MENU)
                while True:
                    answer = input(f'[{group_selected}][{script_running}]>>>> ').strip()
                    if answer:
                        break
                loop_started = time.perf_counter()
                if answer in ['m', 'p', 'ls']:
                    print(RUN_SUB_MENU)
                    continue
                if answer == '0':
                    break
                if answer == 'l':  # lower case of L
                    script_running = multi_consl.list_scripts()
                    if script_running is None:
                        continue
                    if input(f'Run {script_running} [No/yes]: ') not in ['y', 'yes']:
                        continue
                    multi_consl.run_script_bg(group_selected, script_running)
                elif answer == 'r':
                    multi_consl.is_script_running(group_selected, script_running)
                elif answer == 'c':
                    multi_consl.clean_last_results(group_selected)
                elif answer == 'f':
                    multi_consl.fetch_results(group_selected)

                elif answer == 'R':
                    multi_consl.read_log_lines(group_selected)
                elif answer == 'L':
                    multi_consl.list_remote_home(group_selected)
                elif answer == 'A':
                    multi_consl.run_all_scripts(group_selected)

                elif answer.lower() in ['b', 'back', 'q']:
                    break
                print('\nTime taken: {:.2f}s'.format(time.perf_counter() - loop_started))
                # input('Enter to be continued!\n')

        if answer.startswith('0'):
            # _hostname, *_attr = [i.strip() for i in input('Enter hostname, vendor, username, password, port (separate with ,): ').split(',')]
            while True:
                input_cmd = input(f'[{group_selected}][{script_running}]# ').strip()
                if input_cmd.lower() in quit_code:
                    break
                if not input_cmd:
                    continue
                if input_cmd.startswith('tail -f'):
                    continue
                multi_consl.send_command_to_hosts(input_cmd, group_selected)
            continue

        if answer == '3.14':
            multi_consl.rm_tmp_home_all()

        print('\nTime taken: {:.2f}s'.format(time.perf_counter() - loop_started))


