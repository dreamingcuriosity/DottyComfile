#!/usr/bin/env python3
import os
import re
import argparse

def find_source_files():
    sources = []
    for root, _, files in os.walk("."):
        for f in files:
            if f.endswith(".c"):
                sources.append(os.path.join(root, f))
    return sources

def detect_main_file(sources):
    main_candidates = []
    for src in sources:
        try:
            with open(src, "r", errors="ignore") as f:
                code = f.read()
                if re.search(r"\bint\s+main\s*\(", code):  # naive but works
                    main_candidates.append(src)
        except:
            pass
    return main_candidates

def main():
    parser = argparse.ArgumentParser(description="Auto Makefile generator")
    parser.add_argument("-m", "--magic", action="store_true",
                        help="Autodetect main() and set target name automatically")
    args = parser.parse_args()

    sources = find_source_files()
    print(f"Detected c project with {len(sources)} source files:")
    for s in sources:
        print(f"  - {s}")

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
