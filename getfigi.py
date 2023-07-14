from tinkoff.invest import Client, InstrumentIdType
from tinkoff.invest.services import InstrumentsService
import tinkoff.invest.services
import pandas as pd
import tkinter
import tkinter.messagebox
import customtkinter

import creds

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


TOKEN = creds.read_all


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Поиск актива")
        self.geometry(f"{1100}x{580}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Тема:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Светлая", "Тёмная", "Система"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="Масштаб:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # create main entry and button
        self.entry = customtkinter.CTkEntry(self, placeholder_text="Введите ticker")
        self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")

        self.main_button_1 = customtkinter.CTkButton(master=self, text="Поиск", fg_color="transparent", border_width=2,
                                                     text_color=("gray10", "#DCE4EE"), command=self.search_event)
        self.main_button_1.grid(row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # create textbox
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")


    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def sidebar_button_event(self):
        print("sidebar_button click")

    def search_event(self):
        TICKER = self.entry.get()
        with Client(TOKEN) as client:
            # print(client.users.get_accounts())
            instruments: InstrumentsService = client.instruments

            l = []
            for method in ['shares', 'bonds', 'etfs']:
                for item in getattr(instruments, method)().instruments:
                    l.append({
                        'Name:': item.name,
                        'Ticker:': item.ticker,
                        'Figi:': item.figi,
                        'Currency:': item.currency,
                        'Trading status:': item.trading_status,
                        'Sector:': item.sector
                    })
            df = pd.DataFrame(l)

            df = df[df['Ticker:'] == TICKER]
            if df.empty:
                print("Не найдено")
                return

            print(df.iloc[0])
            self.textbox.delete('1.0', tkinter.END)
            self.textbox.insert(tkinter.END, df.iloc[0], tags=None)
            return df.iloc[0]


if __name__ == "__main__":
    app = App()
    app.mainloop()