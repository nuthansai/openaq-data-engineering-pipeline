from src.load import load_postgres
from src.incremental.extract_incremental import incremental_extract
import src.logging_config
def  main():
    incremental_extract()
    load_postgres()

if __name__ == '__main__':
    main()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/

