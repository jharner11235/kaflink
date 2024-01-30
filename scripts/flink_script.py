import logging
import sys

from pyflink.common import Types, Encoder
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import FileSink, OutputFileConfig
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer
from pyflink.datastream.formats.json import JsonRowDeserializationSchema


def read_from_kafka(env):
    # Build the expected data schema we're getting from Kafka
    deserialization_schema = JsonRowDeserializationSchema.Builder() \
        .type_info(Types.ROW_NAMED(
        ["customer", "transaction_type", "online_payment_amount", "in_store_payment_amount", "lat", "lon", "transaction_datetime"],
        [Types.STRING(), Types.STRING(), Types.FLOAT(), Types.FLOAT(), Types.FLOAT(), Types.FLOAT(), Types.SQL_TIMESTAMP()]
    )).build()
    # add the consumer, looking for our topic
    kafka_consumer = FlinkKafkaConsumer(
        topics='transactions',
        deserialization_schema=deserialization_schema,
        properties={'bootstrap.servers': 'kafka:9092', 'group.id': 'fake_data'}
    )
    kafka_consumer.set_start_from_earliest()

    data_stream = env.add_source(kafka_consumer)

    # Configure the sink (output) to write to a .json file
    sink = FileSink.for_row_format(
        base_path='/opt/data',
        encoder=Encoder.simple_string_encoder()
    ).with_output_file_config(
        OutputFileConfig.builder().with_part_prefix("output").with_part_suffix(".json").build()
    ).build()

    # Add the sink and start
    data_stream.sink_to(sink)
    env.execute()

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    # Init the env and add the jar needed to connect to kafka
    env = StreamExecutionEnvironment.get_execution_environment()
    print()
    env.add_jars("file:///opt/flink/lib/flink-sql-connector-kafka-3.0.2-1.18.jar")

    print("start reading data from kafka")
    read_from_kafka(env)