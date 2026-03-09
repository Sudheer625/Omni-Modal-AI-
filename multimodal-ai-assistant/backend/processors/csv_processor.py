import pandas as pd


def extract_text(csv_path: str) -> str:
    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    # Keep a manageable context size while preserving schema and sample rows.
    preview = df.head(200)
    return preview.to_csv(index=False)
