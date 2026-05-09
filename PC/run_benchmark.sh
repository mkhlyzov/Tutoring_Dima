#!/bin/bash

# run_benchmark.sh
# Usage: ./run_benchmark.sh [max_threads] [executable_name] [output_file]

MAX_THREADS=${1:-32}
EXECUTABLE=${2:-"./program"}  # Default executable name
OUTPUT_FILE=${3:-"benchmark_data.txt"}

# Check if executable exists
if [ ! -f "$EXECUTABLE" ]; then
    echo "Error: Executable '$EXECUTABLE' not found!"
    exit 1
fi

# Check if executable is executable
if [ ! -x "$EXECUTABLE" ]; then
    echo "Error: '$EXECUTABLE' is not executable!"
    exit 1
fi

# Write header to output file
echo "# Threads Time_seconds" > "$OUTPUT_FILE"
echo "# Benchmark results" >> "$OUTPUT_FILE"
echo "# Generated on: $(date)" >> "$OUTPUT_FILE"
echo "# Command: OMP_NUM_THREADS=N srun --nodes=1 $EXECUTABLE" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Loop through thread counts
for threads in $(seq 1 $MAX_THREADS); do
    echo "Running with $threads threads..."
    
    # Run the program and capture the time
    # The program outputs "time elapsed: X seconds" line
    # We'll extract that line and parse the time
    
    # Run with specified number of threads
    # OUTPUT=$(OMP_NUM_THREADS=$threads srun --nodes=1 "$EXECUTABLE" 2>&1)
    OUTPUT=$(OMP_NUM_THREADS=$threads "$EXECUTABLE" 2>&1)
    
    # Extract the time from the output
    # Looking for pattern: "time elapsed: X seconds" or similar
    TIME=$(echo "$OUTPUT" | grep -oE 'time elapsed: [0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+')
    
    # Check if we successfully extracted the time
    if [ -z "$TIME" ]; then
        echo "Warning: Could not extract time for threads=$threads"
        echo "Output was:"
        echo "$OUTPUT"
        echo "Skipping this run..."
        continue
    fi
    
    # Append to output file
    echo "$threads $TIME" >> "$OUTPUT_FILE"
    
    # Print to console
    echo "  Time: $TIME seconds"
done

echo "Benchmark complete! Data saved to $OUTPUT_FILE"