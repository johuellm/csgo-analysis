from gui.tk_components.components import MainApplication
from preprocessing.create_graphs import main

def test_addition():
    assert 1 + 1 == 2

def test_gui():
    # do not instantiate it, because it would open a window
    main_window = MainApplication

def test_create_graphs():
    # do not instantiate it, because it would open a window
    main_function = main
