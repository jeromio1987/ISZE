"""Synthetic shell only. This does not rebuild or visually accept the ISZE shell."""
import contextlib
import hashlib
import importlib.util
import io
import os
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_under_test', os.environ.get('AIM_BUILD_UNDER_TEST', str(ROOT / 'tools/build.py')))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

class BuildBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_reference, self.old_dist = build.REFERENCE, build.DIST
        build.REFERENCE = str(self.root / 'synthetic_shell.html')
        build.DIST = str(self.root / 'dist')
        mounts = ''.join('<div id="%s"></div>' % x for x in (
            'case-list','case-header','scope-strip','pack-status','tabs','content','market','sources-top'))
        self.shell = ('<!doctype html><html><head><title>TEST ONLY</title></head><body>'
          '<span class="version">Decision component 0.2</span>' + mounts +
          '<script id="case-data" type="application/json">{}</script></body></html>')
        Path(build.REFERENCE).write_text(self.shell, encoding='utf-8')
        self.payload=json.loads((ROOT/'tests/fixtures/synthetic_payload.json').read_text())
        self.payload_path=self.root/'synthetic_payload.json'

    def tearDown(self):
        build.REFERENCE, build.DIST = self.old_reference, self.old_dist
        self.tmp.cleanup()

    def run_build(self, raw=None):
        self.payload_path.write_text(raw if raw is not None else json.dumps(self.payload,indent=2),encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            report=build.build(str(self.payload_path))
        return report,Path(report['output']).read_text(encoding='utf-8')

    def test_01_script_terminator_stays_data_and_roundtrips(self):
        self.payload['source_note']='</script><script>globalThis.TEST_ONLY=1</script><b>&'
        _,html=self.run_build()
        match=re.search(r'<script id="case-data" type="application/json">(.*?)</script>',html,re.S)
        self.assertIsNotNone(match)
        self.assertEqual(json.loads(match[1]),self.payload)
        self.assertTrue('<script>globalThis.TEST_ONLY=1</script>' not in html, 'The marker must remain JSON data, not a script element.')

    def test_02_payload_version_cannot_inject_markup(self):
        self.payload['meta']['version']='<img src=x data-test-only="yes">'
        _,html=self.run_build()
        self.assertTrue('<img src=x data-test-only=' not in html, 'Source version text must not become markup.')
        self.assertTrue('&lt;img' in html, 'Version markup must be HTML-escaped.')

    def test_03_replacement_backslashes_are_literal(self):
        self.payload['meta']['version']=r'Version \1'
        _,html=self.run_build()
        self.assertIn(r'payload Version \1</span>',html)

    def test_04_shell_has_one_body_and_a_closed_head(self):
        _,html=self.run_build()
        # Count parsed tags, not '<body>' text inside JavaScript export templates.
        class Tags(HTMLParser):
            def __init__(self):
                super().__init__(); self.bodies=0; self.closed_heads=0
            def handle_starttag(self, tag, attrs):
                if tag == 'body': self.bodies += 1
            def handle_endtag(self, tag):
                if tag == 'head': self.closed_heads += 1
        tags=Tags(); tags.feed(html)
        self.assertEqual(tags.bodies,1)
        self.assertEqual(tags.closed_heads,1)

    def test_05_banned_label_refuses_before_writing_any_artifact(self):
        self.payload['source_note']='mode a'
        with self.assertRaises(SystemExit): self.run_build()
        self.assertFalse(Path(build.DIST).exists())

    def test_06_failed_build_preserves_last_good_artifact_and_report(self):
        report,_=self.run_build()
        files={p:p.read_bytes() for p in Path(build.DIST).iterdir()}
        self.payload['source_note']='mode b'
        with self.assertRaises(SystemExit): self.run_build()
        for p,original in files.items(): self.assertEqual(p.read_bytes(),original)

    def test_07_nan_json_is_refused_before_output(self):
        with self.assertRaises((SystemExit,ValueError)):
            self.run_build('{"meta": {}, "bad": NaN}')
        self.assertFalse(Path(build.DIST).exists())

    def test_08_overflowing_json_number_is_refused_before_output(self):
        with self.assertRaises((SystemExit,ValueError)):
            self.run_build('{"meta": {}, "bad": 1e999}')
        self.assertFalse(Path(build.DIST).exists())

    def test_09_raw_and_serialized_payload_digests_are_separate(self):
        report,html=self.run_build()
        self.assertEqual(report['payload_raw_sha256'],hashlib.sha256(self.payload_path.read_bytes()).hexdigest())
        canonical=json.dumps(self.payload,separators=(',',':')).encode('utf-8')
        self.assertEqual(report['payload_canonical_sha256'],hashlib.sha256(canonical).hexdigest())
        embedded=re.search(r'<script id="case-data" type="application/json">\n(.*?)\n</script>',html,re.S)[1]
        self.assertEqual(report['payload_embedded_sha256'],hashlib.sha256(embedded.encode()).hexdigest())
        self.assertNotEqual(report['payload_raw_sha256'],report['payload_canonical_sha256'])

    def test_10_input_source_and_shell_are_not_changed(self):
        reference=Path(build.REFERENCE).read_bytes()
        raw=json.dumps(self.payload,indent=4)
        self.run_build(raw)
        self.assertEqual(self.payload_path.read_text(),raw)
        self.assertEqual(Path(build.REFERENCE).read_bytes(),reference)

if __name__=='__main__': unittest.main(verbosity=2)
