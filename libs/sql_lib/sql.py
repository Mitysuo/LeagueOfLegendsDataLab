import os
import sys

import pandas as pd

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
import pyodbc

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))
from settings import queries_path, DRIVER, SERVER, DATABASE, USER_SQL, PASSWORD_SQL, TRUSTED_CONNECTION

class SQLClient:
    def __init__(self, use_sqlalchemy=True, driver=DRIVER, server=SERVER, database=DATABASE):
        self.use_sqlalchemy = use_sqlalchemy
        self.driver = driver
        self.server = server
        self.database = database
        self.engine = self.__database_connect()

    def __database_connect(self):
        """
        Cria uma conexão com o banco de dados SQL Server usando autenticação do Windows.
        """

        if TRUSTED_CONNECTION == 'yes':
            connection_string = (f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};"
                                f"Trusted_Connection=yes;")
        else:
            connection_string = (f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};"
                                f"UID={USER_SQL};PWD={PASSWORD_SQL}")

        if self.use_sqlalchemy:
            conn_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
            return create_engine(conn_url)
        else:
            return pyodbc.connect(connection_string)
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, primary_key: str = None):
        """
        Insere os dados de um DataFrame em uma tabela SQL Server.
        Se a tabela não existir, cria a tabela e tenta a inserção novamente.
        """

        if not self.table_exists(table_name):
            self.create_table(df, table_name, primary_key)
    
        try:
            conn = self.engine
            if self.use_sqlalchemy:
                cursor = conn.raw_connection().cursor()
            else:
                cursor = conn.cursor()

            columns = ', '.join([f'[{col}]' for col in df.columns])
            values_placeholders = ', '.join(['?'] * len(df.columns))

            sql_file = os.path.join(queries_path, 'insert_data.sql')
            with open(sql_file, 'r', encoding='utf-8') as file:
                sql_query = file.read()
            
            for _, row in df.iterrows():
                cursor.execute(sql_query.format(table_name, columns, values_placeholders), tuple(row))
            
            conn.commit()

        except Exception as e:
            print(f"Erro ao inserir dados: {e}")
        finally:
            cursor.close()

    
    def get_data(self, table_name: str, columns: str):
        """
        Retorna os dados de uma tabela SQL Server.
        """
        sql_file = os.path.join(queries_path, 'get_data.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_query = file.read()

        if self.use_sqlalchemy:
            df = pd.read_sql(sql_query.format(columns, table_name), self.engine)
        else:
            conn = self.engine
            cursor = conn.cursor()
            cursor.execute(sql_query.format(columns, table_name))
            df = pd.DataFrame(cursor.fetchall(), columns=[column[0] for column in cursor.description])
            cursor.close()
        return df
        
    def create_table(self, df: pd.DataFrame, table_name: str, primary_key = None):
        """
        Cria uma tabela no SQL Server com base nas colunas e tipos de dados do DataFrame fornecido.
        Opcionalmente, define uma chave primária.

        :param table_name: Nome da tabela a ser criada no banco de dados.
        :param df: DataFrame cujas colunas e tipos de dados serão usados para criar a tabela.
        :param primary_key: Nome da coluna a ser definida como chave primária (opcional).
        """

        if self.use_sqlalchemy:
            print('Não é possível criar uma tabela com o SQLAlchemy')

        # Definindo os tipos de dados SQL com base no DataFrame
        dtype_mapping = {
            'int64': 'INTEGER',
            'float64': 'FLOAT',
            'object': 'NVARCHAR(255)',
            'datetime64[ns]': 'DATETIME',
            'bool': 'BIT'
        }

        columns_with_types = []
        for column, dtype in zip(df.columns, df.dtypes):
            sql_type = dtype_mapping.get(str(dtype), 'NVARCHAR(255)')
            columns_with_types.append(f"[{column}] {sql_type}")

        columns_with_types_str = ', '.join(columns_with_types)

        if primary_key:
            if isinstance(primary_key, list):
                primary_key_str = ', '.join([f"[{key}]" for key in primary_key])
            else:
                primary_key_str = f"[{primary_key}]"
            columns_with_types_str += f", PRIMARY KEY ({primary_key_str})"

        # Construindo a consulta SQL para criar a tabela
        sql_file = os.path.join(queries_path, 'create_table.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_query = file.read()

        try:
            # Conectando ao banco de dados e executando a consulta
            with self.engine as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query.format(table_name, columns_with_types_str))
                conn.commit() 
        except Exception as e:
            print(f"Erro ao criar a tabela {table_name}: {e}")

    def upsert_data(self, df: pd.DataFrame, table_name: str, match_columns: list):
        """
        Realiza um upsert (inserção ou atualização) em uma tabela SQL Server com base nos valores do DataFrame.

        :param df: DataFrame com os dados a serem inseridos ou atualizados.
        :param table_name: Nome da tabela onde os dados serão inseridos ou atualizados.
        :param match_columns: Lista de colunas que serão usadas para verificar duplicidade (condição de match).
        :param primary_key: Nome da coluna que serve como chave primária (opcional).
        """
        # Colunas avalidas
        columns = ', '.join([f'? AS [{col}]' for col in df.columns])
        
        # Construindo a parte de match
        match_condition = ' AND '.join([f"TARGET.[{col}] = SOURCE.[{col}]" for col in match_columns])

        # Definindo as colunas de atualização e inserção
        update_clause = ', '.join([f"TARGET.[{col}] = SOURCE.[{col}]" for col in df.columns])
        insert_columns = ', '.join([f"[{col}]" for col in df.columns])
        insert_values = ', '.join([f"SOURCE.[{col}]" for col in df.columns])

        sql_file = os.path.join(queries_path, 'upsert_data.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_query = file.read()

        try:
            conn = self.engine
            if self.use_sqlalchemy:
                cursor = conn.raw_connection().cursor()
            else:
                cursor = conn.cursor()

            for _, row in df.iterrows():
                cursor.execute(sql_query.format(table_name, columns, match_condition, update_clause, insert_columns, insert_values), tuple(row))

            conn.commit()
            print(f"Upsert realizado com sucesso na tabela {table_name}")

        except Exception as e:
            print(f"Erro ao realizar upsert na tabela {table_name}: {e}")
        finally:
            cursor.close()

    
    def drop_table(self, table_name: str):
        """
        Exclui uma tabela do banco de dados SQL Server.

        :param table_name: Nome da tabela a ser excluída.
        """
        sql_file = os.path.join(queries_path, 'drop_table.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_query = file.read()

        try:
            conn = self.engine
            if self.use_sqlalchemy:
                cursor = conn.raw_connection().cursor()
            else:
                cursor = conn.cursor()

            cursor.execute(sql_query.format(table_name))
            conn.commit()

        except Exception as e:
            print(f"Erro ao excluir a tabela {table_name}: {e}")
        finally:
            cursor.close()

    def update_data(self, df: pd.DataFrame, table_name: str, match_columns: list):
        """
        Atualiza os dados de uma tabela SQL Server com base nos valores do DataFrame e colunas de match.
        
        :param df: DataFrame contendo os dados a serem atualizados.
        :param table_name: Nome da tabela onde os dados serão atualizados.
        :param match_columns: Lista de colunas usadas para verificar duplicidade (condição de match).
        """
        # Monta a query de atualização
        update_clause = ', '.join([f"[{col}] = ?" for col in df.columns if col not in match_columns])
        match_condition = ' AND '.join([f"[{col}] = ?" for col in match_columns])

        sql_file = os.path.join(queries_path, 'update_data.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_query = file.read()

        try:
            conn = self.engine
            if self.use_sqlalchemy:
                cursor = conn.raw_connection().cursor()
            else:
                cursor = conn.cursor()

            # Executa o update para cada linha do DataFrame
            for _, row in df.iterrows():
                update_values = [row[col] for col in df.columns if col not in match_columns]
                match_values = [row[col] for col in match_columns]
                cursor.execute(sql_query.format(table_name, update_clause, match_condition), tuple(update_values + match_values))

            conn.commit()

        except Exception as e:
            print(f"Erro ao atualizar dados na tabela {table_name}: {e}")
        finally:
            cursor.close()


    
    def table_exists(self, table_name: str) -> bool:
        """
        Verifica se uma tabela existe no banco de dados.

        :param table_name: Nome da tabela a ser verificada.
        :return: True se a tabela existir, False caso contrário.
        """

        sql_file = os.path.join(queries_path, 'table_information.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_query = file.read()

        if self.use_sqlalchemy:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query.format(repr(table_name)))).scalar()
        else:
            with self.engine as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query.format(repr(table_name)))
                result = cursor.fetchone()[0]
        return result > 0

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    import pandas as pd

    # Exemplo de DataFrame
    data = {
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'registered_on': pd.to_datetime(['2021-01-01', '2021-01-02', '2021-01-03']),
        'active': [True, False, True]
    }
    df_test = pd.DataFrame(data)

    sql = SQLClient(use_sqlalchemy=False)
    sql.create_table(df_test, 'Teste', 'id')
