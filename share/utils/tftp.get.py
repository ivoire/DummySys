#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2016 Rémi Duraffort
# This file is part of DummySys.
#
# DummySys is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DummySys is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with DummySys.  If not, see <http://www.gnu.org/licenses/>

import argparse
import os
import pexpect
import shutil
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description="tftp.get.py")
    parser.add_argument("--host", type=str, default="localhost",
                        help="Hostname of the tftp server")
    parser.add_argument("--port", type=int, default=69,
                        help="Port of the tftp server")
    parser.add_argument("file", metavar="FILE", nargs=1,
                        help="The file to download")
    args = parser.parse_args()

    # Create a temp directory
    tmp = tempfile.mkdtemp()
    base_dir = os.getcwd()
    os.chdir(tmp)

    p = pexpect.spawn("tftp", encoding="utf-8")
    p.expect("tftp> ")
    p.sendline("connect %s %d" % (args.host, args.port))
    p.expect("tftp> ")
    p.sendline("get %s" % args.file[0])
    ret = p.expect(["Received \d+ bytes in \d+\.\d+ seconds",
                    "Error code \d+: [\w\s]+"])

    # Restore the working directory
    os.chdir(base_dir)
    shutil.rmtree(tmp)
    sys.exit(ret)


if __name__ == "__main__":
    main()
