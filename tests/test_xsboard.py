import unittest

from xstools.xsboard import XsBoard, XulaNoJtag, all_xsboards
from xstools.xsusb import XsUsb


@unittest.skipUnless(XsUsb.get_xsusb_ports(), 'No Xula board found')
class XsBoardTest(unittest.TestCase):
    def setUp(self):
        self.board = XsBoard.get_xsboard()

    def test_get_xsboard(self):
        # TODO(rheineke): What is the point of None? Not used in project
        board = XsBoard.get_xsboard(xsusb_id=None)
        self.assertIsNone(board)

        # If an explicit board name is provided, then this is chosen first
        # Ensure all boards are accessible by name
        boards = all_xsboards()
        for b in boards:
            board = XsBoard.get_xsboard(xsboard_name=b.name)
            # Will fail on XulaNoJtag
            if b is not XulaNoJtag:
                self.assertEqual(board.__class__, b)

        # If the provided board name is not found, the return the board indexed
        # by xsusb_id
        with self.assertRaises(IndexError):
            XsBoard.get_xsboard(xsusb_id=-2)
        board = XsBoard.get_xsboard(xsusb_id=0)
        self.assertIsNotNone(board)

    def test_blink(self):
        info = self.board.get_board_info()
        self.assertIsNotNone(info)
