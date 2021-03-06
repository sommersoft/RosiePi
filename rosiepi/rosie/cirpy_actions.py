 # The MIT License (MIT)
 #
 # Copyright (c) 2019 Michael Schroeder
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documentation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to whom the Software is
 # furnished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 #

import logging
import os
import pathlib
import subprocess
import time

import sh
from sh.contrib import git

from rosiepi.rosie import find_circuitpython as cirpy_dir

from tests import pyboard

rosiepi_logger = logging.getLogger(__name__) # pylint: disable=invalid-name

_AVAILABLE_PORTS = ["atmel-samd", "nrf"]

def check_local_clone():
    """ Checks if there is a local clone of the circuitpython repository.
        If not, it will clone it to the `circuitpython` directory.
    """
    check_dir = os.listdir(cirpy_dir())
    if ".git" not in check_dir:
        working_dir = os.getcwd()
        os.chdir(cirpy_dir())
        git.clone("https://github.com/adafruit/circuitpython.git",
                  "--depth", "1")
        os.chdir(working_dir)

def build_fw(board, build_ref, test_log): # pylint: disable=too-many-locals,too-many-statements
    """ Builds the firware at `build_ref` for `board`. Firmware will be
        output to `.fw_builds/<build_ref>/<board>/`.

    :param: str board: Name of the board to build firmware for.
    :param: str build_ref: The tag/commit to build firmware for.
    :param: test_log: The TestController.log used for output.
    """
    working_dir = os.getcwd()
    cirpy_ports_dir = pathlib.Path(cirpy_dir(), "ports")

    board_port_dir = None
    for port in _AVAILABLE_PORTS:
        port_dir = cirpy_ports_dir / port / "boards" / board
        if port_dir.exists():
            board_port_dir = (cirpy_ports_dir / port).resolve()
            rosiepi_logger.info("Board source found: %s", board_port_dir)
            break

    if board_port_dir is None:
        err_msg = [
            f"'{board}' board not available to test. Can't build firmware.",
            #"="*60,
            #"Closing RosiePi"
        ]
        raise RuntimeError("\n".join(err_msg))

    build_dir = pathlib.Path.home() / ".fw_builds" / build_ref[:5] / board

    os.chdir(cirpy_dir())
    try:
        test_log.write("Fetching {}...".format(build_ref))
        git.fetch("--depth", "1", "origin", build_ref)

        test_log.write("Checking out {}...".format(build_ref))
        git.checkout(build_ref)

        test_log.write("Syncing submodules...")
        git.submodule("sync")

        test_log.write("Updating submodules...")
        git.submodule("update", "--init", "--depth", "1")
    except sh.ErrorReturnCode as git_err:
        # TODO: change to 'master'
        git.checkout("-f", "rosiepi_test")
        os.chdir(working_dir)
        err_msg = [
            "Building firmware failed:",
            " - {}".format(str(git_err.stderr, encoding="utf-8").strip("\n")),
            #"="*60,
            #"Closing RosiePi"
        ]
        raise RuntimeError("\n".join(err_msg)) from None

    os.chdir(board_port_dir)
    board_cmd = (
        f"make clean BOARD={board} BUILD={build_dir}",
        f"make BOARD={board} BUILD={build_dir}"
    )

    test_log.write("Building firmware...")
    try:
        rosiepi_logger.info("Running make recipe: %s", '; '.join(board_cmd))
        run_envs = {
            "BASH_ENV": "/etc/profile",
        }

        rosiepi_logger.info("Running build clean...")
        # pylint: disable=subprocess-run-check
        subprocess.run(
            board_cmd[0],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            executable="/usr/bin/bash",
            start_new_session=True,
            env=run_envs,
        )

        build_dir.mkdir(mode=0o0774, parents=True)

        # pylint: enable=subprocess-run-check
        rosiepi_logger.info("Running firmware build...")
        fw_build = subprocess.run(
            board_cmd[1],
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            executable="/usr/bin/bash",
            start_new_session=True,
            env=run_envs,
        )

        result = str(fw_build.stdout, encoding="utf-8").split("\n")
        success_msg = [line for line in result if "bytes" in line]
        test_log.write(" - " + "\n - ".join(success_msg))
        rosiepi_logger.info("Firmware built...")

    except subprocess.CalledProcessError as cmd_err:
        # TODO: change to 'master'
        git.checkout("-f", "rosiepi_test")
        os.chdir(working_dir)
        err_msg = [
            "Building firmware failed:",
            " - {}".format(str(cmd_err.stdout, encoding="utf-8").strip("\n")),
            #"="*60,
            #"Closing RosiePi"
        ]
        rosiepi_logger.warning("Firmware build failed...")
        raise RuntimeError("\n".join(err_msg)) from None

    finally:
        # TODO: change to 'master'
        git.checkout("-f", "rosiepi_test")
        os.chdir(working_dir)

    return build_dir

def update_fw(board, board_name, fw_path, test_log):
    """ Resets `board` into bootloader mode, and copies over
        new firmware located at `fw_path`.

    :param: board: The cpboard.py::CPboard object to act upon
    :param: board_name: The name of the board
    :param: fw_path: File path to the firmware UF2 to copy.
    :param: test_log: The TestController.log used for output.
    """
    success_msg = ["Firmware upload successful!"]
    try:
        with board:
            if not board.bootloader:
                test_log.write("Resetting into bootloader mode...")
                board.reset_to_bootloader(repl=True)
                time.sleep(10)

        boot_board = pyboard.CPboard.from_build_name_bootloader(board_name)
        with boot_board:
            test_log.write(
                "In bootloader mode. Current bootloader: "
                f"{boot_board.firmware.info['header']}"
            )
            test_log.write("Uploading firmware...")

            boot_board.firmware.upload(fw_path)

            test_log.write("Waiting for board to reload...")
            time.sleep(10)

        with board:
            pass
            #success_msg.append(" - New firmware: {}".format(board.firmware.info))
        test_log.write("\n".join(success_msg))

    except BaseException as brd_err:
        err_msg = [
            "Updating firmware failed:",
            f" - {brd_err.args}",
            #"="*60,
            #"Closing RosiePi"
        ]
        raise RuntimeError("\n".join(err_msg)) from None
