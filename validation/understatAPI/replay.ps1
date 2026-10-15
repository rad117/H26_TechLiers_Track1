# depexit replay: re-runs the exact commands behind this capsule, so anyone can check our evidence.
# Target: https://github.com/collinb9/understatAPI @ d1252d9734e94ba98c681d2e41d467f1edb7aaf5   Generated: 2026-10-15T11:12:47+00:00
# Usage (PowerShell, needs git + uv):  .\replay.ps1
$capsule = $PSScriptRoot
$root = Join-Path $capsule '_replay'

# ----- Baseline: original dependencies -----
$dir = Join-Path $root 'baseline'
git clone -q https://github.com/collinb9/understatAPI $dir
git -C $dir checkout -q d1252d9734e94ba98c681d2e41d467f1edb7aaf5
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- idna: apply Gemma's patch, then test -----
$dir = Join-Path $root 'idna'
git clone -q https://github.com/collinb9/understatAPI $dir
git -C $dir checkout -q d1252d9734e94ba98c681d2e41d467f1edb7aaf5
git -C $dir apply --ignore-whitespace (Join-Path $capsule 'idna/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- urllib3: apply Gemma's patch, then test -----
$dir = Join-Path $root 'urllib3'
git clone -q https://github.com/collinb9/understatAPI $dir
git -C $dir checkout -q d1252d9734e94ba98c681d2e41d467f1edb7aaf5
git -C $dir apply --ignore-whitespace (Join-Path $capsule 'urllib3/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- certifi: apply Gemma's patch, then test -----
$dir = Join-Path $root 'certifi'
git clone -q https://github.com/collinb9/understatAPI $dir
git -C $dir checkout -q d1252d9734e94ba98c681d2e41d467f1edb7aaf5
git -C $dir apply --ignore-whitespace (Join-Path $capsule 'certifi/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location
