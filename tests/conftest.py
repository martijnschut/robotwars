import os

# Geen echte tik-loop en geen db-bestand tijdens tests.
os.environ["ROBOTWARS_TIK"] = "3600"
os.environ["ROBOTWARS_DB"] = ":memory:"
