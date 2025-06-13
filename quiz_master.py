import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import json
import os

class QuizMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Master")

        self.data = None
        self.filtered_data = pd.DataFrame()
        self.current_question_index = 0
        self.used_questions = set()

        self.scores = {}
        self.current_team = tk.StringVar()
        self.teams = [f"Team {chr(65+i)}" for i in range(15)]
        for team in self.teams:
            self.scores[team] = {}

        self.create_widgets()

    def create_widgets(self):
        filter_frame = tk.Frame(self.root)
        filter_frame.pack(pady=10)

        tk.Label(filter_frame, text="Round:").grid(row=0, column=0)
        self.round_filter = ttk.Combobox(filter_frame, state="readonly")
        self.round_filter.grid(row=0, column=1)

        tk.Label(filter_frame, text="Type:").grid(row=0, column=2)
        self.type_filter = ttk.Combobox(filter_frame, state="readonly")
        self.type_filter.grid(row=0, column=3)

        tk.Label(filter_frame, text="Sub Type:").grid(row=0, column=4)
        self.subtype_filter = ttk.Combobox(filter_frame, state="readonly")
        self.subtype_filter.grid(row=0, column=5)

        tk.Button(filter_frame, text="Apply Filters", command=self.apply_filters).grid(row=0, column=6, padx=5)
        tk.Button(filter_frame, text="Reset Filters", command=self.reset_filters).grid(row=0, column=7, padx=5)

        self.remaining_label = tk.Label(self.root, text="")
        self.remaining_label.pack()

        self.load_button = tk.Button(self.root, text="Load Quiz File", command=self.load_file)
        self.load_button.pack(pady=5)

        self.question_label = tk.Label(self.root, text="", font=('Arial', 14), wraplength=600, justify="center")
        self.question_label.pack(pady=10)

        self.answer_label = tk.Label(self.root, text="", font=('Arial', 12), fg='blue')
        self.answer_label.pack(pady=5)

        team_frame = tk.Frame(self.root)
        team_frame.pack()
        tk.Label(team_frame, text="Answering Team:").pack(side=tk.LEFT)

        self.team_selector = ttk.Combobox(
            team_frame, values=self.teams, textvariable=self.current_team, state="normal"
        )
        self.team_selector.pack(side=tk.LEFT)
        self.team_selector.set("Team A")

        self.team_selector.bind("<FocusIn>", self.select_all_text)
        self.team_selector.bind("<KeyRelease>", self.team_autoselect)

        tk.Button(team_frame, text="Next Team", command=self.next_team).pack(side=tk.LEFT, padx=5)

        score_frame = tk.Frame(self.root)
        score_frame.pack(pady=5)
        tk.Button(score_frame, text="Award 10 Points", command=self.award_point).pack(side=tk.LEFT, padx=5)
        tk.Button(score_frame, text="Deduct 10 Points", command=self.deduct_point).pack(side=tk.LEFT, padx=5)
        tk.Button(score_frame, text="Next Question", command=self.next_question).pack(side=tk.LEFT, padx=5)

        self.score_label = tk.Label(self.root, text="")
        self.score_label.pack(pady=5)

        self.top_scorers_label = tk.Label(self.root, text="")
        self.top_scorers_label.pack(pady=5)

        action_frame = tk.Frame(self.root)
        action_frame.pack(pady=10)
        tk.Button(action_frame, text="Export Scores", command=self.export_scores).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Save Scores", command=self.save_scores).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Load Scores", command=self.load_scores).pack(side=tk.LEFT, padx=5)

    def select_all_text(self, event):
        event.widget.after(10, lambda: event.widget.select_range(0, 'end'))

    def team_autoselect(self, event):
        key = event.char.lower()
        for team in self.teams:
            if team.lower().startswith(f"team {key}"):
                self.team_selector.set(team)
                break

    def next_team(self):
        current = self.teams.index(self.current_team.get())
        next_index = (current + 1) % len(self.teams)
        self.team_selector.set(self.teams[next_index])

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                self.data = pd.read_excel(file_path)
                self.round_filter['values'] = sorted(self.data['Round'].dropna().unique())
                self.type_filter['values'] = sorted(self.data['Type'].dropna().unique())
                self.subtype_filter['values'] = sorted(self.data['Sub Type'].dropna().unique())
                self.filtered_data = self.data.copy()
                self.current_question_index = 0
                self.used_questions.clear()
                self.show_question()
                self.update_remaining_label()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def apply_filters(self):
        if self.data is not None:
            self.filtered_data = self.data.copy()
            if self.round_filter.get():
                self.filtered_data = self.filtered_data[self.filtered_data['Round'] == self.round_filter.get()]
            if self.type_filter.get():
                self.filtered_data = self.filtered_data[self.filtered_data['Type'] == self.type_filter.get()]
            if self.subtype_filter.get():
                self.filtered_data = self.filtered_data[self.filtered_data['Sub Type'] == self.subtype_filter.get()]
            self.filtered_data = self.filtered_data[~self.filtered_data.index.isin(self.used_questions)]
            self.current_question_index = 0
            self.show_question()
            self.update_remaining_label()

    def reset_filters(self):
        self.round_filter.set("")
        self.type_filter.set("")
        self.subtype_filter.set("")
        if self.data is not None:
            self.filtered_data = self.data[~self.data.index.isin(self.used_questions)]
            self.current_question_index = 0
            self.show_question()
            self.update_remaining_label()

    def update_remaining_label(self):
        remaining = len(self.filtered_data) if self.filtered_data is not None else 0
        self.remaining_label.config(text=f"Remaining Questions: {remaining}")

    def show_question(self):
        if not self.filtered_data.empty and self.current_question_index < len(self.filtered_data):
            row = self.filtered_data.iloc[self.current_question_index]
            self.current_index = row.name
            self.question_label.config(text=f"Q{self.current_question_index + 1}: {row['Question']}")
            self.answer_label.config(text=f"Answer: {row['Answer']}")
        else:
            self.question_label.config(text="Quiz Complete!")
            self.answer_label.config(text="")

    def award_point(self):
        team = self.current_team.get()
        if team in self.scores:
            round_name = self.filtered_data.loc[self.current_index, 'Round']
            self.scores[team][round_name] = self.scores[team].get(round_name, 0) + 10
            self.used_questions.add(self.current_index)
            self.apply_filters()
            self.update_scores()

    def deduct_point(self):
        team = self.current_team.get()
        if team in self.scores:
            round_name = self.filtered_data.loc[self.current_index, 'Round']
            self.scores[team][round_name] = self.scores[team].get(round_name, 0) - 10
            self.used_questions.add(self.current_index)
            self.apply_filters()
            self.update_scores()

    def next_question(self):
        self.current_question_index += 1
        self.show_question()

    def update_scores(self):
        score_text = "Scores:\n"
        all_totals = {}
        for team, rounds in self.scores.items():
            total = sum(rounds.values())
            all_totals[team] = total
            round_scores = ", ".join([f"{r}: {s}" for r, s in rounds.items()])
            score_text += f"{team} - {round_scores} | Total: {total}\n"
        self.score_label.config(text=score_text)

        top_teams = sorted(all_totals.items(), key=lambda x: x[1], reverse=True)[:3]
        top_text = "Top Scorers:\n" + "\n".join([f"{t[0]}: {t[1]}" for t in top_teams])
        self.top_scorers_label.config(text=top_text)

    def export_scores(self):
        rows = []
        all_rounds = sorted({r for scores in self.scores.values() for r in scores})
        for team, round_scores in self.scores.items():
            row = {'Team': team}
            total = 0
            for r in all_rounds:
                score = round_scores.get(r, 0)
                row[r] = score
                total += score
            row['Total'] = total
            rows.append(row)
        df = pd.DataFrame(rows)
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Export Successful", f"Scores exported successfully!\nQuestions exported: {len(self.used_questions)}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def save_scores(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(self.scores, f)
            messagebox.showinfo("Saved", "Scores saved successfully!")

    def load_scores(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                self.scores = json.load(f)
            self.update_scores()
            messagebox.showinfo("Loaded", "Scores loaded successfully!")

if __name__ == '__main__':
    root = tk.Tk()
    app = QuizMasterApp(root)
    root.mainloop()
