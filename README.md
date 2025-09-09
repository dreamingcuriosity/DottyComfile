# Makefile-generator
Makefile generator useful if you want to write makefiles way faster, the format is super short and flexible for beginners upto intermediate developers
# How to use
Create a file named makethemake.txt, write the project name at line 1, on line 2 write the object files to compile separated by spaces, on line 3 write the compiler name with the flags and project name, on line 4 just leave it blank and create a new line as line 5 (IMPORTANT), in line 5 upto any line after that, write the object files, example:
header
main.o string.o
gcc -o header

main.c
string.c

After you create the file run the python file and compile the files using make (simple right? ) 
