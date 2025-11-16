#!/bin/bash

# 1. Defina a lista de arquivos
arquivos=("arqp.txt" "poema01.txt" "poema02.txt" "procjuizes.txt")

# [NOVO] Recria a estrutura de pastas no HDFS (porque você apagou tudo)
echo "Criando pasta base no HDFS..."
hdfs dfs -mkdir -p /user/hadoop/wordCount/input

# 2. Loop para processar cada um
for arquivo in "${arquivos[@]}"; do
    echo "=============================="
    echo "Iniciando Job para: $arquivo"
    echo "------------------------------"
    
    # Define caminhos
    INPUT_PATH="/user/hadoop/wordCount/input/$arquivo"
    OUTPUT_PATH="/user/hadoop/wordCount/output/$arquivo"
    
    # [NOVO] Envia o arquivo local para o HDFS
    echo "Enviando arquivo local (textos/$arquivo) para o HDFS..."
    # Remove do HDFS se já existir para garantir versão limpa
    hdfs dfs -rm $INPUT_PATH 2>/dev/null 
    hdfs dfs -put textos/$arquivo $INPUT_PATH

    # Limpeza preventiva do output
    hdfs dfs -rm -r $OUTPUT_PATH 2>/dev/null

    # Roda o Hadoop Streaming com LIMITES DE MEMÓRIA
    hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
      -D mapreduce.map.memory.mb=512 \
      -D mapreduce.reduce.memory.mb=512 \
      -D mapreduce.map.java.opts=-Xmx410m \
      -D mapreduce.reduce.java.opts=-Xmx410m \
      -files mapper.py,reducer.py \
      -input $INPUT_PATH \
      -output $OUTPUT_PATH \
      -mapper "python3 mapper.py" \
      -reducer "python3 reducer.py"
      
    echo "Fim do processamento de $arquivo"
done
