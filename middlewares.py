from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

class RegisterCheck(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Skip registration check for /start command
        if event.text and event.text == '/start':
            return await handler(event, data)
        
        # Get data manager from dispatcher context
        data_manager = data.get('data_manager')
        
        # Check if user is registered
        user_data = data_manager.get_user(event.from_user.id) if data_manager else None
        if not user_data or not user_data.get('is_registered'):
            await event.answer(
                "Please register first using /start command"
            )
            return
        
        return await handler(event, data) 