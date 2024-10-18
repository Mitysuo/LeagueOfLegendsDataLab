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
                # Usar SQLAlchemy
                cursor = conn.raw_connection().cursor()
            else:
                # Usar pyodbc
                cursor = conn.cursor()

            # Colocar nomes de colunas entre colchetes []
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

    
    def get_data(self, table_name, columns):
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
        
    def create_table(self, df: pd.DataFrame, table_name: str, primary_key: str = None):
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
            columns_with_types_str += f", PRIMARY KEY ([{primary_key}])"

        # Construindo a consulta SQL para criar a tabela
        sql_file = os.path.join(queries_path, 'create_table.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_query = file.read()

        sql_query = f"CREATE TABLE [{table_name}] ({columns_with_types_str});"

        try:
            # Conectando ao banco de dados e executando a consulta
            with self.engine as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query.format(table_name, columns_with_types_str))
                conn.commit() 
        except Exception as e:
            print(f"Erro ao criar a tabela {table_name}: {e}")

    
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
