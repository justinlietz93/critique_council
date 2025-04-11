
# LaTeX PDF Generation QuickStart Guide

This guide provides a quick overview of how to use the LaTeX PDF generation feature.

## Prerequisites

- Python 3.8+ with required packages (`pip install -r requirements.txt`)
- LaTeX installation (MiKTeX on Windows recommended)
- Virtual environment activated (if using one)

## Verifying Your LaTeX Installation

Run the test script to verify LaTeX detection:

```bash
python test_latex_config.py
```

This should show that LaTeX is available in your environment.

## Basic Usage

### Step 1: Configure LaTeX Settings (Optional)

The system uses default settings from `config.yaml`. If your LaTeX installation isn't being detected automatically, edit the MiKTeX section:

```yaml
# In config.yaml
latex:
  # ...
  miktex:
    custom_path: "C:/path/to/your/miktex/bin/directory"
```

### Step 2: Run the Analysis with PDF Generation

```bash
python run_critique.py content.txt --latex --latex-compile
```

This will:
1. Analyze `content.txt`
2. Generate a critique report
3. Create a LaTeX document
4. Compile it to PDF

### Step 3: Check the Output

- The critique report is saved in `critiques/`
- LaTeX files and PDF are saved in `latex_output/` (or your custom directory)

## Common Command Options

| Option | Description |
|--------|-------------|
| `--latex` | Enable LaTeX document generation |
| `--latex-compile` | Compile LaTeX document to PDF |
| `--PR` | Enable Peer Review mode |
| `--scientific` | Use scientific methodology |
| `--latex-output-dir DIR` | Specify output directory |

## Complete Example

For a full scientific analysis with peer review and PDF output:

```bash
python run_critique.py content.txt --scientific --PR --latex --latex-compile
```

## Troubleshooting

- **PDF not generated**: Ensure LaTeX is in your PATH or set a custom path in `config.yaml`
- **Compilation errors**: Check log output for LaTeX errors
- **Path issues**: For virtual environments, ensure LaTeX bin directory is in the environment's PATH

For detailed configuration, see `docs/latex_configuration.md`.
