# spark_consumer.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, count, window
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
# import findspark # REMOVIDO! Não é mais necessário.

# findspark.init() # REMOVIDO!

# --- Configurações ---
# ATENÇÃO: Mudamos os hosts de 'localhost' para os nomes dos containers
KAFKA_SERVER = 'kafka:29092'
KAFKA_TOPIC = 'discord_messages'

SPARK_PACKAGES = (
    'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,'
    'org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0'
)
ES_INDEX = 'discord_analytics'

# ATENÇÃO: Mudamos o caminho do checkpoint para o caminho DENTRO do container
CHECKPOINT_DIR = '/app/tmp/spark-checkpoint' 

spark = SparkSession.builder \
    .appName("DiscordKafkaConsumerDocker") \
    .config("spark.jars.packages", SPARK_PACKAGES) \
    .getOrCreate() # O 'getOrCreate' vai funcionar pois o script já está no ambiente Spark

# Esquema do JSON
schema = StructType([
    StructField("author_id", StringType(), True),
    StructField("author_name", StringType(), True),
    StructField("channel_id", StringType(), True),
    StructField("content", StringType(), True),
    StructField("message_timestamp", StringType(), True)
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
        col("data.message_timestamp").cast(TimestampType()).alias("timestamp_processed"),
        col("timestamp").alias("kafka_timestamp")
    )

# 3. Análise (O BLOCO QUE FALTAVA)
df_analysis = df_parsed.withWatermark("timestamp_processed", "1 minute") \
    .groupBy(window(col("timestamp_processed"), "1 minute", "30 seconds"), col("author_name")) \
    .agg(count("*").alias("message_count")) \
    .orderBy("window")

# 4. Achatamos a coluna "window" para o ES
df_to_es = df_analysis.select(
    col("window.start").alias("start_time"),
    col("window.end").alias("end_time"),
    col("author_name"),
    col("message_count")
)

# 5. Saída (Sink) - Envia para o Elasticsearch
query = df_to_es \
    .writeStream \
    .outputMode("update") \
    .format("elasticsearch") \
    .option("es.nodes", 'elasticsearch') \
    .option("es.port", "9200") \
    .option("es.resource", ES_INDEX) \
    .option("checkpointLocation", CHECKPOINT_DIR) \
    .trigger(processingTime='10 seconds') \
    .start()

print("Spark Structured Streaming iniciado DENTRO DO CONTAINER. Enviando dados para o ES...")
query.awaitTermination()