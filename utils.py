# coding=utf-8
import logging
import numpy as np

# def set_seed(seed=42):
#     random.seed(seed)
#     os.environ['PYHTONHASHSEED'] = str(seed)
#     np.random.seed(seed)
#     torch.manual_seed(seed)
#     torch.cuda.manual_seed(seed)
#     torch.backends.cudnn.deterministic = True

def set_logger(path):
    # save the log to the file path
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    np.set_printoptions(threshold=np.inf)


    file_handler = logging.FileHandler(path)
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger