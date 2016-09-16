import time


class PirusPlugin(object):

    def run(self, config):
        self.notify('Dodo', 0.0, "Coussin trouvé")
        for i in range(1,100):
        	time.sleep(3)
        	self.notify('Dodo', i/100, "zzz")
        self.notify('Dodo', 1,"Baille")

    def notify(self, task_name, percent, message):
        print(task_name, " ", str(round(percent*100, 2)) + "%", " ", message) 





if __name__ == '__main__':
	test = PirusPlugin()
	test.run(None)