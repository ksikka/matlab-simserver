from snapshot import snapshot


for i in range(1,2000):
    print 'ok ' + str(i)
    snapshot("C:\\Users\\sikkak\\Desktop\\DemoSim\\", 'demosim%d'%i)
