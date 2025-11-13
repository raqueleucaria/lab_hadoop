hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
  -files mapper.py,reducer.py \
  -input /user/hadoop/input/poema01.txt \
  -output /user/hadoop/output \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py"