import streamlit as st
import pandas as pd
import os
import pytesseract
from pdf2image import convert_from_path
from recogniser import extract_fields, recognise_supplier, append_to_ledger

INVOICE_FOLDER = "invoices"

st.title("📦 Invoice Capture Engine (Batch Mode)")

supplier_df = pd.read_csv("supplier_db.csv")


def process_invoice(filepath):

    pages = convert_from_path(filepath)
    text = pytesseract.image_to_string(pages[0])

    fields = extract_fields(text)
    sup_id, sup_name, gl_code = recognise_supplier(text, supplier_df)

    record = {
        "supplier_id": sup_id,
        "supplier": sup_name,
        "invoice_no": fields["invoice_no"],
        "vat": fields["vat"],
        "gross": fields["gross"],
        "gl_code": gl_code,
        "source_file": os.path.basename(filepath)
    }

    append_to_ledger(record)

    return record


# -----------------------
# UI
# -----------------------

if st.button("🚀 Process All Invoices"):

    files = [f for f in os.listdir(INVOICE_FOLDER) if f.endswith(".pdf")]

    results = []

    progress = st.progress(0)

    for i, file in enumerate(files):
        path = os.path.join(INVOICE_FOLDER, file)
        results.append(process_invoice(path))
        progress.progress((i + 1) / len(files))

    df = pd.DataFrame(results)

    st.success(f"{len(results)} invoices processed!")

    st.subheader("Captured Records")
    st.dataframe(df)

    approved = (df["supplier_id"] != "UNKNOWN").sum()

    st.metric("Recognition Rate", f"{approved/len(df):.1%}")
