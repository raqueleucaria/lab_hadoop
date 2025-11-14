# Configuração e Consumo de Dados do Discord com Spark e Kafka

Este documento descreve o processo de configuração de um pipeline de dados em tempo real, que captura mensagens do Discord e as processa usando Apache Kafka e Apache Spark Structured Streaming.

## 1. Configuração da Origem de Dados: Discord e Kafka (Produtor) 🤖

Esta etapa configura o servidor de mensagens (Kafka) e o bot que atua como Produtor, enviando dados do Discord para o Kafka.

### 1.1. Configuração do Ambiente Kafka (Local via Docker)

O Kafka e o ZooKeeper são executados localmente para simulação de ambiente em tempo real.

-  Instalação: Certifique-se de que o Docker Desktop esteja instalado.
-  Criação do docker-compose.yml: Use a configuração abaixo para iniciar os serviços Kafka e ZooKeeper.
    
```YAML
version: '3.7'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: zookeeper
    ports: ['2181:2181']
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka
    depends_on: [zookeeper]
    ports: ['9092:9092']
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      # Listener para acesso interno (kafka:29092) e externo (localhost:9092)
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
```

Execução: Inicie o cluster Kafka.

```Bash
docker-compose up -d
```

Criação do Tópico: Crie o tópico que armazenará as mensagens do Discord.
```Bash

    docker exec kafka kafka-topics --create --topic discord_messages --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```
### 1.2. Implementação do Bot Produtor

O script Python usa discord.py para monitorar canais e kafka-python para enviar o conteúdo.

    Instalação de Dependências:
```Bash

pip install discord.py kafka-python
```
Estrutura de Dados (JSON Schema): A mensagem é serializada em JSON com o seguinte esquema antes de ser enviada ao Kafka:

```JSON

    {
        "author_id": "...",
        "author_name": "...",
        "content": "Conteúdo da mensagem.",
        "message_timestamp": "2025-11-07 18:00:00.000"
    }
```
Código do Produtor (discord_producer.py):
    Objetivo: No evento on_message, captura os dados e os envia ao tópico discord_messages.

## 2. Configuração e Consumo de Dados: Apache Spark (Consumidor) 🔥

Esta etapa configura o Spark Structured Streaming para consumir o fluxo de dados em tempo real do Kafka e realizar a análise.

### 2.1. Configuração do Ambiente PySpark

Instalação de Dependências:

```Bash
pip install pyspark findspark
```

Identificação do Conector: O Spark precisa do JAR (Java Archive) do conector Kafka. Para PySpark 3.3.0 (versão comum), o pacote é:

```Python
    SPARK_KAFKA_PACKAGE = 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0'
```
| Nota de Compatibilidade: Se ocorrer o erro NoSuchMethodError (conflito de Scala), a versão do conector deve ser ajustada (3.2.0, 3.5.0, etc.) ou o cache do Ivy (~/.ivy2.5.2/cache) deve ser limpo.

2.2. Implementação do Consumidor Spark

O script Python usa SparkSession e readStream para se conectar ao Kafka e processar o fluxo.

- Estrutura de Processamento:
- - readStream: Lê o tópico discord_messages em formato binário.
- - Deserialização: Converte a coluna value (binária) em String e aplica a função from_json() usando um schema definido para extrair os campos.
- - Análise: Aplica o processamento em janelas de tempo (windowing) e realiza a contagem de mensagens por autor.
- - writeStream: Define a saída para o console (format("console")) a cada 5 segundos (trigger(processingTime='5 seconds')).

Código do Consumidor (spark_consumer.py):

```Python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, count, window
from pyspark.sql.types import StructType, StringType, TimestampType
import findspark

findspark.init()

KAFKA_SERVER = 'localhost:9092'
KAFKA_TOPIC = 'discord_messages'
SPARK_KAFKA_PACKAGE = 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0' # Usando 3.5.0 para melhor compatibilidade

spark = SparkSession.builder \
    .appName("DiscordKafkaConsumer") \
    .config("spark.jars.packages", SPARK_KAFKA_PACKAGE) \
    .getOrCreate()

# Define o Schema do JSON publicado pelo bot
schema = StructType([
    StructType([
        StructField("author_id", StringType(), True),
        StructField("author_name", StringType(), True),
        StructField("channel_id", StringType(), True),
        StructField("content", StringType(), True),
        StructField("message_timestamp", StringType(), True)
    ])
])

# Leitura do Stream Kafka
df_raw = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

# Deserialização e Parse
df_parsed = df_raw.selectExpr("CAST(value AS STRING) AS json_value") \
    .select(from_json(col("json_value"), schema).alias("data")) \
    .select(
        col("data.author_name"),
        col("data.content"),
        col("data.message_timestamp").cast(TimestampType()).alias("timestamp_processed")
    )

# Análise de Exemplo: Contagem de Mensagens em Janelas de 1 Minuto
df_analysis = df_parsed.withWatermark("timestamp_processed", "1 minute") \
    .groupBy(window(col("timestamp_processed"), "1 minute", "30 seconds"), col("author_name")) \
    .agg(count("*").alias("message_count")) \
    .orderBy("window")

# Saída para o Console
query = df_analysis.writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .trigger(processingTime='5 seconds') \
    .start()

query.awaitTermination()
```

