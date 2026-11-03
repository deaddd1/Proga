import sqlite3
import time
from datetime import datetime
import customtkinter as ctk

# --- Ініціалізація бази даних SQLite ---
def init_db():
    conn = sqlite3.connect("focus_sessions.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            completed_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_session(task_name, duration_minutes):
    conn = sqlite3.connect("focus_sessions.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (task_name, duration_minutes, completed_at)
        VALUES (?, ?, ?)
    """, (task_name, duration_minutes, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_recent_sessions(limit=5):
    conn = sqlite3.connect("focus_sessions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT task_name, completed_at FROM sessions ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- Головний клас програми ---
class NeonFocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування вікна
        self.title("NeonFocus // Work Tracker")
        self.geometry("460x620")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        # Константи таймера (у секундах для тестів можна зменшити)
        self.WORK_TIME = 25 * 60
        self.BREAK_TIME = 5 * 60
        self.current_time_left = self.WORK_TIME
        self.total_target_time = self.WORK_TIME

        self.is_running = False
        self.is_work_period = True
        self.timer_job = None

        init_db()
        self._create_widgets()
        self._refresh_history()

    def _create_widgets(self):
        # Фоновий контейнер
        self.main_frame = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="NEON FOCUS",
            font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
            text_color="#10B981"
        )
        self.title_label.pack(pady=(25, 5))

        self.mode_label = ctk.CTkLabel(
            self.main_frame,
            text="• FOCUS MODE •",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#94A3B8"
        )
        self.mode_label.pack(pady=(0, 15))

        # Поле введення завдання
        self.task_entry = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Над чим працюєте? (напр., Дослідження)",
            width=320,
            height=38,
            corner_radius=8,
            fg_color="#1E293B",
            border_color="#334155",
            text_color="#F8FAFC"
        )
        self.task_entry.pack(pady=(0, 20))
        self.task_entry.insert(0, "Deep Work Session")

        # Цифровий циферблат
        self.timer_label = ctk.CTkLabel(
            self.main_frame,
            text=self._format_time(self.current_time_left),
            font=ctk.CTkFont(family="Consolas", size=64, weight="bold"),
            text_color="#F8FAFC"
        )
        self.timer_label.pack(pady=(10, 15))

        # Смуга прогресу
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            width=320,
            height=8,
            corner_radius=4,
            progress_color="#10B981",
            fg_color="#1E293B"
        )
        self.progress_bar.set(1.0)
        self.progress_bar.pack(pady=(0, 25))

        # Кнопки керування
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(pady=(0, 25))

        self.start_btn = ctk.CTkButton(
            self.button_frame,
            text="START",
            command=self.toggle_timer,
            width=100,
            height=36,
            corner_radius=6,
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#0F172A",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold")
        )
        self.start_btn.grid(row=0, column=0, padx=8)

        self.reset_btn = ctk.CTkButton(
            self.button_frame,
            text="RESET",
            command=self.reset_timer,
            width=100,
            height=36,
            corner_radius=6,
            fg_color="#334155",
            hover_color="#475569",
            text_color="#F8FAFC",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold")
        )
        self.reset_btn.grid(row=0, column=1, padx=8)

        # Секція історії (SQLite)
        self.history_title = ctk.CTkLabel(
            self.main_frame,
            text="ОСТАННІ ЗАВЕРШЕНІ СЕСІЇ",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#64748B"
        )
        self.history_title.pack(anchor="w", padx=70, pady=(10, 4))

        self.history_box = ctk.CTkTextbox(
            self.main_frame,
            width=320,
            height=110,
            corner_radius=8,
            fg_color="#1E293B",
            text_color="#CBD5E1",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.history_box.pack()
        self.history_box.configure(state="disabled")

    def _format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def toggle_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_btn.configure(text="PAUSE", fg_color="#F59E0B", hover_color="#D97706")
            self._tick()
        else:
            self.is_running = False
            self.start_btn.configure(text="RESUME", fg_color="#10B981", hover_color="#059669")
            if self.timer_job:
                self.after_cancel(self.timer_job)

    def _tick(self):
        if self.is_running and self.current_time_left > 0:
            self.current_time_left -= 1
            self.timer_label.configure(text=self._format_time(self.current_time_left))
            
            progress = self.current_time_left / self.total_target_time
            self.progress_bar.set(progress)
            
            self.timer_job = self.after(1000, self._tick)
        elif self.current_time_left == 0:
            self._handle_session_end()

    def _handle_session_end(self):
        self.is_running = False
        if self.is_work_period:
            task = self.task_entry.get().strip() or "Без назви"
            log_session(task, self.WORK_TIME // 60)
            self._refresh_history()
            
            # Перемикання на перерву
            self.is_work_period = False
            self.current_time_left = self.BREAK_TIME
            self.total_target_time = self.BREAK_TIME
            self.mode_label.configure(text="• SHORT BREAK •", text_color="#38BDF8")
            self.progress_bar.configure(progress_color="#38BDF8")
            self.start_btn.configure(text="START", fg_color="#38BDF8", hover_color="#0284C7")
        else:
            # Перемикання назад на роботу
            self.is_work_period = True
            self.current_time_left = self.WORK_TIME
            self.total_target_time = self.WORK_TIME
            self.mode_label.configure(text="• FOCUS MODE •", text_color="#94A3B8")
            self.progress_bar.configure(progress_color="#10B981")
            self.start_btn.configure(text="START", fg_color="#10B981", hover_color="#059669")

        self.timer_label.configure(text=self._format_time(self.current_time_left))
        self.progress_bar.set(1.0)

    def reset_timer(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.is_running = False
        self.current_time_left = self.WORK_TIME if self.is_work_period else self.BREAK_TIME
        self.total_target_time = self.current_time_left
        self.timer_label.configure(text=self._format_time(self.current_time_left))
        self.progress_bar.set(1.0)
        self.start_btn.configure(
            text="START",
            fg_color="#10B981" if self.is_work_period else "#38BDF8",
            hover_color="#059669" if self.is_work_period else "#0284C7"
        )

    def _refresh_history(self):
        sessions = get_recent_sessions(limit=4)
        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        if not sessions:
            self.history_box.insert("end", "Історія порожня.\nПочніть першу сесію!")
        else:
            for task, dt in sessions:
                time_only = dt.split()[1] if " " in dt else dt
                self.history_box.insert("end", f"✓ [{time_only}] {task[:22]}\n")
        self.history_box.configure(state="disabled")

if __name__ == "__main__":
    app = NeonFocusApp()
    app.mainloop()