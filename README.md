# RISC-V GAP: development platform for [PlatformIO](http://platformio.org)
[![Build Status](https://travis-ci.org/pioplus/platform-riscv_gap.svg?branch=develop)](https://travis-ci.org/pioplus/platform-riscv_gap)
[![Build status](https://ci.appveyor.com/api/projects/status/am41upkan8876k05/branch/develop?svg=true)](https://ci.appveyor.com/project/pioplus/platform-riscv-gap)

GreenWaves’ GAP8 IoT application processor enables the cost-effective development, deployment and autonomous operation of intelligent sensing devices that capture, analyze, classify and act on the fusion of rich data sources such as images, sounds or vibrations.

* [Home](http://platformio.org/platforms/riscv_gap) (home page in PlatformIO Platform Registry)
* [Documentation](http://docs.platformio.org/page/platforms/riscv_gap.html) (advanced usage, packages, boards, frameworks, etc.)

# Usage

1. [Install PlatformIO](http://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](http://docs.platformio.org/page/projectconf.html) file:

## Stable version

```ini
[env:stable]
platform = riscv_gap
board = ...
...
```

## Development version

```ini
[env:development]
platform = https://github.com/pioplus/platform-riscv_gap.git
board = ...
...
```

# Configuration

Please navigate to [documentation](http://docs.platformio.org/page/platforms/riscv_gap.html).
