# Configuração do Ambiente Kafka com Docker

Iniciando os serviços do kafka

```
docker compose up -d
```

Criando um tópico Kafka para mensagens do Discord

```
docker exec kafka kafka-topics --create --topic discord_messages --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```