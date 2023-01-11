/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package de.tu_berlin.flink_jobs;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.assigners.TumblingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.util.Collector;

//import org.slf4j.Logger;
//import org.slf4j.LoggerFactory;

public class WordCount {

	//private static final Logger LOG = LoggerFactory.getLogger(WordCount.class);

	public static void main(String[] args) throws Exception {

		// Flink
		//LOG.info("Starting Word Count Engine");
		StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();


		//Source
		KafkaSource<String> source = KafkaSource.<String>builder()
				.setBootstrapServers("kafka.default.svc.cluster.local:9092")
				.setTopics("data")
				.setGroupId("flink-group")
				.setStartingOffsets(OffsetsInitializer.latest())
				.setValueOnlyDeserializer(new SimpleStringSchema())
				.build();

		DataStream<String> stream = env.fromSource(source, WatermarkStrategy.noWatermarks(), "Kafka Source");
		//LOG.info("Connected to Kafka broker and setup datastream");
		//KafkaSource<String> consumer =
		//        new KafkaSource<String> (inputTopic, new SimpleStringSchema(), properties);
		//DataStream<String> stream = env.addSource(consumer);

		//Transformations
		// Flink

		DataStream<Tuple2<String, Integer>> counts =
				// The text lines read from the source are split into words
				// using a user-defined function. The tokenizer, implemented below,
				// will output each word as a (2-tuple) containing (word, 1)
				stream.flatMap(new Tokenizer())
						.name("tokenizer")
						// keyBy groups tuples based on the "0" field, the word.
						// Using a keyBy allows performing aggregations and other
						// stateful transformations over data on a per-key basis.
						// This is similar to a GROUP BY clause in a SQL query.
						.keyBy(value -> value.f0)
						// For each key, we perform a simple sum of the "1" field, the count.
						// If the input data stream is bounded, sum will output a final count for
						// each word. If it is unbounded, it will continuously output updates
						// each time it sees a new instance of each word in the stream.
						.window(TumblingProcessingTimeWindows.of(Time.seconds(1)))
						.sum(1)
						.name("counter");


		counts.print().name("print-sink");
		//LOG.info("Prepared for Execution");

		//execute
		env.execute("kafka streaming word count");

	}

	public static final class Tokenizer
			implements FlatMapFunction<String, Tuple2<String, Integer>> {

		@Override
		public void flatMap(String value, Collector<Tuple2<String, Integer>> out) {
			// normalize and split the line
			String[] tokens = value.toLowerCase().split("\\W+");

			// emit the pairs
			for (String token : tokens) {
				if (token.length() > 0) {
					out.collect(new Tuple2<>(token, 1));
				}
			}
		}
	}

}