import pytest
import os
import tempfile
from pathlib import Path
import yaml
import argparse

from utils import get_kubeconfig_path, get_download_location, get_config_files
from config_manager import merge_configs, update_kubeconfig
from backup_manager import create_backup, manage_backups
from cli import CustomFormatter, VersionAction

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def mock_args():
    class Args:
        def __init__(self):
            self.kubeconfig = None
            self.download_location = None
            self.conf_name = 'config*.yaml'
            self.number_of_configs = 1
            self.backup = 5
    return Args()

def test_get_kubeconfig_path_default(mock_args):
    path = get_kubeconfig_path(mock_args)
    assert path == Path.home() / '.kube' / 'config'

def test_get_kubeconfig_path_custom(mock_args):
    mock_args.kubeconfig = '/custom/path/config'
    path = get_kubeconfig_path(mock_args)
    assert path == Path('/custom/path/config')

def test_get_kubeconfig_path_env_var(mock_args, monkeypatch):
    monkeypatch.setenv('KUBECONFIG_LOCATION', '/env/path/config')
    path = get_kubeconfig_path(mock_args)
    assert path == Path('/env/path/config')

def test_get_download_location_default(mock_args):
    path = get_download_location(mock_args)
    assert path == Path.home() / '.kube'

def test_get_download_location_custom(mock_args):
    mock_args.download_location = '/custom/download'
    path = get_download_location(mock_args)
    assert path == Path('/custom/download')

def test_get_download_location_env_var(mock_args, monkeypatch):
    monkeypatch.setenv('DEFAULT_DOWNLOAD_LOCATION', '/env/download')
    path = get_download_location(mock_args)
    assert path == Path('/env/download')

def test_get_config_files(temp_dir):
    (temp_dir / 'config1.yaml').touch()
    (temp_dir / 'config2.yaml').touch()
    (temp_dir / 'other.txt').touch()
    files = get_config_files(temp_dir, 'config*.yaml', 2)
    assert len(files) == 2
    assert all(f.name.startswith('config') and f.suffix == '.yaml' for f in files)

def test_merge_configs():
    existing_config = {
        'clusters': [{'name': 'cluster1', 'cluster': {'server': 'https://1.1.1.1'}}],
        'contexts': [{'name': 'context1', 'context': {'cluster': 'cluster1', 'user': 'user1'}}],
        'users': [{'name': 'user1', 'user': {'token': 'token1'}}]
    }
    new_config = {
        'clusters': [
            {'name': 'cluster1', 'cluster': {'server': 'https://2.2.2.2'}},
            {'name': 'cluster2', 'cluster': {'server': 'https://3.3.3.3'}}
        ],
        'contexts': [{'name': 'context2', 'context': {'cluster': 'cluster2', 'user': 'user2'}}],
        'users': [{'name': 'user2', 'user': {'token': 'token2'}}]
    }
    merged = merge_configs(existing_config, new_config)
    assert len(merged['clusters']) == 2
    assert merged['clusters'][0]['cluster']['server'] == 'https://2.2.2.2'
    assert len(merged['contexts']) == 2
    assert len(merged['users']) == 2

def test_create_backup(temp_dir):
    kubeconfig = temp_dir / 'config'
    kubeconfig.write_text('test config')
    backup = create_backup(kubeconfig)
    assert backup.exists()
    assert backup.parent.name == 'kubezap_backups'
    assert backup.read_text() == 'test config'

def test_manage_backups(temp_dir):
    backup_dir = temp_dir / 'kubezap_backups'
    backup_dir.mkdir()
    for i in range(10):
        (backup_dir / f'kubeconfig_backup_{i}').touch()
    manage_backups(backup_dir, 5)
    assert len(list(backup_dir.glob('*'))) == 5

def test_update_kubeconfig(temp_dir):
    kubeconfig = temp_dir / 'config'
    kubeconfig.write_text(yaml.dump({
        'clusters': [{'name': 'cluster1', 'cluster': {'server': 'https://1.1.1.1'}}],
        'contexts': [{'name': 'context1', 'context': {'cluster': 'cluster1', 'user': 'user1'}}],
        'users': [{'name': 'user1', 'user': {'token': 'token1'}}]
    }))
    new_config = temp_dir / 'new_config.yaml'
    new_config.write_text(yaml.dump({
        'clusters': [{'name': 'cluster2', 'cluster': {'server': 'https://2.2.2.2'}}],
        'contexts': [{'name': 'context2', 'context': {'cluster': 'cluster2', 'user': 'user2'}}],
        'users': [{'name': 'user2', 'user': {'token': 'token2'}}]
    }))
    changes, _ = update_kubeconfig(kubeconfig, [new_config], 5)
    assert len(changes) > 0
    updated_config = yaml.safe_load(kubeconfig.read_text())
    assert len(updated_config['clusters']) == 2
    assert len(updated_config['contexts']) == 2
    assert len(updated_config['users']) == 2

def test_custom_formatter():
    formatter = CustomFormatter('test')
    help_text = formatter.format_help()
    assert 'Environment Variables:' in help_text
    assert 'KUBECONFIG_LOCATION' in help_text
    assert 'DEFAULT_DOWNLOAD_LOCATION' in help_text

def test_version_action(capsys):
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action=VersionAction, version='TestVersion 1.0')
    with pytest.raises(SystemExit):
        parser.parse_args(['-v'])
    captured = capsys.readouterr()
    assert captured.out.strip() == 'TestVersion 1.0'

# Edge cases
def test_get_config_files_no_matching_files(temp_dir):
    files = get_config_files(temp_dir, 'nonexistent*.yaml', 1)
    assert len(files) == 0

def test_merge_configs_empty_configs():
    existing_config = {}
    new_config = {}
    merged = merge_configs(existing_config, new_config)
    assert merged == {}

def test_update_kubeconfig_no_changes(temp_dir):
    kubeconfig = temp_dir / 'config'
    kubeconfig.write_text(yaml.dump({
        'clusters': [{'name': 'cluster1', 'cluster': {'server': 'https://1.1.1.1'}}],
        'contexts': [{'name': 'context1', 'context': {'cluster': 'cluster1', 'user': 'user1'}}],
        'users': [{'name': 'user1', 'user': {'token': 'token1'}}]
    }))
    new_config = temp_dir / 'new_config.yaml'
    new_config.write_text(yaml.dump({
        'clusters': [{'name': 'cluster1', 'cluster': {'server': 'https://1.1.1.1'}}],
        'contexts': [{'name': 'context1', 'context': {'cluster': 'cluster1', 'user': 'user1'}}],
        'users': [{'name': 'user1', 'user': {'token': 'token1'}}]
    }))
    changes, _ = update_kubeconfig(kubeconfig, [new_config], 5)
    assert len(changes) == 0

def test_manage_backups_no_backups(temp_dir):
    backup_dir = temp_dir / 'kubezap_backups'
    backup_dir.mkdir()
    manage_backups(backup_dir, 5)
    assert len(list(backup_dir.glob('*'))) == 0

def test_get_config_files_limit(temp_dir):
    for i in range(10):
        (temp_dir / f'config{i}.yaml').touch()
    files = get_config_files(temp_dir, 'config*.yaml', 5)
    assert len(files) == 5
