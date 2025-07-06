import os, pathlib, pytest, pandas as pd, allure
from connect_alchemy import MySQLConnection   # already in your repo

# trying to connect SQL after merging branch and connect to allure

# -------- DB fixture ---------------------------------------------------------
@pytest.fixture(scope="session")
def db():
    conn = MySQLConnection(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
        port=int(os.getenv("DB_PORT", "3306")),
    )
    assert conn.connect()
    yield conn
    conn.close()

# -------- Parametrise every *.sql in the chosen folder -----------------------
SQL_DIR = pathlib.Path("scripts/sql")        # adjust if you store them elsewhere
@pytest.mark.parametrize("sql_path", SQL_DIR.glob("*.sql"))
def test_run_sql(db, sql_path):
    query = sql_path.read_text()
    out_dir = pathlib.Path("csv_out")
    out_dir.mkdir(exist_ok=True)
    csv_ok = out_dir / f"{sql_path.stem}.csv"
    csv_err = out_dir / f"{sql_path.stem}_error.csv"

    try:
        # reuse your own execute_query helper, returns a DataFrame
        df = db.execute_query(query)        # :contentReference[oaicite:0]{index=0}
        df.to_csv(csv_ok, index=False)
        allure.attach.file(str(csv_ok), name=csv_ok.name,
                           attachment_type=allure.attachment_type.CSV)
    except Exception as exc:
        pd.DataFrame({"error": [str(exc)]}).to_csv(csv_err, index=False)
        allure.attach.file(str(csv_err), name=csv_err.name,
                           attachment_type=allure.attachment_type.CSV)
        pytest.fail(str(exc))
