import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import monitor  # noqa: E402

SNAPSHOT_QUOTED = "\n".join([
    '- link [e1]:',
    '- link "Alice":',
    '- link "@alice":',
    '- link "12h":',
    '- text: Replying to',
    '- link "@bob":',
    '- text: How do I fix this?   1     2   185',
    '- link "/pic/orig/media%2FABC.jpg":',
])

SNAPSHOT_URL_LINE = SNAPSHOT_QUOTED.replace(
    '- link "/pic/orig/media%2FABC.jpg":', '- /url: /pic/orig/media%2FABC.jpg'
)


class ParseTweetUrlTest(unittest.TestCase):
    def test_x_com(self):
        self.assertEqual(
            monitor.parse_tweet_url("https://x.com/user/status/123456"),
            ("user", "123456"),
        )

    def test_twitter_com(self):
        self.assertEqual(
            monitor.parse_tweet_url("https://twitter.com/user/status/99"),
            ("user", "99"),
        )

    def test_invalid(self):
        with self.assertRaises(ValueError):
            monitor.parse_tweet_url("x")


class IsQuestionTest(unittest.TestCase):
    def test_positive(self):
        self.assertTrue(monitor.is_question("How do I fix this"))
        self.assertTrue(monitor.is_question("这个怎么装"))
        self.assertTrue(monitor.is_question("works?"))

    def test_no_substring_false_positives(self):
        self.assertFalse(monitor.is_question("Great show"))
        self.assertFalse(monitor.is_question("somehow works"))


class ParseRepliesTest(unittest.TestCase):
    def check(self, snapshot):
        replies = monitor.parse_replies(snapshot, "bob")
        self.assertEqual(len(replies), 1)
        r = replies[0]
        self.assertEqual(r["author"], "@alice")
        self.assertEqual(r["author_name"], "Alice")
        self.assertEqual(r["text"], "How do I fix this?")
        self.assertEqual(r["time_ago"], "12h")
        self.assertEqual(r["likes"], 2)
        self.assertEqual(r["replies"], 1)
        self.assertEqual(r["views"], 185)
        self.assertEqual(r["media"], ["https://pbs.twimg.com/media/ABC.jpg"])
        self.assertTrue(r["is_question"])

    def test_quoted_link_media(self):
        self.check(SNAPSHOT_QUOTED)

    def test_url_line_media(self):
        self.check(SNAPSHOT_URL_LINE)


if __name__ == "__main__":
    unittest.main()
