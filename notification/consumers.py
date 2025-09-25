import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            await self.close()
            return
        self.user = user
        self.group_name = f'user_{user.id}_notifications'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # For now, we only support ping/pong or mark-all-read from WS if needed
        if text_data:
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                return
            action = data.get('action')
            if action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

    async def notify(self, event):
        # event should contain a 'payload' with serializable data
        payload = event.get('payload', {})
        await self.send(text_data=json.dumps(payload))

