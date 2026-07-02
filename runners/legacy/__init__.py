"""Legacy runner scripts — superseded by ``runners/agent/``.

Contents:
  - ``evas_loop.py``              — original 24-task parallel batch loop
  - ``run_adaptive_repair.py``    — layered-repair prototype (2 DWA tasks)
  - ``run_model_assisted_loop.py`` — Table 2/3 A/B experiment harness (8 modes)

All three are kept for reproducibility of prior results. New work should use
``python -m runners.agent`` instead, which absorbs their features:
  - parallel batch + resume         (from evas_loop)
  - 5-layer repair policy           (from run_adaptive_repair, via config.loop.layered_repair)
  - 8 experiment modes              (from run_model_assisted_loop, via config.loop.prompt_mode)

The original import paths (``from evas_loop import ...`` etc.) still work via
re-export stubs in the parent ``runners/`` directory.
"""
