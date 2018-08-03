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
from os.path import isdir, join

from SCons.Script import (COMMAND_LINE_TARGETS, AlwaysBuild, Builder, Default,
                          DefaultEnvironment)


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
        ElfToImg=Builder(
            action=env.VerboseAction(" ".join([
                "$PYTHONEXE",
                join(SDK_DIR, "tools" ,"gap_flasher", "bin", "flashImageBuilder"),
                "--flash-boot-binary", "$SOURCES",
                "--raw", "$TARGET"
            ]), "Building $TARGET"),
            suffix=".raw"
        )
    )
)

#
# Target: Build executable, linkable firmware and raw image
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_img = join("$BUILD_DIR", "${PROGNAME}.raw")
else:
    target_elf = env.BuildProgram()
    target_img = env.ElfToImg(join("$BUILD_DIR", "${PROGNAME}"), target_elf)

AlwaysBuild(env.Alias("nobuild", target_elf))
target_buildprog = env.Alias("buildprog", target_elf, target_elf)

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
            "--binary", "$SOURCE",
            "load", "start", "wait"
        ],
        UPLOADCMD='"$PYTHONEXE" $UPLOADER $UPLOADERFLAGS'
    )

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
