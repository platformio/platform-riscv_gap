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

from os.path import isdir, join

from SCons.Script import Import, Return, SConscript

Import("env")

fenv = env.Clone()
SDK_DIR = fenv.PioPlatform().get_package_dir("framework-gap_sdk")
assert SDK_DIR and isdir(SDK_DIR)

if "pulp-os" not in env.get("PIOFRAMEWORK"):
    SConscript("frameworks/pulp-os.py", exports={"env": fenv})

fenv.Append(
    CPPDEFINES=[
        "fileIO"
    ],

    CCFLAGS=[
        "-O3"
    ],

    CPPPATH=[
        join(SDK_DIR, "tools", "gap_flasher", "include")
    ],

    LINKFLAGS=[
        "-O3",
        "-T", join(SDK_DIR, "tools", "ld", "gapuino.conf.ld")
    ]
)

fenv.Replace(AS="$CC", ASCOM="$ASPPCOM")

flasher = fenv.Program(
    join("$BUILD_DIR", "flasher"),
    fenv.CollectBuildFiles(
        join("$BUILD_DIR", "flasherapp"),
        join(SDK_DIR, "tools", "gap_flasher", "src"),
        src_filter="+<*> -<test_FlashImg>"
    ))

Return("flasher")
