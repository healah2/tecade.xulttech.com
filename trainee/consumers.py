import json, uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Lazy import all Djangohome models
        from django.contrib.auth.models import AnonymousUser, User
        from home.models import UserStatus
        import uuid

        try:
            self.user = self.scope.get("user", AnonymousUser())

            if isinstance(self.user, AnonymousUser):
#========Give a unique temporary "fake" ID for the session=============
                self.user.id = f"anon_{uuid.uuid4().hex}"
                self.is_temp_user = True
            
            if isinstance(self.user, AnonymousUser):
                self.user = await self.get_temp_user()
                self.is_temp_user = True
            else:
                self.is_temp_user = False
                await self.update_user_status(True)
            
            self.room_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.room_name,
                self.channel_name
            )
            print(f"{self.user.username} joined group: {self.room_name}")
    
            await self.accept()
        except Exception as e:
            print(f"Connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'is_temp_user') and not self.is_temp_user:
            await self.update_user_status(False)
            if hasattr(self, 'room_name'):
                await self.channel_layer.group_discard(
                    self.room_name,
                    self.channel_name
                )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data['type']

            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'reaction':
                await self.handle_reaction(data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except KeyError as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Missing required field: {e}'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))    

    async def handle_chat_message(self, data):
        from home.models import Message, Conversation
        
        conversation_id = data['conversation_id']
        content = data['content']

# =========DEBUG: see incoming message==================
        print(f"[DEBUG] {self.user.username} sending to conversation {conversation_id}: {content}")
        
        message = await self.create_message(conversation_id, content)
        
        recipient_ids = await self.get_recipient_ids(conversation_id)


#===========amother added print function below to help in debbugging the conversation IDs==================

        print(f"[DEBUG] Recipients for conversation {conversation_id}: {recipient_ids}")


#===========Just be4 looping recipient/ receiver ID  to ensure the sender getts the message first before sending to other users clients
        await self.channel_layer.group_send(
            f"user_{self.user.id}",
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender_id': self.user.id,
                    'sender_name': self.user.username,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat(),
                    'conversation_id': conversation_id
                }
            }
        )


        for recipient_id in recipient_ids:
            await self.channel_layer.group_send(
                f"user_{recipient_id}",
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender_id': self.user.id,
                        'sender_name': self.user.username,
                        'content': message.content,
                        'timestamp': message.timestamp.isoformat(),
                        'conversation_id': conversation_id
                    }
                }
            )
            
            await self.channel_layer.group_send(
                f"user_{recipient_id}",
                {
                    'type': 'notification',
                    'message': f"New message from {self.user.username}"
                }
            )

    async def handle_typing(self, data):
        from home.models import Conversation
        
        conversation_id = data['conversation_id']
        recipient_ids = await self.get_recipient_ids(conversation_id)
        
        for recipient_id in recipient_ids:
            await self.channel_layer.group_send(
                f"user_{recipient_id}",
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'user_name': self.user.username,
                    'is_typing': data['is_typing'],
                    'conversation_id': conversation_id
                }
            )

    async def handle_reaction(self, data):
        from home.models import MessageReaction, Message
        
        message_id = data['message_id']
        emoji = data['emoji']
        
        reaction = await self.create_reaction(message_id, emoji)
        
        participant_ids = await self.get_conversation_participants(reaction.message.conversation_id)
        
        for participant_id in participant_ids:
            await self.channel_layer.group_send(
                f"user_{participant_id}",
                {
                    'type': 'message_reaction',
                    'message_id': message_id,
                    'user_id': self.user.id,
                    'user_name': self.user.username,
                    'emoji': emoji
                }
            )

    async def chat_message(self, event):
#=========DEBUG: log when message is delivered to client
        print(f"[DEBUG] Delivering chat_message to {self.user.username}: {event['message']}")
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_typing': event['is_typing'],
            'conversation_id': event['conversation_id']
        }))

    async def message_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'emoji': event['emoji']
        }))
    #-----------------------------------------------------------

    # Keep all your existing database operations with lazy imports This is to avoid failure of loading the 
    # javascript and the CSS
    
    # ---------------------------------------------------------]
    @database_sync_to_async
    def create_message(self, conversation_id, content):
        from home.models import Message, Conversation
        conversation = Conversation.objects.get(id=conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        return message

    @database_sync_to_async
    def create_reaction(self, message_id, emoji):
        from home.models import MessageReaction, Message
        message = Message.objects.get(id=message_id)
        reaction, created = MessageReaction.objects.get_or_create(
            message=message,
            user=self.user,
            defaults={'emoji': emoji}
        )
        if not created:
            reaction.emoji = emoji
            reaction.save()
        return reaction

    @database_sync_to_async
    def get_recipient_ids(self, conversation_id):
        from home.models import Conversation
        conversation = Conversation.objects.get(id=conversation_id)
        return list(conversation.participants.exclude(id=self.user.id).values_list('id', flat=True))

    @database_sync_to_async
    def get_conversation_participants(self, conversation_id):
        from home.models import Conversation
        conversation = Conversation.objects.get(id=conversation_id)
        return list(conversation.participants.values_list('id', flat=True))

    @database_sync_to_async
    def update_user_status(self, is_online):
        from home.models import UserStatus
        status, created = UserStatus.objects.get_or_create(user=self.user)
        status.is_online = is_online
        status.save()

    @database_sync_to_async
    def get_temp_user(self):
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            username='anonymous',
            defaults={'password': 'anonymous'}
        )
        return user