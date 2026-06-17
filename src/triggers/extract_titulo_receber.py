import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_titulo_receber(timer: func.TimerRequest) -> None:
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
                SELECT id_titulo_receber,
                       nr_titulo,
                       id_cliente,
                       id_pedido,
                       dt_emissao,
                       dt_vencimento,
                       dt_pagamento,
                       vl_titulo,
                       vl_recebido,
                       ds_status_titulo,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.titulo_receber
            """)

            titulos = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.titulo_receber OFF")

            for titulo in titulos:
                dest_cursor.execute("""
                MERGE dbo.titulo_receber AS target
                USING (
                    SELECT ? AS id_titulo_receber,
                           ? AS nr_titulo,
                           ? AS id_cliente,
                           ? AS id_pedido,
                           ? AS dt_emissao,
                           ? AS dt_vencimento,
                           ? AS dt_pagamento,
                           ? AS vl_titulo,
                           ? AS vl_recebido,
                           ? AS ds_status_titulo,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.nr_titulo = source.nr_titulo
                WHEN MATCHED THEN
                    UPDATE SET
                        id_cliente         = source.id_cliente,
                        id_pedido          = source.id_pedido,
                        dt_emissao         = source.dt_emissao,
                        dt_vencimento      = source.dt_vencimento,
                        dt_pagamento       = source.dt_pagamento,
                        vl_titulo          = source.vl_titulo,
                        vl_recebido        = source.vl_recebido,
                        ds_status_titulo   = source.ds_status_titulo,
                        nm_sistema_origem  = source.nm_sistema_origem,
                        cd_registro_origem = source.cd_registro_origem,
                        dt_atualizacao     = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        nr_titulo,
                        id_cliente,
                        id_pedido,
                        dt_emissao,
                        dt_vencimento,
                        dt_pagamento,
                        vl_titulo,
                        vl_recebido,
                        ds_status_titulo,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.nr_titulo,
                        source.id_cliente,
                        source.id_pedido,
                        source.dt_emissao,
                        source.dt_vencimento,
                        source.dt_pagamento,
                        source.vl_titulo,
                        source.vl_recebido,
                        source.ds_status_titulo,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                titulo.id_titulo_receber,
                titulo.nr_titulo,
                titulo.id_cliente,
                titulo.id_pedido,
                titulo.dt_emissao,
                titulo.dt_vencimento,
                titulo.dt_pagamento,
                titulo.vl_titulo,
                titulo.vl_recebido,
                titulo.ds_status_titulo,
                titulo.nm_sistema_origem,
                titulo.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.titulo_receber ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.titulo_receber: {str(e)}")
        raise