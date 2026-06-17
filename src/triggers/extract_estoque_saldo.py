import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_estoque_saldo(timer: func.TimerRequest) -> None:
    source_conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('SQL_SERVER_SOURCE')};"
        f"DATABASE={os.getenv('SQL_DATABASE_SOURCE')};"
        f"UID={os.getenv('SQL_USER_SOURCE')};"
        f"PWD={os.getenv('SQL_PASSWORD_SOURCE')};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    dest_conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('SQL_SERVER_DEST')};"
        f"DATABASE={os.getenv('SQL_DATABASE_DEST')};"
        f"UID={os.getenv('SQL_USER_DEST')};"
        f"PWD={os.getenv('SQL_PASSWORD_DEST')};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    try:
        with pyodbc.connect(source_conn_str) as source_conn:
            source_cursor = source_conn.cursor()

            source_cursor.execute("""
                SELECT id_estoque_saldo,
                       id_produto,
                       dt_referencia,
                       qt_saldo,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.estoque_saldo
            """)

            registros = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.estoque_saldo OFF")

            for item in registros:
                dest_cursor.execute("""
                MERGE dbo.estoque_saldo AS target
                USING (
                    SELECT ? AS id_estoque_saldo,
                           ? AS id_produto,
                           ? AS dt_referencia,
                           ? AS qt_saldo,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.id_estoque_saldo = source.id_estoque_saldo
                WHEN MATCHED THEN
                    UPDATE SET
                        id_produto         = source.id_produto,
                        dt_referencia      = source.dt_referencia,
                        qt_saldo           = source.qt_saldo,
                        nm_sistema_origem  = source.nm_sistema_origem,
                        cd_registro_origem = source.cd_registro_origem,
                        dt_atualizacao     = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        id_produto,
                        dt_referencia,
                        qt_saldo,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.id_produto,
                        source.dt_referencia,
                        source.qt_saldo,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                item.id_estoque_saldo,
                item.id_produto,
                item.dt_referencia,
                item.qt_saldo,
                item.nm_sistema_origem,
                item.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.estoque_saldo ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.estoque_saldo: {str(e)}")
        raise