#!/bin/bash

INPUT_DIR="/app/input"
OUTPUT_DIR="/app/output"

# Process each PDF
for pdf_file in "$INPUT_DIR"/*.pdf; do
    if [ -f "$pdf_file" ]; then
        filename=$(basename "$pdf_file" .pdf)
        output_json="$OUTPUT_DIR/$filename.json"
        
        echo "Processing: $(basename "$pdf_file")"
        
        # Use absolute path to Python script in container
        python3 /app/extract_outline.py "$pdf_file" "$output_json"
        
        if [ -f "$output_json" ]; then
            echo "Saved to: $output_json"
            # Verify JSON is not empty
            if [ ! -s "$output_json" ]; then
                echo "Warning: Empty JSON output!"
            fi
        else
            echo "Error: Failed to process $pdf_file"
        fi
        echo "------------------------"
    fi
done
