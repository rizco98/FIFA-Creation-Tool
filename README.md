# FC25 Squad Editor

A powerful and flexible tool for editing FC 25 squad files. This tool allows you to load and modify any squad file in a user-friendly interface.

## Features

- Load and parse FC 25 squad files (*.File format)
- Support for multiple squad file versions
- View and edit:
  - Countries and national teams
  - Leagues
  - Teams
  - Players
  - Stadiums
  - Tournaments
  - Kits
- Modern and intuitive dark-themed user interface
- Robust error handling and logging
- Save changes back to the squad file

## Requirements

- Python 3.8 or higher
- PyQt6

## Installation

1. Clone or download this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Click "File > Open Squad File" or press Ctrl+O to open any FC 25 squad file
3. Edit the data in the various tabs
4. Click "File > Save" or press Ctrl+S to save your modifications

## Notes

- Always backup your original squad files before making changes
- The tool supports various squad file formats and versions
- Comprehensive error logging helps diagnose any issues
- Make sure you have the necessary permissions to read and write the squad files

## Troubleshooting

If you encounter any issues:
1. Ensure you have all the required dependencies installed
2. Check the log output for detailed error messages
3. Verify that your squad file is in the correct format
4. Check if you have write permissions in the folder where the squad file is located 