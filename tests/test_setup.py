import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load('setup', 'setup.py')
config = setup.owconfig
payload = load('payload', 'check-payload.py')
ORIGINAL = (b'\xef\xbb\xbf[Render.13]\r\nGraphicsAPI = "Dx11"\r\nDesiredFrameRate = "144"\r\n'
            b'HighQualityUpsample = "2"\r\nCpuForceSyncEnabled = "1"\r\n'
            b'\r\n[Controls.1]\r\nSensitivity = "3.14"\r\n[Sound.3]\r\nVolume = "42"\r\n')


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='overwatch test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.prefix = self.root / 'My Steam Library/steamapps/compatdata/2357570/pfx'
        self.target = self.make_settings(self.prefix)
        self.state = self.root / 'backups'

    def make_settings(self, prefix, user='steamuser'):
        target = prefix / 'drive_c/users' / user / setup.RELATIVE_SETTINGS
        target.parent.mkdir(parents=True)
        target.write_bytes(ORIGINAL)
        return target

    def run_setup(self, *args, expected=0):
        result = subprocess.run(['bash', str(REPO / 'install.sh'), '--gpu', 'unknown',
                                 '--backup-dir', str(self.state), *map(str, args)],
                                capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def install(self, *args):
        return self.run_setup('--prefix', self.prefix, '--yes', *args)

    def test_dry_run_creates_no_files(self):
        result = self.install('--dry-run', '--profile', 'cool')
        self.assertIn('30', result.stdout)
        self.assertEqual(self.target.read_bytes(), ORIGINAL)
        self.assertFalse(self.state.exists())

    def test_doctor_is_read_only(self):
        result = self.install('--doctor')
        self.assertIn('GraphicsAPI = "Dx11"', result.stdout)
        self.assertEqual(self.target.read_bytes(), ORIGINAL)
        self.assertFalse(self.state.exists())

    def test_install_preserves_user_settings_and_renderer(self):
        self.install()
        text = self.target.read_text()
        for value in ['GraphicsAPI = "Dx11"', 'Sensitivity = "3.14"', 'Volume = "42"',
                      'HighQualityUpsample = "2"', 'CpuForceSyncEnabled = "1"']:
            self.assertIn(value, text)
        self.assertIn('DesiredFrameRate = "60"', text)
        self.assertIn('MinWorldScale = "67.000000"', text)
        backup = next(self.state.iterdir())
        self.assertEqual((backup / 'Settings_v0.ini').read_bytes(), ORIGINAL)

    def test_install_is_idempotent(self):
        self.install()
        installed = self.target.read_bytes()
        result = self.install()
        self.assertIn('already in place', result.stdout)
        self.assertEqual(self.target.read_bytes(), installed)
        self.assertEqual(len(list(self.state.iterdir())), 1)

    def test_restore_exact_bytes_including_bom_and_line_endings(self):
        self.install()
        backup = next(self.state.iterdir())
        self.run_setup('--restore', backup, '--yes')
        self.assertEqual(self.target.read_bytes(), ORIGINAL)
        self.assertIn('already restored', self.run_setup('--restore', backup, '--yes').stdout)

    def test_restore_preview(self):
        self.install()
        after = self.target.read_bytes()
        self.run_setup('--restore', next(self.state.iterdir()), '--dry-run')
        self.assertEqual(self.target.read_bytes(), after)

    def test_restore_protects_later_user_edits(self):
        self.install()
        self.target.write_text('[Render.13]\nDesiredFrameRate = "45"\n')
        result = self.run_setup('--restore', next(self.state.iterdir()), '--yes', expected=1)
        self.assertIn('changed after this install', result.stderr)
        self.assertIn('45', self.target.read_text())

    def test_corrupt_backup_is_rejected(self):
        self.install()
        backup = next(self.state.iterdir())
        (backup / 'Settings_v0.ini').write_text('corrupted')
        after = self.target.read_bytes()
        result = self.run_setup('--restore', backup, '--yes', expected=1)
        self.assertIn('checksum', result.stderr)
        self.assertEqual(self.target.read_bytes(), after)

    def test_noninteractive_install_requires_yes(self):
        result = self.run_setup('--prefix', self.prefix, expected=1)
        self.assertIn('--yes', result.stderr)
        self.assertEqual(self.target.read_bytes(), ORIGINAL)
        self.assertFalse(self.state.exists())

    def test_explicit_dx12(self):
        self.install('--renderer', 'dx12', '--profile', 'performance')
        text = self.target.read_text()
        self.assertIn('GraphicsAPI = "Dx12"', text)
        self.assertIn('DesiredFrameRate = "90"', text)
        self.assertNotIn('GraphicsAPI = "Dx11"', text)

    def test_mali_does_not_force_turnip_or_dx12(self):
        result = self.install('--gpu', 'mali', '--profile', 'cool')
        self.assertIn('experimental', result.stdout)
        self.assertIn('Unofficial', result.stdout)
        self.assertIn('GraphicsAPI = "Dx11"', self.target.read_text())
        self.assertIn('DesiredFrameRate = "30"', self.target.read_text())

    def test_unknown_settings_format_stops(self):
        self.target.write_text('[Render.99]\n')
        result = self.run_setup('--prefix', self.prefix, '--yes', expected=1)
        self.assertIn("isn't recognized", result.stderr)
        self.assertFalse(self.state.exists())

    def test_multiple_users_require_selection(self):
        self.make_settings(self.prefix, 'another user')
        result = self.run_setup('--prefix', self.prefix, '--yes', expected=1)
        self.assertIn('more than one', result.stdout)
        self.assertFalse(self.state.exists())

    def test_invalid_prefix_does_not_create_it(self):
        result = self.run_setup('--prefix', self.root / 'missing', '--yes', expected=1)
        self.assertIn("isn't a Wine prefix", result.stderr)
        self.assertFalse((self.root / 'missing').exists())

    def test_prefix_can_be_compatdata_parent(self):
        self.assertEqual(setup.prefix_settings(self.prefix.parent), [self.target])

    def test_paths_with_spaces_quotes_and_dollar_signs(self):
        target = self.make_settings(self.root / 'a "quoted" $HOME prefix')
        prefix = target.parents[6]
        result = self.run_setup('--prefix', prefix, '--yes')
        self.assertIn('All set', result.stdout)
        self.assertIn('60', target.read_text())

    def test_discovery_follows_libraryfolders_and_deduplicates(self):
        home = self.root / 'home'
        steam = home / '.local/share/Steam'
        (steam / 'steamapps').mkdir(parents=True)
        library = self.prefix.parents[3]
        (steam / 'steamapps/libraryfolders.vdf').write_text('"path" "' + str(library) + '"\n')
        (home / '.steam').mkdir()
        (home / '.steam/root').symlink_to(steam)
        self.assertEqual(setup.discover(home, self.root / 'mounts'), [self.target])

    def test_discovery_x64_sd_and_battlenet(self):
        home, mounts = self.root / 'home', self.root / 'mnt'
        a = self.make_settings(home / '.droiddeck-x64/.local/share/Steam/steamapps/compatdata/2357570/pfx')
        b = self.make_settings(mounts / 'droiddeck-sd/x86-64/steamapps/compatdata/2357570/pfx')
        c = self.make_settings(home / '.local/share/Steam/steamapps/compatdata/2596113170/pfx')
        d = self.make_settings(mounts / 'droiddeck-lib/1/x86-64/steamapps/compatdata/2357570/pfx')
        self.assertEqual(set(setup.discover(home, mounts)), {a, b, c, d})

    def test_running_game_is_detected(self):
        proc = self.root / 'proc/123'
        proc.mkdir(parents=True)
        (proc / 'cmdline').write_bytes(b'wine\0C:\\Overwatch\\Overwatch.exe\0')
        with self.assertRaises(setup.SetupError):
            setup.ensure_game_closed(proc.parent)
        (proc / 'cmdline').write_bytes(b'sh\0-c\0echo Overwatch.exe\0')
        setup.ensure_game_closed(proc.parent)

    def test_concurrent_change_is_not_overwritten(self):
        self.target.write_text('a newer save')
        with self.assertRaises(setup.SetupError):
            setup.apply_settings(self.target, ORIGINAL, b'changed', self.state)
        self.assertEqual(self.target.read_text(), 'a newer save')
        self.assertFalse(self.state.exists())

    def test_failed_replace_leaves_original_and_recoverable_backup(self):
        real = os.replace
        def fail_target(src, dst):
            if dst == self.target:
                raise OSError('simulated disk error')
            real(src, dst)
        with patch.object(setup.os, 'replace', side_effect=fail_target):
            with self.assertRaises(OSError):
                setup.apply_settings(self.target, ORIGINAL, b'changed', self.state)
        self.assertEqual(self.target.read_bytes(), ORIGINAL)
        self.assertEqual((next(self.state.iterdir()) / 'Settings_v0.ini').read_bytes(), ORIGINAL)
        self.assertFalse(list(self.target.parent.glob('.overwatch-droid-*')))

    def test_file_permissions_preserved(self):
        self.target.chmod(0o640)
        self.install()
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o640)

    def test_gpu_classification(self):
        for name, expected in [('Adreno (TM) 740', 'adreno'), ('Turnip Adreno 830', 'adreno'),
                               ('Mali-G715', 'mali'), ('Immortalis-G925', 'mali'),
                               ('Samsung Xclipse 940', 'xclipse'), ('PowerVR DXT', 'powervr'),
                               ('llvmpipe', 'unknown'), ('RADV AMD desktop GPU', 'unknown')]:
            with self.subTest(name=name):
                self.assertEqual(setup.gpu_family(name), expected)

    def test_renderer_keep_does_not_create_override(self):
        text = config.render_settings('[Render.13]\n', setup.preset_text('balanced', 'keep'))
        self.assertNotIn('GraphicsAPI', text)
        self.assertNotIn('HighQualityUpsample', text)

    def test_all_profiles_and_renderer_combinations(self):
        for profile, (fps, scale, _) in setup.PROFILES.items():
            for renderer in ('keep', 'dx11', 'dx12'):
                with self.subTest(profile=profile, renderer=renderer):
                    text = config.render_settings(ORIGINAL.decode('utf-8-sig'), setup.preset_text(profile, renderer))
                    self.assertIn(f'DesiredFrameRate = "{fps}"', text)
                    self.assertIn(f'MinWorldScale = "{scale:.6f}"', text)
                    self.assertEqual(text, config.render_settings(text, setup.preset_text(profile, renderer)))

    def test_legacy_env_merge_preserves_other_games_and_custom_options(self):
        dev, repo, out = [self.root / name for name in ('device.json', 'repo.json', 'out.json')]
        original = {'version': 1, 'shared': {'CUSTOM': 'shared'},
                    'games': {'2357570': {'CUSTOM': 'keep', 'FEX_TSOENABLED': '0'}, '42': {'X': 'Y'}},
                    'dxvkConfig': {'key': 'value'}}
        dev.write_text(json.dumps(original))
        repo.write_text(json.dumps({'games': {'2357570': {'FEX_TSOENABLED': '1'}}}))
        config.merge_env(dev, repo, out)
        result = json.loads(out.read_text())
        self.assertEqual(result['games']['2357570'], {'CUSTOM': 'keep', 'FEX_TSOENABLED': '1'})
        self.assertEqual(result['games']['42'], original['games']['42'])
        self.assertEqual(result['shared'], original['shared'])
        self.assertEqual(result['dxvkConfig'], original['dxvkConfig'])

    def test_legacy_corrupt_env_is_not_silently_erased(self):
        dev, repo, out = [self.root / name for name in ('device.json', 'repo.json', 'out.json')]
        repo.write_text('{"games":{"2357570":{}}}')
        for invalid in ('{broken', '[]', '{"version":2}', '{"games":[]}'):
            dev.write_text(invalid)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                config.merge_env(dev, repo, out)
            self.assertFalse(out.exists())

    def test_bundled_payload_verifies(self):
        payload.verify(REPO)

    def test_corrupt_payload_is_rejected(self):
        root = self.root / 'payload'
        (root / 'store').mkdir(parents=True)
        (root / 'store/file').write_bytes(b'changed')
        (root / 'SHA256SUMS').write_text(setup.digest(b'original') + '  ./file\n')
        with self.assertRaises(ValueError):
            payload.verify(root)

    def test_finder_metadata_is_ignored_but_other_extras_are_not(self):
        root = self.root / 'payload'
        (root / 'store/dir').mkdir(parents=True)
        (root / 'store/file').write_bytes(b'original')
        (root / 'SHA256SUMS').write_text(setup.digest(b'original') + '  ./file\n')
        (root / 'store/.DS_Store').write_bytes(b'finder')
        (root / 'store/dir/.DS_Store').write_bytes(b'finder')
        payload.verify(root)
        (root / 'store/dir/extra.dll').write_bytes(b'planted')
        with self.assertRaises(ValueError):
            payload.verify(root)

    def test_regenerated_sums_leave_out_finder_metadata(self):
        root = self.root / 'payload'
        (root / 'scripts').mkdir(parents=True)
        (root / 'store').mkdir()
        shutil.copy(REPO / 'scripts/sums.sh', root / 'scripts/sums.sh')
        (root / 'store/file').write_bytes(b'original')
        (root / 'store/.DS_Store').write_bytes(b'finder')
        subprocess.run(['bash', str(root / 'scripts/sums.sh')], check=True)
        self.assertNotIn('.DS_Store', (root / 'SHA256SUMS').read_text())
        payload.verify(root)

    def test_help_does_not_need_adb(self):
        result = subprocess.run(['bash', str(REPO / 'install.sh'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('without root or ADB', result.stdout)

    def test_legacy_help_still_works(self):
        result = subprocess.run(['bash', str(REPO / 'install.sh'), '--legacy', '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('dry-run', result.stdout)


if __name__ == '__main__':
    unittest.main()
