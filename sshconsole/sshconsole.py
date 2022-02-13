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
import tarfile
import random
import time
import socket
import threading
import sys
import paramiko
import tempfile

try:
    import busybox
except ModuleNotFoundError:
    from . import busybox

# define a parameter to store the start time
_date_time = time.strftime("%y%m%d_%H%M")
# define the parameter of the HOME directory
_home = os.path.abspath(os.path.dirname(__file__))
# define directory for storing log locally
_log_path = os.path.join(_home, 'log')
try:
    os.makedirs(_log_path)
except FileExistsError as e:
    pass
_log_file = os.path.join(_log_path, 'sshconsole.log')


class SshConsole(paramiko.SSHClient):
    def __init__(self, dis_log=True, log_path=None):
        paramiko.SSHClient.__init__(self)
        self.class_name = __class__.__name__
        self.logger_suffix = 'Unknown Host'
        self.dis_log = dis_log
        self.lost_conn = False
        self._transport = None
        self.sftp = None
        self._log_file = log_path if log_path is not None else _log_file
        self.pid = None

    def _colorlog(self, msg=None, level=None):
        msg = '' if msg is None else msg
        level = 'debug' if level is None else level
        name = self.class_name + ' {:<15s}'.format(self.logger_suffix)
        colorlogger = busybox.ColorLogger(name, self._log_file, display=self.dis_log)
        busybox.LogAutoClean(self._log_file, 50)
        colorlogger.colorlog(msg, level)

    def ssh_connect(self, hostname, port=22, username=None, password=None, pkey=None, key_filename=None, timeout=10,
                    allow_agent=True, look_for_keys=True, compress=False, sock=None,
                    gss_auth=False, gss_kex=False, gss_deleg_creds=True, gss_host=None,
                    banner_timeout=None, auth_timeout=5,
                    gss_trust_dns=True, passphrase=None, disabled_algorithms=None):
        self.logger_suffix = hostname if hostname else 'Unknown'
        self.load_system_host_keys()
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._colorlog(f'Attempting connect to server {hostname} with port {port}.', 'debug')
        try:
            self.connect(hostname=hostname,
                         port=port,
                         username=username,
                         password=password,
                         pkey=pkey,
                         key_filename=key_filename,
                         timeout=timeout,
                         allow_agent=allow_agent,
                         look_for_keys=look_for_keys,
                         compress=compress,
                         sock=sock,
                         gss_auth=gss_auth,
                         gss_kex=gss_kex,
                         gss_deleg_creds=gss_deleg_creds,
                         gss_host=gss_host,
                         banner_timeout=banner_timeout,
                         auth_timeout=auth_timeout,
                         gss_trust_dns=gss_trust_dns,
                         passphrase=passphrase,
                         disabled_algorithms=disabled_algorithms)
            self._colorlog('Connection established!', 'debug')
            self._transport = self.get_transport()

            # create sftp transport
            self._colorlog('Establish sftp connection.', 'debug')
            try:
                self.sftp = paramiko.SFTPClient.from_transport(self._transport)
            except paramiko.sftp.SFTPError as error:
                self._colorlog(error, 'critical')

            return True
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            self._colorlog(e, 'error')
        except socket.timeout as e:
            self._colorlog(e, 'critical')
        except OSError as e:
            self._colorlog(e, 'warn')
        except paramiko.ssh_exception.AuthenticationException as e:
            self._colorlog(e)
        except paramiko.ssh_exception.SSHException as e:
            self._colorlog(e)
        self.lost_conn = True
        return False

    def sftp_put(self, local_file_path, remote_file_path):
        self._colorlog(f'Put {local_file_path} to {remote_file_path} via SFTP.', 'debug')
        # if parent directory of 'remote_file_path' not exit, created one.
        remote_dir_name = os.path.dirname(remote_file_path)
        # self.fetch_output_str(f'[ -d {remote_dir_name} ] || mkdir -p {remote_dir_name}')
        self.fetch_return_stat(f'[ -d {remote_dir_name} ] || mkdir -p {remote_dir_name}')
        # put file to remote machine.
        return self.sftp.put(local_file_path, remote_file_path)

    def sftp_put_dir(self, local_dir_path, remote_dir_path):
        """
        put local_dir_path to directory under remote_dir_path on remote host
        /abc/def /remote/dir/def
        """
        # pack local director as one file
        _tar_name = f'sftp_trans_tmp_{random.randint(1000, 9999)}.tar'
        _tar_path = os.path.join('/tmp', _tar_name)
        # generate tar format file
        with tarfile.open(_tar_path, 'w:tar') as tar:
            # add the directory to tar file as a relative path, such as ./package ../tools
            # [tar.add(os.path.join(os.path.relpath(local_dir_path), i)) for i in os.listdir(local_dir_path)]
            tar.add(os.path.relpath(local_dir_path))
            # tar.add(local_dir_path, recursive=True)

        # define the path on remote host of the tar file
        # if not exist, create.
        _remote_pkg_tar_path = os.path.join(remote_dir_path, _tar_name)
        self.exec_command(f' [ -d {remote_dir_path} ] || mkdir -p {remote_dir_path}')
        # _remote_dir_par_path = os.path.dirname(remote_dir_path)
        # _remote_pkg_tar_path = os.path.join(_remote_dir_par_path, _tar_name)
        try:
            # put packaged tar file to parent directory of 'remote_dir_path'
            self.sftp_put(_tar_path, _remote_pkg_tar_path)
            # unpack the tar file
            self.fetch_output_str(f'tar -xvf {_remote_pkg_tar_path} -C {remote_dir_path}')
            self.fetch_output_str(f'rm -rf {_remote_pkg_tar_path}')
            # clean the temp tar file
            os.remove(_tar_path)
            # print(self.sftp.listdir(_REMOTE_PKG_PATH))
            # try list the directory just transfer sth to
            self.sftp.listdir(remote_dir_path)
            return True
        except FileNotFoundError as error:
            self._colorlog(error, 'error')
            return False
        except OSError as error:
            self._colorlog(error, 'error')
            return False

    def sftp_get(self, remote_path, local_path):
        self._colorlog(f'Get {remote_path} as {local_path} from remote via SFTP.', 'debug')
        try:
            return self.sftp.get(remote_path, local_path)
        except FileNotFoundError as _e:
            self._colorlog(_e, 'critical')
            return False

    def sftp_ls(self, remote_path):
        return self.sftp.listdir(remote_path)

    def fetch_output_list(self, cmd, timeout=None) -> list:
        """
        return output list
        """
        self._colorlog(f'Send command [{cmd}] to remote host.', 'debug')
        try:
            stdin, stdout, stderr = self.exec_command(cmd, timeout=timeout)
            error = ''.join(stderr.readlines()).strip('\n')
            if error:
                self._colorlog(error, 'warn')
            return stdout.readlines() if stdout else []
        # todo handle None type return
        except AttributeError as _e:
            self._colorlog(_e, 'error')
        except paramiko.ssh_exception.SSHException as _e:
            self._colorlog(_e, 'critical')
        except EOFError as _e:
            self._colorlog(_e, 'critical')
        self.lost_conn = True

    def fetch_output_str(self, cmd) -> str:
        try:
            return ''.join(self.fetch_output_list(cmd)).strip('\n')
        except TypeError as alert:
            self._colorlog(alert, 'error')
            return ''

    def fetch_return_stat(self, cmd) -> int:
        cmd = f'{cmd}; echo $?'
        return True if self.fetch_output_str(cmd)[-1] == '0' else False

    @staticmethod
    def _get_abs_path(filepath):
        return os.path.abspath(filepath)

    def script_fetch_output_list(self, script_path, remote_path) -> list:
        """
        parameters:
            end_of_line --> the end of the command line. such as &>/dev/null, &
        """
        script_path = self._get_abs_path(script_path)
        remote_path = os.path.join(remote_path, os.path.basename(script_path)) \
            if os.path.isdir(remote_path) else remote_path
        self.sftp.put(script_path, remote_path)
        self.fetch_output_str(f'chmod +x {remote_path}')
        return self.fetch_output_list(f'{remote_path}')

    def script_fetch_output_str(self, script_path, remote_path=None) -> str:
        remote_path = '/tmp' if remote_path is None else remote_path
        try:
            return ''.join(self.script_fetch_output_list(script_path, remote_path)).strip('\n')
        except TypeError as alert:
            self._colorlog(alert, 'error')
            return ''

    def script_run_bg(self, script_path, remote_path, remote_log_path=None) -> int:
        """
        make script running background;
        attention: script MUST print $$ (PID) at the first place

        return: PID of the script
                Remember write 'echo $$' to the script
        """
        _remote_log_file_name = 'remoteconsole.log'
        _remote_log_path = remote_log_path if remote_log_path is not None else '/var/log/'
        # check if the log path exist, otherwise created one.
        self.fetch_output_str(f'[ -d {_remote_log_path} ] || mkdir -p {_remote_log_path}')
        _remote_log_file_path = os.path.join(_remote_log_path, _remote_log_file_name)

        _script_path = self._get_abs_path(script_path)
        _remote_path = os.path.join(remote_path, os.path.basename(script_path)) \
            if os.path.isdir(remote_path) else remote_path

        try:
            self.sftp_put(_script_path, _remote_path)
        except OSError as error:
            self._colorlog(error, 'error')
        self.fetch_output_str(f'chmod +x {_remote_path}')
        chan = self.get_transport().open_session()
        # chan.get_pty()
        self._colorlog(f'Execute {_remote_path} via channel.', 'debug')
        chan.exec_command(f'nohup sh {_remote_path} &>> {_remote_log_file_path} &')
        # chan.exec_command(f' nohup {_remote_path} 2>1 | tee -a {_remote_log_file_path} &')
        # iozone3 and ltp run failed with 'tee' command.
        return chan.recv_exit_status()

    def bg_proc_run_stat(self, proc_name):
        """
        jobs  -l | awk '{if ($4="{0}")} {print $2" "$3" "$4}'
        list jobs running background
        """
        # todo after tested, delete the print line.
        # print(self.logger_suffix, proc_name, self.fetch_return_stat(f'lsof -n /tmp/sysperftest/bin/{proc_name}'))
        # return True if self.fetch_output_str(f'pidof -x {proc_name}') else False
        return True if self.fetch_return_stat(f'lsof -n /tmp/sysperftest/bin/{proc_name}') else False

    def authorizeSshAgent(self, hostname, username, port=22):
        """
        generate authorization-based SSH agent
        briefly, append localhost 'id_rsa.put' to remote host 'authorized_keys'
        """
        localHome = os.environ['HOME']
        sshLocalHome = os.path.join(localHome, '.ssh')
        sshKeyPath = os.path.join(sshLocalHome, 'id_rsa.pub')
        if os.path.isfile(sshKeyPath):
            self._colorlog(f'{sshKeyPath} already exist!', 'info')
        else:
            msg = 'Generate new public key for remote agent, do NOT change any default options!'
            self._colorlog(msg, 'info')
            os.system("ssh-keygen -t rsa -P ''")

        sshCmd = f'ssh -l {username} -p {port} {hostname}'
        testSshCmd = f'{sshCmd} "-o NumberOfPasswordPrompts=0 echo" &>/dev/null'
        # return code equal to 0
        if not os.system(testSshCmd):
            return True

        with open(sshKeyPath, 'r+') as f:
            localPubKeyContent = f.readline().strip('\n')
        generatePriKeyOnRemote = 'mkdir ~/.ssh &>/dev/null && chmod 700 ~/.ssh &>/dev/null'
        appendKeyToSshAuthFile = 'echo {} >> ~/.ssh/authorized_keys'.format(localPubKeyContent)

        genPriKey = f'{sshCmd} "{generatePriKeyOnRemote}"'
        appendKey = f'{sshCmd} "{appendKeyToSshAuthFile}"'
        os.system(genPriKey)
        if not os.system(appendKey):
            return True


USAGE = """
Usage: sshconsole [options] [HOSTNAME | IP ADDRESS]

Options:
  -u, --username USERNAME       Specifies the user to log in as on the remote machine, default is 'root'
  -P, --port PORT               Port to connect to on remote host, default is 22.
  -p, --password PASSWORD       Specifies the password of the USERNAME to log in as on the remote machine.
  -c, --command COMMAND         Execute COMMAND specified on remote machine.
  -h, --hostname HOSTNAME       Specifies the hostname or IP address of the remote machine.
  
      --btrfs-subvolume-home    use BTRFS subvolume for home directory
                                faillog databases
  -m, --create-home             create the user's home directory
  -M, --no-create-home          do not create the user's home directory
  -N, --no-user-group           do not create a group with the same name as
        --badnames                do not check for bad names
"""

if __name__ == '__main__':
    pass
