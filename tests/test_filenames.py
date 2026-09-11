"""Tests for the --dated-filenames output template (stdlib unittest).

Run: python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reels import build_filename_template


class BuildFilenameTemplate(unittest.TestCase):
    def test_default_is_unchanged(self):
        self.assertEqual(build_filename_template("jireel"), "%(id)s.%(ext)s")

    def test_dated_prefixes_date_and_channel(self):
        self.assertEqual(
            build_filename_template("jireel", dated=True),
            "%(upload_date>%d%m%Y|NA)s_jireel_%(id)s.%(ext)s",
        )

    def test_dated_escapes_percent_in_channel_name(self):
        # "%" is the yt-dlp output-template escape character; a channel name
        # containing one must be doubled so the template still parses and the
        # "%" appears literally in the resulting filename.
        self.assertEqual(
            build_filename_template("100% Real Page", dated=True),
            "%(upload_date>%d%m%Y|NA)s_100%% Real Page_%(id)s.%(ext)s",
        )


if __name__ == "__main__":
    unittest.main()
