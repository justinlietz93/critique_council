# LaTeX Configuration Guide

This document explains how to configure and use the LaTeX PDF generation functionality in the Critique Council application.

## Overview

The LaTeX module allows the application to generate PDF documents from critique reports and peer reviews. It uses external LaTeX engines (like pdflatex) to compile the documents.

As of the latest update, the configuration has been centralized in the `config.yaml` file at the project root, making it easier to customize all aspects of the system without code changes. The system now has improved support for MiKTeX 25.3 and better detection of LaTeX installations in virtual environments.

> **Quick Start**: For a concise guide to get started quickly, see [LaTeX QuickStart Guide](./latex_quickstart.md).

## Configuration

### Basic Settings

The LaTeX configuration is under the `latex` section in `config.yaml`:

```yaml
latex:
  # Output settings
  output_dir: "latex_output"
  output_filename: "critique_report"
  compile_pdf: true  # Set to true to compile PDF with LaTeX
  keep_tex: true     # Keep .tex files after PDF compilation
  
  # LaTeX compilation settings
  latex_engine: "pdflatex"
  latex_args: ["-interaction=nonstopmode", "-halt-on-error"]
  bibtex_run: true
  latex_runs: 2  # Number of LaTeX compilation passes
```

### MiKTeX Configuration

If you're using MiKTeX on Windows, additional settings are available:

```yaml
latex:
  # ... other settings ...
  
  # MiKTeX configuration (Windows-specific)
  miktex:
    # Set a custom MiKTeX path if LaTeX isn't found in PATH
    # Leave empty to use automatic detection
    custom_path: ""
    
    # Additional search paths for MiKTeX, beyond the default search locations
    additional_search_paths: []
```

If LaTeX is not automatically found in your PATH, you can set a custom path:

```yaml
miktex:
  custom_path: "C:/Program Files/MiKTeX 25.3/miktex/bin/x64"
```

## Command-Line Interface

The LaTeX functionality can be controlled via command-line arguments, which override the settings in `config.yaml`:

- `--latex`: Enable LaTeX document generation
- `--latex-compile`: Compile LaTeX document to PDF (requires LaTeX installation)
- `--latex-output-dir`: Directory for LaTeX output files
- `--latex-scientific-level`: Level of scientific objectivity (low, medium, high)

Example:
```
python run_critique.py --latex --latex-compile input.txt
```

## Troubleshooting

### Testing LaTeX Configuration

To test if LaTeX is properly configured, run the test script:

```
python test_latex_config.py
```

This script will:
1. Load the LaTeX configuration from YAML
2. Initialize the LaTeX compiler
3. Search for a LaTeX installation
4. Report if LaTeX is available and which engine will be used

### Common Issues

1. **LaTeX engine not found**: If LaTeX is installed but not found, ensure it's in your system PATH or set a custom path in `config.yaml`.

2. **PDF compilation fails**: Check the LaTeX logs for detailed error messages. They will be displayed in the console output.

3. **Compilation succeeds but PDF not generated**: Make sure the `compile_pdf` setting is `true` in `config.yaml` or use the `--latex-compile` flag.

### LaTeX Environment Variables

If you're using LaTeX within a Python virtual environment, make sure that the PATH environment variable from the system is properly inherited. On Windows, you might need to add the MiKTeX bin directory to the PATH of your virtual environment.

## Sample Configuration

Here's a complete sample configuration:

```yaml
latex:
  # Document settings
  document_class: "article"
  document_options: ["12pt", "a4paper"]
  title: "Critique Council Report"
  use_hyperref: true
  
  # Template settings
  template_dir: "src/latex/templates"
  main_template: "academic_paper.tex"
  scientific_template: "scientific_paper.tex"
  philosophical_template: "philosophical_paper.tex"
  preamble_template: "preamble.tex"
  bibliography_template: "bibliography.bib"
  
  # Output settings
  output_dir: "latex_output"
  output_filename: "critique_report"
  compile_pdf: true
  keep_tex: true
  
  # LaTeX compilation settings
  latex_engine: "pdflatex"
  latex_args: ["-interaction=nonstopmode", "-halt-on-error"]
  bibtex_run: true
  latex_runs: 2
  
  # MiKTeX configuration (Windows-specific)
  miktex:
    custom_path: "C:/Program Files/MiKTeX 25.3/miktex/bin/x64"
    additional_search_paths: []
