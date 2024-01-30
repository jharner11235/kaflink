Naming this file in all caps feels like I'm screaming...  

If you're a tl;dr person, just skim for the code blocks. If you're looking for some more info, this attempts to provide some of that to you with links for more info.

This is the culmination of a lot of documentation and some antiquated tutorials... and a little GPT help. I didn't like most of the docker images I saw for these specific parts because they seemed to take too much away from the dev or had too much added to "make things easier" that frankly confused me... If you're gonna learn a tech it seems wise to learn the real tool first, and tools built on it after. I'm still learning so I'll still be playing here :)  

Lets bring this online.  
```
docker compose up
```
Going in order of apperance in docker-compose.yml:
 - [Zookeeper](https://zookeeper.apache.org/) is a config manager/coordinator that Kafka needs to run - luckily it's shipped with Kafka so we can just run the same image for both.
 - [Kafka](https://kafka.apache.org/) is a streaming platform and we're using it to emit (fake) data that we'll catch and write in a database
 - Jobmanager is part of [Flink](https://nightlies.apache.org/flink/flink-docs-master/docs/concepts/flink-architecture/); Flink is what we're using to capture that data and do stuff with it. We can do a lot with this data, but in this case we're simply reading the Kafka topic and writing what we read. Jobmanager specifically is coordinating work within Flink.
 - Taskmanager is the other part of Flink that we're using, it's a single worker node that can do multiple tasks (which we limited to only 2) 

Now, we need to send a command to Kafka to create a new topic. Since we don't have Kafka locally, we're going to execute the command in the container - if you have Kafka (the [download](https://www.apache.org/dyn/closer.cgi?path=/kafka/3.6.1/kafka_2.13-3.6.1.tgz) not the python library) locally you could execute it from the command line instead
```
docker-compose exec kafka kafka/bin/kafka-topics.sh --create  --replication-factor 1 --partitions 1 --topic transactions --bootstrap-server kafka:9092
```
or, if you have kafka already 
```
kafka_2.13-3.6.1 % bin/kafka-topics.sh --create  --replication-factor 1 --partitions 1 --topic transactions --bootstrap-server localhost:19092
```
This will create a topic named transactions - `a topic is similar to a folder in a filesystem, and the events are the files in that folder`. This is saying that we want 1 copy of data (replication-factor), we only need it stored on the 1 broker (partitions), and the kafka server is at localhost:19092 (or, if we're inside of docker, it's kakfa:9092). feel free to run  
```
docker-compose exec kafka kafka/bin/kafka-topics.sh --help
```
for some extra info, or read https://kafka.apache.org/documentation/#intro_concepts_and_terms

Now that we have a topic set up, we can run scripts/kafka_script.py locally to simulate an external data producer. First, make sure you've set up your env.... feels like I upgrade pip every 10min
```
python3 -m pip install --upgrade pip && \
python3 -m venv .venv && \
source .venv/bin/activate && \
pip install -r requirements.txt
```
And then run the script
```
python3 scripts/kafka_script.py
```
This script is just using Faker to create some data and send it to our Kafka topic (I didn't write the script I found it and other small bits of my work [here](https://thingsolver.com/blog/streaming-analytics-in-banking-how-to-start-with-apache-flink-and-kafka-in-7-steps/) don't sue me)

Now that our "external source" is producing "data", we can set up a flink job (written in Python using Pyflink) to ingest the data. We're going to tell the job manager to schedule this job.
```
docker-compose exec jobmanager ./bin/flink run -py /opt/scripts/flink_script.py
```
This will read the data that is being created by our external source and write it to a .json file on our task manager (which can be conveniently viewed in the /data folder of this repo) 
