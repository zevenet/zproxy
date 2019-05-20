# WIP Zevenet Http proxy
L7 proxy core for NG zevenet load balancer
## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

 * A modern C/C++ compiler
 * CMake 3.6+ installed
 * libssl  (1.1 for now)
 * zlib
 * doxygen for source code documentation generation

### Building The Project

#### Git Clone

First we need to check out the git repo:

```bash
$ git clone https://github.com/abdessamad-zevenet/zhttp zhttp.git
$ cd zhttp.git
$ mkdir build
$ cd build && cmake ..
$ make [&& make install]
$ Run bin/zhttp -f /path/to/pound/config/file.cfg

# Check the command line interface controller help output:
$ bin/zhttpctl

# Run the tests: WIP
$ bin/zhttptests
```

#### Project Structure

 * `src/*` — C++ code that compiles into a library (libzhttp.a) and the main zhttp binary.
 * `src/ctl` — Generate a command line interface binary.
 * `test/lib` — C++ libraries used for tests ( Google Test).
 * `test/src` — C++ test suite.
 * `cmake/*` — Cmake input files.
 * `docs/` _ Doxygen configuration file (Doxyfile).
 * `build-pkg/` _ docker based automated Debian installation package generation.
 * `docker/` _ Files for creation and running a complete GUI IDE (QTCreator) in a docker container based on debian stretch.
## Feature Description


Tests:

 * Tests compile into a single binary `zhttptest` that is run on a command line to run the tests.

#### Contributing

**Pull Requests are WELCOME!** Please submit any fixes or improvements:

 * [Project Github Home](https://github.com/abdessamad-zevenet/zhttp)
 * [Submit Issues](https://github.com/abdessamad-zevenet/zhttp/issues)
 * [Pull Requests](https://github.com/abdessamad-zevenet/zhttp/pulls)

### License

&copy; 2019 Zevenet.


### Authors

## Acknowledgments

* Hat tip to anyone whose code was used

