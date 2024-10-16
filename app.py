import cv2
import pandas as pd
import tkinter as tk
from PIL import Image, ImageTk
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
            min_frame += 0.2
            for player in self.video_players: player.update()
            print('--------------------------')
        self.window.after(speed, self.update_min_frame)


class VideoPlayer:
    def __init__(self, window, video_source, annotation, row, col):
        self.frame_id = 0 #Счётчик кадров
        self.name = int(f"{row}{col}", 2) #Имя (id) объекта плеера
        self.previous_frame = None #Обозначение предыдущего кадра
        self.annotation_pd = annotation #Аннотация для видео
        self.is_able_to_play = True #Флаг разрешения на воспроизведение
        
        self.video_file = cv2.VideoCapture(video_source) #Захват видео объектом OpenCV

        #Создание и настройка канваса для отображения кадров видео
        self.canvas = tk.Canvas(window, width=int(self.video_file.get(cv2.CAP_PROP_FRAME_WIDTH)) / 2,
                                        height=int(self.video_file.get(cv2.CAP_PROP_FRAME_HEIGHT)) / 2,
                                background="black")
        self.canvas.grid(row=row, column=col)

    def update(self):
        global is_playing
        if not self.is_able_to_play: return #Пропустить, если нет разрешения на воспроизведение
        try:
            next_frame_timestamp = self.annotation_pd.iloc[self.frame_id + 1].values[0]

            # Если разница между следующим кадром ролика и текущей временной меткой в пределах 200мс, отобразить следующий кадр
            if 0 <= ceil((next_frame_timestamp - min_frame) / 0.1) <= 2:
                ret, frame = self.video_file.read()
                if ret is None: return ValueError()

                self.previous_frame = frame

                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = img.resize((canvas_width, canvas_height))

                imgtk = ImageTk.PhotoImage(image=img)

                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.imgtk = imgtk

                print(f"Player {self.name} \t frame {self.frame_id}\t\tGOOD")
                self.frame_id += 1
                    

            # Иначе, если предыдущий кадр непустой, то повторить его (разница временных меток больше 200мс => больше одного кадра)
            elif self.previous_frame is not None:
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                frame = self.previous_frame

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = img.resize((canvas_width, canvas_height))

                imgtk = ImageTk.PhotoImage(image=img)

                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.imgtk = imgtk
                print(f"Player {self.name} \t frame {self.frame_id}\t\tBAD")

            # Иначе ничего не отображать (ситуация, когда видео начинается позже самой ранней временной метки как минимум на 1 кадр)
            else:
                print(f"Player {self.name} \t frame {self.frame_id}\t\tNone")
                

        except Exception as e:
            print(f"{e} : {e.__class__.__name__}")

            if e.__class__.__name__ == "error":
                print(f"Player {self.name} \t frame {self.frame_id}\t\tBROKEN")
                self.frame_id += 1

            # Если видео закончилось, то сбрасываем счётчик кадров и запрещаем дальнейшее его воспроизведение
            if e is IndexError:
                self.video_file.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.frame_id = 0
                self.is_able_to_play = False


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

    #Контейнер для кнопок изменения скорости
    speed_buttons_frame = tk.Frame(root)
    speed_buttons_frame.grid(row=3, column=0)

    button1 = tk.Button(speed_buttons_frame, text="x0.2", command=lambda: change_speed(0.2), background="black", foreground="white")
    button1.grid(row=0, column=0)

    button2 = tk.Button(speed_buttons_frame, text="x1", command=lambda: change_speed(1), background="black", foreground="white")
    button2.grid(row=0, column=1)

    button3 = tk.Button(speed_buttons_frame, text="x10", command=lambda: change_speed(10), background="black", foreground="white")
    button3.grid(row=0, column=2)
    
    button4 = tk.Button(root, text="play / pause", command=lambda: play_pause(), background="black", foreground="white")
    button4.grid(row=3, column=1)    

    cells = 2 #Сетка 2х2 
    sync = SyncCheker(root) #Объект класса, обновляющего отображаемые кадры в канвасах

    #Наполнение GUI канвасами
    for index, video_path in enumerate(video_paths):
        row = index // cells if index > 0 else 0
        col = index % cells if index > 0 else 0
        sync.video_players.append(VideoPlayer(root, video_path, all_timestamps[index], row, col))
    sync.update_min_frame()

    root.mainloop()

#Обработчик нажатия на кнопки изменения скорости
def change_speed(koeff):
    global speed, is_playing

    saved_flag = is_playing
    is_playing = False
    speed = int(200//koeff)
    print(f'\nupdate period:{speed}ms / {1000//speed}fps\n')
    is_playing = saved_flag

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
