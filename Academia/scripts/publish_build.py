"""Entrega de artefatos no mesmo repositório, sem criar uma publicação pública."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

root = Path(os.environ['GITHUB_WORKSPACE'])
app = root / 'Academia'
run_id = os.environ['GITHUB_RUN_ID']
branch = 'build/power-academia-installers'
header = subprocess.check_output(['git', '-C', str(root), 'config', '--get', 'http.https://github.com/.extraheader'], text=True).strip()

git_env = {**os.environ, 'GIT_CONFIG_COUNT': '1',
           'GIT_CONFIG_KEY_0': 'http.https://github.com/.extraheader',
           'GIT_CONFIG_VALUE_0': header}

with tempfile.TemporaryDirectory(prefix='power-artifacts-') as temporary:
    repo = Path(temporary)
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    def git(*args, check=True, capture=False):
        return subprocess.run(['git', '-C', str(repo), *args], check=check, text=True, env=git_env,
                              stdout=subprocess.PIPE if capture else None,
                              stderr=subprocess.PIPE if capture else None)
    git('remote', 'add', 'origin', 'https://github.com/' + os.environ['GITHUB_REPOSITORY'] + '.git')
    fetched = git('fetch', '--depth', '1', 'origin', branch, check=False, capture=True)
    if fetched.returncode == 0:
        git('checkout', '-q', '-b', 'results', 'FETCH_HEAD')
    else:
        git('checkout', '-q', '--orphan', 'results')
    destination = repo / 'runs' / run_id
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {'run_id': run_id, 'status': os.environ['BUILD_STATUS'],
                'source_commit': os.environ['GITHUB_SHA'], 'files': []}
    for log in sorted(app.glob('*.log')):
        shutil.copy2(log, destination / log.name)
    for executable in sorted((app / 'output').glob('*.exe')):
        content_hash = hashlib.sha256()
        parts = []
        with executable.open('rb') as source:
            index = 0
            while chunk := source.read(45 * 1024 * 1024):
                name = executable.name + f'.part{index:02d}'
                (destination / name).write_bytes(chunk)
                content_hash.update(chunk)
                parts.append(name)
                index += 1
        manifest['files'].append({'name': executable.name, 'size': executable.stat().st_size,
                                  'sha256': content_hash.hexdigest(), 'parts': parts})
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (repo / 'latest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    git('config', 'user.name', 'Power Academia Build')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    git('add', 'runs/' + run_id, 'latest.json')
    git('commit', '-q', '-m', 'Build Windows Power Academia: ' + run_id)
    git('push', 'origin', 'HEAD:refs/heads/' + branch)
print('Resultado disponível em ' + branch + ', execução ' + run_id)
