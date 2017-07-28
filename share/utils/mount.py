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
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description="mount.py")
    parser.add_argument("--host", type=str,
                        help="Hostname of the nfs server")
    parser.add_argument("--path", type=str,
                        help="Path on the nfs server")
    parser.add_argument("file", metavar="FILE", nargs=1,
                        help="The file to check")
    args = parser.parse_args()

    # Create a temp directory
    tmp = tempfile.mkdtemp()
    # Mount the nfs directory
    ret = subprocess.call(["mount", "-t", "nfs",
                           "%s:%s" % (args.host, args.path), tmp],
                          timeout=2)

    if os.path.exists("%s/%s" % (tmp, args.file[0])):
        ret = 0
    else:
        ret = 1
    # Un-mount
    subprocess.call(["umount", tmp], timeout=2)

    # Restore the working directory
    shutil.rmtree(tmp)
    sys.exit(ret)


if __name__ == "__main__":
    main()
