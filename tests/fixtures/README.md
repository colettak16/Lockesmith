# Randomizer log fixtures

Drop Universal Pokemon Randomizer ZX spoiler logs for Emerald here (`*.log` or `*.txt`). None has been
added: no ROM was available (docs/decisions.md D19). `tests/test_full_logs.py` runs full-size logs written
in UPR's format for all five games instead, but only a real log can confirm the format itself.
`*.log` files are gitignored; never commit a ROM.

The fixture tests in `tests/test_log_parser.py` run automatically once a log is here. Most useful:

1. A log with **wild Pokémon left unchanged** (randomize something else, e.g. starters). This checks
   the fishing slot split and the set-order alignment against vanilla, as PLAN.md section 4.5 asks.
2. A log with wild Pokémon and trainers randomized, ideally with trainer moveset logging on, to
   exercise both trainer line formats.
