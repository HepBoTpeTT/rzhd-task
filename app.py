import cv2
import pandas as pd
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from pathlib import Path
from math import ceil

class SyncCheker:
    def __init__(self, window):
        self.window = window
        self.video_players = []

    def update_min_frame(self):
        global min_frame
        if min_frame >= max_frame: return

        if is_playing:
            min_frame += 0.2 #Обновление минимальной временной метки 
            for player in self.video_players: player.update() #Обновление кадра для каждого объекта видеоплеера
            print('--------------------------')

        self.window.after(200, self.update_min_frame) #Функция запускается раз в speed времени главным окном tkinter


class VideoPlayer:
    def __init__(self, window, video_source, annotation, row, col):
        self.frame_id = 0
        self.name = int(f"{row}{col}", 2)
        self.previous_frame = None
        self.annotation_pd = annotation
        self.is_able_to_play = True
        
        self.video_file = cv2.VideoCapture(video_source)

        # Настройка канваса
        self.canvas_width = int(self.video_file.get(cv2.CAP_PROP_FRAME_WIDTH)) // 2
        self.canvas_height = int(self.video_file.get(cv2.CAP_PROP_FRAME_HEIGHT)) // 2
        self.canvas = tk.Canvas(window, width=self.canvas_width, height=self.canvas_height,
                                background="black", borderwidth=1, highlightthickness=0)
        self.canvas.grid(row=row, column=col)

        #Шрифт и размер текста метки старого кадра
        try:
            self.font = ImageFont.truetype(str(Path('fonts','arial.ttf')), 24)  # Укажите путь к шрифту и размер
        except IOError:
            self.font = ImageFont.load_default()

    def update(self):
        #Пропускаем, если нет разрешения на воспроизведение
        if not self.is_able_to_play: return
        
        try:
            next_frame_timestamp = self.annotation_pd.iloc[self.frame_id + 1].values[0]
            time_diff = (next_frame_timestamp - min_frame) / 0.1 #Вычисление разницы между текущей временной меткой и следующей для этого видео
            
            if 0 <= ceil(time_diff) <= 2: #Если разница в пределах 200мс, то выводим новый кадр
                self.display_frame()

            elif self.previous_frame is not None: #Иначе, если прошлый кадр непустой, выводим его
                self.display_previous_frame()

            else: #Если прошлый кадр пустой, то не выводим ничего.
                print(f"Player {self.name} \t frame {self.frame_id}\t\tNone")

        except IndexError:
            self.video_file.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.frame_id = 0
            self.is_able_to_play = False
            
        except Exception as e:
            print(f"{e} : {e.__class__.__name__}")

    def display_frame(self):
        ret, frame = self.video_file.read()
        if not ret: return
        
        self.previous_frame = frame
        self.show_image(frame, "GOOD")
        self.frame_id += 1

    def display_previous_frame(self):
        self.show_image(self.previous_frame, "BAD")

    def show_image(self, frame, status):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame).resize((self.canvas_width, self.canvas_height))
        
        # Добавление условной метки
        draw = ImageDraw.Draw(img)
        text = "OLD" if status == "BAD" else ""
        
        if text:
            # Получаем размеры текста
            text_bbox = draw.textbbox((0, 0), text, font=self.font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            position = (10, 10)  # Позиция текста на изображении
            draw.rectangle([position, (position[0] + text_width, position[1] + text_height + 10)], fill="red")
            draw.text(position, text, fill="white", font=self.font)

        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.canvas.imgtk = imgtk
        print(f"Player {self.name} \t frame {self.frame_id}\t\t{status}")

def read_timestamps(file_path):
        return pd.read_csv(file_path, header=None) #Получение данных из анноатции посредством pandas

def find_border_frames():
    min_frame = min([timestamps.min().values[0] for timestamps in all_timestamps]) #В массив собираются минимальные временные метки каждой аннотации и из них выбирается наименьшая
    max_frame = max([timestamps.max().values[0] for timestamps in all_timestamps]) #В массив собираются максимальные временные метки каждой аннотации и из них выбирается наибольшая

    return [min_frame, max_frame]



def main():
    #Инициализация и настройка главного окна GUI 
    root = tk.Tk()
    root.title("Video Player Test Task")
    root.resizable(True, True)

    
    play_pause_button = tk.Button(root, text="play / pause", command=lambda: play_pause(), background="black", foreground="white")
    play_pause_button.grid(row=2, column=1)    

    cells = 2 #Сетка 2х2 
    sync = SyncCheker(root) #Объект класса, обновляющего отображаемые кадры в канвасах

    #Наполнение GUI канвасами
    for index, video_path in enumerate(video_paths):
        row, col = divmod(index, cells)
        sync.video_players.append(VideoPlayer(root, video_path, all_timestamps[index], row, col))
    sync.update_min_frame()

    root.mainloop()

#Обработчик нажатия на плэй/паузу
def play_pause():
    global is_playing
    is_playing = not is_playing

if __name__ == "__main__":
    speed = 200 #Начальный период обновления кадров
    is_playing = True #Флаг паузы
    video_paths = [i for i in Path('data').iterdir() if i.suffix == ".avi"] #Сбор видео для вывода в GUI
    all_timestamps = [read_timestamps(i.with_suffix(".txt")) for i in video_paths] #Сбор и обработка аннотаций к видео
    min_frame, max_frame = find_border_frames()

    main()
