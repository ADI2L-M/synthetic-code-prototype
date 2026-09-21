from functools import lru_cache
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _stylesheet() -> str:
    return (ROOT / "ui" / "styles.css").read_text(encoding="utf-8")


def load_styles() -> None:
    st.html(f"<style>{_stylesheet()}</style>")
