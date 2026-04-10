import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import PrivateChat, PrivateMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope['user']

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if not self.user.is_anonymous:
            await self.set_user_online(self.user.id, True)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if not self.user.is_anonymous:
            await self.set_user_online(self.user.id, False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')

        if message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'username': data['username'],
                    'typing': data['typing'],
                }
            )
        elif message_type == 'heartbeat':
            pass
        else:
            message = data['message']
            sender_id = int(data['sender_id'])
            chat_id = int(data['chat_id'])

            await self.save_message(chat_id, sender_id, message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': data['username'],
                    'sender_id': sender_id,
                    'created_at': 'Just now',
                }
            )

            # Save notification and get recipient ID for WS push
            recipient_id = await self.save_notification_and_get_recipient(
                chat_id, sender_id, data['username'], message
            )
            if recipient_id:
                await self.channel_layer.group_send(
                    f"notify_{recipient_id}",
                    {
                        'type': 'send_notification',
                        'data': {
                            'notification_type': 'message',
                            'sender': data['username'],
                            'message': message[:100],
                            'url': f'/chat/{sender_id}/',
                        }
                    }
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'created_at': event['created_at'],
        }))

    async def typing_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username'],
            'typing': event['typing'],
        }))

    @database_sync_to_async
    def save_message(self, chat_id, sender_id, message):
        chat = PrivateChat.objects.get(id=chat_id)
        sender = User.objects.get(id=sender_id)
        return PrivateMessage.objects.create(chat=chat, sender=sender, message=message)

    @database_sync_to_async
    def set_user_online(self, user_id, is_online):
        User.objects.filter(id=user_id).update(is_online=is_online, last_seen=timezone.now())

    @database_sync_to_async
    def save_notification_and_get_recipient(self, chat_id, sender_id, sender_username, message):
        from notifications.models import Notification
        try:
            chat = PrivateChat.objects.get(id=chat_id)
            recipient = chat.user2 if chat.user1_id == sender_id else chat.user1
            Notification.objects.create(
                user=recipient,
                notification_type='message',
                message=f"{sender_username}: {message[:100]}",
            )
            return recipient.id
        except Exception:
            return None


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f"group_{self.group_id}"
        self.user = self.scope['user']

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if not self.user.is_anonymous:
            await self.set_user_online(self.user.id, True)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if not self.user.is_anonymous:
            await self.set_user_online(self.user.id, False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = int(data['sender_id'])

        await self.save_group_message(int(self.group_id), sender_id, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'group_message',
                'message': message,
                'username': data['username'],
                'sender_id': sender_id,
                'created_at': 'Just now',
            }
        )

        # Notify group members and get their IDs
        member_ids, group_name = await self.save_group_notifications(
            int(self.group_id), sender_id, data['username'], message
        )
        for mid in member_ids:
            await self.channel_layer.group_send(
                f"notify_{mid}",
                {
                    'type': 'send_notification',
                    'data': {
                        'notification_type': 'group_message',
                        'sender': data['username'],
                        'group': group_name,
                        'message': message[:100],
                        'url': f'/groups/{self.group_id}/',
                    }
                }
            )

    async def group_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def save_group_message(self, group_id, sender_id, message):
        from groups.models import ChatGroup, GroupMessage
        group = ChatGroup.objects.get(id=group_id)
        sender = User.objects.get(id=sender_id)
        return GroupMessage.objects.create(group=group, sender=sender, message=message)

    @database_sync_to_async
    def set_user_online(self, user_id, is_online):
        User.objects.filter(id=user_id).update(is_online=is_online, last_seen=timezone.now())

    @database_sync_to_async
    def save_group_notifications(self, group_id, sender_id, sender_username, message):
        from groups.models import ChatGroup
        from notifications.models import Notification
        try:
            group = ChatGroup.objects.get(id=group_id)
            member_ids = []
            for member in group.members.exclude(id=sender_id):
                Notification.objects.create(
                    user=member,
                    notification_type='message',
                    message=f"{sender_username} in {group.name}: {message[:80]}",
                )
                member_ids.append(member.id)
            return member_ids, group.name
        except Exception:
            return [], ''
