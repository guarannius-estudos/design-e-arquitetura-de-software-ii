import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_pedido_item(timer: func.TimerRequest) -> None:
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
                SELECT id_pedido_item,
                       id_pedido,
                       id_produto,
                       nr_sequencia_item,
                       qt_item,
                       vl_preco_unitario,
                       vl_bruto,
                       vl_desconto,
                       vl_liquido,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.pedido_item
            """)

            itens = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.pedido_item OFF")

            for item in itens:
                dest_cursor.execute("""
                MERGE dbo.pedido_item AS target
                USING (
                    SELECT ? AS id_pedido_item,
                           ? AS id_pedido,
                           ? AS id_produto,
                           ? AS nr_sequencia_item,
                           ? AS qt_item,
                           ? AS vl_preco_unitario,
                           ? AS vl_bruto,
                           ? AS vl_desconto,
                           ? AS vl_liquido,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.id_pedido_item = source.id_pedido_item
                WHEN MATCHED THEN
                    UPDATE SET
                        id_pedido          = source.id_pedido,
                        id_produto         = source.id_produto,
                        nr_sequencia_item  = source.nr_sequencia_item,
                        qt_item            = source.qt_item,
                        vl_preco_unitario  = source.vl_preco_unitario,
                        vl_bruto           = source.vl_bruto,
                        vl_desconto        = source.vl_desconto,
                        vl_liquido         = source.vl_liquido,
                        nm_sistema_origem  = source.nm_sistema_origem,
                        cd_registro_origem = source.cd_registro_origem,
                        dt_atualizacao     = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        id_pedido,
                        id_produto,
                        nr_sequencia_item,
                        qt_item,
                        vl_preco_unitario,
                        vl_bruto,
                        vl_desconto,
                        vl_liquido,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.id_pedido,
                        source.id_produto,
                        source.nr_sequencia_item,
                        source.qt_item,
                        source.vl_preco_unitario,
                        source.vl_bruto,
                        source.vl_desconto,
                        source.vl_liquido,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                item.id_pedido_item,
                item.id_pedido,
                item.id_produto,
                item.nr_sequencia_item,
                item.qt_item,
                item.vl_preco_unitario,
                item.vl_bruto,
                item.vl_desconto,
                item.vl_liquido,
                item.nm_sistema_origem,
                item.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.pedido_item ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.pedido_item: {str(e)}")
        raise