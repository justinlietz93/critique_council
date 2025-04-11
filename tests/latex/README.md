# LaTeX Generation Tests

This directory contains tests for the LaTeX document generation functionality of the Critique Council system.

## Overview

The test script `test_latex_generation.py` allows you to test the LaTeX generation without running the full critique pipeline. This is useful for debugging and development, especially when working on the bibliography generation and scientific mode integration.

## Usage

You can run the test script with various command-line options:

```bash
# Standard test (philosophical mode) - will attempt to compile PDF if LaTeX is installed
python tests/latex/test_latex_generation.py

# Test scientific mode
python tests/latex/test_latex_generation.py --scientific

# Clean output directory before testing
python tests/latex/test_latex_generation.py --clean

# Specify a different output directory
python tests/latex/test_latex_generation.py --output-dir my_test_output

# Skip PDF compilation (generate only TEX files)
python tests/latex/test_latex_generation.py --no-compile

# Combined options
python tests/latex/test_latex_generation.py --scientific --clean
```

Note: PDF compilation is attempted by default if LaTeX is installed on your system. If LaTeX is not available, the test will only generate the .tex files and print debugging information about why PDF compilation couldn't be performed.

## What the Test Does

1. Generates sample content based on the selected mode (scientific or philosophical)
2. Sets up the LaTeX formatter with appropriate configurations
3. Attempts to generate a LaTeX document
4. Verifies that the bibliography was correctly created
5. Displays snippets of the generated files for inspection
6. Optionally compiles to PDF if requested

## Example Output

```
Testing LaTeX generation (Scientific Mode: True)...
Bibliography file generated: latex_output/bibliography.bib
Bibliography header:
% Bibliography file copied from template on 2025-04-11 11:58:00

...
LaTeX document generated: latex_output/scientific_test_20250411_115820.tex
LaTeX header:
\documentclass[12pt,a4paper]{article}
\usepackage{times}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
...

Test completed successfully!
Generated LaTeX file: latex_output/scientific_test_20250411_115820.tex
```

## Troubleshooting

If the test fails, it will display an error message indicating what went wrong. Common issues include:

- Missing template files
- Issues with file paths
- Problems with LaTeX formatting
- PDF compilation errors

### LaTeX Engine Detection

The system will attempt to compile the LaTeX document into a PDF if a LaTeX engine is available. The search process is:

1. First, it checks if LaTeX engines (pdflatex, pdftex, etc.) are available in your system PATH
2. If not found in PATH, it searches common MiKTeX and TeX Live installation locations:
   - User's AppData directory (for MiKTeX)
   - Program Files directories
   - Standard TeX Live directories

This should work even if you're running from a Git Bash terminal where the PATH variable might not include the LaTeX binaries.

### Other Potential Issues

- Missing template files: Check that `src/latex/templates` directory contains all necessary template files, including `academic_paper.tex`, `preamble.tex`, and `bibliography.bib`.
- If you see "LaTeX engine not available" despite having LaTeX installed, you might need to add the MiKTeX bin path to your PATH environment variable.
