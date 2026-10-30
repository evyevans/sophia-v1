"""The release tool must detect altered content and exclude unreviewed files."""
from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/'tools'/'release.py'
if TOOL.is_file():
    spec=importlib.util.spec_from_file_location('release_tool',TOOL); release=importlib.util.module_from_spec(spec); spec.loader.exec_module(release)
else: release=None

class ReleaseTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(release,'Release checker is not implemented.')
    def test_secret_pattern_detects_realistic_token(self):
        token='gh'+'p_'+'A'*36
        self.assertIn('credential_pattern',release.scan_text(token))
    def test_email_and_private_path_patterns_detected(self):
        self.assertIn('email',release.scan_text('personal'+'@'+'mail.invalid'))
        self.assertIn('local_path',release.scan_text('/'+'Users'+'/operator/private.txt'))
    def test_public_urls_are_not_credentials(self):
        self.assertEqual(release.scan_text('https://docs.kraken.com/api-reference/market-data/get-order-book'),[])
    def test_manifest_detects_modification_and_extra_file(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'README.md').write_text('safe\n'); (root/'ALLOWLIST.json').write_text(json.dumps(['README.md','ALLOWLIST.json','RELEASE_FILES.json']))
            release.make_manifest(root)
            self.assertEqual(release.check(root),[])
            (root/'README.md').write_text('modified\n')
            self.assertTrue(any('hash_mismatch' in v for v in release.check(root)))
            (root/'unexpected.txt').write_text('surprise')
            self.assertTrue(any('unlisted_file' in v for v in release.check(root)))
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'outside').write_text('safe'); (root/'README.md').symlink_to(root/'outside')
            (root/'ALLOWLIST.json').write_text(json.dumps(['README.md','ALLOWLIST.json','RELEASE_FILES.json']))
            with self.assertRaises(ValueError): release.make_manifest(root)
    def test_allowlist_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'ALLOWLIST.json').write_text(json.dumps(['../outside','ALLOWLIST.json','RELEASE_FILES.json']))
            with self.assertRaises(ValueError): release.make_manifest(root)
    def test_broken_local_markdown_link_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'README.md').write_text('[missing](missing.md)')
            (root/'ALLOWLIST.json').write_text(json.dumps(['README.md','ALLOWLIST.json','RELEASE_FILES.json']))
            release.make_manifest(root); self.assertTrue(any('broken_link' in v for v in release.check(root)))
    def test_archive_cannot_overwrite_source_file(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); p=root/'README.md'; p.write_text('safe\n')
            (root/'ALLOWLIST.json').write_text(json.dumps(['README.md','ALLOWLIST.json','RELEASE_FILES.json']))
            release.make_manifest(root)
            with self.assertRaises(ValueError): release.archive(root,p)
            self.assertEqual(p.read_text(),'safe\n')
    def test_exact_private_term_check_avoids_substring_false_positive(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); p=root/'README.md'; p.write_text('An adaptable design.\n')
            (root/'ALLOWLIST.json').write_text(json.dumps(['README.md','ALLOWLIST.json','RELEASE_FILES.json']))
            release.make_manifest(root)
            self.assertFalse(any('private_term' in v for v in release.check(root,['Ada'])))
            p.write_text('Prepared for Ada.\n'); release.make_manifest(root)
            self.assertTrue(any('private_term' in v for v in release.check(root,['Ada'])))

if __name__=='__main__': unittest.main()
