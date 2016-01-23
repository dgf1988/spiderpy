import unittest
import logging

import lib.sql as sql


logging.basicConfig(level=logging.INFO)


class TestNode(unittest.TestCase):
    def test_hash(self):
        node = sql.Node()
        logging.info('node.hash() = %s' % (node.hash()))
        self.assertEqual(node.hash(), hash(node))

    def test_is_true(self):
        node = sql.Node()
        logging.info('node.is_true() = %s' % (node.is_true()))
        self.assertEqual(node.is_true(), bool(node))

    def test_is_equal(self):
        node = sql.Node()
        logging.info('node.is_equal(sql.Node()) = %s' % (node.is_equal(sql.Node())))
        self.assertEqual(node.is_equal(sql.Node()), node == sql.Node())
        self.assertEqual(node, sql.Node())
        self.assertEqual(node, '')
        self.assertNotEqual(node, object())

    def test_to_dict(self):
        pass


if __name__ == '__main__':
    unittest.main()
