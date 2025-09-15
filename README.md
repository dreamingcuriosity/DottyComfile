# DottyComfile 🟢

**Tiny Buildfile Generator for C, C++, Objective-C, Go, and Rust projects.**  
Automatically detects your source files and generates a ready-to-use Makefile—zero configuration required.

---

## 🚀 Features

- ✅ **Cross-language support:** C, C++, Objective-C, Go, Rust  
- ✅ **.comignore support:** Skip build artifacts, IDE files, and more  
- ✅ **OS-aware:** Works on Windows, Linux, macOS, and Termux  
- ✅ **Interactive build options:** Customize target name, compiler, and flags  
- ✅ **ASCII art header** if `pyfiglet` is installed  
- ✅ **Automatic object directories** and clean commands  

---

## ⚡ Quick Start

```bash
# Run the generator
python3 main.py

# Follow prompts to set target executable & compiler flags
make programname         # Build the project
make clean    # Remove built files
make help     # Show available targets
