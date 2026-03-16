from pathlib import Path
from utils.db import fetch_df

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

def export_results_excel(subject=None):
    if subject and subject != "الكل":
        df = fetch_df("SELECT * FROM results WHERE subject=? ORDER BY test_date DESC", (subject,))
        safe_subject = subject.replace(" ", "_")
        path = EXPORT_DIR / f"results_{safe_subject}.xlsx"
    else:
        df = fetch_df("SELECT * FROM results ORDER BY test_date DESC")
        path = EXPORT_DIR / "results_all.xlsx"

    df.to_excel(path, index=False)
    return str(path)
