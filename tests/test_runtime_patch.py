import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from test_setup import REPO, load
runtime = load('runtime_patch', 'runtime_patch.py')


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='runtime patch ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.proton = self.root / 'Proton Experimental (ARM64)'
        self.proton.mkdir()
        (self.proton / 'version').write_text('123456 ' + runtime.VERSION + '\n')
        self.originals = {}
        for name in runtime.FILES:
            original = ((REPO / 'store/original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll' / name).read_bytes()
                        if name == runtime.NTDLL else b'original FEX: ' + name.encode())
            target = self.proton / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original)
            self.originals[name] = original
        self.state = self.root / 'backups'

    def run_patch(self, *args, expected=0):
        result = subprocess.run(['bash', str(REPO / 'install.sh'), *map(str, args), '--backup-dir', str(self.state)],
                                capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def assert_originals(self):
        for name, data in self.originals.items():
            self.assertEqual((self.proton / name).read_bytes(), data)

    def test_preview_has_no_side_effects(self):
        result = self.run_patch('--legacy-runtime', self.proton, '--dry-run')
        self.assertIn('EVERY game', result.stdout)
        self.assertFalse(self.state.exists())
        self.assert_originals()

    def test_exact_build_patch_and_full_restore(self):
        self.run_patch('--legacy-runtime', self.proton, '--yes')
        for name, source in runtime.FILES.items():
            self.assertEqual((self.proton / name).read_bytes(), (REPO / 'store' / source).read_bytes())
        backup = next(self.state.iterdir())
        self.run_patch('--restore-runtime', backup, '--yes')
        self.assert_originals()
        self.assertEqual(len(list(self.state.iterdir())), 2)  # Restore also has an undo.

    def test_newer_proton_is_rejected(self):
        (self.proton / 'version').write_text('123 experimental-11.0-20261105-arm64\n')
        self.run_patch('--legacy-runtime', self.proton, '--yes', expected=1)
        self.assert_originals()
        self.assertFalse(self.state.exists())

    def test_unknown_ntdll_is_rejected(self):
        (self.proton / runtime.NTDLL).write_bytes(b'new or corrupted ntdll')
        result = self.run_patch('--legacy-runtime', self.proton, '--yes', expected=1)
        self.assertIn("isn't the known", result.stderr)
        self.assertFalse(self.state.exists())

    def test_linked_runtime_is_rejected(self):
        relative = next(name for name in runtime.FILES if name != runtime.NTDLL)
        target = self.proton / relative
        outside = self.root / 'outside.so'
        outside.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(outside)
        self.run_patch('--legacy-runtime', self.proton, '--yes', expected=1)
        self.assertFalse(self.state.exists())
        self.assertEqual(outside.read_bytes(), self.originals[relative])

    def test_idempotent_patch(self):
        self.run_patch('--legacy-runtime', self.proton, '--yes')
        result = self.run_patch('--legacy-runtime', self.proton, '--yes')
        self.assertIn('already in place', result.stdout)
        self.assertEqual(len(list(self.state.iterdir())), 1)

    def test_corrupt_backup_refuses_restore(self):
        self.run_patch('--legacy-runtime', self.proton, '--yes')
        backup = next(self.state.iterdir())
        (backup / '0').write_bytes(b'corrupt')
        result = self.run_patch('--restore-runtime', backup, '--yes', expected=1)
        self.assertIn('checksum', result.stderr)
        self.assertEqual(runtime.setup.digest((self.proton / runtime.NTDLL).read_bytes()), runtime.PATCHED)

    def test_restore_protects_updated_proton(self):
        self.run_patch('--legacy-runtime', self.proton, '--yes')
        backup = next(self.state.iterdir())
        (self.proton / runtime.NTDLL).write_bytes(b'updated by Steam')
        result = self.run_patch('--restore-runtime', backup, '--yes', expected=1)
        self.assertIn('Proton changed', result.stderr)
        self.assertEqual((self.proton / runtime.NTDLL).read_bytes(), b'updated by Steam')

    def test_partial_failure_rolls_back(self):
        changes = runtime.plan(self.proton)
        write = runtime.setup.atomic_write
        def fail_second(path, data, mode=0o600):
            if path == self.proton / changes[1][0] and data == changes[1][2]:
                raise OSError('simulated full disk')
            write(path, data, mode)
        with patch.object(runtime.setup, 'atomic_write', side_effect=fail_second):
            with self.assertRaises(OSError):
                runtime.apply(self.proton, changes, self.state)
        self.assert_originals()
        self.assertTrue((next(self.state.iterdir()) / 'manifest.json').exists())

    def test_unexpected_backup_path_is_rejected(self):
        self.run_patch('--legacy-runtime', self.proton, '--yes')
        backup = next(self.state.iterdir())
        manifest = json.loads((backup / 'manifest.json').read_text())
        manifest['files'][0]['path'] = '../other'
        (backup / 'manifest.json').write_text(json.dumps(manifest))
        self.run_patch('--restore-runtime', backup, '--yes', expected=1)

    def test_live_windows_launcher_is_rejected(self):
        proc = self.root / 'proc/123'
        proc.mkdir(parents=True)
        (proc / 'cmdline').write_bytes(b'wine\0C:\\Battle.net.exe\0')
        with self.assertRaises(runtime.setup.SetupError):
            runtime.ensure_idle(proc.parent)
        (proc / 'cmdline').write_bytes(b'konsole\0')
        runtime.ensure_idle(proc.parent)
