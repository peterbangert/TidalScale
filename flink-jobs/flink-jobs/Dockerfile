FROM flink
RUN mkdir -p $FLINK_HOME/usrlib
COPY ./target/flink-job-0.1.jar $FLINK_HOME/usrlib/flink-job-0.1.jar
#RUN chown -R flink:flink $FLINK_HOME/usrlib/flink-job-0.1.jar
#RUN chmod 644 $FLINK_HOME/usrlib/flink-job-0.1.jar
#ENTRYPOINT ["tail", "-f", "/dev/null"]
