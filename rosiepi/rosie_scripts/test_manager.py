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

import argparse
import os
import sys
import datetime
from rosiepi import screen, file_copy


cli_parser = argparse.ArgumentParser(description="rosiepi Test Manager")
cli_parser.add_argument(
    "board",
    help="Name of the board to run test(s) on."
)
cli_parser.add_argument(
    "--unit",
    action="store_true",
    dest="unit_test",
    help="Run unit tests on the board."
)
cli_parser.add_argument(
    "--physical",
    dest="physical_test",
    action="store_true",
    help=("Run physical tests that require interaction with the test controller"
          ". For example, testing the physical functioning of GPIOs with "
          "'digitalio.DigitalInOut'.")
)

def start_test():
    """ Starts the board tests in the following order:
        1. Download firmware to test (Pull Request, Release, etc.)
           and place it in the `/board_data/firmware` folder
        2. Reset the board into bootloader mode
        3. Copy new firmware UF2 file to board
        4. Restart normal screen session
        5. Run tests as determined by `--unit` or `--physical`
    """
    cli_args = cli_parser.parse_args()
    if cli_args.unit_test and cli_args.physical_test:
        raise ValueError("Cannot run more than one test type per instance.")

    run_info = [
        "Starting rosiepi...\n",
        " > Date: ",
        datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S%Z"),
        "\n",
        " > Board: {}\n".format(cli_args.board.lower()),
        " > Test type: {}\n".format(("unit" if cli_args.unit_test else
                                     "physical")),
    ]
    print("".join(run_info))
    # 1
    # will be deterined later after "when do we test" is answered

    # 2
    board_name = cli_args.board.lower()
    board_session = screen.ScreenController(board_name)
    print("{}\n".format(board_session))
    print("Reseting {} into bootloader mode.\n".format(board_name))
    board_session.reset_to_boot()
    print("{}\n".format(board_session))

    # 3 (firmware filename hardcoded for now)
    fw_file = "adafruit-circuitpython-metro_m4_express-en_US-4.0.1.uf2"
    print("Copying new firmware to {}.\n".format(board_name))
    file_copy.copy_firmware(fw_file, board_session.usb_mnt)
    print("Firmware update successful.\n")

    # 4
    board_session.start_screen()
