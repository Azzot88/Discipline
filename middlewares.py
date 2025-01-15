from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from config import users

class RegisterCheck(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Skip registration check for /start command
        if event.text and event.text == '/start':
            return await handler(event, data)
            
        # Check if user is registered
        if user_id not in users or not users[user_id].is_registered:
            await event.answer(
                "Please register first using /start command"
            )
            return
        
        return await handler(event, data) 