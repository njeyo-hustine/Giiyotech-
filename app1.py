import calendar
import html
from datetime import date, datetime
import pandas as pd
import streamlit as st

from database import (
    initialize_database,
    seed_demo_data,
    add_expense,
    get_expenses,
    get_expense_programmes,
    get_expense_total,
    get_spending_by_programme,
    add_inventory,
    get_inventory,
    get_inventory_item,
    update_inventory,
    delete_inventory,
    get_inventory_count,
    get_attention_items,
)

st.set_page_config(
    page_title="Giiyo Tech Operations Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_database()

# Styling
st.markdown("""
<style>
    .stApp {
        background: #f6f8fb;
    }

    [data-testid="stSidebar"] {
        background: #10233f;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    .brand {
        padding: 6px 0 18px 0;
    }

    .brand-title {
        font-size: 1.55rem;
        font-weight: 800;
        margin: 0;
    }

    .brand-subtitle {
        color: #b9c8dc;
        font-size: .9rem;
        margin-top: 3px;
    }

    .hero {
        background: linear-gradient(135deg, #10233f 0%, #1c4d75 100%);
        padding: 28px 32px;
        border-radius: 18px;
        color: white;
        margin-bottom: 22px;
    }

    .hero h1 {
        margin: 0 0 6px 0;
        font-size: 2rem;
    }

    .hero p {
        margin: 0;
        color: #dce8f5;
    }

    .section-title {
        font-size: 1.45rem;
        font-weight: 750;
        color: #10233f;
        margin: 8px 0 14px 0;
    }

    .metric-note {
        color: #637083;
        font-size: .85rem;
    }

    .attention {
        border-left: 5px solid #d97706;
        background: #fff7ed;
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 8px;
    }

    .good {
        border-left: 5px solid #15803d;
        background: #f0fdf4;
        padding: 12px 15px;
        border-radius: 8px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5eaf0;
        padding: 14px;
        border-radius: 14px;
    }

    .small-muted {
        color: #68778a;
        font-size: .82rem;
    }
</style>
""", unsafe_allow_html=True)

# Helpers
def money(value):
    return f"{value:,.0f} FCFA"


def month_options():
    today = date.today()
    options = []
    for year in range(today.year - 2, today.year + 1):
        for month in range(1, 13):
            if (year, month) <= (today.year, today.month):
                options.append(f"{year:04d}-{month:02d}")
    return list(reversed(options))


def month_label(ym):
    year, month = map(int, ym.split("-"))
    return f"{calendar.month_name[month]} {year}"


def inventory_dataframe(rows):
    data = []
    for row in rows:
        data.append({
            "ID": row["id"],
            "Item": row["item_name"],
            "Qty": row["quantity"],
            "Programme / Purpose": row["programme"],
            "Location": row["location"],
            "Responsible": row["responsible_person"] or "",
            "Condition": row["condition"],
            "Notes": row["notes"] or "",
        })
    return pd.DataFrame(data)


def flash(message):
    st.session_state["flash"] = message


def show_flash():
    message = st.session_state.pop("flash", None)
    if message:
        st.success(message)


# Sidebar
with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-title">GIiYO TECH</div>
        <div class="brand-subtitle">Operations Tracker</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Dashboard", "Expenses", "Inventory"],
        index=0,
    )

    st.divider()

    if st.button("Load Demo Data", use_container_width=True):
        seed_demo_data()
        flash("Demo data is ready.")
        st.rerun()


# Dashboard
show_flash()

if page == "Dashboard":
    st.markdown("""
    <div class="hero">
        <h1>Operations Dashboard</h1>
        <p>A simple overview of spending and inventory that needs attention.</p>
    </div>
    """, unsafe_allow_html=True)

    selected_month = st.selectbox(
        "Dashboard month",
        month_options(),
        format_func=month_label,
    )

    total_spending = get_expense_total(selected_month)
    inventory_count = get_inventory_count()
    attention = get_attention_items()
    spending_rows = get_spending_by_programme(selected_month)

    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly spending", money(total_spending))
    c2.metric("Inventory records", inventory_count)
    c3.metric("Needs attention", len(attention))

    st.divider()

    left, right = st.columns([1.15, 1])

    with left:
        st.markdown(
            f'<div class="section-title">Spending by programme — {month_label(selected_month)}</div>',
            unsafe_allow_html=True,
        )

        if spending_rows:
            spending_df = pd.DataFrame([
                {"Programme / Purpose": r["programme"], "Amount": r["total"]}
                for r in spending_rows
            ])
            st.bar_chart(
                spending_df.set_index("Programme / Purpose"),
                y="Amount",
            )
            st.dataframe(
                spending_df.assign(Amount=spending_df["Amount"].map(money)),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No spending has been recorded for this month.")

    with right:
        st.markdown(
            '<div class="section-title">Items needing attention</div>',
            unsafe_allow_html=True,
        )

        if attention:
            for item in attention[:10]:
                st.markdown(
                    f"""
                    <div class="attention">
                        <strong>{html.escape(item["item_name"])}</strong> — {html.escape(item["condition"])}<br>
                        Quantity: {item["quantity"]} • Location: {html.escape(item["location"])}<br>
                        <span class="small-muted">{html.escape(item["programme"])}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="good"><strong>Everything looks good.</strong><br>No inventory items currently need attention.</div>',
                unsafe_allow_html=True,
            )

# Expenses
elif page == "Expenses":
    st.markdown("""
    <div class="hero">
        <h1>Expense Tracking</h1>
        <p>Record spending and quickly review what has already been paid.</p>
    </div>
    """, unsafe_allow_html=True)

    add_tab, history_tab = st.tabs(["Add Expense", "Previous Expenses"])

    with add_tab:
        st.markdown('<div class="section-title">Add a new expense</div>', unsafe_allow_html=True)

        with st.form("expense_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            expense_date = c1.date_input("Date", value=date.today())
            amount = c2.number_input(
                "Amount (FCFA)",
                min_value=0.0,
                step=500.0,
                format="%.0f",
            )

            c1, c2 = st.columns(2)
            category = c1.selectbox(
                "Category",
                ["Transport", "Equipment", "Printing", "Communication",
                 "Venue", "Food", "Supplies", "Other"],
            )
            programme = c2.text_input(
                "Programme / Purpose",
                placeholder="e.g. STEM Programme",
            )

            c1, c2 = st.columns(2)
            paid_by = c1.text_input("Who paid?", placeholder="Name")
            payment_method = c2.selectbox(
                "Payment method",
                ["Cash", "Mobile Money", "Bank Transfer", "Card", "Other"],
            )

            notes = st.text_area("Notes", placeholder="Optional details")
            receipt = st.checkbox("Receipt is available")

            submitted = st.form_submit_button(
                "Save Expense",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if not programme.strip():
                    st.error("Please enter the programme or purpose.")
                elif not paid_by.strip():
                    st.error("Please enter who paid.")
                elif amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    add_expense(
                        expense_date.isoformat(),
                        amount,
                        category,
                        programme.strip(),
                        paid_by.strip(),
                        payment_method,
                        notes.strip(),
                        receipt,
                    )
                    flash("Expense saved successfully.")
                    st.rerun()

    with history_tab:
        st.markdown('<div class="section-title">Previous expenses</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        selected_month = c1.selectbox(
            "Filter by month",
            ["All"] + month_options(),
            format_func=lambda x: "All months" if x == "All" else month_label(x),
            key="expense_month_filter",
        )
        programmes = ["All"] + get_expense_programmes()
        selected_programme = c2.selectbox(
            "Filter by programme / purpose",
            programmes,
            key="expense_programme_filter",
        )

        month_filter = None if selected_month == "All" else selected_month
        rows = get_expenses(month_filter, selected_programme)
        total = get_expense_total(month_filter, selected_programme)

        st.metric("Total spending in current filter", money(total))

        if rows:
            df = pd.DataFrame([dict(row) for row in rows])
            df["receipt_available"] = df["receipt_available"].map(
                {0: "No", 1: "Yes"}
            )
            df = df.rename(columns={
                "expense_date": "Date",
                "amount": "Amount (FCFA)",
                "category": "Category",
                "programme": "Programme / Purpose",
                "paid_by": "Paid By",
                "payment_method": "Payment Method",
                "notes": "Notes",
                "receipt_available": "Receipt",
            })
            df = df[
                ["Date", "Amount (FCFA)", "Category",
                 "Programme / Purpose", "Paid By",
                 "Payment Method", "Receipt", "Notes"]
            ]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Amount (FCFA)": st.column_config.NumberColumn(
                        format="%d"
                    )
                },
            )
        else:
            st.info("No expenses match the selected filters.")

# Inventory
elif page == "Inventory":
    st.markdown("""
    <div class="hero">
        <h1>Inventory Tracking</h1>
        <p>Keep a simple record of equipment and materials, where they are, and their condition.</p>
    </div>
    """, unsafe_allow_html=True)

    add_tab, view_tab, edit_tab = st.tabs([
        "Add Item", "Current Inventory", "Edit / Remove"
    ])

    with add_tab:
        st.markdown('<div class="section-title">Add inventory item</div>', unsafe_allow_html=True)

        with st.form("inventory_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            item_name = c1.text_input("Item name", placeholder="e.g. Laptop")
            quantity = c2.number_input("Quantity", min_value=0, step=1)

            c1, c2 = st.columns(2)
            programme = c1.text_input(
                "Programme / Purpose",
                placeholder="e.g. Digital Skills",
            )
            location = c2.text_input(
                "Current location",
                placeholder="e.g. Main Office",
            )

            c1, c2 = st.columns(2)
            responsible = c1.text_input("Responsible person (optional)")
            condition = c2.selectbox(
                "Condition",
                ["Good", "Fair", "Damaged", "Missing", "Low Quantity"],
            )

            notes = st.text_area("Notes", placeholder="Optional details")

            submitted = st.form_submit_button(
                "Save Inventory Item",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if not item_name.strip():
                    st.error("Please enter the item name.")
                elif not programme.strip():
                    st.error("Please enter the programme or purpose.")
                elif not location.strip():
                    st.error("Please enter the current location.")
                else:
                    add_inventory(
                        item_name.strip(),
                        int(quantity),
                        programme.strip(),
                        location.strip(),
                        responsible.strip(),
                        condition,
                        notes.strip(),
                    )
                    flash("Inventory item saved successfully.")
                    st.rerun()

    with view_tab:
        rows = get_inventory()

        if rows:
            df = inventory_dataframe(rows)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No inventory items have been recorded yet.")

    with edit_tab:
        rows = get_inventory()

        if not rows:
            st.info("There are no inventory records to edit.")
        else:
            item_options = {
                f'{row["item_name"]} — ID {row["id"]}': row["id"]
                for row in rows
            }
            selected_label = st.selectbox(
                "Select an inventory item",
                list(item_options.keys()),
            )
            selected_id = item_options[selected_label]
            item = get_inventory_item(selected_id)

            st.markdown('<div class="section-title">Edit inventory item</div>', unsafe_allow_html=True)

            with st.form("edit_inventory_form"):
                c1, c2 = st.columns(2)
                edit_name = c1.text_input("Item name", value=item["item_name"])
                edit_quantity = c2.number_input(
                    "Quantity",
                    min_value=0,
                    step=1,
                    value=int(item["quantity"]),
                )

                c1, c2 = st.columns(2)
                edit_programme = c1.text_input(
                    "Programme / Purpose",
                    value=item["programme"],
                )
                edit_location = c2.text_input(
                    "Current location",
                    value=item["location"],
                )

                c1, c2 = st.columns(2)
                edit_responsible = c1.text_input(
                    "Responsible person",
                    value=item["responsible_person"] or "",
                )
                conditions = ["Good", "Fair", "Damaged", "Missing", "Low Quantity"]
                edit_condition = c2.selectbox(
                    "Condition",
                    conditions,
                    index=conditions.index(item["condition"])
                    if item["condition"] in conditions else 0,
                )

                edit_notes = st.text_area(
                    "Notes",
                    value=item["notes"] or "",
                )

                save_changes = st.form_submit_button(
                    "Save Changes",
                    type="primary",
                )

                if save_changes:
                    if not edit_name.strip() or not edit_programme.strip() or not edit_location.strip():
                        st.error("Item name, programme/purpose, and location are required.")
                    else:
                        update_inventory(
                            selected_id,
                            edit_name.strip(),
                            int(edit_quantity),
                            edit_programme.strip(),
                            edit_location.strip(),
                            edit_responsible.strip(),
                            edit_condition,
                            edit_notes.strip(),
                        )
                        flash("Inventory record updated.")
                        st.rerun()

            st.divider()

            st.warning(
                "Deleting an inventory record permanently removes it from the database."
            )
            if st.button("Delete Selected Inventory Record", type="secondary"):
                st.session_state["confirm_delete"] = selected_id

            if st.session_state.get("confirm_delete") == selected_id:
                st.error("Are you sure you want to delete this record?")
                c1, c2 = st.columns(2)
                if c1.button("Yes, delete it", type="primary"):
                    delete_inventory(selected_id)
                    st.session_state.pop("confirm_delete", None)
                    flash("Inventory record deleted.")
                    st.rerun()
                if c2.button("Cancel"):
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()
