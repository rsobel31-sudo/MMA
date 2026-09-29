"""Importers that build the fight table from public MMA record sites.

Sherdog and Tapology list every professional bout a fighter has had
(regional shows included), which gives full-career Elo, records, finishing
tendencies and durability. They don't publish per-bout striking/grappling
stats, so those corners are left empty and the model falls back to shrunk
priors for them. Use ``merge`` to combine a career dataset with a
stats-rich one.
"""
