import os
import logging
import time
import threading
import random
import inspect
import asyncio
from telegram import Bot
from telegram.ext import Application, ApplicationBuilder

logger = logging.getLogger(__name__)

class MediaManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.media_group = int(os.getenv("MEDIA_GROUP_ID"))
        self.ad_path = os.getenv("MEDIA_AD_PATH")
        self.licence_path = os.getenv("MEDIA_LIC_PATH")
        self.update_interval = float(os.getenv("MEDIA_UPDATE_FREQ"))
        self.licence_photos = {}
        self.advert_media = {}
        self.last_update = 0.0
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self._load_ad())
            loop.create_task(self._load_licence())
        else:
            loop.run_until_complete(self._load_ad())
            loop.run_until_complete(self._load_licence())
        self._start_update_thread()

    def _start_update_thread(self):
        """Запускает поток для периодического обновления медиафайлов"""
        def update_thread():

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            while True:
                try:
                    current_time = time.time()
                    if current_time - self.last_update >= self.update_interval:
                        logger.info("Обновление списка медиафайлов...")

                        loop.run_until_complete(asyncio.gather(
                            self._load_ad(),
                            self._load_licence(),
                            return_exceptions=True))
                        
                        self.last_update = current_time
                except Exception as e:
                    logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при обновлении медиафайлов: {e}")
                time.sleep(self.update_interval)  # Проверяем каждую минуту

        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()

    async def _load_licence(self):
        try:
            if not os.path.exists(self.licence_path):
                    os.makedirs(self.licence_path)
                    logger.info(f"Создана директория {self.licence_path}")
                    return
            
            file_names = ["".join([self.licence_path, "/", f]) for f in os.listdir(self.licence_path) 
                        if f.lower().endswith((".png", ".jpg", ".jpeg"))]

            for file in file_names:
                    try:
                        msg = await self.bot.send_photo(self.media_group, open(file, "rb").read())
                        time.sleep(.5)
                        file_id = msg.photo[-1].file_id
                        self.licence_photos[int(file.split(".")[0][-1])] = file_id
                    except Exception as e:
                        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nНе удалось загрузить файл {file}. Ошибка {e}")
            
            logger.info(f"Загружено {len(self.licence_photos)} лицензионных файлов")
            self.last_update = time.time()
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при загрузке лицензионных файлов\n{e}")

    async def _load_ad(self):

        if not os.path.exists(self.ad_path):
                os.makedirs(self.ad_path)
                logger.info(f"Создана директория {self.ad_path}")
                return

        file_names = ["".join([self.ad_path, "/", f]) for f in os.listdir(self.ad_path) 
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".mp4", ".avi", ".mov", ".mkv"))]
        index = 0
        for file in file_names:
            index += 1
            try:
                if file.lower()[-4:] in ['.mp4', ".avi", ".mov", ".mkv"]:
                    msg = await self.bot.send_video(self.media_group, open(file, "rb").read())
                    file_id = msg.video.file_id
                    extention = 'vid'
                elif file.lower()[-4:] in [".png", ".jpg", ".jpeg"]:
                    msg = await self.bot.send_photo(self.media_group, open(file, "rb").read())
                    file_id = msg.photo[-1].file_id
                    extention = 'pic'
                else:
                    logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nНе удалось загрузить файл {file}. Расширение файла не поддерживается.\n" \
                                "Поддерживаемые расширения png, jpg, jpeg, mp4, avi, mov, mkv")
                    continue
                time.sleep(.5)
                self.advert_media[index] = {"data": file_id, "extention": extention}
            except Exception as ex:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nНе удалось загрузить файл {file}. Ошибка {ex}")

        logger.info(f"Загружено {len(self.advert_media)} рекламных файлов")
    
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
            media_id = self.advert_media[index]['data']
            extention = self.advert_media[index]['extention']
            return media_id, extention
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при выборе случайного рекламного файла: {e}")
            return None, None