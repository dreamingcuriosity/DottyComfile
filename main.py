from datetime import datetime
import glob
import os
import fnmatch
from pathlib import Path
import re


def load_comignore():
    """Load .comignore patterns, similar to .gitignore"""
    ignore_patterns = []
    comignore_path = ".comignore"

    if os.path.exists(comignore_path):
        with open(comignore_path, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    ignore_patterns.append(line)

    # Add some default patterns if no .comignore exists
    if not ignore_patterns:
        ignore_patterns = [
            "build/",
            "CMakeFiles/",
            "target/",
            "pkg/mod/",
            "*.o",
            "*.obj",
            "*.exe",
            ".git/",
            ".vscode/",
            "__pycache__/",
            "node_modules/",
            "*.bak",
            "*.tmp",
        ]

    return ignore_patterns


def compile_ignore_patterns(ignore_patterns):
    """Compile ignore patterns into regex for faster matching"""
    compiled_patterns = []

    for pattern in ignore_patterns:
        pattern = pattern.replace("\\", "/")

        # Convert fnmatch pattern to regex
        regex_pattern = fnmatch.translate(pattern)

        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            # For directory patterns, we want to match any file under that directory
            dir_pattern = pattern[:-1]
            regex_pattern = fnmatch.translate(dir_pattern)
            # Make it match directory anywhere in path
            regex_pattern = r"(?:^|/)" + regex_pattern.replace(r"\Z", "") + r"(?:/|$)"

        compiled_patterns.append(re.compile(regex_pattern, re.IGNORECASE))

    return compiled_patterns


def should_ignore_fast(file_path, compiled_patterns):
    """Fast check if a file should be ignored using compiled regex patterns"""
    file_path = file_path.replace("\\", "/")
    filename = os.path.basename(file_path)

    for pattern in compiled_patterns:
        if (
            pattern.search(file_path)
            or pattern.search(filename)
            or any(pattern.search(part) for part in file_path.split("/"))
        ):
            return True

    return False


def get_all_files_once():
    """Get all files in one pass using pathlib for better performance"""
    extensions = {".c", ".cpp", ".cxx", ".cc", ".C", ".m", ".mm", ".go", ".rs"}
    special_files = {"Cargo.toml"}

    all_files = {"c": [], "cpp": [], "objc": [], "go": [], "rust": [], "cargo": []}

    # Use pathlib for faster recursive traversal
    for file_path in Path(".").rglob("*"):
        if file_path.is_file():
            suffix = file_path.suffix.lower()
            name = file_path.name
            path_str = str(file_path)

            if name in special_files:
                if name == "Cargo.toml":
                    all_files["cargo"].append(path_str)
            elif suffix in extensions:
                if suffix == ".c":
                    all_files["c"].append(path_str)
                elif suffix in {".cpp", ".cxx", ".cc", ".C"}:
                    all_files["cpp"].append(path_str)
                elif suffix in {".m", ".mm"}:
                    all_files["objc"].append(path_str)
                elif suffix == ".go":
                    all_files["go"].append(path_str)
                elif suffix == ".rs":
                    all_files["rust"].append(path_str)

    return all_files


def detect_language_and_sources():
    """Detect programming language and source files with optimized file scanning"""
    ignore_patterns = load_comignore()
    compiled_patterns = compile_ignore_patterns(ignore_patterns)

    def filter_sources(sources):
        """Filter out ignored files using compiled patterns"""
        filtered = []
        for src in sources:
            if not should_ignore_fast(src, compiled_patterns):
                filtered.append(src)
            else:
                print(f"Ignoring: {src}")
        return filtered

    # Get all files in one pass
    all_files = get_all_files_once()

    # Check languages in priority order
    if all_files["c"]:
        sources = filter_sources(all_files["c"])
        objects = [f.replace(".c", ".o") for f in sources]
        return "c", sources, objects

    elif all_files["cpp"]:
        cpp_sources = filter_sources(all_files["cpp"])
        cpp_objects = [f.rsplit(".", 1)[0] + ".o" for f in cpp_sources]
        return "c++", cpp_sources, cpp_objects

    elif all_files["objc"]:
        objc_sources = filter_sources(all_files["objc"])
        objc_objects = [f.rsplit(".", 1)[0] + ".o" for f in objc_sources]
        return "objective-c", objc_sources, objc_objects

    elif all_files["go"]:
        sources = filter_sources(all_files["go"])
        objects = [os.path.basename(f).replace(".go", "") for f in sources]
        return "go", sources, objects

    elif all_files["cargo"]:
        cargo_files = filter_sources(all_files["cargo"])
        if cargo_files:
            return "rust", cargo_files, ["target/release/*"]

    elif all_files["rust"]:
        sources = filter_sources(all_files["rust"])
        objects = [f.replace(".rs", "") for f in sources]
        return "rust", sources, objects

    return "unknown", [], []


def generate_makefile(language, sources, objects):
    """Generate Makefile based on detected language with interactive input"""

    # --- Interactive prompts ---
    target = input("Enter the target executable name (default: a.out): ").strip()
    if not target:
        target = "a.out"

    compiler_with_flags = input(
        "Enter compiler and flags (leave empty for default): "
    ).strip()
    parts = compiler_with_flags.split()
    compiler = parts[0] if parts else None
    flags = parts[1:] if len(parts) > 1 else []

    # Language-specific defaults if user didn't provide any
    if not compiler:
        defaults = {
            "c": ("gcc", ["-Wall", "-Wextra"]),
            "c++": ("g++", ["-Wall", "-Wextra", "-std=c++17"]),
            "objective-c": ("clang", ["-Wall", "-Wextra", "-framework", "Foundation"]),
            "go": ("go", ["build"]),
            "rust": (
                "cargo" if glob.glob("**/Cargo.toml", recursive=True) else "rustc",
                (
                    ["build", "--release"]
                    if glob.glob("**/Cargo.toml", recursive=True)
                    else ["-o", target]
                ),
            ),
        }

        if language in defaults:
            compiler, flags = defaults[language]

    cc_line = " ".join([compiler] + flags)

    # --- Color codes ---
    COLORS = {
        "GREEN": "\\033[92m",
        "BLUE": "\\033[94m",
        "YELLOW": "\\033[93m",
        "RED": "\\033[91m",
        "CYAN": "\\033[96m",
        "MAGENTA": "\\033[95m",
        "BOLD": "\\033[1m",
        "RESET": "\\033[0m",
    }

    # --- Write Makefile ---
    with open("makefile", "w") as f:
        size_bytes = os.path.getsize(__file__)
        size_kb = (size_bytes + 1023) // 1024  # round up to whole KB
        
        # Header
        f.write("# =====================================================\n")
        f.write("# Auto-generated Makefile by main.py\n")
        f.write(f"# Generated on: {datetime.now().isoformat()}\n")
        f.write(f"# Detected language: {language.upper()}\n")
        f.write(f"# Sources: {', '.join(sources)}\n")
        f.write("# Licensed under the MIT License\n")
        f.write("# =====================================================\n\n")

        # ASCII art header (cached approach)
        f.write(
            f"""# Autogenerated makefile by:
# =====================================================
  #  DottyComfile — tiny buildfile generator ({size_kb} KB)
# =====================================================
# → Generates Makefiles in 0.5s
# → Builds projects from C, C++, Obj-C, Go, Rust
# → Zero configs, just run `python3 main.py`

# Why "DottyComfile"?
# - dotty = don't wait around
# - .COM = retro small executables
# - common file = works everywhere

# Licensed MIT. Enjoy.
# =====================================================

"""
        )

        try:
            import pyfiglet

            ascii_art = pyfiglet.figlet_format("DottyComfile", font="slant")
            ascii_art_commented = "\n".join(
                f"# {line}" for line in ascii_art.splitlines()
            )
            f.write(ascii_art_commented + "\n\n")
        except ImportError:
            f.write("# DottyComfile ASCII art requires pyfiglet\n\n")

        # Color definitions
        for color_name, value in COLORS.items():
            f.write(f"{color_name} = {value}\n")
        f.write("\n")

        # Variables
        f.write(f"TARGET = {target}\n")
        f.write(f"CC = {cc_line}\n")
        f.write(f"SOURCES = {' '.join(sources)}\n")
        f.write(f"OBJECTS = {' '.join(objects)}\n\n")

        # For nested directories, we might need to create object directories
        if language in ["c", "c++", "objective-c"]:
            # Create object directories rule
            obj_dirs = {os.path.dirname(obj) for obj in objects if os.path.dirname(obj)}

            if obj_dirs:
                f.write("# Create necessary directories for object files\n")
                f.write("directories:\n")
                for obj_dir in sorted(obj_dirs):
                    f.write(f"\t@mkdir -p {obj_dir}\n")
                f.write("\n")

        # Build rules
        if language in ["c", "c++", "objective-c"]:
            if "obj_dirs" in locals() and obj_dirs:
                f.write("$(TARGET): directories $(OBJECTS)\n")
            else:
                f.write("$(TARGET): $(OBJECTS)\n")
            f.write('\t@echo "$(BOLD)$(GREEN)Linking $(TARGET)...$(RESET)"\n')
            f.write("\t$(CC) $(OBJECTS) -o $(TARGET)\n")
        elif language == "go":
            f.write("$(TARGET): $(SOURCES)\n")
            f.write('\t@echo "$(BOLD)$(GREEN)Building Go project...$(RESET)"\n')
            f.write("\t$(CC) -o $(TARGET)\n")
        elif language == "rust":
            if compiler == "cargo":
                f.write("$(TARGET): $(SOURCES)\n")
                f.write(
                    '\t@echo "$(BOLD)$(GREEN)Building Rust project with Cargo...$(RESET)"\n'
                )
                f.write("\t$(CC)\n")
                f.write(f"\tcp target/release/{target} .\n")
            else:
                f.write("$(TARGET): $(SOURCES)\n")
                f.write('\t@echo "$(BOLD)$(GREEN)Building Rust project...$(RESET)"\n')
                f.write("\t$(CC) $(SOURCES)\n")
        f.write('\t@echo "$(BOLD)$(CYAN)✓ Successfully built $(TARGET)$(RESET)"\n\n')

        # Object rules for C/C++/ObjC
        if language in ["c", "c++", "objective-c"]:
            for src in sources:
                obj = src.rsplit(".", 1)[0] + ".o"
                f.write(f"{obj}: {src}\n")
                f.write(f'\t@echo "$(BOLD)$(YELLOW)Compiling {src}...$(RESET)"\n')
                # Create directory for object file if it doesn't exist
                obj_dir = os.path.dirname(obj)
                if obj_dir:
                    f.write(f"\t@mkdir -p {obj_dir}\n")
                f.write(f"\t$(CC) -c {src} -o {obj}\n")
                f.write(f'\t@echo "$(GREEN)✓ Compiled {obj}$(RESET)"\n\n')
        # ... existing code ...

        # Clean
        f.write("clean:\n")
        f.write('\t@echo "$(BOLD)$(RED)Cleaning up...$(RESET)"\n')
        if language in ["c", "c++", "objective-c"]:
            f.write(
                "\t$(if $(OS),rm -f $(TARGET) $(OBJECTS),del /q $(TARGET) $(subst /,\\,$(OBJECTS)) 2>nul)\n"
            )
        elif language == "go":
            f.write("\t$(if $(OS),rm -f $(TARGET),del /q $(TARGET) 2>nul)\n")
        elif language == "rust":
            if compiler == "cargo":
                f.write("\tcargo clean\n")
                f.write("\t$(if $(OS),rm -f $(TARGET),del /q $(TARGET) 2>nul)\n")
            else:
                f.write(
                    "\t$(if $(OS),rm -f $(TARGET) $(OBJECTS),del /q $(TARGET) $(subst /,\\,$(OBJECTS)) 2>nul)\n"
                )
        f.write('\t@echo "$(CYAN)✓ Clean complete$(RESET)"\n\n')

        # ... existing code ...

        # Help
        f.write("help:\n")
        f.write('\t@echo "$(BOLD)$(MAGENTA)Available targets:$(RESET)"\n')
        f.write('\t@echo "  $(YELLOW)$(TARGET)$(RESET) - Build the main executable"\n')
        f.write('\t@echo "  $(YELLOW)clean$(RESET) - Remove all built files"\n')
        f.write('\t@echo "  $(YELLOW)help$(RESET)  - Show this help message"\n\n')

        f.write(".DEFAULT_GOAL := help\n")
        if (
            language in ["c", "c++", "objective-c"]
            and "obj_dirs" in locals()
            and obj_dirs
        ):
            f.write(".PHONY: clean help directories\n")
        else:
            f.write(".PHONY: clean help\n")


if __name__ == "__main__":
    # Check if .comignore exists, if not create a sample one
    if not os.path.exists(".comignore"):
        print("No .comignore file found. Creating a sample .comignore file...")
        with open(".comignore", "w") as f:
            f.write(
                """# DottyComfile ignore patterns (similar to .gitignore)
# Lines starting with # are comments
# Patterns support wildcards: * ? [abc]
# Directory patterns should end with /

# Build directories
build/
target/
CMakeFiles/
.cmake/

# Package managers and dependencies
pkg/mod/
go/pkg/
node_modules/
vendor/

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~

# Compiled objects and executables
*.o
*.obj
*.exe
*.dll
*.so
*.dylib
a.out

# Backup and temporary files
*.bak
*.tmp
*.temp
*~

# Version control
.git/
.svn/
.hg/

# OS files
.DS_Store
Thumbs.db

# Test and example directories (customize as needed)
test/
tests/
examples/
samples/

# Add your custom patterns below:

"""
            )
        print("Created .comignore file. You can edit it to customize ignore patterns.")
        print("Re-run the script after editing .comignore if needed.")

    language, sources, objects = detect_language_and_sources()

    if language == "unknown":
        print("Error: No supported source files found.")
        print(
            "Supported languages: C (.c), C++ (.cpp, .cxx, .cc, .C), Objective-C (.m, .mm), Go (.go), Rust (.rs or Cargo.toml)"
        )
        exit(1)

    print(f"Detected {language} project with {len(sources)} source files:")
    for src in sources:
        print(f"  - {src}")
    print()

    generate_makefile(language, sources, objects)
        return "rust", ["Cargo.toml"], ["target/release/*"]
    elif glob.glob("**/*.rs", recursive=True):
        sources = glob.glob("**/*.rs", recursive=True)
        objects = [f.replace('.rs', '') for f in sources]
        return "rust", sources, objects
    else:
        return "unknown", [], []

def generate_makefile(language, sources, objects):
    """Generate Makefile based on detected language with interactive input"""
    
    # --- Interactive prompts ---
    target = input("Enter the target executable name (default: a.out): ").strip()
    if not target:
        target = "a.out"

    compiler_with_flags = input("Enter compiler and flags (leave empty for default): ").strip()
    parts = compiler_with_flags.split()
    compiler = parts[0] if parts else None
    flags = parts[1:] if len(parts) > 1 else []

    # Language-specific defaults if user didn't provide any
    if not compiler:
        if language == "c":
            compiler = "gcc"
            flags = ["-Wall", "-Wextra"]
        elif language == "c++":
            compiler = "g++"
            flags = ["-Wall", "-Wextra", "-std=c++17"]
        elif language == "objective-c":
            compiler = "clang"
            flags = ["-Wall", "-Wextra", "-framework", "Foundation"]
        elif language == "go":
            compiler = "go"
            flags = ["build"]
        elif language == "rust":
            if glob.glob("**/Cargo.toml", recursive=True):
                compiler = "cargo"
                flags = ["build", "--release"]
            else:
                compiler = "rustc"
                flags = ["-o", target]

    cc_line = " ".join([compiler] + flags)

    # --- Color codes ---
    COLORS = {
        'GREEN': '\\033[92m',
        'BLUE': '\\033[94m',
        'YELLOW': '\\033[93m',
        'RED': '\\033[91m',
        'CYAN': '\\033[96m',
        'MAGENTA': '\\033[95m',
        'BOLD': '\\033[1m',
        'RESET': '\\033[0m'
    }

    # --- Write Makefile ---
    with open("makefile", "w") as f:
        # Header
        f.write("# =====================================================\n")
        f.write("# Auto-generated Makefile by main.py\n")
        f.write(f"# Generated on: {datetime.now().isoformat()}\n")
        f.write(f"# Detected language: {language.upper()}\n")
        f.write(f"# Sources: {', '.join(sources)}\n")
        f.write("# Licensed under the MIT License\n")
        f.write("# =====================================================\n\n")

        # Color definitions
        for color_name, value in COLORS.items():
            f.write(f"{color_name} = {value}\n")
        f.write("\n")

        # Variables
        f.write(f"TARGET = {target}\n")
        f.write(f"CC = {cc_line}\n")
        f.write(f"SOURCES = {' '.join(sources)}\n")
        f.write(f"OBJECTS = {' '.join(objects)}\n\n")

        # For nested directories, we might need to create object directories
        if language in ["c", "c++", "objective-c"]:
            # Create object directories rule
            obj_dirs = set()
            for obj in objects:
                obj_dir = os.path.dirname(obj)
                if obj_dir:
                    obj_dirs.add(obj_dir)
            
            if obj_dirs:
                f.write("# Create necessary directories for object files\n")
                f.write("directories:\n")
                for obj_dir in sorted(obj_dirs):
                    f.write(f"\t@mkdir -p {obj_dir}\n")
                f.write("\n")

        # Build rules
        if language in ["c", "c++", "objective-c"]:
            if obj_dirs:
                f.write("$(TARGET): directories $(OBJECTS)\n")
            else:
                f.write("$(TARGET): $(OBJECTS)\n")
            f.write('\t@echo "$(BOLD)$(GREEN)Linking $(TARGET)...$(RESET)"\n')
            f.write("\t$(CC) $(OBJECTS) -o $(TARGET)\n")
        elif language == "go":
            f.write("$(TARGET): $(SOURCES)\n")
            f.write('\t@echo "$(BOLD)$(GREEN)Building Go project...$(RESET)"\n')
            f.write("\t$(CC) -o $(TARGET)\n")
        elif language == "rust":
            if compiler == "cargo":
                f.write("$(TARGET): $(SOURCES)\n")
                f.write('\t@echo "$(BOLD)$(GREEN)Building Rust project with Cargo...$(RESET)"\n')
                f.write("\t$(CC)\n")
                f.write(f"\tcp target/release/{target} .\n")
            else:
                f.write("$(TARGET): $(SOURCES)\n")
                f.write('\t@echo "$(BOLD)$(GREEN)Building Rust project...$(RESET)"\n')
                f.write("\t$(CC) $(SOURCES)\n")
        f.write('\t@echo "$(BOLD)$(CYAN)✓ Successfully built $(TARGET)$(RESET)"\n\n')

        # Object rules for C/C++/ObjC
        if language in ["c", "c++", "objective-c"]:
            for src in sources:
                obj = src.rsplit('.', 1)[0] + ".o"
                f.write(f"{obj}: {src}\n")
                f.write(f'\t@echo "$(BOLD)$(YELLOW)Compiling {src}...$(RESET)"\n')
                # Create directory for object file if it doesn't exist
                obj_dir = os.path.dirname(obj)
                if obj_dir:
                    f.write(f"\t@mkdir -p {obj_dir}\n")
                f.write(f"\t$(CC) -c {src} -o {obj}\n")
                f.write(f'\t@echo "$(GREEN)✓ Compiled {obj}$(RESET)"\n\n')

        # Clean
        f.write("clean:\n")
        f.write('\t@echo "$(BOLD)$(RED)Cleaning up...$(RESET)"\n')
        if language in ["c", "c++", "objective-c"]:
            f.write("\trm -f $(TARGET) $(OBJECTS)\n")
        elif language == "go":
            f.write("\trm -f $(TARGET)\n")
        elif language == "rust":
            if compiler == "cargo":
                f.write("\tcargo clean\n")
                f.write("\trm -f $(TARGET)\n")
            else:
                f.write("\trm -f $(TARGET) $(OBJECTS)\n")
        f.write('\t@echo "$(CYAN)✓ Clean complete$(RESET)"\n\n')

        # Help
        f.write("help:\n")
        f.write('\t@echo "$(BOLD)$(MAGENTA)Available targets:$(RESET)"\n')
        f.write('\t@echo "  $(YELLOW)$(TARGET)$(RESET) - Build the main executable"\n')
        f.write('\t@echo "  $(YELLOW)clean$(RESET) - Remove all built files"\n')
        f.write('\t@echo "  $(YELLOW)help$(RESET)  - Show this help message"\n\n')

        f.write(".DEFAULT_GOAL := help\n")
        if language in ["c", "c++", "objective-c"] and obj_dirs:
            f.write(".PHONY: clean help directories\n")
        else:
            f.write(".PHONY: clean help\n")

if __name__ == "__main__":
    language, sources, objects = detect_language_and_sources()

    if language == "unknown":
        print("Error: No supported source files found.")
        print("Supported languages: C (.c), C++ (.cpp, .cxx, .cc, .C), Objective-C (.m, .mm), Go (.go), Rust (.rs or Cargo.toml)")
        exit(1)

    print(f"Detected {language} project with {len(sources)} source files:")
    for src in sources:
        print(f"  - {src}")
    print()

    generate_makefile(language, sources, objects)
    if args.magic:
        mains = detect_main_file(sources)
        if len(mains) == 0:
            print("No main() found, falling back to a.out")
            target = "a.out"
        elif len(mains) == 1:
            target = os.path.splitext(os.path.basename(mains[0]))[0]
            print(f"Magic mode: found main() in {mains[0]}")
            print(f"Target set to: {target}")
        else:
            print("Multiple files with main() detected:")
            for i, m in enumerate(mains, 1):
                print(f"  {i}. {m}")
            choice = input("Choose which to use: ")
            try:
                idx = int(choice) - 1
                target = os.path.splitext(os.path.basename(mains[idx]))[0]
            except:
                target = "a.out"
                print("Invalid choice, defaulting to a.out")
    else:
        target = input("Enter the target executable name (default: a.out): ") or "a.out"

    print(f"Final target: {target}")
    # 🔮 generate makefile here using `sources` + `target`

if __name__ == "__main__":
    main()
        return "rust", ["Cargo.toml"], ["target/release/*"]
    elif glob.glob("**/*.rs", recursive=True):
        sources = glob.glob("**/*.rs", recursive=True)
        objects = [f.replace('.rs', '') for f in sources]
        return "rust", sources, objects
    else:
        return "unknown", [], []

def generate_makefile(language, sources, objects):
    """Generate Makefile based on detected language with interactive input"""
    
    # --- Interactive prompts ---
    target = input("Enter the target executable name (default: a.out): ").strip()
    if not target:
        target = "a.out"

    compiler_with_flags = input("Enter compiler and flags (leave empty for default): ").strip()
    parts = compiler_with_flags.split()
    compiler = parts[0] if parts else None
    flags = parts[1:] if len(parts) > 1 else []

    # Language-specific defaults if user didn't provide any
    if not compiler:
        if language == "c":
            compiler = "gcc"
            flags = ["-Wall", "-Wextra"]
        elif language == "c++":
            compiler = "g++"
            flags = ["-Wall", "-Wextra", "-std=c++17"]
        elif language == "objective-c":
            compiler = "clang"
            flags = ["-Wall", "-Wextra", "-framework", "Foundation"]
        elif language == "go":
            compiler = "go"
            flags = ["build"]
        elif language == "rust":
            if glob.glob("**/Cargo.toml", recursive=True):
                compiler = "cargo"
                flags = ["build", "--release"]
            else:
                compiler = "rustc"
                flags = ["-o", target]

    cc_line = " ".join([compiler] + flags)

    # --- Color codes ---
    COLORS = {
        'GREEN': '\033[92m',
        'BLUE': '\033[94m',
        'YELLOW': '\033[93m',
        'RED': '\033[91m',
        'CYAN': '\033[96m',
        'MAGENTA': '\033[95m',
        'BOLD': '\033[1m',
        'RESET': '\033[0m'
    }

    # --- Write Makefile ---
    with open("makefile", "w") as f:
        # Header
        f.write("# =====================================================\n")
        f.write("# Auto-generated Makefile by main.py\n")
        f.write(f"# Generated on: {datetime.now().isoformat()}\n")
        f.write(f"# Detected language: {language.upper()}\n")
        f.write(f"# Sources: {', '.join(sources)}\n")
        f.write("# Licensed under the MIT License\n")
        f.write("# =====================================================\n\n")

        # Color definitions
        for color_name, value in COLORS.items():
            f.write(f"{color_name} = {value.replace(chr(27),'\\033')}\n")
        f.write("\n")

        # Variables
        f.write(f"TARGET = {target}\n")
        f.write(f"CC = {cc_line}\n")
        f.write(f"SOURCES = {' '.join(sources)}\n")
        f.write(f"OBJECTS = {' '.join(objects)}\n\n")

        # For nested directories, we might need to create object directories
        if language in ["c", "c++", "objective-c"]:
            # Create object directories rule
            obj_dirs = set()
            for obj in objects:
                obj_dir = os.path.dirname(obj)
                if obj_dir:
                    obj_dirs.add(obj_dir)
            
            if obj_dirs:
                f.write("# Create necessary directories for object files\n")
                f.write("directories:\n")
                for obj_dir in sorted(obj_dirs):
                    f.write(f"\t@mkdir -p {obj_dir}\n")
                f.write("\n")

        # Build rules
        if language in ["c", "c++", "objective-c"]:
            if obj_dirs:
                f.write("$(TARGET): directories $(OBJECTS)\n")
            else:
                f.write("$(TARGET): $(OBJECTS)\n")
            f.write('\t@echo "$(BOLD)$(GREEN)Linking $(TARGET)...$(RESET)"\n')
            f.write("\t$(CC) $(OBJECTS) -o $(TARGET)\n")
        elif language == "go":
            f.write("$(TARGET): $(SOURCES)\n")
            f.write('\t@echo "$(BOLD)$(GREEN)Building Go project...$(RESET)"\n')
            f.write("\t$(CC) -o $(TARGET)\n")
        elif language == "rust":
            if compiler == "cargo":
                f.write("$(TARGET): $(SOURCES)\n")
                f.write('\t@echo "$(BOLD)$(GREEN)Building Rust project with Cargo...$(RESET)"\n')
                f.write("\t$(CC)\n")
                f.write(f"\tcp target/release/{target} .\n")
            else:
                f.write("$(TARGET): $(SOURCES)\n")
                f.write('\t@echo "$(BOLD)$(GREEN)Building Rust project...$(RESET)"\n')
                f.write("\t$(CC) $(SOURCES)\n")
        f.write('\t@echo "$(BOLD)$(CYAN)✓ Successfully built $(TARGET)$(RESET)"\n\n')

        # Object rules for C/C++/ObjC
        if language in ["c", "c++", "objective-c"]:
            for src in sources:
                obj = src.rsplit('.', 1)[0] + ".o"
                f.write(f"{obj}: {src}\n")
                f.write(f'\t@echo "$(BOLD)$(YELLOW)Compiling {src}...$(RESET)"\n')
                # Create directory for object file if it doesn't exist
                obj_dir = os.path.dirname(obj)
                if obj_dir:
                    f.write(f"\t@mkdir -p {obj_dir}\n")
                f.write(f"\t$(CC) -c {src} -o {obj}\n")
                f.write(f'\t@echo "$(GREEN)✓ Compiled {obj}$(RESET)"\n\n')

        # Clean
        f.write("clean:\n")
        f.write('\t@echo "$(BOLD)$(RED)Cleaning up...$(RESET)"\n')
        if language in ["c", "c++", "objective-c"]:
            f.write("\trm -f $(TARGET) $(OBJECTS)\n")
        elif language == "go":
            f.write("\trm -f $(TARGET)\n")
        elif language == "rust":
            if compiler == "cargo":
                f.write("\tcargo clean\n")
                f.write("\trm -f $(TARGET)\n")
            else:
                f.write("\trm -f $(TARGET) $(OBJECTS)\n")
        f.write('\t@echo "$(CYAN)✓ Clean complete$(RESET)"\n\n')

        # Help
        f.write("help:\n")
        f.write('\t@echo "$(BOLD)$(MAGENTA)Available targets:$(RESET)"\n')
        f.write('\t@echo "  $(YELLOW)$(TARGET)$(RESET) - Build the main executable"\n')
        f.write('\t@echo "  $(YELLOW)clean$(RESET) - Remove all built files"\n')
        f.write('\t@echo "  $(YELLOW)help$(RESET)  - Show this help message"\n\n')

        f.write(".DEFAULT_GOAL := help\n")
        if language in ["c", "c++", "objective-c"] and obj_dirs:
            f.write(".PHONY: clean help directories\n")
        else:
            f.write(".PHONY: clean help\n")

if __name__ == "__main__":
    language, sources, objects = detect_language_and_sources()

    if language == "unknown":
        print("Error: No supported source files found.")
        print("Supported languages: C (.c), C++ (.cpp, .cxx, .cc, .C), Objective-C (.m, .mm), Go (.go), Rust (.rs or Cargo.toml)")
        exit(1)

    print(f"Detected {language} project with {len(sources)} source files:")
    for src in sources:
        print(f"  - {src}")
    print()

    generate_makefile(language, sources, objects)
