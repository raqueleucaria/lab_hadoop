echo "=============================="
echo "Iniciando Job para: arpq"
echo "------------------------------"

echo "Removendo diretórios antigos..."
hdfs dfs -rm -r /user/hadoop/output
hdfs dfs -rm -r /user/hadoop/input

echo "Enviando arquivo para o HDFS..."
hdfs dfs -put textos/palavras_wiki.txt /user/hadoop/input

hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
  -files mapper.py,reducer.py \
  -input /user/hadoop/input \
  -output /user/hadoop/output \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py"