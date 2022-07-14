import os
import matplotlib.pyplot as plt

if __name__ == "__main__":

    data_files = os.listdir('../data')
    for file in data_files:
        if '_5min' in file:
            print(file)

            with open('../data/'+ file, 'r') as f:
                lines = f.readlines()
                y = [float(x.split(',')[1].strip('\n')) for x in lines[1:]]

                fig = plt.figure()
                plt.plot(range(len(y)), y)
                plt.ylabel('load')
                plt.xlabel('time')
                plt.suptitle(file)

                plt.savefig(file.replace('.csv','.png'))




