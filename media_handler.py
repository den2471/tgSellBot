import os
import logging
import time
import threading
import random
import inspect

logger = logging.getLogger(__name__)

class MediaManager:
    def __init__(self):
        self.ad_path = os.getenv("MEDIA_AD_PATH")
        self.licence_path = os.getenv("MEDIA_LIC_PATH")
        self.update_interval = float(os.getenv("MEDIA_UPDATE_FREQ"))
        self.licence_photos = {}
        self.advert_media = {}
        self.last_update = 0.0
        self.load_media()
        self.start_update_thread()

    def start_update_thread(self):
        """Запускает поток для периодического обновления медиафайлов"""
        def update_thread():
            while True:
                try:
                    current_time = time.time()
                    if current_time - self.last_update >= self.update_interval:
                        logger.info("Обновление списка медиафайлов...")
                        self.load_media()
                        self.last_update = current_time
                except Exception as e:
                    logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при обновлении медиафайлов: {e}")
                time.sleep(self.update_interval)  # Проверяем каждую минуту

        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()

    def load_media(self):
        """Загрузка медиафайлов из директории"""
        self.licence_photos = {}
        self.advert_media = {}
        try:
            # ad load
            if not os.path.exists(self.ad_path):
                os.makedirs(self.ad_path)
                logger.info(f"Создана директория {self.ad_path}")
                return

            file_names = ["".join([self.ad_path, "/", f]) for f in os.listdir(self.ad_path) 
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".mp4", ".gif"))]
            index = 0
            for file in file_names:
                index += 1
                try:
                    data = open(file, "rb").read()
                    if ".gif" in file.lower()[-4:]:
                        extention = 'doc'
                    elif file.lower()[-4:] in ['.mp4', ".avi", ".mov", ".mkv"]:
                        extention = 'vid'
                    elif file.lower()[-4:] in [".png", ".jpg", ".jpeg"]:
                        extention = 'pic'
                    else:
                        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nНе удалось загрузить файл {file}. Расширение файла не поддерживается.\n" \
                                    "Поддерживаемые расширения png, jpg, jpeg, mp4, gif")
                        continue
                    self.advert_media[index] = {"data": data, "extention": extention}
                except Exception as ex:
                    logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nНе удалось загрузить файл {file}. Ошибка {ex}")

            logger.info(f"Загружено {len(self.advert_media)} рекламных файлов")

            # licence load
            if not os.path.exists(self.licence_path):
                os.makedirs(self.licence_path)
                logger.info(f"Создана директория {self.licence_path}")
                return
            
            file_names = []

            file_names = ["".join([self.licence_path, "/", f]) for f in os.listdir(self.licence_path) 
                    if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            
            for file in file_names:
                try:
                    self.licence_photos[int(file.split(".")[0][-1])] = open(file, "rb").read()
                except Exception as ex:
                    logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nНе удалось загрузить файл {file}. Ошибка {ex}")

            logger.info(f"Загружено {len(self.licence_photos)} лицензионных файлов")

            self.last_update = time.time()
            
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при загрузке медиафайлов: {e}")
            self.photos = []
    
    def get_licence_by_index(self, index):
        try:
            if not self.licence_photos:
                return None, None
            return self.licence_photos[index], len(self.licence_photos)
        except KeyError:
            return None, None
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при выборе лицензионного файла: {e}")
            return None, None

    def get_random_ad(self):
        try:
            if not self.advert_media:
                return None, None
            index = random.choice(list(self.advert_media))
            media = self.advert_media[index]['data']
            extention = self.advert_media[index]['extention']
            return media, extention
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при выборе случайного рекламного файла: {e}")
            return None, None

# Создаем глобальный экземпляр MediaManager
media_manager = MediaManager() 