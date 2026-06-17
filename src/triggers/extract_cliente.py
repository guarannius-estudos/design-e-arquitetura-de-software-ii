import azure.functions as func
import logging
import os
import pyodbc

app = func.Blueprint()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def extract_cliente(timer: func.TimerRequest) -> None:
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
                SELECT id_cliente,
                       cd_cliente,
                       nm_cliente,
                       tp_pessoa,
                       nr_cnpj_cpf,
                       ds_email,
                       ds_telefone,
                       id_regiao,
                       id_representante,
                       dt_cadastro,
                       fl_ativo,
                       nm_sistema_origem,
                       cd_registro_origem
                  FROM erp.cliente
            """)

            clientes = source_cursor.fetchall()

        with pyodbc.connect(dest_conn_str) as dest_conn:
            dest_cursor = dest_conn.cursor()

            dest_cursor.execute("SET IDENTITY_INSERT dbo.cliente OFF")

            for cliente in clientes:
                dest_cursor.execute("""
                MERGE dbo.cliente AS target
                USING (
                    SELECT ? AS id_cliente,
                           ? AS cd_cliente,
                           ? AS nm_cliente,
                           ? AS tp_pessoa,
                           ? AS nr_cnpj_cpf,
                           ? AS ds_email,
                           ? AS ds_telefone,
                           ? AS id_regiao,
                           ? AS id_representante,
                           ? AS dt_cadastro,
                           ? AS fl_ativo,
                           ? AS nm_sistema_origem,
                           ? AS cd_registro_origem
                ) AS source
                ON target.cd_cliente = source.cd_cliente
                WHEN MATCHED THEN
                    UPDATE SET
                        nm_cliente         = source.nm_cliente,
                        tp_pessoa          = source.tp_pessoa,
                        nr_cnpj_cpf        = source.nr_cnpj_cpf,
                        ds_email           = source.ds_email,
                        ds_telefone        = source.ds_telefone,
                        id_regiao          = source.id_regiao,
                        id_representante   = source.id_representante,
                        dt_cadastro        = source.dt_cadastro,
                        fl_ativo           = source.fl_ativo,
                        nm_sistema_origem  = source.nm_sistema_origem,
                        cd_registro_origem = source.cd_registro_origem,
                        dt_atualizacao     = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (
                        cd_cliente,
                        nm_cliente,
                        tp_pessoa,
                        nr_cnpj_cpf,
                        ds_email,
                        ds_telefone,
                        id_regiao,
                        id_representante,
                        dt_cadastro,
                        fl_ativo,
                        nm_sistema_origem,
                        cd_registro_origem
                    ) VALUES (
                        source.cd_cliente,
                        source.nm_cliente,
                        source.tp_pessoa,
                        source.nr_cnpj_cpf,
                        source.ds_email,
                        source.ds_telefone,
                        source.id_regiao,
                        source.id_representante,
                        source.dt_cadastro,
                        source.fl_ativo,
                        source.nm_sistema_origem,
                        source.cd_registro_origem
                    );
                """,
                cliente.id_cliente,
                cliente.cd_cliente,
                cliente.nm_cliente,
                cliente.tp_pessoa,
                cliente.nr_cnpj_cpf,
                cliente.ds_email,
                cliente.ds_telefone,
                cliente.id_regiao,
                cliente.id_representante,
                cliente.dt_cadastro,
                cliente.fl_ativo,
                cliente.nm_sistema_origem,
                cliente.cd_registro_origem
                )

            dest_cursor.execute("SET IDENTITY_INSERT dbo.cliente ON")

            dest_conn.commit()

    except Exception as e:
        logging.error(f"Erro ao ler erp.cliente: {str(e)}")
        raise