# GIiYO TECH Operations Tracker

A small internal prototype built for the Giiyo Tech Operations Coordinator task.

## Technology

- Python
- Streamlit
- SQLite
- Pandas

## Main files

- `app.py` - the Streamlit interface (Dashboard, Expenses and Inventory pages).
- `database.py` - all SQLite code: creating tables, adding, editing, deleting and reading records, plus the demo data.
- `requirements.txt` - the packages that need to be installed.
- `giiyo_operations.db` - the local database. It is created automatically the first time the app runs.

## Packages to install

- `streamlit` (the interface)
- `pandas` (tables and charts)

Both are listed in `requirements.txt`. SQLite is built into Python, so nothing extra is needed for it.

## Features

### Dashboard
- Monthly spending
- Spending by programme/purpose
- Inventory record count
- Items needing attention

### Expense Tracking
- Add expenses
- Date, amount, category
- Programme/purpose
- Person who paid
- Payment method
- Notes
- Receipt availability
- Filter by month
- Filter by programme/purpose
- Total spending

### Inventory Tracking
- Add inventory items
- Quantity
- Programme/purpose
- Location
- Responsible person
- Condition
- Notes
- Edit records
- Delete records
- Attention list for damaged, missing, and low-quantity items

## How to run

1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the app:

```bash
streamlit run app.py
```

5. Streamlit will open the application in your browser.

The SQLite database `giiyo_operations.db` is created automatically beside `app.py`.

## Demo data

Use **Load / Reset Demo Data** in the sidebar to insert a small set of example records.

The demo-data function only adds records when the corresponding table is empty; it does not delete existing data.
