# discord_producer.py
import os
import json
import discord
import datetime

from kafka import KafkaProducer

KAFKA_SERVER = 'localhost:9092' # Conecta ao Kafka no Docker
KAFKA_TOPIC = 'discord_messages'
BOT_TOKEN = os.getenv('BOT_TOKEN')

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_SERVER],
    # Serializa o objeto Python para um JSON string codificado em UTF-8
    value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
)

class DiscordToKafka(discord.Client):
    def __init__(self, *args, **kwargs):
        # É necessário habilitar 'message_content' nas intents
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, *args, **kwargs)

    async def on_ready(self):
        print(f'Bot logado como {self.user} e pronto para enviar para o Kafka!')

    async def on_message(self, message):
        # Ignora mensagens de bots
        if message.author.bot:
            return

        # Estrutura de dados que será enviada para o Kafka
        data = {
            'author_id': str(message.author.id),
            'author_name': message.author.display_name,
            'channel_id': str(message.channel.id),
            'content': message.content,
            'message_timestamp': message.created_at # datetime object
        }

        # Envia a mensagem para o Kafka
        producer.send(KAFKA_TOPIC, value=data)
        print(f"✅ Enviado: {data['content'][:50]}... para o tópico {KAFKA_TOPIC}")

client = DiscordToKafka()
client.run(BOT_TOKEN)