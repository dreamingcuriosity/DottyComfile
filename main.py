makethemake = []
with open("makeymakey.txt", "r") as a:
    for line in a:
        makethemake.append(line.strip())

target = makethemake[0]
objects = makethemake[1].split()   # split "main.o util.o extra.o" into list
compiler_with_flags = makethemake[2]
sources = makethemake[3:]          # everything else are .c files

with open("makefile", "w") as f:
    # main target rule
    f.write(f"{target}: {' '.join(objects)}\n")
    f.write(f"\t{compiler_with_flags} {' '.join(objects)}\n\n")

    # rules for each source file -> object file
    for src in sources:
        obj = src.replace(".c", ".o")
        f.write(f"{obj}: {src}\n")
        f.write(f"\tgcc -c {src}\n\n")  # Use -c flag for compiling to object files
# clean rule
    f.write("clean:\n")
    f.write(f"\trm -f {target} {' '.join(objects)}\n")
