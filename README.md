# RISC-V GAP: development platform for [PlatformIO](https://platformio.org)

[![Build Status](https://github.com/platformio/platform-riscv_gap/workflows/Examples/badge.svg)](https://github.com/platformio/platform-riscv_gap/actions)

GreenWaves' GAP8 IoT application processor enables the cost-effective development, deployment and autonomous operation of intelligent sensing devices that capture, analyze, classify and act on the fusion of rich data sources such as images, sounds or vibrations.

* [Home](https://registry.platformio.org/platforms/platformio/riscv_gap) (home page in the PlatformIO Registry)
* [Documentation](https://docs.platformio.org/page/platforms/riscv_gap.html) (advanced usage, packages, boards, frameworks, etc.)

# Usage

1. [Install PlatformIO](https://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](https://docs.platformio.org/page/projectconf.html) file:

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
platform = https://github.com/platformio/platform-riscv_gap.git
board = ...
...
```

# Configuration

Please navigate to [documentation](https://docs.platformio.org/page/platforms/riscv_gap.html).
