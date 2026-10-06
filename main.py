from src.load import load_orchestrator
from src.incremental.extract_incremental import run_incremental_extract
import src.logging_config
def  main():
    run_incremental_extract()
    load_orchestrator()

if __name__ == '__main__':
    main()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/

