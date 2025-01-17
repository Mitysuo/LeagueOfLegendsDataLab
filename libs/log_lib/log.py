import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, log_directory='log'):
        # Define o diretório para os logs
        self.log_directory = log_directory
        # Cria o diretório se não existir
        os.makedirs(self.log_directory, exist_ok=True)
        
        # Define o nome do arquivo de log como a data atual
        log_file = datetime.now().strftime('%Y-%m-%d') + '.log'
        log_path = os.path.join(self.log_directory, log_file)
        
        # Configura o logger
        logging.basicConfig(
            filename=log_path,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def log(self, message, level='info'):
        # Mapeia o nível de log para a função correspondente
        level = level.lower()
        match level:
            case 'info':
                logging.info(message)
            case 'error':
                logging.error(message)
            case 'warning':
                logging.warning(message)
            case _:
                logging.info(f'Invalid log level: {level}. Logging as info: {message}')

if __name__ == '__main__':
    logger = Logger()
    logger.log('Este é um log de informação.', level='info')
    logger.log('Este é um aviso.', level='warning')
    logger.log('Este é um erro.', level='error')
