import azure.functions as func
import logging
import os
import time
import statistics

from sqlalchemy import create_engine, text

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_categoria_produto_sqlalchemy(timer: func.TimerRequest) -> None:
    server = os.getenv("SQL_SERVER_SOURCE")
    database = os.getenv("SQL_DATABASE_SOURCE")
    user = os.getenv("SQL_USER_SOURCE")
    password = os.getenv("SQL_PASSWORD_SOURCE")

    logging.info(f"Server: {server}, Database: {database}, User: {user}, Password: {password}")

    conn_str = (
        f"mssql+pyodbc://{user}:{password}@{server}/{database}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
    )

    tempos = []

    try:
        engine = create_engine(conn_str)

        for i in range(2):
            inicio = time.perf_counter()

            with engine.connect() as conn:
                query = text("SELECT * FROM erp.categoria_produto")
                result = conn.execute(query)
                rows = result.fetchall()

            fim = time.perf_counter()
            tempo = fim - inicio
            tempos.append(tempo)

            logging.info(f"[SQLAlchemy] Execução {i+1}: {tempo:.4f}s")
            logging.info(f"[SQLAlchemy] Total linhas: {len(rows)}")

        media = statistics.mean(tempos)

        logging.info(f"[SQLAlchemy] Média final: {media:.4f}s")
    except Exception as e:
        logging.error(f"Erro ao ler erp.categoria_produto: {str(e)}")
        raise