# depexit replay: re-runs the exact commands behind this capsule, so anyone can check our evidence.
# Target: https://github.com/rishrek/LinkWatch @ f52f3930c8e7c33d934ccf614955a38e26984bd5   Generated: 2026-10-15T10:06:59+00:00
# Usage (PowerShell, needs git + uv):  .\replay.ps1
$capsule = $PSScriptRoot
$root = Join-Path $capsule '_replay'

# ----- Baseline: original dependencies -----
$dir = Join-Path $root 'baseline'
git clone -q https://github.com/rishrek/LinkWatch $dir
git -C $dir checkout -q f52f3930c8e7c33d934ccf614955a38e26984bd5
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- Jinja2: apply Gemma's patch, then test -----
$dir = Join-Path $root 'Jinja2'
git clone -q https://github.com/rishrek/LinkWatch $dir
git -C $dir checkout -q f52f3930c8e7c33d934ccf614955a38e26984bd5
git -C $dir apply (Join-Path $capsule 'Jinja2/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- pydantic: apply Gemma's patch, then test -----
$dir = Join-Path $root 'pydantic'
git clone -q https://github.com/rishrek/LinkWatch $dir
git -C $dir checkout -q f52f3930c8e7c33d934ccf614955a38e26984bd5
git -C $dir apply (Join-Path $capsule 'pydantic/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- idna: apply Gemma's patch, then test -----
$dir = Join-Path $root 'idna'
git clone -q https://github.com/rishrek/LinkWatch $dir
git -C $dir checkout -q f52f3930c8e7c33d934ccf614955a38e26984bd5
git -C $dir apply (Join-Path $capsule 'idna/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- chardet: apply Gemma's patch, then test -----
$dir = Join-Path $root 'chardet'
git clone -q https://github.com/rishrek/LinkWatch $dir
git -C $dir checkout -q f52f3930c8e7c33d934ccf614955a38e26984bd5
git -C $dir apply (Join-Path $capsule 'chardet/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- toml: apply Gemma's patch, then test -----
$dir = Join-Path $root 'toml'
git clone -q https://github.com/rishrek/LinkWatch $dir
git -C $dir checkout -q f52f3930c8e7c33d934ccf614955a38e26984bd5
git -C $dir apply (Join-Path $capsule 'toml/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- appdirs: apply Gemma's patch, then test -----
$dir = Join-Path $root 'appdirs'
git clone -q https://github.com/rishrek/LinkWatch $dir
git -C $dir checkout -q f52f3930c8e7c33d934ccf614955a38e26984bd5
git -C $dir apply (Join-Path $capsule 'appdirs/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location

# ----- setuptools: apply Gemma's patch, then test -----
$dir = Join-Path $root 'setuptools'
git clone -q https://github.com/rishrek/LinkWatch $dir
git -C $dir checkout -q f52f3930c8e7c33d934ccf614955a38e26984bd5
git -C $dir apply (Join-Path $capsule 'setuptools/patch.diff')
Push-Location $dir
py -3.12 -m venv --clear .venv
& .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
& .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml
Pop-Location
