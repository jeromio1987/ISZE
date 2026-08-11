"""Back-compat wrapper — Hungary full deck now uses build_full_deck.py."""
from build_full_deck import build_full


def main():
    build_full("HUNGARY")


if __name__ == "__main__":
    main()
