# spark_consumer.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, count, window
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import findspark

# Inicializa o PySpark (necessário se não estiver usando o spark-submit)
findspark.init()

# --- Configurações ---
KAFKA_SERVER = 'localhost:9092'
KAFKA_TOPIC = 'discord_messages'
SPARK_KAFKA_PACKAGE = 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0'

spark = SparkSession.builder \
    .appName("DiscordKafkaConsumerLocal") \
    .config("spark.jars.packages", SPARK_KAFKA_PACKAGE) \
    .getOrCreate()

# O Spark deve inferir o timestamp do Kafka, mas o esquema precisa ser definido para o JSON
schema = StructType([
    StructField("author_id", StringType(), True),
    StructField("author_name", StringType(), True),
    StructField("channel_id", StringType(), True),
    StructField("content", StringType(), True),
    StructField("message_timestamp", StringType(), True) # Mantenha como String e converta depois
])

# 1. Leitura do Kafka
df_raw = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

# 2. Deserialização e Parse
df_parsed = df_raw.selectExpr("CAST(value AS STRING) AS json_value") \
    .select(from_json(col("json_value"), schema).alias("data")) \
    .select(
        col("data.author_name"),
        col("data.content"),
        col("data.message_timestamp").cast(TimestampType()).alias("timestamp_processed"), # Converte o campo de timestamp
        col("timestamp").alias("kafka_timestamp") # Timestamp que o Kafka adicionou
    )

# 3. Exemplo de Análise: Contar mensagens a cada 1 minuto (Windowing)
df_analysis = df_parsed.withWatermark("timestamp_processed", "1 minute") \
    .groupBy(window(col("timestamp_processed"), "1 minute", "30 seconds"), col("author_name")) \
    .agg(count("*").alias("message_count")) \
    .orderBy("window")

# 4. Saída (Sink) - Imprime no console a cada 5 segundos
query = df_analysis \
    .writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .trigger(processingTime='5 seconds') \
    .start()

print("Spark Structured Streaming iniciado. Enviando mensagens no Discord para ver os resultados...")
query.awaitTermination()