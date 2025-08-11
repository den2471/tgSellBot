"""
This file contains patterns and rules for the GameHub Support Bot.
These patterns are used to match user messages and determine appropriate responses.
"""

# Common support patterns
SUPPORT_PATTERNS = {
    'greeting': [
        'привет',
        'здравствуйте',
        'добрый день',
        'доброе утро',
        'добрый вечер',
        'hi',
        'hello',
        'hey'
    ],
    'help': [
        'помощь',
        'help',
        'поддержка',
        'support',
        'как пользоваться',
        'инструкция'
    ],
    'ticket': [
        'тикет',
        'заявка',
        'обращение',
        'вопрос',
        'проблема',
        'ticket',
        'issue'
    ],
    'goodbye': [
        'спасибо',
        'до свидания',
        'пока',
        'thanks',
        'thank you',
        'bye',
        'goodbye'
    ]
}

# Response templates
RESPONSE_TEMPLATES = {
    'greeting': 'Здравствуйте! Чем могу помочь?',
    'help': 'Я бот поддержки GameHub. Вы можете:\n1. Создать тикет\n2. Проверить статус тикета\n3. Получить помощь по использованию',
    'ticket_created': 'Ваш тикет успешно создан. Номер тикета: {ticket_id}',
    'ticket_status': 'Статус вашего тикета: {status}',
    'goodbye': 'Спасибо за обращение! Хорошего дня!'
}

# Error messages
ERROR_MESSAGES = {
    'invalid_command': 'Извините, я не понял команду. Пожалуйста, используйте доступные команды.',
    'ticket_not_found': 'Тикет не найден. Пожалуйста, проверьте номер тикета.',
    'permission_denied': 'У вас нет прав для выполнения этой операции.',
    'system_error': 'Произошла системная ошибка. Пожалуйста, попробуйте позже.'
} 