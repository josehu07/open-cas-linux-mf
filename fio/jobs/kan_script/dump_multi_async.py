import matplotlib
matplotlib.use('Agg')
from pylab import *
import os
import sys
from pyreuse.helpers import *


check_dir = sys.argv[1]


print 'type qd write_ratio read_write_shared_space throughput'

results = []

draw_graph = False


def analyze_lat(blktrace):
    lats = []
    this_res = ''
    overall_lat = 0
    for line in blktrace:
        latency = float(line.split(' ')[-2])
        if latency > 0:
            overall_lat += latency
            lats.append(latency)

    this_res += str(sorted(lats)[0] * 1000000) + ' ' + str(sorted(lats)[len(lats)/2] * 1000000) + ' ' + str(overall_lat/len(lats) * 1000000) + ' ' + str(sorted(lats)[len(lats)/100*75] * 1000000) + ' ' + str(sorted(lats)[len(lats)/100*99] * 1000000) + ' ' + str(sorted(lats)[-1] * 1000000) + ' '
    return this_res

two_drawed = False
for subdir in os.listdir(check_dir):
    #print subdir
    res = ''
    res1 = ''
    res2 = ''
    res3 = ''
    jump = False
    i = 0
    X_s = []
    QD = -1
    for each_file in os.listdir(check_dir + '/' + subdir):
       if each_file == 'config.json':
           with open(check_dir + '/' + subdir + '/' + each_file, 'r')  as config_file:
               dict_from_file = eval(config_file.read())
               res1 = dict_from_file['type'] + ' ' + str(dict_from_file['qd']) + ' ' + str(dict_from_file['write_ratio']) + ' ' + str(dict_from_file['read_write_shared_space']) + ' '
       if each_file == 'running' and jump == False:
           with open(check_dir + '/' + subdir + '/' + each_file, 'r') as running_result:
               last_line = running_result.readlines()[-1]
               #res2 = running_result.readlines()[-1].split(',')[-1].split(':')[-1].strip(' MB/s\n') + ' '
               res2 = last_line.split(',')[-1].split(':')[-1].strip(' MB/s\n') + ' ' 
       if each_file == 'blkparse-output.txt.parsed' and jump == False:
           with open(check_dir + '/' + subdir + '/' + each_file, 'r') as blocktrace:
               res3 = analyze_lat(blocktrace)
           #with open(check_dir + '/' + subdir + '/' + each_file, 'r')  as latency_file:
           #    lines = latency_file.readlines()
           #    res += lines[1].strip('us\n').split(':')[1] + lines[2].strip('us\n').split(':')[1] + lines[3].strip('us\n').split(':')[1] + lines[4].strip('us\n').split(':')[1]
       if each_file == 'latency.sort' and jump == False:
           #clf()
           #cla()
           if not draw_graph:
               continue
           X = []
           with open(check_dir + '/' + subdir + '/' + each_file, 'r') as input_file:
               for line in input_file:
                   X.append(float(line))
           Y = map(lambda x: float(x)/len(X), range(1, len(X)+1))
           #label_str='QD=' + str(QD)
           #label_str='offset=' + str(OFF)
           label_str=str(TYPE)  + '_QD=' + str(QD) + '_offset=' + str(OFF)
           X_s.append(X)
           plot(Y, X_s[i], label=label_str)
           xticks([0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
           yticks(range(0,int(max(X)),5),rotation=0)
           #legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
           legend(loc='upper right')
           savefig(check_dir + '/' + subdir + '/' + 'latency_cdf.png')
           i += 1
    if QD == 2:
        two_drawed = True
    if jump == True:
        continue
    else:
        print res1+res2+res3#, subdir
    #results.append(res1+res2+res3)
if draw_graph:
    savefig(check_dir + '/' + 'latency_cdf.png')
#print("\n".join(sorted(results)))

