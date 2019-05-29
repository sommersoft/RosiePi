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

import os
import pkg_resources
import subprocess

def board_data_dir():
    return pkg_resources.resource_filename("rosiepi", "board_data")


def _copy(source_file, destination):
    copy_result = subprocess.run(
        ["cp", source_file, destination],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    str_stdout = str(copy_result.stdout,
                     encoding="utf-8")
    print("copy:", str_stdout)
    return copy_result


def copy_firmware(filename, destination):
    source_file = os.path.join(board_data_dir(), "firmware", filename)
    if not os.path.exists(source_file):
        raise FileNotFoundError("'{}'".format(source_file))

    firmware_result = _copy(source_file, destination)
    if firmware_result.returncode != 0:
        tb = sys.exc_info()[2]
        msg_stdout = [
            " Command: '{}'".format(" ".join(firmware_result.args)),
            " Error: {}".format(str(firmware_result.stdout, encoding="utf-8"))
        ]
        raise RuntimeError(
            "The following error occurred while copying new firmware:"
            "\n{}".format("\n".join(msg_stdout))
        ).with_traceback(tb) from None

    return firmware_result

def copy_testfile(filename, destination):
    source_file = os.path.join(board_data_dir(), "test_files", filename)
    if not os.path.exists(source_file):
        raise FileNotFoundError("'{}'".format(source_file))

    firmware_result = _copy(source_file, destination)
    if firmware_result.returncode != 0:
        tb = sys.exc_info()[2]
        msg_stdout = [
            " Command: '{}'".format(" ".join(firmware_result.args)),
            " Error: {}".format(str(firmware_result.stdout, encoding="utf-8"))
        ]
        raise RuntimeError(
            "The following error occurred while copying the test file:"
            "\n{}".format("\n".join(msg_stdout))
        ).with_traceback(tb) from None


def discover_board_tests(filter=None):
    """ A helper to get a list of available board test files,
        and pre-filter them.
    """
    test_file_dir = os.path.join(board_data_dir(), "test_files")
    test_files = os.listdir(test_file_dir)

    # TODO: filter files using `filter`
    #for file in test_files:

    return test_files
