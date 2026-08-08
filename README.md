# arwLint

An interactive pylint session for [agentRW](https://github.com/linuxrebel/agentRW).

`/lint <file>` walks findings one at a time. For each you decide: fix it, skip
it, ignore the whole kind, defer it to a ledger, or see the raw message. Style
findings are never asked about — autopep8 fixes all of them at the end.

```
[bad-indentation] line 8   (11 of this kind)
  meaning: PEP 8 wants 4 spaces per level.
  action : re-indent to 4 spaces
  note   : Style only. The code runs the same.
```

Plugin identity: **`linuxrebel/lint`**

---

## Why it exists

A report you cannot act on is not worth reading. `pylint file.py` tells you
there are 17 problems; it does not help you fix any of them, and pasting the
whole thing at a model costs ~2400 tokens — more than a small model's entire
context window.

This sends **five** findings to a model and hands the other eleven to autopep8.

---

## What it does that a linter does not

**Translates.** pylint says *"Module name doesn't conform to snake_case"* and
never mentions that it means the filename. This says:

> Python takes the module name from the filename. `dr-strange` is not
> importable — `import dr-strange` is a syntax error.
> **action**: rename the file to `dr_strange.py`
> **note**: Renaming can break anything that calls this file by name — scripts,
> symlinks, cron entries. Leaving it alone costs nothing.

**Knows how each finding can be fixed.** A missing docstring is *inserted*, not
written over the line below it. A module rename is a rename, not an edit. A
finding with no mechanical fix says so instead of inventing one.

**Never sends style to a model.** autopep8 is deterministic, free, and cannot
alter the code either side of the whitespace. Asking a model to fix indentation
once produced a line that kept the wrong indent *and* silently dropped a `*`
from `join(*lines)` — a style request that caused a runtime error.

**Reverts if it broke the file.** If the finished result no longer compiles,
the entire run is undone.

---

## Measured

35-line file, 17 findings, pylint baseline 2.61:

| model | score after | model's share |
|---|---|---|
| gemma4:31b-cloud | 9.57 | 5 docstrings |
| qwen2.5-coder:7b | 9.13 | 3 |
| ornith:latest | 8.26 | 2 |
| qwen3.5 / qwen3.6 / ornith:35b | 7.39 | 0 |

All six improve the file; none break it. **7.39 is autopep8 alone** — a model
that contributes nothing costs you time, not correctness.

Peak context: 227 tokens, constant per finding. A 300-finding file costs the
same *per decision* as a 3-finding one.

---

## What this will do

Installing a plugin means running someone else's code. "Read the source first"
is advice nobody follows, so here is what this one actually touches — check it
against `plugin.py` if you want, but you should not have to read 400 lines to
decide.

**It will:**

- Read and rewrite the `.py` file you point `/lint` at, one line at a time, and
  only after you approve each change
- Write a `.bak` beside that file before the first change, so the original is
  recoverable
- Run `autopep8` over the file once at the end, to fix every style finding in
  one pass
- Append a line to `DEBT.md` in your working directory when you answer `defer`
- Rename the file, but only if the finding is about the filename and only if
  you answer `fix` to that specific one
- Run `pylint` and `autopep8` as subprocesses
- Send short snippets — the finding, plus a few lines around it — to whichever
  model agentRW is pointed at. If that is a cloud model, those lines leave your
  machine

**It will not:**

- Touch any file except the one you named, and nothing outside agentRW's write
  scope
- Apply anything you have not seen and agreed to
- Install packages, change your configuration, or reach the network itself
- Keep the file if the result stops compiling — the whole run is reverted

---

## Requirements

- [agentRW](https://github.com/linuxrebel/agentRW) with plugin API 1 or later
- `pylint` — finds the issues
- `autopep8` — fixes every style issue, no model involved

Both are distro packages: Fedora `python3-pylint` / `python3-autopep8`, Debian
and Ubuntu `pylint` / `python3-autopep8`. Prefer those or a venv — pip on top
of a distro copy is a known way to break a system Python. The plugin invokes
them as executables on `PATH`, so either source works.

Without them `/lint` is not registered at all, and `/plugins` says why.

---

## Install

agentRW has no plugin installer yet, so a plugin is installed by copying two
files into place. Install agentRW first — see
[its README](https://github.com/linuxrebel/agentRW) — then:

```bash
git clone https://github.com/linuxrebel/arwLint
```

### Linux and macOS

agentRW installs to `/opt/agentRW`, which is owned by root, so copying a plugin
in needs `sudo`:

```bash
sudo mkdir -p /opt/agentRW/tools/linuxrebel/lint
sudo cp arwLint/install.md arwLint/plugin.py /opt/agentRW/tools/linuxrebel/lint/
```

### Windows

In **PowerShell**. agentRW installs per-user, so no administrator rights are
needed:

```powershell
$dest = "$env:LOCALAPPDATA\Programs\agentRW\tools\linuxrebel\lint"
New-Item -ItemType Directory -Force -Path $dest
Copy-Item arwLint\install.md, arwLint\plugin.py -Destination $dest
```

These will not work in cmd — `$env:` is PowerShell syntax. If you are in cmd,
open PowerShell instead.

### Check it took

Restart `cagent` — plugins are discovered at startup, so a session that was
already running will not see it. Then run `/plugins`:

```
  linuxrebel/lint ACTIVE   tools: lint_file; commands: /lint
      needs pylint: found
      needs autopep8: found
```

If `/plugins` does not list it at all, the files are in the wrong place — the
directory must be exactly `tools/linuxrebel/lint/` and must contain both
`install.md` and `plugin.py`.

If it says `MISSING` against either requirement, the plugin does not register
at all, so `/lint` will not exist. Install them (below) and restart.

Then `/lint help`, and `/lint somefile.py` for the real thing.

### If pylint or autopep8 are missing

See Requirements above for the distro packages, which are the better option.
With pip, use `python3 -m pip` rather than bare `pip`, so it installs for the
interpreter that runs agentRW:

```bash
python3 -m pip install --user pylint autopep8
```

On macOS a `--user` install puts the executables in `~/Library/Python/3.9/bin`,
which is not on `PATH` by default:

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
```

## Uninstall

Delete the directory. Nothing else is written anywhere.

Linux and macOS:

```bash
sudo rm -rf /opt/agentRW/tools/linuxrebel/lint
```

Windows, in PowerShell:

```powershell
Remove-Item -Recurse "$env:LOCALAPPDATA\Programs\agentRW\tools\linuxrebel\lint"
```

Note that reinstalling agentRW itself preserves `tools/`, so plugins survive an
upgrade. Uninstalling agentRW removes them.

---

## Usage

```
/lint <file>                    every finding
/lint <file> unused-import      one kind
/lint <file> max=5              stop after five
/lint help                      full reference
```

Per finding: `[f]ix` `[s]kip` `[i]gnore kind` `[d]efer` `[r]aw` `[q]uit`

`defer` appends to `DEBT.md` so a deliberate "not now" is recorded instead of
forgotten. `ignore kind` drops every remaining finding of that type for the
run — the answer to pylint complaining eleven times about two-space
indentation.

---

## License

Same as agentRW.
