FROM flink
RUN mkdir -p $FLINK_HOME/usrlib
COPY ./target/quickstart-0.1.jar $FLINK_HOME/usrlib/quickstart-0.1.jar
#RUN chown -R flink:flink $FLINK_HOME/usrlib/quickstart-0.1.jar
#RUN chmod 644 $FLINK_HOME/usrlib/quickstart-0.1.jar
#ENTRYPOINT ["tail", "-f", "/dev/null"]
