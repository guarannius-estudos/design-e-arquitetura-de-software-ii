import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_produto(timer: func.TimerRequest) -> None:
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
                SELECT cd_produto,
                       cd_sku,
                       nm_produto,
                       id_categoria,
                       nm_unidade_medida,
                       qt_ponto_reposicao,
                       fl_ativo,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.produto
            """)

            registros = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.produto OFF")

            for item in registros:
                dest_cursor.execute("""
                MERGE dbo.produto AS target
                USING (
                    SELECT ? AS cd_produto,
                           ? AS cd_sku,
                           ? AS nm_produto,
                           ? AS id_categoria,
                           ? AS nm_unidade_medida,
                           ? AS qt_ponto_reposicao,
                           ? AS fl_ativo,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.cd_sku = source.cd_sku
                WHEN MATCHED THEN
                    UPDATE SET
                        cd_produto          = source.cd_produto,
                        nm_produto          = source.nm_produto,
                        id_categoria        = source.id_categoria,
                        nm_unidade_medida   = source.nm_unidade_medida,
                        qt_ponto_reposicao  = source.qt_ponto_reposicao,
                        fl_ativo            = source.fl_ativo,
                        nm_sistema_origem   = source.nm_sistema_origem,
                        cd_registro_origem  = source.cd_registro_origem,
                        dt_atualizacao      = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        cd_produto,
                        cd_sku,
                        nm_produto,
                        id_categoria,
                        nm_unidade_medida,
                        qt_ponto_reposicao,
                        fl_ativo,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.cd_produto,
                        source.cd_sku,
                        source.nm_produto,
                        source.id_categoria,
                        source.nm_unidade_medida,
                        source.qt_ponto_reposicao,
                        source.fl_ativo,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                item.cd_produto,
                item.cd_sku,
                item.nm_produto,
                item.id_categoria,
                item.nm_unidade_medida,
                item.qt_ponto_reposicao,
                item.fl_ativo,
                item.nm_sistema_origem,
                item.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.produto ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.produto: {str(e)}")
        raise