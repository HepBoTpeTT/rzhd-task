import cv2
import pandas as pd
import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path
from math import ceil, sqrt
# import asyncio
# from datetime import datetime

class SyncCheker:
    def __init__(self, window):
        self.window = window
        self.video_players = []

    def update_min_frame(self):
        global min_frame
        if min_frame >= max_frame: return

        min_frame += 0.2
        for video_player in self.video_players:
            video_player.update()
        self.window.after(speed, self.update_min_frame)


class VideoPlayer:
    def __init__(self, window, video_source, annotation, row, col):
        self.frame_id = 0
        self.previous_frame = None
        self.annotation_pd = annotation
        
        self.video_file = cv2.VideoCapture(video_source)
        self.canvas = tk.Canvas(window, width=int(self.video_file.get(cv2.CAP_PROP_FRAME_WIDTH)) / 2,
                                        height=int(self.video_file.get(cv2.CAP_PROP_FRAME_HEIGHT)) / 2,
                                background="black")
        self.canvas.grid(row=row, column=col)

        # self.update()

    def update(self):
        global is_playing
        try:
            next_frame_timestamp = self.annotation_pd.iloc[self.frame_id + 1].values[0]

            if (next_frame_timestamp - min_frame) // 0.1 <= 2 and is_playing:
                # print('----------', self.name, 'НОВЫЙ')

                ret, frame = self.video_file.read()

                if ret is not None:
                    self.previous_frame = frame

                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()

                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img = img.resize((canvas_width, canvas_height))

                    imgtk = ImageTk.PhotoImage(image=img)

                    self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                    self.canvas.imgtk = imgtk 
                self.frame_id += 1
                    


            else:
                # print('-', self.name, "СТАРЫЙ")

                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                frame = self.previous_frame

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = img.resize((canvas_width, canvas_height))

                imgtk = ImageTk.PhotoImage(image=img)

                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.imgtk = imgtk  # Сохраняем ссылку на изображение

        except Exception as e:
            print(f"{e} : {e.__class__.__name__}")

            if e.__class__.__name__ == "error":
                self.frame_id += 1
                

            if e is IndexError:
                self.video_file.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.frame_id = 0
                is_playing = False


def read_timestamps(file_path):
        return pd.read_csv(file_path, header=None)

def find_border_frames():
    min_frame = min([timestamps.min().values[0] for timestamps in all_timestamps])
    max_frame = max([timestamps.max().values[0] for timestamps in all_timestamps])

    return [min_frame, max_frame]



def main():
    root = tk.Tk()

    root.title("Video Player Test Task")
    root.resizable(True, True)

    speed_buttons_frame = tk.Frame(root)
    speed_buttons_frame.grid(row=3, column=0)

    button1 = tk.Button(speed_buttons_frame, text="x0.2", command=lambda: change_speed(0.2), background="black", foreground="white")
    button1.grid(row=0, column=0)

    button2 = tk.Button(speed_buttons_frame, text="x1", command=lambda: change_speed(1), background="black", foreground="white")
    button2.grid(row=0, column=1)

    button3 = tk.Button(speed_buttons_frame, text="x10", command=lambda: change_speed(10), background="black", foreground="white")
    button3.grid(row=0, column=2)

    button3 = tk.Button(root, text="play / pause", command=lambda: play_pause(), background="black", foreground="white")
    button3.grid(row=3, column=1)    

    cells = ceil(sqrt(len(video_paths)))
    sync = SyncCheker(root)

    for index, video_path in enumerate(video_paths):
        row = index // cells if index > 0 else 0
        col = index % cells if index > 0 else 0
        sync.video_players.append(VideoPlayer(root, video_path, all_timestamps[index], row, col))
        # print('----------------', (datetime.now() - start_time).total_seconds())
    sync.update_min_frame()

    root.mainloop()
        
def change_speed(speed_new):
    global speed
    speed = int(200//speed_new)

def play_pause():
    global is_playing
    is_playing = not is_playing

if __name__ == "__main__":
    speed = 200
    is_playing = True
    video_paths = [i for i in Path('data').iterdir() if i.suffix == ".avi"]
    annotations = [i.with_suffix(".txt") for i in video_paths]
    all_timestamps = [read_timestamps(i) for i in annotations]
    min_frame, max_frame = find_border_frames()

    main()