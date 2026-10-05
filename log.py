import logging


def get_logger(name: str) -> logging.Logger:
    """Логгер с NullHandler по умолчанию.

    Без настройки логи никуда не пишутся; с флагом --debug срабатывает
    logging.basicConfig в main.py, и сообщения уходят в root-обработчики."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
