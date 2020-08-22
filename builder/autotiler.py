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

import re
import sys
from os import listdir, makedirs
from os.path import basename, dirname, isdir, isfile, getmtime, join, relpath

from SCons.Script import ARGUMENTS, Import

from platformio import fs
from platformio.builder.tools.platformio import SRC_FILTER_DEFAULT

try:
    from platformio.project.helpers import get_project_lib_dir
except ImportError:
    from platformio.util import get_projectlib_dir as get_project_lib_dir


Import("env")

SDK_DIR = env.PioPlatform().get_package_dir("framework-gap_sdk")
AUTOTILER_DIR = join(SDK_DIR, "tools", "autotiler")


def list_autotiler_generators():
    return [f for f in listdir(join(AUTOTILER_DIR, "generators"))]


def parse_cpp_includes(path):
    result = []
    include_re = re.compile(r"^#include\s+(?:\"|\<)([^\">]+)(?:\"|\>)$")
    with open(path) as fp:
        for line in fp:
            line = line.strip()
            if not line.startswith("#include"):
                continue
            match = include_re.match(line)
            if not match:
                continue
            result.append(match.group(1))
    return result


def find_generator_by_includes(includes):
    generators = list_autotiler_generators()
    for inc in includes:
        for generator in generators:
            gen_inc_path = join(AUTOTILER_DIR, "generators", generator,
                                "generator", "include", inc)
            if not isfile(gen_inc_path):
                continue
            return generator
    return None


def find_model(src_dir):
    model_files = [
        f for f in listdir(src_dir)
        if f.endswith(".c") and "model" in f.lower()
    ]
    for fname in model_files:
        includes = parse_cpp_includes(join(src_dir, fname))
        if "AutoTilerLib.h" not in includes:
            continue
        generator = find_generator_by_includes(includes)
        if not generator:
            continue
        return dict(generator=generator, model_path=join(src_dir, fname))

    return None


def build_autotiler(build_dir, generator, model_path):
    if isdir(build_dir):
        fs.rmtree(build_dir)

    # parse custom library path from `platformio.ini`
    tmpenv = env.Clone()
    tmpenv.ProcessFlags(env.get("BUILD_FLAGS"))

    genv = env.Environment(
        tools=["ar", "gas", "gcc", "g++", "gnulink"],
        CC="gcc",
        CPPPATH=[
            join(AUTOTILER_DIR, "include"),
            join(AUTOTILER_DIR, "generators", generator, "generator",
                 "include")
        ],
        LIBPATH=[join(AUTOTILER_DIR, "lib"),
                 get_project_lib_dir()] + tmpenv.get("LIBPATH", []),
        LIBS=["tile"])

    # CHECK "libtile.a"
    found_libtile = False
    for d in genv['LIBPATH']:
        if isfile(genv.subst(join(d, "libtile.a"))):
            found_libtile = True
            break

    if not found_libtile:
        sys.stderr.write(
            "Error: AutoTiler library has not been found. Please read => "
            "https://docs.platformio.org/page/platforms/riscv_gap.html"
            "#autotiler\n")
        env.Exit(1)

    variant_dirs = [(join(build_dir, "model"), dirname(model_path)),
                    (join(build_dir, "generator"),
                     join(AUTOTILER_DIR, "generators", generator, "generator",
                          "src"))]
    for (var_dir, src_dir) in variant_dirs:
        if not isdir(genv.subst(var_dir)):
            makedirs(genv.subst(var_dir))
        genv.VariantDir(var_dir, src_dir, duplicate=0)

    src_files = [join(build_dir, "model", basename(model_path))]
    src_files.extend(genv.Glob(join(build_dir, "generator", "*Generator?.c")))

    for o in genv.Object(src_files):
        if not int(ARGUMENTS.get("PIOVERBOSE", 0)):
            genv.Replace(CCCOMSTR="Compiling %s" % relpath(str(o)))
        o.build()

    if not int(ARGUMENTS.get("PIOVERBOSE", 0)):
        genv.Replace(LINKCOMSTR="Linking AutoTiler")

    return genv.Program(join(build_dir, "program"), src_files)[0].build()


def generate_user_kernel(kernel_user_dir, program_path):
    if not isdir(kernel_user_dir):
        makedirs(kernel_user_dir)
    args = [program_path]
    if "pulp-os" not in env.subst("$PIOFRAMEWORK"):
        args.append("-m")
    with fs.cd(kernel_user_dir):
        env.Execute(env.VerboseAction(" ".join(args), "Running AutoTiler"))
    print("")


def main():
    model = find_model(env.subst("$PROJECTSRC_DIR"))
    if not model:
        return

    env.SetDefault(SRC_FILTER=SRC_FILTER_DEFAULT)
    env.Append(SRC_FILTER=["-<%s>" % basename(model['model_path'])])

    env.PrintConfiguration()
    env.AddMethod(lambda *arg, **args: None, "PrintConfiguration")

    build_dir = env.subst(join("$BUILD_DIR", "autotiler"))
    kernel_dir = join(build_dir, "kernel")
    kernel_user_dir = join(kernel_dir, "user")
    program_path = join(build_dir, "program")

    if (not isfile(program_path)
            or getmtime(model['model_path']) > getmtime(program_path)):
        build_autotiler(build_dir, **model)
        generate_user_kernel(kernel_user_dir, program_path)

    # export kernel includes
    env.AppendUnique(
        CPPPATH=[
            join(AUTOTILER_DIR, "include"),
            join(AUTOTILER_DIR, "generators", model['generator'], "kernels",
                 "include"), kernel_user_dir
        ],
        CCFLAGS=[
            "-mno-memcpy", "-w"
        ],
        LINKFLAGS=["-flto"])

    # build basic and user kernels
    env.BuildSources(
        join(kernel_dir, "basic"),
        join(AUTOTILER_DIR, "generators", model['generator'], "kernels",
             "src"))
    env.BuildSources(join(kernel_user_dir, "build"), kernel_user_dir)


main()
