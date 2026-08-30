"""Tests for URL handling (stdlib unittest, no extra dependencies).

Run: python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reels import looks_shell_truncated, normalize_channel_url


class NormalizeChannelUrl(unittest.TestCase):
    def test_profile_url_gets_reels_tab(self):
        # This is what CMD/bash hand us after the shell eats "&sk=reels_tab".
        self.assertEqual(
            normalize_channel_url("https://www.facebook.com/profile.php?id=61554746552594"),
            "https://www.facebook.com/profile.php?id=61554746552594&sk=reels_tab",
        )

    def test_profile_url_with_reels_tab_is_unchanged(self):
        url = "https://www.facebook.com/profile.php?id=61554746552594&sk=reels_tab"
        self.assertEqual(normalize_channel_url(url), url)

    def test_explicit_other_tab_is_respected(self):
        url = "https://www.facebook.com/profile.php?id=61554746552594&sk=photos"
        self.assertEqual(normalize_channel_url(url), url)

    def test_people_style_profile_gets_reels_tab(self):
        self.assertEqual(
            normalize_channel_url("https://www.facebook.com/people/Some-Page/61554746552594/"),
            "https://www.facebook.com/people/Some-Page/61554746552594/?sk=reels_tab",
        )

    def test_vanity_name_gets_reels_path(self):
        self.assertEqual(
            normalize_channel_url("https://www.facebook.com/jireel"),
            "https://www.facebook.com/jireel/reels",
        )

    def test_reels_path_is_unchanged(self):
        url = "https://www.facebook.com/jireel/reels"
        self.assertEqual(normalize_channel_url(url), url)

    def test_surrounding_quotes_are_stripped(self):
        # People paste the URL still wrapped in the quotes they typed in the shell.
        self.assertEqual(
            normalize_channel_url('"https://www.facebook.com/jireel/reels"'),
            "https://www.facebook.com/jireel/reels",
        )

    def test_inline_cmd_escaping_is_cleaned(self):
        # cmd.exe users are told to write ...id=1"&"sk=reels_tab ; if the quotes
        # survive into argv (copy/paste, quoted whole string) we must clean them.
        self.assertEqual(
            normalize_channel_url('https://www.facebook.com/profile.php?id=615"&"sk=reels_tab'),
            "https://www.facebook.com/profile.php?id=615&sk=reels_tab",
        )

    def test_missing_scheme_is_added(self):
        self.assertEqual(
            normalize_channel_url("facebook.com/jireel/reels"),
            "https://facebook.com/jireel/reels",
        )

    def test_whitespace_is_trimmed(self):
        self.assertEqual(
            normalize_channel_url("  https://www.facebook.com/jireel/reels \n"),
            "https://www.facebook.com/jireel/reels",
        )

    def test_non_facebook_url_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_channel_url("https://www.youtube.com/@someone")

    def test_empty_url_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_channel_url("   ")


class LooksShellTruncated(unittest.TestCase):
    def test_profile_id_only_looks_truncated(self):
        self.assertTrue(
            looks_shell_truncated("https://www.facebook.com/profile.php?id=61554746552594")
        )

    def test_full_url_does_not_look_truncated(self):
        self.assertFalse(
            looks_shell_truncated(
                "https://www.facebook.com/profile.php?id=61554746552594&sk=reels_tab"
            )
        )

    def test_vanity_url_does_not_look_truncated(self):
        self.assertFalse(looks_shell_truncated("https://www.facebook.com/jireel/reels"))


if __name__ == "__main__":
    unittest.main()
