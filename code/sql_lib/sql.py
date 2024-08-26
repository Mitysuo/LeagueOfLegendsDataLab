import os
import sys

import pandas as pd

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
import pyodbc

from settings import queries_path

class SQLClient:
    def __init__(self, use_sqlalchemy=True, driver='SQL Server', server='LAPTOP-UQSSFDU1\SQLEXPRESS01', database='LOL_Analytics'):
        self.use_sqlalchemy = use_sqlalchemy
        self.driver = driver
        self.server = server
        self.database = database
        self.engine = self.__database_connect()

    def __database_connect(self):
        """
        Cria uma conexão com o banco de dados SQL Server usando autenticação do Windows.
        """
        connection_string = (f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};"
                             f"Trusted_Connection=yes;")

        if self.use_sqlalchemy:
            conn_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
            return create_engine(conn_url)
        else:
            return pyodbc.connect(connection_string)
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str):
        """
        Insere os dados de um DataFrame em uma tabela SQL Server.
        """

        if self.use_sqlalchemy:
            print('Não é possível realizar a atualização usando SQLAlchemy diretamente.')

        conn = self.engine
        cursor = conn.cursor()

        columns = ', '.join(df.columns)
        values_placeholders = ', '.join(['?'] * len(df.columns))

        sql_file = os.path.join(queries_path, 'insert_data.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_query = file.read()
        
        for _, row in df.iterrows():
            cursor.execute(sql_query.format(table_name, columns, values_placeholders), tuple(row))
        
        conn.commit()
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
        

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
