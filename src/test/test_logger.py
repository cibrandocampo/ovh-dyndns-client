import logging
import unittest

from infrastructure.logger import Logger

class TestLogger(unittest.TestCase):
    def test_logger_default(self):
        logger = Logger.get_logger()
        self.assertEqual(logger.name, 'ovh-dydns')
        self.assertEqual(logger.level, logging.INFO)

    def test_logger_custom_name_and_level(self):
        logger = Logger.get_logger(name='custom_logger', level='DEBUG')
        self.assertEqual(logger.name, 'custom_logger')
        self.assertEqual(logger.level, logging.DEBUG)

    def test_invalid_level(self):
        with self.assertRaises(ValueError):
            Logger.get_logger(level='INVALID')
