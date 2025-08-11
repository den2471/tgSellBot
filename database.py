import sqlite3
import logging
from datetime import datetime, timedelta
import os
import string
import random
import inspect
import keyboards
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)

class TicketDb:
    def __init__(self, db_name="resources/tickets.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Initialize the database with required tables"""
        # Create tickets table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticket_id INTEGER NOT NULL,
            description TEXT,
            photo_id TEXT,
            video_id TEXT,
            file_id TEXT,
            phone TEXT,
            status TEXT DEFAULT "pending",
            date TEXT,
            UNIQUE(user_id, ticket_id)
        )
        """)

        # Create ticket_responses table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            user_id INTEGER,
            response_text TEXT,
            photo_id TEXT,
            video_id TEXT,
            file_id TEXT,
            date TEXT,
            rating INTEGER DEFAULT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
        )
        """)

        # Create users table for newsletter
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            date_joined TEXT
        )
        """)

        self.conn.commit()

    def add_ticket(self, user_id, ticket_id, description, photo_id=None, video_id=None, file_id=None, phone=None):
        self.cursor.execute("""
        INSERT INTO tickets (user_id, ticket_id, description, photo_id, video_id, file_id, phone, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, ticket_id, description, photo_id, video_id, file_id, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.conn.commit()

    def get_ticket(self, user_id, ticket_id):
        self.cursor.execute("SELECT * FROM tickets WHERE user_id = ? AND ticket_id = ?", (user_id, ticket_id))
        ticket = self.cursor.fetchone()
        return ticket

    def add_response(self, ticket_id, user_id, response_text, photo_id=None, video_id=None, file_id=None):
        self.cursor.execute("""
        INSERT INTO ticket_responses (ticket_id, user_id, response_text, photo_id, video_id, file_id, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticket_id, user_id, response_text, photo_id, video_id, file_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.conn.commit()

    def add_user(self, user_id, username, first_name, last_name):
        self.cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, date_joined)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.conn.commit()

    def get_all_users(self):
        self.cursor.execute("SELECT user_id FROM users")
        users = self.cursor.fetchall()
        return [user[0] for user in users]

    def get_all_tickets(self, user_id):
        """Get all tickets for a specific user"""
        self.cursor.execute("SELECT * FROM tickets WHERE user_id = ? ORDER BY date DESC", (user_id,))
        tickets = self.cursor.fetchall()
        return tickets

    def get_latest_ticket(self, user_id):
        """Get the latest ticket for a user"""
        self.cursor.execute("SELECT * FROM tickets WHERE user_id = ? ORDER BY date DESC LIMIT 1", (user_id,))
        ticket = self.cursor.fetchone()
        return ticket

    def update_ticket_phone(self, ticket_id, phone):
        """Update phone number for a ticket"""
        self.cursor.execute("UPDATE tickets SET phone = ? WHERE id = ?", (phone, ticket_id))
        self.conn.commit()

    def update_ticket_status(self, ticket_id, status):
        """Update status for a ticket"""
        self.cursor.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        self.conn.commit()

    def get_ticket_responses(self, ticket_id):
        """Получает все ответы на тикет"""
        self.cursor.execute("""
            SELECT * FROM ticket_responses 
            WHERE ticket_id = ? 
            ORDER BY date ASC
        """, (ticket_id,))
        return self.cursor.fetchall()

    def get_active_ticket(self, user_id):
        """Получает активный (незакрытый) тикет пользователя"""
        self.cursor.execute("""
            SELECT * FROM tickets 
            WHERE user_id = ? AND status != "answered" 
            ORDER BY date DESC 
            LIMIT 1
        """, (user_id,))
        return self.cursor.fetchone()
    
    def rate_ticket(self, ticket_id, rating):
        """
        Добавляет оценку закрытому тикету
        :param ticket_id: ID тикета
        :param rating: Оценка от 1 до 5
        """
        try:
            self.cursor.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
            ticket = self.cursor.fetchone()
            
            if not ticket:
                return None
                
            if ticket[0] != "answered":
                return None
                
            self.cursor.execute("""
                UPDATE ticket_responses 
                SET rating = ?
                WHERE id = ?
            """, (rating, ticket_id))
            
            self.conn.commit()
            return 1
            
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name}\nОшибка при добавлении оценки тикету: {e}")
            return None


class WarrantyDb:
    def __init__(self):
        logger.info("Инициализация базы данных гарантий")
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name("resources/sheets_credentials.json", scope)
            client = gspread.authorize(creds)
            spreadsheet_url = os.getenv("WARRANTY_DB_URL")
            spreadsheet_id = spreadsheet_url.split("/d/")[1].split("/")[0]
            self.warranty_db_table = client.open_by_key(spreadsheet_id)
            logger.info("База данных гарантий успешно инициализирована")
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name}\nОшибка при инициализации базы данных гарантий: {e}")
            return None 
        
    def get_console_data(self, console_id):
        try:
            data = self.warranty_db_table.get_worksheet_by_id(0).get_all_records()
            for index, row in enumerate(data, start=2):
                if str(console_id) == str(row["console id"]):
                    return (index, row)
            return None
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name}\nОшибка при получении данных о консоли {console_id}")
            return None

    def warranty_approval_write(self, console_id, index=None):
        if not index:
            index, _ = self.get_console_data(console_id)
        try:
            range = f"E{index}:F{index}"
            date = datetime.now().strftime("%d.%m.%Y")
            self.warranty_db_table.get_worksheet_by_id(0).update(range, [[date, "1"]])
            return 1
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name}\nОшибка при обновлении статуса гарантии для консоли {console_id}")
            return None

    def generate_warranty_id(self, console_id):
        try:
            data = self.warranty_db_table.get_worksheet_by_id(0).get_all_records()
            if self.get_console_data(console_id):
                logger.info(f"Генерация когда гарантии для консоли {console_id}")
                characters = (string.ascii_letters).upper()
                while True:
                    code = "".join(random.choice(characters) for _ in range(8))
                    if not any(row["warranty id"] == code for row in data):
                        break
                return code
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name}\nОшибка при генерации кода гарантии для консоли {console_id}: {e}")
            return None
        
    def bind_console_to_user(self, console_id, console_index, user_id, warranty_id):
        """
        Привязка консоли к пользователю, заполнение полей "tg id", "warranty id" и "warranty check" в базе гарантий
    
        Args:
            console_id: ID консоли
            console_index: индекс консоли в таблице
            user_id: tg ID пользователя
            warranty_id: код гарантии
        Returns:
            1 - привязка прошла успешно
            None - привязка не удалась
        """
        try:
            logger.info(f"Привязка консоли {console_id} к пользователю {user_id}")
            range = f"C{console_index}:F{console_index}"
            self.warranty_db_table.get_worksheet_by_id(0).update(range, [[user_id, warranty_id, "", "0"]])
            return 1
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name}\nОшибка при привязке консоли {console_id} к пользователю {user_id}: {e}")
            return None
    
    def warranty_check(self, console_id):
        """
        Проверка статуса гарантии консоли по коду
    
        Args:
            console_code: Код консоли для проверки
            
        Returns:
            list: [текст сообщения, <class "function"> для получения клавиатуры]
        """
        console_index, console_data = self.get_console_data(console_id)
        if console_data:
            if str(console_data["warranty check"]) == "1":
                registration_date = datetime.strptime(console_data["sell date"], "%d.%m.%Y")
                warranty_end = registration_date + timedelta(days=int(os.getenv("WARRANTY_DURATION")) + int(os.getenv("WARRANTY_COMPENSATION")))
                remaining_days = (warranty_end - datetime.now()).days
                if remaining_days <= 0:
                    return [f"❌ Ваша гарантия истекла.", keyboards.get_main_menu_keyboard]
                else:
                    return [f"✅ Ваша гарантия подтверждена и активна. Осталось дней гарантии: {remaining_days}", keyboards.get_main_menu_keyboard]
            else:
                return [f'⏹Ваша гарантия не подтверждена. Для подтверждения выберите пункт "📝 Отправить отзыв на проверку"', keyboards.get_warranty_keyboard]
        else:
            return None
