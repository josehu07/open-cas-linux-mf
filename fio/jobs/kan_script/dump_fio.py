import os
import sys


check_dir = sys.argv[1]


print 'type queue_depth fio_avg_lat(us) fio_50_lat(us) fio_p99_lat(us) fio_bw(MB/s)'

results = []



def analyze_lat(blktrace):
    lats = []
    this_res = ''
    overall_lat = 0
    for line in blktrace:
        latency = float(line.split(' ')[-2])
        if latency > 0:
            overall_lat += latency
            lats.append(latency)

    this_res += str(sorted(lats)[0] * 1000000) + ' ' + str(sorted(lats)[len(lats)/2] * 1000000) + ' ' + str(overall_lat/len(lats) * 1000000) + ' ' + str(sorted(lats)[len(lats)/100*99] * 1000000) + ' ' + str(sorted(lats)[-1] * 1000000) + ' '
    return this_res


for subdir in os.listdir(check_dir):
    #print subdir
    res = ''
    res1 = ''
    res2 = ''
    res3 = ''
    jump = False
    for each_file in os.listdir(check_dir + '/' + subdir):
       if each_file == 'config.json':
           with open(check_dir + '/' + subdir + '/' + each_file, 'r')  as config_file:
               dict_from_file = eval(config_file.read())
               res1 = dict_from_file['type'] + ' ' + str(dict_from_file['qd']) + ' ' + str(dict_from_file['script']) + ' '
       if each_file == 'running':
           with open(check_dir + '/' + subdir + '/' + each_file, 'r')  as fio_output_file:
               unit = 1.0
               for line in fio_output_file:
                  # parse latency
                  if 'clat' in line and 'percentiles' not in line:
                      for item in line.split(','):
                          if 'avg=' in item:
                              if 'nsec' in line:
                                  res2 += str(float(item.split('=')[-1])/1000) + ' '
                              elif 'msec' in line:
                                  res2 += str(float(item.split('=')[-1])*1000) + ' '
                              else:
                                  res2 += str(float(item.split('=')[-1])) + ' '
                  if 'clat' in line and 'percentiles' in line:
                      if 'nsec' in line:
                          unit = 1.0/1000
                      if 'msec' in line:
                          unit = 1.0*1000
                  if '50.0th=' in line and '99.0th=' in line:
                      items = line.strip('\n').replace(' ','').split(',')
                      lat_50 = 0
                      lat_99 = 0
                      for item in items:
                          if '50.0th' in item:
                              lat_50 = float(item.split('[')[-1].strip(']'))
                          if '99.0th' in item:
                              lat_99 = float(item.split('[')[-1].strip(']'))
                      #res2 += line.strip('\n').replace(' ','') + unit + ' '
                      res2 += str(lat_50*unit) + ' ' + str(lat_99*unit) + ' '
                  
                  #if 'WRITE: bw=' in line:
                  if 'READ: bw=' in line:
                      res2 += line.split('(')[0].split('bw=')[1].strip('MiB/s ') + ' '
                      #res2 += line.split(',')[0].split('(')[1].strip('MB/s)') + ' '
    
    print res1+res2+res3#, subdir
    #results.append(res1+res2+res3)

#print("\n".join(sorted(results)))
