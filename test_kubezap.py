
import unittest
import tempfile
import os
import shutil
from pathlib import Path
from kubezap import get_kubeconfig_path, get_download_location, get_config_files, merge_configs, create_backup, manage_backups, update_kubeconfig

class TestKubeZap(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.kubeconfig_path = Path(self.temp_dir) / 'config'
        self.download_location = Path(self.temp_dir) / 'downloads'
        self.download_location.mkdir()
        
        # Create a sample kubeconfig file
        with open(self.kubeconfig_path, 'w') as f:
            f.write("apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\nusers: []")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_get_kubeconfig_path(self):
        # Test default path
        self.assertEqual(get_kubeconfig_path(type('Args', (), {'kubeconfig': None})()), Path.home() / '.kube' / 'config')
        
        # Test custom path
        custom_path = Path('/custom/path/config')
        self.assertEqual(get_kubeconfig_path(type('Args', (), {'kubeconfig': custom_path})()), custom_path)
        
        # Test environment variable
        os.environ['KUBECONFIG_LOCATION'] = str(self.kubeconfig_path)
        self.assertEqual(get_kubeconfig_path(type('Args', (), {'kubeconfig': None})()), self.kubeconfig_path)
        del os.environ['KUBECONFIG_LOCATION']

    def test_get_download_location(self):
        # Test default path
        self.assertEqual(get_download_location(type('Args', (), {'download_location': None})()), Path.home() / '.kube')
        
        # Test custom path
        custom_path = Path('/custom/download/path')
        self.assertEqual(get_download_location(type('Args', (), {'download_location': custom_path})()), custom_path)
        
        # Test environment variable
        os.environ['DEFAULT_DOWNLOAD_LOCATION'] = str(self.download_location)
        self.assertEqual(get_download_location(type('Args', (), {'download_location': None})()), self.download_location)
        del os.environ['DEFAULT_DOWNLOAD_LOCATION']

    def test_get_config_files(self):
        # Create sample config files
        (self.download_location / 'config1.yaml').touch()
        (self.download_location / 'config2.yaml').touch()
        (self.download_location / 'other_file.txt').touch()
        
        # Test with default pattern
        files = get_config_files(self.download_location, 'config*.yaml', 2)
        self.assertEqual(len(files), 2)
        self.assertTrue(all(file.name.startswith('config') and file.suffix == '.yaml' for file in files))
        
        # Test with custom pattern
        files = get_config_files(self.download_location, '*.txt', 1)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, 'other_file.txt')
        
        # Test with non-existent files
        files = get_config_files(self.download_location, 'nonexistent*.yaml', 1)
        self.assertEqual(len(files), 0)

    def test_merge_configs(self):
        existing_config = {'clusters': [{'name': 'cluster1'}], 'contexts': [], 'users': []}
        new_config = {'clusters': [{'name': 'cluster2'}], 'contexts': [{'name': 'context1'}], 'users': []}
        
        merged_config = merge_configs(existing_config, new_config)
        self.assertEqual(len(merged_config['clusters']), 2)
        self.assertEqual(len(merged_config['contexts']), 1)
        self.assertEqual(len(merged_config['users']), 0)

    def test_create_backup(self):
        backup_path = create_backup(self.kubeconfig_path)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.name.startswith('kubeconfig_backup_'))

    def test_manage_backups(self):
        backup_dir = self.kubeconfig_path.parent / 'kubezap_backups'
        backup_dir.mkdir()
        
        # Create 15 backup files
        for i in range(15):
            (backup_dir / f'kubeconfig_backup_{i}').touch()
        
        manage_backups(backup_dir, max_backups=10)
        
        backups = list(backup_dir.glob('kubeconfig_backup_*'))
        self.assertEqual(len(backups), 10)

    def test_update_kubeconfig(self):
        # Create a new config file
        new_config_path = self.download_location / 'new_config.yaml'
        with open(new_config_path, 'w') as f:
            f.write("apiVersion: v1\nkind: Config\nclusters: [{'name': 'new_cluster'}]\ncontexts: []\nusers: []")
        
        changes = update_kubeconfig(self.kubeconfig_path, [new_config_path])
        self.assertEqual(len(changes), 1)
        
        # Verify the kubeconfig has been updated
        with open(self.kubeconfig_path, 'r') as f:
            updated_config = f.read()
        self.assertIn('new_cluster', updated_config)
        
        # Verify backup was created
        backups = list((self.kubeconfig_path.parent / 'kubezap_backups').glob('kubeconfig_backup_*'))
        self.assertEqual(len(backups), 1)

    def test_update_kubeconfig_failure(self):
        # Create an invalid config file
        invalid_config_path = self.download_location / 'invalid_config.yaml'
        with open(invalid_config_path, 'w') as f:
            f.write("invalid: yaml: content")
        
        original_content = self.kubeconfig_path.read_text()
        changes = update_kubeconfig(self.kubeconfig_path, [invalid_config_path])
        self.assertEqual(len(changes), 0)
        
        # Verify the kubeconfig has not been changed
        self.assertEqual(self.kubeconfig_path.read_text(), original_content)

if __name__ == '__main__':
    unittest.main()
