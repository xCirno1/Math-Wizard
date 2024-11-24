import logging

old_factory = logging.getLogRecordFactory()


def set_log_equation(equation: str, wrap_in_string: bool = True):
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.equation = equation if not wrap_in_string else f'"{equation}"'
        return record

    logging.setLogRecordFactory(record_factory)


def setup_log(filename: str | None = None, logger_name: str | None = None):
    handler = logging.FileHandler(filename or 'logs.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(equation)s - %(funcName)s - %(message)s'))

    log = logging.getLogger(logger_name or "wizard")
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    return log


_log = setup_log()
