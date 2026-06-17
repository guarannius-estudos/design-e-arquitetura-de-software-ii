import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_regiao(timer: func.TimerRequest) -> None:
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
                SELECT cd_regiao,
                       nm_regiao,
                       sg_uf,
                       nm_cidade,
                       fl_ativo,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.regiao
            """)

            registros = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.regiao OFF")

            for item in registros:
                dest_cursor.execute("""
                MERGE dbo.regiao AS target
                USING (
                    SELECT ? AS cd_regiao,
                           ? AS nm_regiao,
                           ? AS sg_uf,
                           ? AS nm_cidade,
                           ? AS fl_ativo,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.cd_regiao = source.cd_regiao
                WHEN MATCHED THEN
                    UPDATE SET
                        nm_regiao          = source.nm_regiao,
                        sg_uf              = source.sg_uf,
                        nm_cidade          = source.nm_cidade,
                        fl_ativo           = source.fl_ativo,
                        nm_sistema_origem  = source.nm_sistema_origem,
                        cd_registro_origem = source.cd_registro_origem,
                        dt_atualizacao     = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        cd_regiao,
                        nm_regiao,
                        sg_uf,
                        nm_cidade,
                        fl_ativo,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.cd_regiao,
                        source.nm_regiao,
                        source.sg_uf,
                        source.nm_cidade,
                        source.fl_ativo,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                item.cd_regiao,
                item.nm_regiao,
                item.sg_uf,
                item.nm_cidade,
                item.fl_ativo,
                item.nm_sistema_origem,
                item.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.regiao ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.regiao: {str(e)}")
        raise