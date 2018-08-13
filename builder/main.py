# Copyright 2018-present PIO Plus <contact@pioplus.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from os import listdir
from os.path import isdir, join

from SCons.Script import (COMMAND_LINE_TARGETS, AlwaysBuild, Builder, Default,
                          DefaultEnvironment)

from platformio import util

env = DefaultEnvironment()
platform = env.PioPlatform()
board_config = env.BoardConfig()

SDK_DIR = platform.get_package_dir("framework-gap_sdk")
assert SDK_DIR and isdir(SDK_DIR)

env.Replace(
    AR="riscv32-unknown-elf-gcc-ar",
    AS="riscv32-unknown-elf-as",
    CC="riscv32-unknown-elf-gcc",
    GDB="riscv32-unknown-elf-gdb",
    CXX="riscv32-unknown-elf-g++",
    OBJCOPY="riscv32-unknown-elf-objcopy",
    RANLIB="riscv32-unknown-elf-gcc-ranlib",
    SIZETOOL="riscv32-unknown-elf-size",

    ARFLAGS=["rc"],

    SIZEPRINTCMD='$SIZETOOL -d $SOURCES',

    PROGSUFFIX=".elf"
)


# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")


env.Append(
    BUILDERS=dict(
        DataToBin=Builder(
            action=env.VerboseAction(" ".join([
                "$PYTHONEXE",
                join(SDK_DIR, "tools", "gap_flasher", "bin", "flashImageBuilder"),
                "--flash-boot-binary", "$SOURCES",
                "--comp-dir-rec=%s" % util.get_projectdata_dir(),
                "--raw", "$TARGET"
            ]), "Building data image $TARGET"),
            suffix=".bin"
        )
    )
)

#
# Target: Build executable, linkable firmware and data image
#

data_available = isdir(util.get_projectdata_dir()) and listdir(
    util.get_projectdata_dir())

if data_available:
    target_flasher = env.SConscript("flasher.py", exports="env")

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
else:
    target_elf = env.BuildProgram()

if data_available:
    target_firm = env.DataToBin(join("$BUILD_DIR", "data"), target_elf)
    env.Depends(target_firm, target_flasher)
else:
    target_firm = target_elf

AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)

#
# Target: Upload by default .img file
#

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
debug_tools = board_config.get("debug.tools", {})
upload_actions = []

if upload_protocol == "ftdi":
    env.Replace(
        UPLOADER=join(
            platform.get_package_dir("tool-pulp-debug-bridge") or "", "bin", "plpbridge"),
        UPLOADERFLAGS=[
            "--debug",
            "--verbose=3",
            "--cable=ftdi@digilent",
            "--chip=gap",
            "--boot-mode=jtag",
            "--binary", "$SOURCE"
        ],
        UPLOADCMD='"$PYTHONEXE" $UPLOADER $UPLOADERFLAGS'
    )

    if data_available:
        env.Append(
            UPLOADERFLAGS=[
                "--flash-image", target_firm,
                "--flasher", target_flasher,
                "flash"
            ]
        )

    env.Append(UPLOADERFLAGS=["load", "start", "wait"])

    upload_actions = [
        env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")
    ]

# custom upload tool
elif "UPLOADCMD" in env:
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

AlwaysBuild(env.Alias("upload", target_elf, upload_actions))

#
# Setup default targets
#

Default([target_buildprog, target_size])
