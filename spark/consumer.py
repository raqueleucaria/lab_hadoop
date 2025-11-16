from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Inicializa sessão Spark
spark = SparkSession.builder \
    .appName("DiscordKafkaConsumer") \
    .config("spark.sql.shuffle.partitions", "2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# lendo do kafka
df_raw = (
    spark.readStream
         .format("kafka")
         .option("kafka.bootstrap.servers", "localhost:9092")
         .option("subscribe", "discord_messages")
         .option("startingOffsets", "latest")  # pode usar earliest
         .load()
)

df_text = df_raw.selectExpr("CAST(value AS STRING) as json_str")

schema = StructType([
    StructField("author_id", StringType(), True),
    StructField("author_name", StringType(), True),
    StructField("channel_id", StringType(), True),
    StructField("content", StringType(), True),
    StructField("message_timestamp", StringType(), True)
])

# Converte JSON → colunas estruturadas
df_parsed = df_text.select(
    from_json(col("json_str"), schema).alias("data")
).select("data.*")

# Converte para timestamp real (já que vem string do Kafka)
df_parsed = df_parsed.withColumn(
    "message_timestamp", to_timestamp("message_timestamp")
)

# df_parsed.writeStream \
#     .format("org.elasticsearch.spark.sql") \
#     .option("es.nodes", "elasticsearch:9200") \
#     .option("es.nodes.wan.only", "true") \
#     .option("es.resource", "discord_messages/_doc") \
#     .option("checkpointLocation", "/app/tmp/checkpoint") \
#     .start()

query = (
    df_parsed.writeStream
        .outputMode("append")
        .format("console")
        .option("truncate", False)
        .start()
)



query.awaitTermination()
