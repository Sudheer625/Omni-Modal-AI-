import pandas as pd


def extract_text(xlsx_path: str) -> str:
    sheets = pd.read_excel(xlsx_path, sheet_name=None, engine="openpyxl")
    if not sheets:
        return ""

    parts = []
    for sheet_name, df in sheets.items():
        if df.empty:
            continue
        preview = df.head(200)
        parts.append(f"Sheet: {sheet_name}\n{preview.to_csv(index=False)}")

    return "\n\n".join(parts).strip()
