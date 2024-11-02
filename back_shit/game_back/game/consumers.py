import json
import uuid
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

players_queue = []

class Game(WebsocketConsumer):
    def connect(self):
        global  players_queue

        if hasattr(self, 'room_name') and self.room_name in player_queue:
            player_queue.remove(self.room_name)

        if not players_queue:
            self.room_name = f"room_{uuid.uuid4().hex}"
            self.role = "host"
            players_queue.append(self.room_name)
        else:
            self.room_name = players_queue.pop()
            self.role = "guest"

        self.room_group_name = f"game_{self.room_name}"
        
        async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
        )

        self.accept()

        if self.role == "guest":
            self.send(text_data=json.dumps({
                'msg_type': 'server update',
                'role': self.role,
            }))
            async_to_sync(self.channel_layer.group_send) (
                    self.room_group_name,
                    {
                        'type': 'send_msg',
                        'message': 'you just got a pair',
                        'room_name': self.room_group_name,
                    }
            )
        else:
            self.send(text_data=json.dumps({
                'msg_type': 'server update',
                'role': self.role,
                'message': 'waiting for you pair',
                'room_name': self.room_group_name
            }))
        #print("queue len after connect: ", len(players_queue))


    def disconnect(self, close_code):
        global players_queue
        if self.room_name in players_queue:
            players_queue.remove(self.room_name)
        async_to_sync(self.channel_layer.group_send) (
                self.room_group_name,
                {
                    'type': 'send_msg',
                    'message': 'pair disconnected',
                    'room_name': self.room_group_name
                }
        )
        async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
        )
        #print("queue len after disconnect: ", len(players_queue))

    def receive(self, text_data):
        data = json.loads(text_data)
#        if data['message'] == "player move":
#            print('server: just sent a move')
        async_to_sync(self.channel_layer.group_send) (
            self.room_group_name,
            {
                'type': 'send_update',
                'obj': data['obj'],
                'message': data['message'],
                'target': data['target'],
            }
        )
        #print("receive: ", len(players_queue))

    def send_msg(self, event):
        message = event['message']
        room_name = event['room_name']
        self.send(text_data=json.dumps({
            'msg_type': 'server update',
            'message': message,
            'room_name': room_name
        }))

    def send_update(self, event):
        message = event['message']
        obj = event['obj']
        target = event['target']
        self.send(text_data=json.dumps({
            'msg_type': 'pair update',
            'message': message,
            'target': target,
            'obj': obj,
        }))
        

