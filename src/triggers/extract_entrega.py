import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_entrega(timer: func.TimerRequest) -> None:
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
                SELECT id_entrega,
                       id_pedido,
                       id_transportadora,
                       id_regiao,
                       dt_prometida,
                       dt_entrega,
                       ds_status_entrega,
                       cd_rastreio,
                       ds_observacao,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.entrega
            """)

            entregas = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.entrega OFF")

            for entrega in entregas:
                dest_cursor.execute("""
                MERGE dbo.entrega AS target
                USING (
                    SELECT ? AS id_entrega,
                           ? AS id_pedido,
                           ? AS id_transportadora,
                           ? AS id_regiao,
                           ? AS dt_prometida,
                           ? AS dt_entrega,
                           ? AS ds_status_entrega,
                           ? AS cd_rastreio,
                           ? AS ds_observacao,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.id_entrega = source.id_entrega
                WHEN MATCHED THEN
                    UPDATE SET
                        id_pedido          = source.id_pedido,
                        id_transportadora  = source.id_transportadora,
                        id_regiao          = source.id_regiao,
                        dt_prometida       = source.dt_prometida,
                        dt_entrega         = source.dt_entrega,
                        ds_status_entrega  = source.ds_status_entrega,
                        cd_rastreio        = source.cd_rastreio,
                        ds_observacao      = source.ds_observacao,
                        nm_sistema_origem  = source.nm_sistema_origem,
                        cd_registro_origem = source.cd_registro_origem,
                        dt_atualizacao     = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        id_pedido,
                        id_transportadora,
                        id_regiao,
                        dt_prometida,
                        dt_entrega,
                        ds_status_entrega,
                        cd_rastreio,
                        ds_observacao,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.id_pedido,
                        source.id_transportadora,
                        source.id_regiao,
                        source.dt_prometida,
                        source.dt_entrega,
                        source.ds_status_entrega,
                        source.cd_rastreio,
                        source.ds_observacao,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                entrega.id_entrega,
                entrega.id_pedido,
                entrega.id_transportadora,
                entrega.id_regiao,
                entrega.dt_prometida,
                entrega.dt_entrega,
                entrega.ds_status_entrega,
                entrega.cd_rastreio,
                entrega.ds_observacao,
                entrega.nm_sistema_origem,
                entrega.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.entrega ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.entrega: {str(e)}")
        raise