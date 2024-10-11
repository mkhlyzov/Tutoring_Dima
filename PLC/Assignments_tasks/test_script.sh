#!/bin/bash

# Step 1: Compile the Java source files
echo "Compiling Java files..."
javac ./src/*.java -d bin
if [ $? -ne 0 ]; then
    echo "Compilation failed."
    exit 1
fi
echo "Compilation successful."

# Test cases
declare -a test_cases=(
    "list" 
    "list 3"
    "add OA 1 95 3 4 1898 1080 \"Florianigasse\" 42 20 1.55 0.45"
    "add RA 2 95.0 3 3 1894 1080 \"Lange Gasse\" 15 16 8.75 2"
    "delete 2"
    "count"
    "count RA"
    "meancosts"
    "oldest"
)

# Step 2: Create the test file
test_file="test_apartments.dat"

# Step 3: Execute the test cases
for test_case in "${test_cases[@]}"
do
    echo "Running test case: java PropertyManagementClient $test_file $test_case"
    java -cp bin PropertyManagementClient $test_file $test_case > output.txt
    cat output.txt

    # Optional: Compare output with expected results
    # If you have expected output files, you can use:
    # diff -u expected_output_$test_case.txt output.txt
done

echo "All tests executed."
