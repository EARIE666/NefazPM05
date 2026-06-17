import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import Database

class WarehouseApp:
    def __init__(self, root):
        self.db = Database()
        self.root = root
        self.root.title("ИС Учёт складских комплектующих - ПАО НЕФАЗ")
        self.root.geometry("800x500")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_products = ttk.Frame(self.notebook)
        self.tab_operations = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_products, text="Товары")
        self.notebook.add(self.tab_operations, text="Операции")
        self.notebook.add(self.tab_reports, text="Отчёты")

        self.init_products_tab()
        self.init_operations_tab()
        self.init_reports_tab()

        self.load_products()

    # ---------- Вкладка Товары ----------
    def init_products_tab(self):
        frame_top = ttk.Frame(self.tab_products)
        frame_top.pack(fill="x", pady=5)

        ttk.Label(frame_top, text="Поиск:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        ttk.Entry(frame_top, textvariable=self.search_var).pack(side="left", padx=5)
        ttk.Button(frame_top, text="Найти",
                   command=self.search_products).pack(side="left", padx=5)
        ttk.Button(frame_top, text="Сбросить",
                   command=self.load_products).pack(side="left", padx=5)

        columns = ("id", "name", "article", "unit", "quantity")
        self.tree = ttk.Treeview(self.tab_products, columns=columns, show="headings")
        for col, text in zip(columns,
                             ["ID", "Наименование", "Артикул", "Ед.изм.", "Остаток"]):
            self.tree.heading(col, text=text)
        self.tree.pack(fill="both", expand=True, pady=5)

        frame_btn = ttk.Frame(self.tab_products)
        frame_btn.pack(fill="x", pady=5)
        ttk.Button(frame_btn, text="Добавить",
                   command=self.add_product_window).pack(side="left", padx=5)
        ttk.Button(frame_btn, text="Удалить",
                   command=self.delete_product).pack(side="left", padx=5)

    def load_products(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in self.db.get_products():
            self.tree.insert("", "end",
                             values=(row[0], row[1], row[2], row[3], row[5]))

    def search_products(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in self.db.get_products(self.search_var.get()):
            self.tree.insert("", "end",
                             values=(row[0], row[1], row[2], row[3], row[5]))

    def add_product_window(self):
        win = tk.Toplevel(self.root)
        win.title("Добавить товар")
        win.geometry("300x250")

        ttk.Label(win, text="Наименование:").pack(pady=2)
        e_name = ttk.Entry(win)
        e_name.pack(pady=2)

        ttk.Label(win, text="Артикул:").pack(pady=2)
        e_article = ttk.Entry(win)
        e_article.pack(pady=2)

        ttk.Label(win, text="Единица измерения:").pack(pady=2)
        e_unit = ttk.Entry(win)
        e_unit.pack(pady=2)

        def save():
            name = e_name.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите наименование!")
                return
            self.db.add_product(name, e_article.get(), e_unit.get(), None)
            self.load_products()
            self.refresh_operation_combo()
            win.destroy()

        ttk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар!")
            return
        pid = self.tree.item(selected[0])["values"][0]
        self.db.delete_product(pid)
        self.load_products()
        self.refresh_operation_combo()

    # ---------- Вкладка Операции ----------
    def init_operations_tab(self):
        frame = ttk.Frame(self.tab_operations)
        frame.pack(fill="x", pady=10)

        ttk.Label(frame, text="Товар:").grid(row=0, column=0, padx=5, pady=5)
        self.op_product = ttk.Combobox(frame, state="readonly", width=30)
        self.op_product.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Тип операции:").grid(row=1, column=0, padx=5, pady=5)
        self.op_type = ttk.Combobox(frame, state="readonly",
                                    values=["Приход", "Расход"])
        self.op_type.current(0)
        self.op_type.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Количество:").grid(row=2, column=0, padx=5, pady=5)
        self.op_amount = ttk.Entry(frame)
        self.op_amount.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(frame, text="Выполнить операцию",
                   command=self.do_operation).grid(row=3, column=1, pady=10)

        self.refresh_operation_combo()

    def refresh_operation_combo(self):
        self.products_map = {}
        names = []
        for row in self.db.get_products():
            display = f"{row[1]} ({row[2]})"
            names.append(display)
            self.products_map[display] = row[0]
        self.op_product["values"] = names
        if names:
            self.op_product.current(0)

    def do_operation(self):
        product = self.op_product.get()
        if not product:
            messagebox.showerror("Ошибка", "Выберите товар!")
            return
        try:
            amount = float(self.op_amount.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество!")
            return

        pid = self.products_map[product]
        op_type = self.op_type.get()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            self.db.add_operation(pid, op_type, amount, date)
            messagebox.showinfo("Успех", "Операция выполнена!")
            self.op_amount.delete(0, "end")
            self.load_products()
            self.load_reports()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    # ---------- Вкладка Отчёты ----------
    def init_reports_tab(self):
        columns = ("id", "product", "type", "amount", "date")
        self.tree_rep = ttk.Treeview(self.tab_reports, columns=columns,
                                     show="headings")
        for col, text in zip(columns,
                             ["ID", "Товар", "Тип", "Кол-во", "Дата"]):
            self.tree_rep.heading(col, text=text)
        self.tree_rep.pack(fill="both", expand=True, pady=5)

        ttk.Button(self.tab_reports, text="Обновить отчёт",
                   command=self.load_reports).pack(pady=5)
        self.load_reports()

    def load_reports(self):
        for i in self.tree_rep.get_children():
            self.tree_rep.delete(i)
        for row in self.db.get_operations():
            self.tree_rep.insert("", "end", values=row)


if __name__ == "__main__":
    root = tk.Tk()
    app = WarehouseApp(root)
    root.mainloop()