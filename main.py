"""Точка входа: собирает MVP и запускает приложение."""
from __future__ import annotations

import tkinter as tk

from model.app_model import AppModel
from view.main_view import MainView
from presenter.main_presenter import MainPresenter


def main() -> None:
    root = tk.Tk()
    root.title("Code Bundler")
    root.geometry("1000x650")

    model = AppModel()
    view = MainView(root)
    view.pack(fill="both", expand=True)

    # Presenter связывает View и Model
    MainPresenter(view, model)

    root.mainloop()


if __name__ == "__main__":
    main()