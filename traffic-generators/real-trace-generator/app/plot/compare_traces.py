import os
import matplotlib.pyplot as plt

if __name__ == "__main__":

    real_trace_file = 'alibaba_5min.csv'
    #simulated_trace = 'alibaba_kafka_msg_in_mean_300.csv'
    #mean_factor = 360.0
    simulated_trace = 'alibaba_kafka_msg_in_mean_108k.csv'
    mean_factor = 1.0

    with open('../traces/'+ real_trace_file, 'r') as f:
        lines = f.readlines()
        y_real = [float(x.split(',')[1].strip('\n')) for x in lines[1:]]

    with open('../traces/simulated-traces/' + simulated_trace, 'r') as f:
        lines = f.readlines()
        y_sim = [float(x.split(',')[1].strip('\n')) * mean_factor for x in lines[1:]]

    filename = 'alibaba_real_trace_vs_simulated_trace.png'
    y_real = y_real[0:len(y_sim)]



    ax1 = plt.subplot(311)
    plt.plot(range(len(y_sim)), y_sim, label='Traffic Trace from Traffic Generator')
    plt.plot(range(len(y_real)), y_real, label='Real Alibaba Trace Data')
    plt.ylabel('Traffic Load (messages per second)')
    plt.xlabel('Time (5 Minute Intervals)')
    plt.legend()

    ax2 = plt.subplot(312,sharex=ax1)
    percent_difference = [abs(x - y) for x,y in zip(y_sim,y_real)]
    plt.plot(range(len(y_real)), percent_difference, label='Real Error')
    plt.ylabel('Real Error')
    plt.xlabel('Time (5 Minute Intervals)')
    plt.legend()
    

    ax3 = plt.subplot(313,sharex=ax1)
    percent_difference = [abs(x - y)/(sum(y_real)/len(y_real)) for x,y in zip(y_sim,y_real)]
    plt.plot(range(len(y_real)), percent_difference, label='Real Error Normalized to Mean')
    plt.ylabel('Real Error Normalized to Mean')
    plt.xlabel('Time (5 Minute Intervals)')
    
    plt.suptitle("Alibaba Real Trace vs Simulated Trace with Remote Trace Topic")
    plt.legend()

    
    #plt.savefig(filename)
    plt.show()



