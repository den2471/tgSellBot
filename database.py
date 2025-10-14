import sqlite3
import logging
import datetime
import inspect
import re

logger = logging.getLogger(__name__)

class TicketDb:
    def __init__(self, db_name="resources/tickets.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def _close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

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
        """, (user_id, ticket_id, description, photo_id, video_id, file_id, phone, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.conn.commit()

    def get_ticket(self, user_id, ticket_id):
        self.cursor.execute("SELECT * FROM tickets WHERE user_id = ? AND ticket_id = ?", (user_id, ticket_id))
        ticket = self.cursor.fetchone()
        return ticket

    def add_response(self, ticket_id, user_id, response_text, photo_id=None, video_id=None, file_id=None):
        self.cursor.execute("""
        INSERT INTO ticket_responses (ticket_id, user_id, response_text, photo_id, video_id, file_id, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticket_id, user_id, response_text, photo_id, video_id, file_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.conn.commit()

    def add_user(self, user_id, username, first_name, last_name):
        self.cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, date_joined)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
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
    

class PackedData:

    def __init__(self, console_id=None, sell_date=None, tg_id=None, warranty_id=None, approval_date=None):
        self.console_id = console_id
        self.sell_date = sell_date
        self.tg_id = tg_id
        self.warranty_id = warranty_id
        self.approval_date = approval_date
    
    async def exist(self):
        if self.console_id:
            return True
        else:
            return False
    
    async def sold(self):
        if self.sell_date:
            return True
        else:
            return False
    
    async def bound(self):
        if self.tg_id:
            return True
        else:
            return False
        
    async def approved(self):
        if self.approval_date:
            return True
        else:
            return False


class WarrantyDb:
    def __init__(self, db_name='resources/warranty.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS warranty (
            console_id INTEGER NOT NULL UNIQUE,
            sell_date TEXT,
            tg_id TEXT,
            warranty_id TEXT UNIQUE,
            approval_date TEXT
        )
        ''')
    
    def _close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()
    
    def _get_warranty_id(self, console_id):
        result = ''.join(re.findall(r'\d+', console_id))
        return result

    def _commit_changes(self):
        try:
            self.conn.commit()
            return True
        except:
            self.conn.rollback()
            return False
        
    def _pack_data(self, data):
        if data:
            return PackedData(data[0], data[1], data[2], data[3], data[4])
        else:
            return PackedData()

    def get_packed(self, console_id):
        console_data = self._pack_data(self.get_raw(console_id))
        return console_data
        
    def get_raw(self, console_id):
        self.cursor.execute('SELECT * FROM warranty WHERE console_id = ?', (console_id,))
        data = self.cursor.fetchone()
        return data
    
    def add_console(self, console_id, sell_date=None):
            self.cursor.execute('INSERT OR IGNORE INTO warranty (console_id, sell_date, tg_id, warranty_id, approval_date) VALUES (?, ?, ?, ?, ?)', (console_id, sell_date, None, None, None))
            return self._commit_changes() 
    
    def remove_console(self, console_id):
        self.cursor.execute('DELETE FROM warranty WHERE console_id = ?', (console_id,))
        return self._commit_changes()
    
    def sell_console(self, console_id, date = None):
        if not date:
            date = datetime.date.today().strftime('%d-%m-%Y')
        self.cursor.execute('UPDATE warranty SET sell_date = ? WHERE console_id = ?', (date, console_id))
        return self._commit_changes()
    
    def unsell_console(self, console_id):
        self.cursor.execute('UPDATE warranty SET sell_date = ?, tg_id = ?, warranty_id = ?, approval_date = ? WHERE console_id = ?', (None, None, None, None, console_id))
        return self._commit_changes()
        
    def bind_warranty(self, console_id, tg_id):
        warranty_id = self._get_warranty_id(console_id)
        self.cursor.execute('UPDATE warranty SET tg_id = ?, warranty_id = ? WHERE console_id = ?', (tg_id, warranty_id, console_id))
        return self._commit_changes()
    
    def unbind_warranty(self, console_id):
        self.cursor.execute('UPDATE warranty SET tg_id = ?, warranty_id = ?, approval_date = ? WHERE console_id = ?', (None, None, None, console_id))
        return self._commit_changes()

    def approve_warranty(self, console_id, date = None):
        if not date:
            date = datetime.date.today().strftime('%d-%m-%Y')
        self.cursor.execute('UPDATE warranty SET approval_date = ? WHERE console_id = ?', (date, console_id))
        return self._commit_changes()
    
    def unapprove_warranty(self, console_id):
        self.cursor.execute('UPDATE warranty SET approval_date = ? WHERE console_id = ?', (None, console_id))
        return self._commit_changes()