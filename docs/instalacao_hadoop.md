# Instalação do Hadoop

## Pré-Requisito:
É preciso ter o java
   
Atualize: `sudo apt update && sudo apt upgrade -y`

Instale jdk: `sudo apt install openjdk-11-jdk -y`
Verfique a instalacao: `java --version`

Adicine a variavel de ambiente: `nano ~/.bashrc`

``` bash
# JAVA
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

Aplique as alteracoes `source ~/.bashrc`

## Baixar e Distribuir o Hadoop:

Baixe e descompacte apenas no master e, em seguida, copie a pasta pronta para os slaves.

1.  No master (`hadoop@master:~$`):

``` bash
# 1. Baixe o Hadoop
wget https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz

# 2. Descompacte
tar -xzvf hadoop-3.3.6.tar.gz

# 3. Mova para um local padrão (/usr/local)
sudo mv hadoop-3.3.6 /usr/local/hadoop

# 4. Dê permissão da pasta para o usuário 'hadoop'
sudo chown -R hadoop:hadoop /usr/local/hadoop

```

1. Do master, copie para os slaves:

``` bash
scp -r /usr/local/hadoop hadoop@slave-1:/usr/local/
scp -r /usr/local/hadoop hadoop@slave-2:/usr/local/
scp -r /usr/local/hadoop hadoop@slave-3:/usr/local/
```

resultado esperado
![alt text](image-9.png)
``` bash

hadoop@master:~$ scp hadoop-3.3.6.tar.gz hadoop@slave-1:~/
hadoop-3.3.6.tar.gz                           100%  696MB 105.9MB/s   00:06    
hadoop@master:~$ scp hadoop-3.3.6.tar.gz hadoop@slave-2:~/
hadoop-3.3.6.tar.gz                           100%  696MB 116.0MB/s   00:06    
hadoop@master:~$ scp hadoop-3.3.6.tar.gz hadoop@slave-3:~/
hadoop-3.3.6.tar.gz                           100%  696MB  77.0MB/s   00:09

```

1. Em CADA slave, conecte-se e faça a instalação manualmente.

``` bash
# Conecte no slave
ssh hadoop@slave-X

# 1. Descompacte o arquivo
tar -xzvf hadoop-3.3.6.tar.gz

# 2. Mova para /usr/local
sudo mv hadoop-3.3.6 /usr/local/hadoop

# 3. Dê permissão ao usuário hadoop
sudo chown -R hadoop:hadoop /usr/local/hadoop


```


## Configurar Variáveis de Ambiente (em TODAS as 4 VMs)

``` bash
# HADOOP
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
```

## Configurando os Arquivos do Cluster


1. `cd $HADOOP_HOME/etc/hadoop`
2. Abra no nano e edite os arquivos:
   - `hadoop-env.sh`: descomente java_home e adicione o caminho
		```bash
		export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
		```
   - `workers`: Apague o localhost e adicione os nomes dos seus slaves:
		```bash
		slave-1
		slave-2
		slave-3
		```
   - `core-site.xml`: edite o configuration
		```xml
		<configuration>
			<property>
					<name>fs.defaultFS</name>
					<value>hdfs://master:9000</value>
			</property>
		</configuration>
		```
   - `hdfs-site.xml`: edite o configuration
		```xml
		<configuration>
			<property>
					<name>dfs.replication</name>
					<value>3</value>
			</property>
			<property>
					<name>dfs.namenode.name.dir</name>
					<value>file:///usr/local/hadoop/data/hdfs/namenode</value>
			</property>
			<property>
					<name>dfs.datanode.data.dir</name>
					<value>file:///usr/local/hadoop/data/hdfs/datanode</value>
			</property>
		</configuration>
		```
   - `mapred-site.xml`: edite o configuration
		```xml
		<configuration>
			<property>
					<name>mapreduce.framework.name</name>
					<value>yarn</value>
			</property>
		</configuration>
		```

    - `yarn-site.xml`: edite o configuration
		```bash
		<configuration>
		<!-- Site specific YARN configuration properties -->
			<property>
					<name>yarn.resourcemanager.hostname</name>
				<value>master</value>
			</property>
			<property>
					<name>yarn.nodemanager.aux-services</name>
					<value>mapreduce_shuffle</value>
			</property>
		</configuration>
		```



## Distribuir Configuração e Criar Pastas

1. No master, copie todos esses arquivos de configuração para os slaves:
```bash
# Ainda na pasta $HADOOP_HOME/etc/hadoop
scp * hadoop@slave-1:$HADOOP_HOME/etc/hadoop/
scp * hadoop@slave-2:$HADOOP_HOME/etc/hadoop/
scp * hadoop@slave-3:$HADOOP_HOME/etc/hadoop/
```

2 No master, crie as pastas que definimos no hdfs-site.xml:

- Para o NameNode (só no master):
```bash
mkdir -p /usr/local/hadoop/data/hdfs/namenode
```
- Para os DataNodes (só nos slaves, execute do master):

```bash
ssh hadoop@slave-1 "mkdir -p /usr/local/hadoop/data/hdfs/datanode"
ssh hadoop@slave-2 "mkdir -p /usr/local/hadoop/data/hdfs/datanode"
ssh hadoop@slave-3 "mkdir -p /usr/local/hadoop/data/hdfs/datanode"
```
## Formatar e Iniciar o Cluster

(SÓ no master)

1. Formate o HDFS: Isso apaga tudo do HDFS e o prepara.
	```bash
	hdfs namenode -format
	```

2. Você deve ver uma mensagem de successfully formatted.

3. Inicie os Serviços:
	```bash
	# Inicia o HDFS (NameNode no master, DataNodes nos slaves)
	start-dfs.sh

	# Inicia o YARN (ResourceManager no master, NodeManagers nos slaves)
	start-yarn.sh
	```

## Verifique o Cluster

1. JPS
- No seu terminal hadoop@master:~$, digite:```jps```
	```bash
	# saida esperada
	10516 SecondaryNameNode
	10712 ResourceManager
	10282 NameNode
	11039 Jps
	```
- Verifiue o slave: ```ssh hadoop@slave-1 "jps"```

	```bash
	# saida esperada
	10098 DataNode
	10396 Jps
	10238 NodeManager
	```

2. Criando pasta

- Tente criar uma pasta dentro do sistema de arquivos do Hadoop:
```hdfs dfs -mkdir /hello-world```
- Se o comando rodar sem erros, PARABÉNS! Seu cluster está 100% funcional.
	```hdfs dfs -ls```

	```
	hadoop@master:~$ hdfs dfs -mkdir /hello-world
	hadoop@master:~$ hdfs dfs -ls /
	Found 1 items
	drwxr-xr-x   - hadoop supergroup          0 2025-11-09 20:44 /hello-world
	```
