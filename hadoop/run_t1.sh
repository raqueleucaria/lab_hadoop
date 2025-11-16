#!/bin/bash
echo "========================================="
echo "Iniciando Job para: palavras_wiki.txt"
echo "-----------------------------------------"

# 1. Caminhos Diretos (Sem ../)
# Como você está na pasta wordCount, o arquivo está em textos/
ARQUIVO_LOCAL="textos/palavras_wiki.txt"
MAPPER="mapper.py"
REDUCER="reducer.py"

HDFS_INPUT="/user/hadoop/input"
HDFS_OUTPUT="/user/hadoop/output"

echo "1. Limpando HDFS..."
hdfs dfs -rm -r $HDFS_OUTPUT 2>/dev/null
hdfs dfs -rm -r $HDFS_INPUT 2>/dev/null

echo "2. Criando pasta e enviando arquivo..."
hdfs dfs -mkdir -p $HDFS_INPUT

# Verificação de segurança
if [ -f "$ARQUIVO_LOCAL" ]; then
    echo "Enviando $ARQUIVO_LOCAL para o HDFS..."
    hdfs dfs -put $ARQUIVO_LOCAL $HDFS_INPUT
else
    echo "ERRO CRÍTICO: O arquivo '$ARQUIVO_LOCAL' não existe nesta pasta!"
    echo "Confira se você está na pasta ~/wordCount e se a pasta 'textos' está aí."
    ls -l
    exit 1
fi

echo "3. Rodando Hadoop..."
# Mantemos os limites de memória para proteger seu notebook
time hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
  -D mapreduce.map.memory.mb=768 \
  -D mapreduce.reduce.memory.mb=768 \
  -D mapreduce.map.java.opts=-Xmx614m \
  -D mapreduce.reduce.java.opts=-Xmx614m \
  -D mapreduce.job.running.map.limit=2 \
  -files $MAPPER,$REDUCER \
  -input $HDFS_INPUT \
  -output $HDFS_OUTPUT/teste \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py"
