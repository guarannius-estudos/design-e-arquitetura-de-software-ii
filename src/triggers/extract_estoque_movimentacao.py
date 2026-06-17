import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_estoque_movimentacao(timer: func.TimerRequest) -> None:
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
                SELECT id_estoque_movimentacao,
                       id_produto,
                       dt_movimentacao,
                       ds_tipo_movimentacao,
                       qt_movimentacao,
                       nr_documento_origem,
                       id_pedido,
                       ds_observacao,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.estoque_movimentacao
            """)

            movimentos = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.estoque_movimentacao OFF")

            for movimento in movimentos:
                dest_cursor.execute("""
                MERGE dbo.estoque_movimentacao AS target
                USING (
                    SELECT ? AS id_estoque_movimentacao,
                           ? AS id_produto,
                           ? AS dt_movimentacao,
                           ? AS ds_tipo_movimentacao,
                           ? AS qt_movimentacao,
                           ? AS nr_documento_origem,
                           ? AS id_pedido,
                           ? AS ds_observacao,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.id_estoque_movimentacao = source.id_estoque_movimentacao
                WHEN MATCHED THEN
                    UPDATE SET
                        id_produto          = source.id_produto,
                        dt_movimentacao     = source.dt_movimentacao,
                        ds_tipo_movimentacao= source.ds_tipo_movimentacao,
                        qt_movimentacao     = source.qt_movimentacao,
                        nr_documento_origem = source.nr_documento_origem,
                        id_pedido           = source.id_pedido,
                        ds_observacao       = source.ds_observacao,
                        nm_sistema_origem   = source.nm_sistema_origem,
                        cd_registro_origem  = source.cd_registro_origem,
                        dt_atualizacao      = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        id_produto,
                        dt_movimentacao,
                        ds_tipo_movimentacao,
                        qt_movimentacao,
                        nr_documento_origem,
                        id_pedido,
                        ds_observacao,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.id_produto,
                        source.dt_movimentacao,
                        source.ds_tipo_movimentacao,
                        source.qt_movimentacao,
                        source.nr_documento_origem,
                        source.id_pedido,
                        source.ds_observacao,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                movimento.id_estoque_movimentacao,
                movimento.id_produto,
                movimento.dt_movimentacao,
                movimento.ds_tipo_movimentacao,
                movimento.qt_movimentacao,
                movimento.nr_documento_origem,
                movimento.id_pedido,
                movimento.ds_observacao,
                movimento.nm_sistema_origem,
                movimento.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.estoque_movimentacao ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.estoque_movimentacao: {str(e)}")
        raise