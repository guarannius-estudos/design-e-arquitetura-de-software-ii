import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_pedido(timer: func.TimerRequest) -> None:
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
                SELECT id_pedido,
                       nr_pedido,
                       id_cliente,
                       id_representante,
                       id_regiao,
                       dt_emissao,
                       dt_faturamento,
                       ds_status_pedido,
                       vl_bruto,
                       vl_desconto,
                       vl_liquido,
                       ds_observacao,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.pedido
            """)

            pedidos = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.pedido OFF")

            for pedido in pedidos:
                dest_cursor.execute("""
                MERGE dbo.pedido AS target
                USING (
                    SELECT ? AS id_pedido,
                           ? AS nr_pedido,
                           ? AS id_cliente,
                           ? AS id_representante,
                           ? AS id_regiao,
                           ? AS dt_emissao,
                           ? AS dt_faturamento,
                           ? AS ds_status_pedido,
                           ? AS vl_bruto,
                           ? AS vl_desconto,
                           ? AS vl_liquido,
                           ? AS ds_observacao,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.nr_pedido = source.nr_pedido
                WHEN MATCHED THEN
                    UPDATE SET
                        id_cliente         = source.id_cliente,
                        id_representante   = source.id_representante,
                        id_regiao          = source.id_regiao,
                        dt_emissao         = source.dt_emissao,
                        dt_faturamento     = source.dt_faturamento,
                        ds_status_pedido   = source.ds_status_pedido,
                        vl_bruto           = source.vl_bruto,
                        vl_desconto        = source.vl_desconto,
                        vl_liquido         = source.vl_liquido,
                        ds_observacao      = source.ds_observacao,
                        nm_sistema_origem  = source.nm_sistema_origem,
                        cd_registro_origem = source.cd_registro_origem,
                        dt_atualizacao     = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        nr_pedido,
                        id_cliente,
                        id_representante,
                        id_regiao,
                        dt_emissao,
                        dt_faturamento,
                        ds_status_pedido,
                        vl_bruto,
                        vl_desconto,
                        vl_liquido,
                        ds_observacao,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.nr_pedido,
                        source.id_cliente,
                        source.id_representante,
                        source.id_regiao,
                        source.dt_emissao,
                        source.dt_faturamento,
                        source.ds_status_pedido,
                        source.vl_bruto,
                        source.vl_desconto,
                        source.vl_liquido,
                        source.ds_observacao,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                pedido.id_pedido,
                pedido.nr_pedido,
                pedido.id_cliente,
                pedido.id_representante,
                pedido.id_regiao,
                pedido.dt_emissao,
                pedido.dt_faturamento,
                pedido.ds_status_pedido,
                pedido.vl_bruto,
                pedido.vl_desconto,
                pedido.vl_liquido,
                pedido.ds_observacao,
                pedido.nm_sistema_origem,
                pedido.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.pedido ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.pedido: {str(e)}")
        raise