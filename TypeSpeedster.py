import tkinter as tk
from tkinter import Text, INSERT, Scrollbar, Label, Entry, Button, Listbox, END
import random
import time
import sqlite3

class TypingSpeedTester:
    def __init__(self, master, participants):
        self.master = master
        self.master.title("Typing Speed Tester")
        self.master.geometry("500x400")  # Set the main window size
        self.master.configure(bg='#3498db')  # Set background color

        self.participants = participants
        self.current_participant_index = 0
        self.participant_results = []
        self.backspace_enabled = True  # Flag to enable/disable backspacing

        self.sentence_text = Text(master, height=6, wrap="word", font=("Helvetica", 16), bg='#ecf0f1', state=tk.DISABLED, width=50)
        self.sentence_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.scrollbar = Scrollbar(master, command=self.sentence_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sentence_text.config(yscrollcommand=self.scrollbar.set)

        self.instruction_label = Label(master, text="", font=("Helvetica", 12), fg='#2ecc71')
        self.instruction_label.pack(pady=5)

        self.result_label = Label(master, text="", font=("Helvetica", 12), fg='#2ecc71')
        self.result_label.pack(pady=10)

        self.entry = Entry(master, font=("Helvetica", 12), width=40, state=tk.DISABLED)  # Set the width here
        self.entry.pack(pady=10)

        self.start_button = Button(master, text="Start Typing", command=self.start_typing, font=("Helvetica", 12), bg='#2ecc71', fg='white')
        self.start_button.pack(pady=5)

        self.final_window_button = Button(master, text="Show Final Results", command=self.show_final_results, font=("Helvetica", 12), bg='#00008B', fg='white', state=tk.DISABLED)
        self.final_window_button.pack(pady=5)

        self.display_data_button = Button(master, text="Display All Data", command=self.display_all_data, font=("Helvetica", 12), bg='#FFD700', fg='black')
        self.display_data_button.pack(pady=5)

        # Connect to SQLite database
        self.conn = sqlite3.connect("typing_test_final_results.db")
        self.create_table()

        self.reset()

    def create_table(self):
        # Create a table if it doesn't exist
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS typing_results (
                participant_name TEXT,
                accuracy REAL,
                words_per_minute REAL
            );
        '''
        self.conn.execute(create_table_query)
        self.conn.commit()

    def generate_sentence(self):
        sentences = [
            "The quick brown fox jumps over the lazy dog.",
            "Programming is fun and challenging.",
            "Python is a powerful programming language.",
            "Keep calm and code on.",
            "Learning to code opens up new possibilities.",
            "Coding is the language of the future."
        ]
        return random.choice(sentences)

    def start_typing(self):
        if self.current_participant_index < len(self.participants):
            self.participant_name = self.participants[self.current_participant_index]
            self.sentence = self.generate_sentence()

            self.sentence_text.config(state=tk.NORMAL)
            self.sentence_text.delete("1.0", tk.END)
            self.sentence_text.insert(INSERT, self.sentence)
            self.sentence_text.config(state=tk.DISABLED)

            self.instruction_label.config(text=f"{self.participant_name}, type the sentence below:")
            self.start_time = time.time()
            self.entry.config(state=tk.NORMAL)
            self.entry.bind('<Return>', self.check_typing)
            self.entry.bind('<Key>', self.handle_keypress)
            self.start_button.config(state=tk.DISABLED)

            if self.current_participant_index == 0:
                self.entry.focus_set()

        else:
            self.show_final_results()

    def check_typing(self, event):
        typed_text = self.entry.get()
        words = self.sentence.split()
        typed_words = typed_text.split()

        elapsed_time = time.time() - self.start_time
        correct_letters = sum(len(word) for word in typed_words if word in words)
        words_per_minute = ((correct_letters/5) / elapsed_time) * 60 if elapsed_time > 0 else 0
        total_letters = sum(len(word) for word in words)

        # Penalize for backspacing
        backspace_penalty = len(typed_text) - len(typed_text.rstrip())

        # Adjust correct letters based on backspace penalty
        correct_letters -= backspace_penalty

        accuracy = (correct_letters / total_letters) * 100 if total_letters > 0 else 0

        # Calculate combined score
        combined_score = (0.8 * words_per_minute) + (0.2 * accuracy)

        result_text = f"{self.participant_name}'s Accuracy: {accuracy:.2f}%, Speed: {words_per_minute:.2f} wpm"
        self.result_label.config(text=result_text)

        # Save participant name and results to the database
        self.conn.execute("INSERT INTO typing_results VALUES (?, ?, ?)", (self.participant_name, accuracy, words_per_minute))
        self.conn.commit()

        self.participant_results.append((self.participant_name, accuracy, words_per_minute, combined_score))

        self.current_participant_index += 1
        self.reset()
        self.backspace_enabled = False  # Disable backspacing after the first key has been pressed

    def handle_keypress(self, event):
        if event.keysym == 'BackSpace' and not self.backspace_enabled:
            self.entry.delete(len(self.entry.get()) - 1, tk.END)  # Delete the last character to prevent backspacing

    def reset(self):
        self.entry.delete(0, tk.END)
        self.entry.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.result_label.config(text="")
        if self.current_participant_index < len(self.participants):
            self.instruction_label.config(text=f"{self.participants[self.current_participant_index]}, press Enter to start typing:")
        else:
            self.instruction_label.config(text="All participants have completed the test.")
            self.final_window_button.config(state=tk.NORMAL)

    def show_final_results(self):
        final_window = tk.Toplevel(self.master)
        final_window.title("Final Results")

        # Sort participants by combined score in descending order
        self.participant_results.sort(key=lambda x: x[3], reverse=True)

        listbox = Listbox(final_window, font=("Helvetica", 12), selectbackground='#3498db', selectmode=tk.SINGLE)
        listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        for participant in self.participant_results:
            listbox.insert(tk.END, f"{participant[0]} - Accuracy: {participant[1]:.2f}%, Speed: {participant[2]:.2f} wpm, Combined Score: {participant[3]:.2f}")

        fastest_typist = self.participant_results[0] if self.participant_results else ("No participants", 0, 0, 0)
        fastest_label = Label(final_window, text=f"Fastest Typist: {fastest_typist[0]} with {fastest_typist[2]:.2f} wpm, {fastest_typist[1]:.2f}% accuracy, Combined Score: {fastest_typist[3]:.2f}", font=("Helvetica", 12), fg='#2ecc71')
        fastest_label.pack(pady=10)

        final_window.mainloop()

    def display_all_data(self):
        # Fetch all records from the database and display them in the terminal
        cursor = self.conn.execute("SELECT * FROM typing_results")
        records = cursor.fetchall()

        if not records:
            print("No records found.")
        else:
            print("All Records:")
            for record in records:
                print(record)

if __name__ == "__main__":
    participants_window = tk.Tk()
    participants_window.title("Participant Names")
    participants_label = Label(participants_window, text="Enter participant names (comma-separated):", font=("Helvetica", 12), fg='#2ecc71')
    participants_label.pack(pady=10)
    participants_entry = Entry(participants_window, font=("Helvetica", 12), width=40)
    participants_entry.pack(pady=10)
    participants_button = Button(participants_window, text="Submit", command=lambda: participants_window.quit(), font=("Helvetica", 12), bg='#2ecc71', fg='white')
    participants_button.pack(pady=10)
    participants_window.mainloop()

    participant_names = participants_entry.get().split(',')

    root = tk.Tk()
    app = TypingSpeedTester(root, participant_names)
    root.mainloop()
