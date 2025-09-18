# DottyComfile 🚀

**Tiny, zero-config buildfile generator for C, C++, Objective-C, Go, and Rust projects.**

![Python](https://img.shields.io/badge/python-3.6%2B-yellow) ![License](https://img.shields.io/badge/license-MIT-black) ![Cross-platform](https://img.shields.io/badge/platform-Windows%20|%20Linux%20|%20macOS-lightgrey) ![Date](https://img.shields.io/badge/released%20on-9%2F18%2F25-orange)

---

## Overview

DottyComfile automatically detects your project language, scans for source files, and generates a ready-to-use Makefile. Just run `python3 main.py` and build your project—no manual Makefile edits required.

---

## Features

- ✅ Cross-language support: C, C++, Objective-C, Go, Rust  
- ✅ `.comignore` support to skip unwanted files (similar to `.gitignore`)  
- ✅ OS-aware clean commands (Windows & Unix)  
- ✅ Interactive compiler & flags input  
- ✅ Automatic object directory creation  
- ✅ Optional ASCII art header if [`pyfiglet`](https://pypi.org/project/pyfiglet/) is installed  
- ✅ Works on Windows, Linux, macOS, Termux  

---

## Supported Languages & Files

| Language       | File Extensions / Special Files        |
|----------------|--------------------------------------|
| C              | `.c`                                  |
| C++            | `.cpp`, `.cxx`, `.cc`, `.C`           |
| Objective-C    | `.m`, `.mm`                           |
| Go             | `.go`                                 |
| Rust           | `.rs`, `Cargo.toml`                   |

---

## Usage

1. Run the generator:

```bash
python3 main.py
make programname         # Build the project
make clean    # Remove built files
make help     # Show available targets
