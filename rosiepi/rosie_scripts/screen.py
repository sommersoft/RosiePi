# MIT License
# Copyright (c) 2019 Michael Schroeder
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import os
import pkg_resources
import subprocess
import sys
import time

_SCREEN_CMD = "screen -S"
_SCREEN_ILLEGAL_CMDS = ["at", "deflogin", "defshell", "exec"]

def dev_iface_dir():
    return pkg_resources.resource_filename("rosiepi", "rosie_scripts/bash_scripts")

class ScreenLogReader():
    """ Class that holds each ScreenController's attrs and functions for
        reading the log file.
    """
    def __init__(self, log_name):
        self.log_name = log_name
        self._last_read_time = 0
        last_line = 0
        if os.path.exists(log_name):
            with open(log_name, 'r') as logfile:
                last_line = len(logfile.readlines())
        self._last_read_line = last_line


    def __repr__(self):
        name = self.log_name
        last_read = datetime.datetime.fromtimestamp(self._last_read_time)
        last_line = self._last_read_line
        msg = "({}, {}, {})".format(name, last_read, last_line)
        return msg


    def _log_updated(self):
        log_mtime = os.stat(self.log_name).st_mtime
        return (self._last_read_time < log_mtime)


    def log_clear(self):
        """ Force clears a log.
        """
        # TODO: decide to check for `_log_updated()` or not
        if os.path.exists(log_name):
            with open(log_name, 'w') as logfile:
                logfile.write("")


    def log_tail(self, *, blocking=False, timeout=30):
        """ Mimics `tail -f` functionality for getting new information
            from the screen logfile. Returns only the new lines since
            the last time the logfile was read, if there are any.

            :param: bool blocking: Runs a blocking loop until an update
                                   is detected.

            :param: int timeout: Limits the `blocking` loop to the
                                 number of seconds. Default is `30`
                                 seconds.
        """
        if timeout < 0:
            raise ValueError("'timeout' must be zero or greater.")

        if blocking:
            time_sentinel = time.time() + timeout
            while not self._log_updated():
                print("waiting..")
                if time_sentinel < time.time():
                    break
                pass
        last_line = []
        with open(self.log_name) as logfile:
            last_line = logfile.readlines()
        #print(last_line)
        log_update = last_line[self._last_read_line:]
        self._last_read_time = os.stat(self._log_name).st_mtime
        self._last_read_line = len(last_line)
        return log_update

    def log_wait_for_response(self, response_string, *, search_type=None,
                              timeout=None, auto_exception=True):
        """ Continuously reads the log searching for `response_string`.
            Evaluation is by each line. The `search_type` can be changed.
            If the `response_string` is found, the entire line is returned.
            If any exceptions are found and `auto_exception` is True,
            the search will stop and the exception line will return.

            This function uses `log_tail()`, but will always be BLOCKING.
            However, a `timeout` can be set.

            :param: str response_string: The response string in the log
                                         to search for.

            :param: search_type: The type of search to use. Available options:
                                 `startswith`, `endswith`, or `in`. Default
                                 is `None`, which uses equivilency (`==`).

            :param: int timeout: The `timeout` in seconds. Default is no
                                 timeout.

            :param: bool auto_exception: Automatically stop and return
                                         when any exception is found.
                                         Default is `True`.
        """
        types_of_search = ["startswith", "endswith", "in", None]
        if search_type not in types_of_search:
            raise ValueError(
                "'{0}' not a valid search type.\n"
                "Valid type are: {1}".format(search_type,
                                             ", ".join(types_of_search))
            )
        if not isinstance(response_string, str):
            raise ValueError("'response_string' must be a string.")

        response_found = False
        start_time = time.time()
        while not response_found:
            log_result = self.log_tail(blocking=True, timeout=1)
            for line in log_result:
                # check for exceptions first
                if auto_exception:
                    if "exception:" in line.lower():
                        response_found = line
                        break

                if search_type is None:
                    if line == response_string:
                        response_found = line
                elif search_type == "startswith":
                    if line.startswith(response_string):
                        response_found = line
                elif search_type == "endswith":
                    if line.endswith(response_string):
                        response_found = line
                elif search_type == "in":
                    if line in response_string:
                        response_found = line

            if timeout:
                if (start_time + timeout) < time.time():
                    if not response_found:
                        response_found = ""
                        break

        return response_found


class ScreenController():
    """ Container for interacting with boards through bash scripts
        in `dev_interface/`.

        :param: session_name: Name of the device. This name is used
                              to determine which bash scripts to
                              interact with.

        :param: bool start_session: Starts the screen session upon
                                    `ScreenController()` object creation.
                                    Default is `True`
    """
    def __init__(self, session_name, *, start_session=True):
        self.session_name = session_name
        self._dev_iface_dir = os.path.join(dev_iface_dir(), session_name)
        self._boot_mode = False
        self.logfile = ScreenLogReader(self._dev_iface_dir + ".log")
        self.usb_mnt = None
        self.tty = None
        if start_session:
            self.start_screen()

    def __repr__(self):
        repr_dict = {
            "Session Name": self.session_name,
            "Boot Mode": self._boot_mode,
            "USB Mountpoint": self.usb_mnt,
            "Serial Device Address": self.tty,
        }
        return str(repr_dict)


    def start_screen(self):
        try:
            start_result = subprocess.run(
                ["bash", self._dev_iface_dir + ".sh", self.logfile.log_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True
            )
            str_stdout = str(start_result.stdout,
                             encoding="utf-8")
            print(str_stdout)
            for line in str_stdout.split("\n"):
                if "> USB" in line:
                    self.usb_mnt = line[line.rfind(":") + 2:]
                elif "> Serial tty" in line:
                    self.tty = line[line.rfind(":") + 2:]
            # make sure we're at an input line by sending a newline
            self.send_command(["stuff", ""])
            self._boot_mode = False

        except subprocess.CalledProcessError as cpe:
            # check if board is mounted as boot
            if self.find_boot_mount():
                # TODO: do something. but...what?
                pass

            tb = sys.exc_info()[2]
            msg_stdout = [
                " Command: '{}'".format(" ".join(cpe.cmd)),
                " Error: {}".format(str(cpe.stdout, encoding="utf-8"))
            ]
            raise RuntimeError(
                "The following error occurred while starting the screen"
                " session:\n{}".format("\n".join(msg_stdout))
            ).with_traceback(tb) from None


    def find_boot_mount(self):
        """ Run the bootloader version of the bash script to locate
            the mountpoint to copy over firmware
        """
        try:
            start_result = subprocess.run(
                ["bash", self._dev_iface_dir + "_boot.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True
            )
            str_stdout = str(start_result.stdout,
                             encoding="utf-8")
            print(str_stdout)
            for line in str_stdout.split("\n"):
                if "> USB" in line:
                    self.usb_mnt = line[line.rfind(":") + 2:]
                    if not self._boot_mode:
                        self._boot_mode = True
            return self._boot_mode

        except subprocess.CalledProcessError as cpe:
            tb = sys.exc_info()[2]
            msg_stdout = [
                " Command: '{}'".format(" ".join(cpe.cmd)),
                " Error: {}".format(str(cpe.stdout, encoding="utf-8"))
            ]
            raise RuntimeError(
                "The following error occurred while starting the screen"
                " session:\n{}".format("\n".join(msg_stdout))
            ).with_traceback(tb) from None


    def send_command(self, cmd, *, screen_args=None):
        """ Sends commands to the screen session.
            Returns a `CompletedProcess` object with the result of
            Python subprocess command.

            :note: `screen -S <sessionname> -X` is automatically included.
                   Including it in the parameters will lead to undefined
                   behavior.

            :param: cmd: A string or list of the command to send. Use
                         a string for commands that take no arguments
                         (e.g. `kill`). Use a list for commands that
                         take arguments (e.g. `["stuff", "'import os'"']`)

            :param: screen_args: A string or list of any additional
                                 arguments for `screen` itself
                                 (e.g. "-L" to turn off logging).
                                 Keyword arg only.
        """

        command = _SCREEN_CMD.split() + [self.session_name, "-X"]

        if screen_args:
            if not isinstance(screen_args, (str, list)):
                raise ValueError("'screen_args must be string or list.'")
            elif isinstance(screen_args, str):
                command.append(screen_args)
            else:
                command.extend(screen_args)

        commands_in = [cmd] if isinstance(cmd, str) else cmd
        for verify in commands_in:
            if verify in _SCREEN_ILLEGAL_CMDS:
                raise ValueError("'{}' command is not allowed.".format(verify))

        command.extend(commands_in)
        command[-1] = str(command[-1] + "\r\n")
        #print(" ..command preview:", command)
        result = subprocess.run(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        return result


    def reset_to_boot(self):
        """ Resets the board into bootloader mode.
            Both `find_boot_mount` and `send_command` raise exceptions
            when they fail, so call this with a `try: except` block to catch
            errors.
        """
        if not self._boot_mode:
            # sync the filesystem to reduce board fs corruption
            os.sync()
            # set the `microcontroller.RunMode` to `BOOTLOADER`
            cmds = [
                ["stuff", "import microcontroller"],
                ["stuff", "microcontroller.on_next_reset(microcontroller.RunMode.BOOTLOADER)"],
                ["stuff", "microcontroller.reset()"]
            ]
            for cmd in cmds:
                cmd_result = self.send_command(cmd)
                if cmd_result.returncode != 0:
                    tb = sys.exc_info()[2]
                    msg_stdout = [
                        " Command: '{}'".format(" ".join(cmd_result.args)),
                        " Error: {}".format(
                            str(cmd_result.stdout, encoding="utf-8")
                        )
                    ]
                    raise RuntimeError(
                        "The following error occurred while sending commands"
                        " to the session:\n{}".format("\n".join(msg_stdout))
                    ).with_traceback(tb) from None
            print("Waiting 30 seconds for board to re-enumerate...\n")
            time.sleep(30)
            self.find_boot_mount()

        return self._boot_mode
