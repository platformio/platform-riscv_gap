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
                          DefaultEnvironment, SConscript)


env = DefaultEnvironment()
env.SConscript("compat.py", exports="env")
platform = env.PioPlatform()
board_config = env.BoardConfig()

SDK_DIR = platform.get_package_dir("framework-gap_sdk")
PULP_TOOLS_DIR = platform.get_package_dir("tool-pulp_tools")
assert SDK_DIR and isdir(SDK_DIR)
assert PULP_TOOLS_DIR and isdir(PULP_TOOLS_DIR)

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
                join(PULP_TOOLS_DIR, "bin", "flashImageBuilder"),
                "--flash-boot-binary", "$SOURCES",
                "--comp-dir-rec", "$PROJECTDATA_DIR",
                "--raw", "$TARGET"
            ]), "Building data image $TARGET"),
            suffix=".bin"
        )
    )
)

#
# Autotiler
#

SConscript("autotiler.py", exports={"env": env})

#
# Target: Build executable, linkable firmware and data image
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
else:
    target_elf = env.BuildProgram()

if "uploadfs" in COMMAND_LINE_TARGETS:
    data_dir = env.subst("$PROJECTDATA_DIR")
    if not (isdir(data_dir) and listdir(data_dir)):
        sys.stderr.write(
            "Please create `data` directory in a project and put some files\n")
        env.Exit(1)
    target_firm = env.DataToBin(join("$BUILD_DIR", "data"), target_elf)
else:
    target_firm = target_elf

env.AddPlatformTarget("buildfs", target_firm, None, "Build Filesystem Image")
AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)

#
# Target: Print binary size
#

target_size = env.AddPlatformTarget(
    "size",
    target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"),
    "Program Size",
    "Calculate program size",
)

#
# Target: Upload by default .img file
#

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
debug_tools = board_config.get("debug.tools", {})
upload_actions = []

if upload_protocol == "ftdi":
    env.Replace(
        UPLOADER=join(PULP_TOOLS_DIR, "bin", "plpbridge"),
        UPLOADERFLAGS=[
            "--debug",
            "--verbose=3",
            "--cable=ftdi@digilent",
            "--chip=gap",
            "--boot-mode=%s" % board_config.get("upload.boot_mode"),
            "--binary", target_elf
        ],
        UPLOADCMD='"$PYTHONEXE" $UPLOADER $UPLOADERFLAGS'
    )

    if "uploadfs" in COMMAND_LINE_TARGETS:
        env.Append(
            UPLOADERFLAGS=[
                "--flash-image", target_firm,
                "--flasher", join(PULP_TOOLS_DIR, "bin", "flasher"),
                "flash"
            ]
        )

    env.Append(UPLOADERFLAGS=[
        c.strip() for c in board_config.get("upload.commands").split(" ")
        if c.strip()
    ])

    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

env.AddPlatformTarget("upload", target_firm, upload_actions, "Upload")
env.AddPlatformTarget(
    "uploadfs", target_firm, upload_actions, "Upload Filesystem Image")

#
# Setup default targets
#

Default([target_buildprog, target_size])
