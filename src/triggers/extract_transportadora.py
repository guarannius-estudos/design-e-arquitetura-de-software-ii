import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_transportadora(timer: func.TimerRequest) -> None:
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
                SELECT cd_transportadora,
                       nm_transportadora,
                       nr_cnpj,
                       ds_telefone,
                       fl_ativo,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.transportadora
            """)

            registros = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()
            
            dest_cursor.execute("SET IDENTITY_INSERT dbo.transportadora OFF")

            for item in registros:
                dest_cursor.execute("""
                MERGE dbo.transportadora AS target
                USING (
                    SELECT ? AS cd_transportadora,
                           ? AS nm_transportadora,
                           ? AS nr_cnpj,
                           ? AS ds_telefone,
                           ? AS fl_ativo,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.cd_transportadora = source.cd_transportadora
                WHEN MATCHED THEN
                    UPDATE SET
                        nm_transportadora  = source.nm_transportadora,
                        nr_cnpj            = source.nr_cnpj,
                        ds_telefone        = source.ds_telefone,
                        fl_ativo           = source.fl_ativo,
                        nm_sistema_origem  = source.nm_sistema_origem,
                        cd_registro_origem = source.cd_registro_origem,
                        dt_atualizacao     = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        cd_transportadora,
                        nm_transportadora,
                        nr_cnpj,
                        ds_telefone,
                        fl_ativo,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.cd_transportadora,
                        source.nm_transportadora,
                        source.nr_cnpj,
                        source.ds_telefone,
                        source.fl_ativo,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                item.cd_transportadora,
                item.nm_transportadora,
                item.nr_cnpj,
                item.ds_telefone,
                item.fl_ativo,
                item.nm_sistema_origem,
                item.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.transportadora ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.transportadora: {str(e)}")
        raise