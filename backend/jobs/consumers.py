import json
from channels.generic.websocket import AsyncWebsocketConsumer

class JobLogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.group_name = f'job_logs_{self.job_id}'

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from group
    async def send_log(self, event):
        await self.send(text_data=json.dumps({
            'log': event['log']
        }))
