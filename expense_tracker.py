# expense_tracker.py
# Pastel-themed Expense Tracker (Tkinter + sqlite3)
# Save and run: python expense_tracker.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import csv
import os
from math import pi, sin, cos

DB = "expenses.db"

# -------------------------
# Database helpers
# -------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS expenses (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT NOT NULL,
                 amount REAL NOT NULL,
                 category TEXT,
                 date TEXT NOT NULL,
                 note TEXT)""")
    conn.commit()
    conn.close()

def run_query(query, params=()):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    rows = c.fetchall()
    conn.close()
    return rows

# -------------------------
# UI constants (pastel)
# -------------------------
BG = "#fff9fb"
CARD = "#fff4f8"
ACCENT = "#FFB6C1"   # light pink
ACCENT2 = "#CBE7E6"  # mint
TEXT = "#42323a"
MUTED = "#8a6f74"
FONT = ("Helvetica", 11)
BIG_FONT = ("Helvetica", 16, "bold")
SMALL = ("Helvetica", 9)

CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"]
CATEGORY_COLORS = {
    "Food": "#FFD1DC",
    "Transport": "#CDEDF6",
    "Shopping": "#FFE6C2",
    "Bills": "#E5D8FF",
    "Entertainment": "#FDE2F3",
    "Other": "#DFF8E2"
}

# -------------------------
# App
# -------------------------
class ExpenseTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aishu's Pastel Expense Tracker")
        self.geometry("980x640")
        self.configure(bg=BG)
        self.minsize(900, 600)
        self.style = ttk.Style(self)
        self.setup_style()
        init_db()
        self.selected_id = None
        self.create_header()
        self.create_main_layout()
        self.refresh_list()

    def setup_style(self):
        self.style.theme_use('clam')
        self.style.configure("TLabel", background=BG, foreground=TEXT, font=FONT)
        self.style.configure("Header.TLabel", font=BIG_FONT, background=BG, foreground=TEXT)
        self.style.configure("Accent.TButton", font=FONT, background=ACCENT, foreground=TEXT)
        self.style.map("Accent.TButton", background=[('active', ACCENT2)])
        self.style.configure("Small.TButton", font=SMALL)
        self.style.configure("Treeview", rowheight=30, font=FONT)
        self.style.configure("TEntry", padding=5)

    def create_header(self):
        header = tk.Frame(self, bg=BG, height=80)
        header.pack(fill='x', padx=12, pady=(12,6))
        left = tk.Frame(header, bg=BG)
        left.pack(side='left', anchor='nw')
        ttk.Label(left, text="Pastel Expense Tracker", style="Header.TLabel").pack(anchor='w')
        ttk.Label(left, text="cute. soft. organized.", font=SMALL, foreground=MUTED).pack(anchor='w')

        # Decorative canvas icon
        icon = tk.Canvas(header, width=120, height=60, bg=BG, highlightthickness=0)
        icon.pack(side='right', padx=10)
        icon.create_oval(8,8,48,48, fill="#FFF0F5", outline="")
        icon.create_text(86,30, text="Aishu's 💸", font=("Helvetica",10,"bold"), fill=MUTED)

    def create_main_layout(self):
        main = tk.Frame(self, bg=BG)
        main.pack(fill='both', expand=True, padx=12, pady=6)

        # Left card - form + chart
        left_card = tk.Frame(main, bg=CARD, bd=0, relief='flat')
        left_card.pack(side='left', fill='y', padx=(0,8), pady=6)
        left_card.config(width=360)
        left_card.pack_propagate(False)

        # Form
        frm = tk.Frame(left_card, bg=CARD, pady=10, padx=12)
        frm.pack(fill='x')
        ttk.Label(frm, text="Add / Edit Expense", font=("Helvetica",13,"bold")).pack(anchor='w', pady=(2,8))

        self.title_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.date_var = tk.StringVar(value=datetime.date.today().isoformat())
        self.note_var = tk.StringVar()

        def add_field(label, var, hint=""):
            ttk.Label(frm, text=label).pack(anchor='w', pady=(6,2))
            e = ttk.Entry(frm, textvariable=var)
            e.pack(fill='x')
            if hint:
                ttk.Label(frm, text=hint, font=SMALL, foreground=MUTED).pack(anchor='w')

        add_field("Title", self.title_var)
        add_field("Amount (₹)", self.amount_var)
        ttk.Label(frm, text="Category").pack(anchor='w', pady=(6,2))
        cat_frame = tk.Frame(frm, bg=CARD)
        cat_frame.pack(fill='x')
        # category dropdown & chips
        cat_dropdown = ttk.Combobox(cat_frame, values=CATEGORIES, textvariable=self.category_var, state="readonly")
        cat_dropdown.pack(side='left', fill='x', expand=True)
        ttk.Button(cat_frame, text="+ Add Cat", command=self.add_category, style="Small.TButton").pack(side='left', padx=6)

        ttk.Label(frm, text="Date (YYYY-MM-DD)").pack(anchor='w', pady=(8,2))
        ttk.Entry(frm, textvariable=self.date_var).pack(fill='x')

        ttk.Label(frm, text="Note").pack(anchor='w', pady=(8,2))
        ttk.Entry(frm, textvariable=self.note_var).pack(fill='x')

        btns = tk.Frame(frm, bg=CARD)
        btns.pack(fill='x', pady=10)
        ttk.Button(btns, text="Save", command=self.save_expense, style="Accent.TButton").pack(side='left', padx=(0,6))
        ttk.Button(btns, text="Clear", command=self.clear_form).pack(side='left')

        # Summary card (small)
        summary = tk.Frame(left_card, bg=CARD, pady=10, padx=12)
        summary.pack(fill='both', expand=True, pady=(8,0))
        ttk.Label(summary, text="Summary", font=("Helvetica",12,"bold")).pack(anchor='w')
        self.total_label = ttk.Label(summary, text="Total: ₹0", font=("Helvetica",14,"bold"))
        self.total_label.pack(anchor='w', pady=(8,6))

        # Category summary list
        self.cat_listbox = tk.Listbox(summary, height=6, borderwidth=0, highlightthickness=0, font=FONT)
        self.cat_listbox.pack(fill='both', expand=True, pady=(4,8))

        # Simple pie chart area
        chart_card = tk.Frame(left_card, bg=CARD, pady=6, padx=6)
        chart_card.pack(fill='x')
        self.canvas_chart = tk.Canvas(chart_card, width=320, height=180, bg=CARD, highlightthickness=0)
        self.canvas_chart.pack()

        # Right area - list and controls
        right = tk.Frame(main, bg=BG)
        right.pack(side='left', fill='both', expand=True)

        controls = tk.Frame(right, bg=BG)
        controls.pack(fill='x', pady=(0,6))

        ttk.Label(controls, text="Search / Filter:").pack(side='left', padx=(0,6))
        self.search_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.search_var).pack(side='left', padx=6)
        ttk.Button(controls, text="Search", command=self.search_items).pack(side='left', padx=6)
        ttk.Button(controls, text="Show All", command=self.refresh_list).pack(side='left', padx=6)

        # Date filter
        ttk.Label(controls, text="From").pack(side='left', padx=(20,4))
        self.from_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.from_var, width=12).pack(side='left')
        ttk.Label(controls, text="To").pack(side='left', padx=(8,4))
        self.to_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.to_var, width=12).pack(side='left')
        ttk.Button(controls, text="Filter", command=self.filter_by_date).pack(side='left', padx=6)

        # List (Treeview)
        columns = ("id", "title", "amount", "category", "date")
        self.tree = ttk.Treeview(right, columns=columns, show='headings', selectmode='browse')
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40, anchor='center')
        self.tree.heading("title", text="Title")
        self.tree.column("title", width=240)
        self.tree.heading("amount", text="Amount (₹)")
        self.tree.column("amount", width=110, anchor='e')
        self.tree.heading("category", text="Category")
        self.tree.column("category", width=120)
        self.tree.heading("date", text="Date")
        self.tree.column("date", width=100)
        self.tree.pack(fill='both', expand=True, pady=(6,0))

        # action buttons
        action_frame = tk.Frame(right, bg=BG)
        action_frame.pack(fill='x', pady=8)
        ttk.Button(action_frame, text="Edit", command=self.load_selected).pack(side='left', padx=6)
        ttk.Button(action_frame, text="Delete", command=self.delete_selected).pack(side='left', padx=6)
        ttk.Button(action_frame, text="Export CSV", command=self.export_csv).pack(side='left', padx=6)

    # -------------------------
    # Functionality
    # -------------------------
    def add_category(self):
        new = tk.simpledialog.askstring("New Category", "Enter category name:")
        if new and new.strip():
            cat = new.strip()
            if cat not in CATEGORIES:
                CATEGORIES.append(cat)
                CATEGORY_COLORS[cat] = "#F5E6FF"  # default pastel
                messagebox.showinfo("Added", f"Category '{cat}' added.")
            else:
                messagebox.showinfo("Exists", "Category already exists.")

    def save_expense(self):
        title = self.title_var.get().strip()
        amt = self.amount_var.get().strip()
        cat = self.category_var.get().strip() or "Other"
        date = self.date_var.get().strip()
        note = self.note_var.get().strip()
        if not title or not amt:
            messagebox.showerror("Error", "Title and Amount are required.")
            return
        try:
            amt_f = float(amt)
        except:
            messagebox.showerror("Error", "Amount must be a number.")
            return
        # validate date
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except:
            messagebox.showerror("Error", "Date must be YYYY-MM-DD.")
            return

        if self.selected_id:
            run_query("UPDATE expenses SET title=?, amount=?, category=?, date=?, note=? WHERE id=?",
                      (title, amt_f, cat, date, note, self.selected_id))
            messagebox.showinfo("Updated", "Expense updated.")
            self.selected_id = None
        else:
            run_query("INSERT INTO expenses (title, amount, category, date, note) VALUES (?,?,?,?,?)",
                      (title, amt_f, cat, date, note))
            messagebox.showinfo("Saved", "Expense saved.")
        self.clear_form()
        self.refresh_list()

    def clear_form(self):
        self.title_var.set("")
        self.amount_var.set("")
        self.category_var.set(CATEGORIES[0] if CATEGORIES else "Other")
        self.date_var.set(datetime.date.today().isoformat())
        self.note_var.set("")
        self.selected_id = None

    def refresh_list(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        rows = run_query("SELECT id,title,amount,category,date FROM expenses ORDER BY date DESC")
        total = 0
        for row in rows:
            self.tree.insert("", "end", values=row)
            total += row[2]
        self.total_label.config(text=f"Total: ₹{total:.2f}")
        self.update_category_summary()
        self.draw_chart()

    def search_items(self):
        q = self.search_var.get().strip()
        if not q:
            self.refresh_list()
            return
        for r in self.tree.get_children():
            self.tree.delete(r)
        rows = run_query("""SELECT id,title,amount,category,date FROM expenses
                            WHERE title LIKE ? OR category LIKE ? OR note LIKE ?
                            ORDER BY date DESC""", (f"%{q}%", f"%{q}%", f"%{q}%"))
        total = 0
        for row in rows:
            self.tree.insert("", "end", values=row)
            total += row[2]
        self.total_label.config(text=f"Total: ₹{total:.2f}")
        self.update_category_summary(rows)
        self.draw_chart(rows)

    def filter_by_date(self):
        f = self.from_var.get().strip()
        t = self.to_var.get().strip()
        try:
            if f: datetime.datetime.strptime(f, "%Y-%m-%d")
            if t: datetime.datetime.strptime(t, "%Y-%m-%d")
        except:
            messagebox.showerror("Error", "Dates must be YYYY-MM-DD.")
            return
        q = "SELECT id,title,amount,category,date FROM expenses WHERE 1=1"
        params = []
        if f:
            q += " AND date >= ?"
            params.append(f)
        if t:
            q += " AND date <= ?"
            params.append(t)
        q += " ORDER BY date DESC"
        rows = run_query(q, tuple(params))
        for r in self.tree.get_children():
            self.tree.delete(r)
        total = 0
        for row in rows:
            self.tree.insert("", "end", values=row)
            total += row[2]
        self.total_label.config(text=f"Total: ₹{total:.2f}")
        self.update_category_summary(rows)
        self.draw_chart(rows)

    def load_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select an expense to edit.")
            return
        vals = self.tree.item(sel[0], 'values')
        eid = vals[0]
        row = run_query("SELECT id,title,amount,category,date,note FROM expenses WHERE id=?", (eid,))
        if not row:
            return
        r = row[0]
        self.selected_id = r[0]
        self.title_var.set(r[1])
        self.amount_var.set(str(r[2]))
        self.category_var.set(r[3])
        self.date_var.set(r[4])
        self.note_var.set(r[5] or "")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select an expense to delete.")
            return
        vals = self.tree.item(sel[0], 'values')
        eid = vals[0]
        if messagebox.askyesno("Confirm", "Delete this expense?"):
            run_query("DELETE FROM expenses WHERE id=?", (eid,))
            messagebox.showinfo("Deleted", "Expense deleted.")
            self.refresh_list()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path:
            return
        rows = run_query("SELECT id,title,amount,category,date,note FROM expenses ORDER BY date DESC")
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["ID","Title","Amount","Category","Date","Note"])
            w.writerows(rows)
        messagebox.showinfo("Exported", f"Exported {len(rows)} rows to {os.path.basename(path)}")

    def update_category_summary(self, rows=None):
        if rows is None:
            rows = run_query("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        else:
            # rows is list of tuples from treeview or query; produce summary
            sums = {}
            for r in rows:
                cat = r[3]
                sums[cat] = sums.get(cat, 0) + float(r[2])
            rows = [(k, v) for k, v in sums.items()]

        # Clear listbox
        self.cat_listbox.delete(0, 'end')
        total = 0
        for cat, amt in rows:
            total += amt
            display = f"{cat}: ₹{amt:.2f}"
            self.cat_listbox.insert('end', display)
        if not rows:
            self.cat_listbox.insert('end', "No records yet.")

    def draw_chart(self, rows=None):
        # Draw a simple pie-like chart on canvas
        self.canvas_chart.delete("all")
        w = 320; h = 180; cx = w//2; cy = h//2; r = 60
        if rows is None:
            rows = run_query("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        data = [(cat, amt) for cat, amt in rows if amt and float(amt) > 0] if rows else []
        if not data:
            self.canvas_chart.create_text(cx, cy, text="No data to show", fill=MUTED, font=FONT)
            return
        total = sum([float(x[1]) for x in data])
        angle_start = 0
        # palette fallback
        pal = list(CATEGORY_COLORS.values())
        i = 0
        legend_x = 10
        for cat, amt in data:
            frac = float(amt) / total
            angle = frac * 360
            color = CATEGORY_COLORS.get(cat, pal[i % len(pal)])
            # arc (simulate by many small polygons)
            self.canvas_chart.create_arc(cx-r, cy-r, cx+r, cy+r, start=angle_start, extent=angle, fill=color, outline="")
            # legend
            lx = legend_x; ly = 10 + i*22
            self.canvas_chart.create_rectangle(lx, ly, lx+14, ly+14, fill=color, outline="")
            self.canvas_chart.create_text(lx+20, ly+7, anchor='w', text=f"{cat} ₹{float(amt):.0f}", font=SMALL, fill=TEXT)
            angle_start += angle
            i += 1

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    init_db()
    app = ExpenseTracker()
    app.mainloop()
