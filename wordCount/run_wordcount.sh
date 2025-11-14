#!/bin/bash

# Defina a lista de arquivos
arquivos=("arqp" "poema01" "poema02" "procjuizes")

# Recria a estrutura de pastas no HDFS
echo "Criando pasta base no HDFS..."
hdfs dfs -mkdir -p /user/hadoop/wordCount/input

# Envia todos os arquivos de texto para o HDFS
hdfs dfs -put textos/* /user/hadoop/wordCount/input

# Loop para processar cada arquivo
for arquivo in "${arquivos[@]}"; do
    echo "=============================="
    echo "Iniciando Job para: $arquivo"
    echo "------------------------------"
    
    # Define caminhos
    INPUT_PATH="/user/hadoop/wordCount/input"
    OUTPUT_PATH="/user/hadoop/wordCount/output/$arquivo"

    # Limpeza preventiva do output
    hdfs dfs -rm -r $OUTPUT_PATH 2>/dev/null

    hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
      -D mapreduce.map.memory.mb=512 \
      -D mapreduce.reduce.memory.mb=512 \
      -D mapreduce.map.java.opts=-Xmx410m \
      -D mapreduce.reduce.java.opts=-Xmx410m \
      -files mapper.py,reducer.py \
      -input $INPUT_PATH/$arquivo.txt \
      -output $OUTPUT_PATH \
      -mapper "python3 mapper.py" \
      -reducer "python3 reducer.py"
      
    echo "Fim do processamento de $arquivo"
done