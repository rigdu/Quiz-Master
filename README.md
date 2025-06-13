# Quiz Master

A Python Tkinter-based application for hosting quiz competitions, managing teams, scoring, and exporting results.

## Features

- Load quiz questions from an Excel file
- Filter questions by round, type, and sub type
- Track and manage scores for up to 15 teams
- Award/deduct points by round
- Save/load scores as JSON
- Export scores as Excel

## Requirements

- Python 3.x
- pandas
- openpyxl

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python quiz_master.py
```

## Question File Format

Questions should be in an Excel `.xlsx` file with columns:
- **Round**
- **Type**
- **Sub Type**
- **Question**
- **Answer**

## License

MIT
