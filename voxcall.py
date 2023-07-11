import time
import datetime
import subprocess
import pyaudio
import wave
import sys
import os
import errno
from numpy import short, array, chararray, frombuffer, log10
import traceback
from tkinter import *
from tkinter import ttk
from configparser import ConfigParser
import _thread
import urllib3
from shutil import copyfile
import logging

#logging.basicConfig(filename='log.txt',filemode='w',level=logger.debug)

# create logger
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

#create file handler and set level to debug
fh = logging.FileHandler('log.txt',mode='w')
fh.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# add ch and fh to logger
logger.addHandler(ch)
logger.addHandler(fh)


#record_threshold = 800
vox_silence_time = 2            # Reset twice, below, based on settings in "Section1" and "Section" of config file
mp3_bitrate = 32000
start_minimized = 0
rectime = .1
rec_debounce_counter = 0
timeout_time_sec = 120
'''
class Logger(object):
	def __init__(self):
		self.terminal = sys.stdout
		self.logfilename = 'log.txt'
		self.log = open(self.logfilename, "w")
	def __del__(self):
		self.log.close()
	def write(self, message):
		self.terminal.write(message)
		self.log.write(message)
		self.log.close()
		self.log = open(self.logfilename, "a")
		#log.close()
	def flush(self):
		self.terminal.flush()
		#log = open(self.logfilename, "w")
		self.log.flush()
		#self.log.close()

sys.stdout = Logger()
'''
# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
	version = os.path.basename(sys.executable).split('.')[0]
elif __file__:
	version = os.path.basename(__file__).split('.')[0]
	
config = ConfigParser()
config.read('config.cfg')

try:
	audio_dev_index = config.getint('Section1','audio_dev_index')
except:
	audio_dev_index = 0
try:
	record_threshold_config = config.getint('Section1','record_threshold')
except:
	record_threshold_config = 75
try:
	vox_silence_time = config.getfloat('Section1','vox_silence_time')
except:
	vox_silence_time = 3
try:
	in_channel_config = config.get('Section1','in_channel')
except:
	in_channel_config = 'mono'
try:
	BCFY_SystemId_config = config.get('Section1','BCFY_SystemId')
except:
	BCFY_SystemId_config = ''
try:
	BCFY_SlotId_config = config.get('Section1','BCFY_SlotId')
except:
	BCFY_SlotId_config = '1'
try:
	RadioFreq_config = config.get('Section1','RadioFreq')
except:
	RadioFreq_config = ''
try:
	BCFY_APIkey_config = config.get('Section1','BCFY_APIkey')
except:
	BCFY_APIkey_config = ''
try:
	saveaudio_config = config.getint('Section1','saveaudio')
except:
	saveaudio_config = 0
try:
	vox_silence_time = config.getfloat('Section','vox_silence_time')
except:
	vox_silence_time = 2
try:
	RDIO_APIkey_config = config.get('Section1','RDIO_APIkey')
except:
	RDIO_APIkey_config = ''
try:
	RDIO_APIurl_config = config.get('Section1','RDIO_APIurl')
except:
	RDIO_APIurl_config = ''
try:
	RDIO_system_config = config.get('Section1','RDIO_system')
except:
	RDIO_system_config = ''
try:
	RDIO_tg_config = config.get('Section1','RDIO_tg')
except:
	RDIO_tg_config = ''

try:
	root = Tk()
	if start_minimized==1:
		root.iconify()
	root.title('voxcall')
except:
	root = ''
try:
	root.iconbitmap('voxcall.ico')
except:
	pass

try:
	p = pyaudio.PyAudio()
	#list of the names of the audio input and output devices
	input_devices = []
	input_device_indices = {}

	#FIND THE AUDIO DEVICES ON THE SYSTEM
	info = p.get_host_api_info_by_index(0)
	numdevices = info.get('deviceCount')

	#find index of pyaudio input and output devices
	for i in range (0,numdevices):
		if p.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')>0:
			input_devices.append(p.get_device_info_by_host_api_device_index(0,i).get('name'))
			input_device_indices[p.get_device_info_by_host_api_device_index(0,i).get('name')] = i
			inv_input_device_indices = dict((v,k) for k,v in input_device_indices.items())
	p.terminate()
except:
	#exc_type, exc_value, exc_traceback = sys.exc_info()
	#traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2,file=sys.stdout)
	logging.exception('Got exception on main handler')

if root != '':
	record_threshold = IntVar()
	record_threshold.set(record_threshold_config)
	#make sure the record_threshold value is not zero to avoid math issues
	if record_threshold.get() < 1:
		record_threshold.set(1)
	input_device = StringVar()
	output_device = StringVar()
	freqvar = StringVar()
	statvar = StringVar()
	statvar.set("Waiting For Audio")
	BCFY_APIkey = StringVar()
	BCFY_APIkey.set(BCFY_APIkey_config)
	BCFY_SystemId = StringVar()
	BCFY_SystemId.set(BCFY_SystemId_config)
	BCFY_SlotId = StringVar()
	BCFY_SlotId.set(BCFY_SlotId_config)
	RadioFreq = StringVar()
	RadioFreq.set(RadioFreq_config)
	RDIO_APIkey = StringVar()
	RDIO_APIkey.set(RDIO_APIkey_config)
	RDIO_system = StringVar()
	RDIO_system.set(RDIO_system_config)
	RDIO_tg = StringVar()
	RDIO_tg.set(RDIO_tg_config)
	RDIO_APIurl = StringVar()
	RDIO_APIurl.set(RDIO_APIurl_config)
	saveaudio = IntVar()
	saveaudio.set(saveaudio_config)
	in_channel = StringVar()
	in_channel.set(in_channel_config)
	barvar = IntVar()
	barvar.set(10)
	input_device.set(inv_input_device_indices.get(audio_dev_index,input_devices[0]))

RATE = 22050
chunk = 2205
FORMAT = pyaudio.paInt16
def start_audio_stream():
	global pr
	global recordstream
	try:
		pr = pyaudio.PyAudio()
		CHANNELS = 1
		if root != '':
			if in_channel.get() == 'left' or in_channel.get() == 'right':
				CHANNELS = 2 #chan
		else:
			if in_channel_config == 'left' or in_channel_config == 'right':
				CHANNELS = 2
		if root != '':
			index = input_device_indices[input_device.get()]
		else:
			index = audio_dev_index
		recordstream = pr.open(format = FORMAT,
					channels = CHANNELS,
					rate = RATE,
					input = True,
					output = True,
					frames_per_buffer = chunk,
					input_device_index = index,)
	except:
		#exc_type, exc_value, exc_traceback = sys.exc_info()
		#traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2,file=sys.stdout)
		logging.exception('Got exception on main handler')

start_audio_stream()

def change_audio_input(junk):
	recordstream.close()
	pr.terminate()
	start_audio_stream()
	
def record(seconds,channel='mono'):
	alldata = bytearray()
	for i in range(0, int(RATE / chunk * seconds)):
		data = recordstream.read(chunk)
		alldata.extend(data)
	data  = frombuffer(alldata, dtype=short)
	if channel == 'left':
		data = data[0::2]
	elif channel == 'right':
		data = data[1::2]
	else:
		data = data
	return data

def heartbeat():
	if (root != '' and BCFY_APIkey.get() != '') or (root == '' and BCFY_APIkey_config != ''):
		if version.endswith('DEV'):
			url = 'https://api.broadcastify.com/call-upload-dev'
		else:
			url = 'https://api.broadcastify.com/call-upload'
		http = urllib3.PoolManager()
		if root != '':
			apiKey = BCFY_APIkey.get()
			systemId = BCFY_SystemId.get()
		else:
			apiKey = BCFY_APIkey_config
			systemId = BCFY_SystemId_config
		r = http.request(
			'POST',
			url,
			fields={'apiKey': apiKey,'systemId': systemId,'test': '1'})
		if r.status != 200:
			logger.debug("heartbeat failed with status " + str(r.status))
			logger.debug(r.data)
		else:
			logger.debug("heartbeat OK at " + str(time.time()))

def upload_rdio(fname):
	if root != '':
		url = RDIO_APIurl.get()
		key = RDIO_APIkey.get()
		system = RDIO_system.get()
		tg = RDIO_tg.get()
	else:
		url = RDIO_APIurl_config
		key = RDIO_APIkey_config
		system = RDIO_system_config
		tg = RDIO_tg_config
	if url != '' and key != '' and system != '' and tg != '':
		http = urllib3.PoolManager()
		f = open(fname,'rb')
		audio_data = f.read()
		f.close()
		r = http.request(
			'POST',
			url,
			fields={'key': key,'dateTime': datetime.datetime.utcnow().isoformat() + 'Z','system':str(system),'talkgroup':str(tg),'audio': (fname, audio_data, 'application/octet-stream')},
			timeout=30)
		if r.status != 200:
			logger.debug("initial connect failed with status " + str(r.status))
			logger.debug(r.data)
		else:
			logger.debug("upload to rdio-scanner OK")
	else:
		logger.info("No rdio-scanner config detected, skipping upload to rdio-scanner API")

def upload(fname,duration):
	if (root != '' and BCFY_APIkey.get() != '') or (root == '' and BCFY_APIkey_config != ''):
		if version.endswith('DEV'):
			url = 'https://api.broadcastify.com/call-upload-dev'
		else:
			url = 'https://api.broadcastify.com/call-upload'
		http = urllib3.PoolManager()
		if root != '':
			r = http.request(
				'POST',
				url,
				fields={'apiKey': BCFY_APIkey.get(),'systemId': BCFY_SystemId.get(),'callDuration': str(duration),'ts': fname.split('-')[0],'tg': BCFY_SlotId.get(),'src': '0','freq': RadioFreq.get(),'enc': 'mp3'})
		else:
			r = http.request(
				'POST',
				url,
				fields={'apiKey': BCFY_APIkey_config,'systemId': BCFY_SystemId_config,'callDuration': str(duration),'ts': fname.split('-')[0],'tg': BCFY_SlotId_config,'src': '0','freq': RadioFreq_config,'enc': 'mp3'})

		if r.status != 200:
			logger.debug("initial connect failed with status " + str(r.status))
			logger.debug(r.data)
		else:
			resp = r.data.decode('utf-8').split(' ')
			if resp[0] == '0':
				upload_url = resp[1]
				file_data = open(fname,"rb").read()
				r1 = http.request(
				'PUT',
				upload_url,
				fields={
					'filefield': (fname, file_data, 'audio/mpeg'),
				})
				if r1.status == 200:
					logger.debug("upload to BCFY OK")
				else:
					logger.debug("upload failed with status " + str(r1.status))
					logger.debug(r1.data)
			else:
				logger.debug("error response from server: " + r.data.decode('utf-8'))
	else:
		logger.info("No BCFY config found, not attempting to upload there")
	if root != '':
		saveit = saveaudio.get()
	else:
		saveit = saveaudio_config
	if saveit == 0:
		time.sleep(10)  #wait to make sure the other thread uploading to rdio-scanner has time to grab the file before deleting it
		os.remove(fname)
	else:
		try:
			os.makedirs('./audiosave')
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise
		copyfile(fname,'./audiosave/'+fname)
		time.sleep(10)  #wait to make sure the other thread uploading to rdio-scanner has time to grab the file before deleting it
		os.remove(fname)

def start():
	global rec_debounce_counter
	last_API_attempt = 0
	#wait for audio to be present
	counter = 0
	while 1:
		if time.time()-last_API_attempt > 10*60:
			_thread.start_new_thread(heartbeat,())  #ping the API every 10 minutes so it knows we're alive
			last_API_attempt = time.time()
		#get 100 ms of audio
		if root != '':
			chan = in_channel.get()
		else:
			chan = in_channel_config
		audio_data = record(rectime,chan)
		if max(abs(audio_data)) == 0 and root != '':
				barvar.set(1)
		elif counter >=6 and root != '':
			#set the bar graph display based on the current audio peak using a log scale
			barvar.set(max(100-int(log10(max(max(abs(audio_data)),1.0)/32768.)*10/-25.*100),3))  #min of scale is -25 dB
			counter = 0
		counter = counter + 1
		if root != '':
			if 100-log10(max(max(abs(audio_data)),1.0)/32768.)*10/-25.*100 > record_threshold.get() or record_threshold.get()==0:
				rec_debounce_counter = rec_debounce_counter + 1
				logger.debug('Level: ' + str(100-log10(max(max(abs(audio_data)),1.0)/32768.)*10/-25.*100) + " Threshold: " + str(record_threshold.get()))
			else:
				rec_debounce_counter = 0
		else:
			if  max(abs(audio_data))> record_threshold_config:
				rec_debounce_counter = rec_debounce_counter + 1
				logger.debug('Level: ' + str(max(abs(audio_data))) + " Threshold: " + str(record_threshold_config))
			else:
				rec_debounce_counter = 0
		if rec_debounce_counter >=2:
			rec_debounce_counter = 0
			logger.debug("threshold exceeded")
			start_time = time.time()
			quiet_samples=0
			total_samples = 0
			alldata = bytearray()
			logger.debug("Waiting for Silence " + time.strftime('%Y-%m-%d %H:%M:%S'))
			if root != '':
				statvar.set("Recording")
				StatLabel.config(fg='green')
			timed_out = 0
			while (quiet_samples < (vox_silence_time*(1/rectime))):
				if (total_samples > (timeout_time_sec*(1/rectime))):
					if root != '':
						statvar.set("RECORDING TIMED OUT")
						StatLabel.config(fg='red')
					else:
						logger.debug("RECORDING TIMED OUT")
					timed_out = 1
				temp =bytearray()
				for i in range(0, int(RATE / chunk * rectime)):
					data = recordstream.read(chunk)
					temp.extend(data)
				if timed_out == 0:
					alldata.extend(temp)
				audio_data  = frombuffer(temp, dtype=short)
				if root != '':
					if max(abs(audio_data)) == 0:
						barvar.set(1)
					else:
						#set the bar graph display based on the current audio peak using a log scale
						barvar.set(max(100-int(log10(max(max(abs(audio_data)),1.0)/32768.)*10/-25.*100),3))  #min of scale is -25 dB
				if root != '':
					if 100-log10(max(max(abs(audio_data)),1.0)/32768.)*10/-25.*100 < record_threshold.get() and record_threshold.get()!=0:
						quiet_samples = quiet_samples+1
					else:
						quiet_samples = 0
				else:
					if max(abs(audio_data)) < record_threshold_config:
						quiet_samples = quiet_samples+1
					else:
						quiet_samples = 0
				total_samples = total_samples+1
			logger.debug("Done recording " + time.strftime('%Y-%m-%d %H:%M:%S'))
			if int(vox_silence_time*-(1/rectime)) > 0:
				alldata = alldata[:int(vox_silence_time*-round(1/rectime))]
			data = frombuffer(alldata, dtype=short)  #convert from string to list to separate channels
			if chan == 'left':
				data = data[0::2]
			elif chan == 'right':
				data = data[1::2]
			else:
				data = data
			duration = len(data)/float(RATE)
			#convert back to binary to write to WAV later
			data = chararray.tostring(array(data))
			# write data to WAVE file
			BCFYsuffix = '' if str(BCFY_SlotId.get()) == '' else "-" + str(BCFY_SlotId.get())
			fname = time.strftime('%Y-%m-%dT%H:%M:%S') + BCFYsuffix + ".wav"
			furl = 'file:' + fname

			wf = wave.open( fname, 'wb')
			wf.setnchannels(1)
			wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
			wf.setframerate(RATE)
			wf.writeframes(data)
			wf.close()
			logger.debug("done writing WAV "  + time.strftime('%Y-%m-%d %H:%M:%S'))
			try:			
				logger.debug(fname)
				try:
					flags = subprocess.CREATE_NO_WINDOW
				except:
					flags = 0
				subprocess.call(["ffmpeg","-y","-i",furl,"-b:a",str(mp3_bitrate),"-ar","22050",furl.replace('.wav','.mp3')],creationflags=flags)
				logger.debug("done converting to MP3 " + time.strftime('%Y-%m-%d %H:%M:%S'))				#use ffmpeg.exe 
				os.remove(fname)
			except:
				#exc_type, exc_value, exc_traceback = sys.exc_info()
				#traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2,file=sys.stdout)
				logging.exception('Got exception on main handler')
			_thread.start_new_thread(upload,(fname.replace('.wav','.mp3'),duration))
			_thread.start_new_thread(upload_rdio,(fname.replace('.wav','.mp3'),))
			last_API_attempt = time.time()
			logger.debug("duration: " + str(duration) + " sec")
			logger.debug("waiting for audio " + time.strftime('%Y-%m-%d %H:%M:%S'))
			if root != '':
				statvar.set("Waiting For Audio")
				StatLabel.config(fg='blue')

def saveconfigdata():
	if root != '':
		config = ConfigParser()
		config.read('config.cfg')
		if 'Section1' not in config.sections():
			config.add_section('Section1')
		cfgfile = open('config.cfg','w')
		config.set('Section1','audio_dev_index',str(input_device_indices[input_device.get()]))
		config.set('Section1','record_threshold',str(record_threshold.get()))
		config.set('Section1','vox_silence_time',str(vox_silence_time)) # See [1], below
		config.set('Section1','in_channel',in_channel.get())
		config.set('Section1','BCFY_SystemId',BCFY_SystemId.get())
		config.set('Section1','RadioFreq',RadioFreq.get())
		config.set('Section1','BCFY_APIkey',BCFY_APIkey.get())
		config.set('Section1','BCFY_SlotId',BCFY_SlotId.get())
		config.set('Section1','saveaudio',str(saveaudio.get()))
		config.set('Section1','vox_silence_time',str(vox_silence_time)) # [1] Why is this set a 2nd time?
		config.set('Section1','RDIO_APIkey',RDIO_APIkey.get())
		config.set('Section1','RDIO_APIurl',RDIO_APIurl.get())
		config.set('Section1','RDIO_system',RDIO_system.get())
		config.set('Section1','RDIO_tg',RDIO_tg.get())
		config.write(cfgfile)
		cfgfile.close()
		root.destroy()

if root != '':
	f = Frame(bd=10)
	f.grid(row = 1)

	def validate_number(P): 
		if str.isdigit(P) or P == "":
			return True
		else:
			return False
	vcmd = (f.register(validate_number),"%P") 

	StatLabel = Label(f,textvar = statvar,font=("Helvetica", 12))
	StatLabel.grid(row = 1, column = 1,columnspan = 4,sticky = W)
	StatLabel.config(fg='blue')
	Label(f, text="Audio Input Device:").grid(row = 3, column = 0,sticky = E)
	OptionMenu(f,input_device,*input_devices,command = change_audio_input).grid(row = 3,column = 1,columnspan = 4,sticky = E+W)
	Label(f,text = 'Audio Input Channel').grid(row = 5,column = 0,sticky=E)
	audiochannellist = OptionMenu(f,in_channel,"mono","left","right")
	audiochannellist.config(width=20)
	audiochannellist.grid(row = 5,column = 1,sticky=W)
	Label(f,text='Broadcastify API Key:').grid(row=7,column=0,sticky = E)
	BCFY_APIkey_Entry = Entry(f,width=40,textvariable = BCFY_APIkey)
	BCFY_APIkey_Entry.grid(row = 7, column = 1,columnspan = 4,sticky=W)
	Label(f,text='Broadcastify System ID:').grid(row=9,column=0,sticky = E)
	BCFY_SystemId_Entry = Entry(f,width=20,validate='key',validatecommand=vcmd,textvariable = BCFY_SystemId)
	BCFY_SystemId_Entry.grid(row = 9, column = 1,sticky=W)
	Label(f,text='Broadcastify Slot ID:').grid(row=11,column=0,sticky = E)
	BCFY_SlotId_Entry = Entry(f,width=20,validate='key',validatecommand=vcmd,textvariable = BCFY_SlotId)
	BCFY_SlotId_Entry.grid(row = 11, column = 1,sticky=W)
	Label(f,text='Radio Frequency (MHz):').grid(row=19,column=0,sticky = E)
	Freq_Entry = Entry(f,width=20,textvariable = RadioFreq)
	Freq_Entry.grid(row = 19, column = 1,sticky=W)

	Label(f,text='rdio-scanner url:').grid(row=20,column=0,sticky = E)
	RDIO_APIurl_Entry = Entry(f,width=40,textvariable = RDIO_APIurl)
	RDIO_APIurl_Entry.grid(row = 20, column = 1,sticky=W)
	Label(f,text='rdio-scanner API Key:').grid(row=21,column=0,sticky = E)
	RDIO_APIkey_Entry = Entry(f,width=40,textvariable = RDIO_APIkey)
	RDIO_APIkey_Entry.grid(row = 21, column = 1,columnspan = 4,sticky=W)
	Label(f,text='rdio-scanner System ID:').grid(row=22,column=0,sticky = E)
	RDIO_system_Entry = Entry(f,width=20,validate='key',validatecommand=vcmd,textvariable = RDIO_system)
	RDIO_system_Entry.grid(row = 22, column = 1,sticky=W)
	Label(f,text='rdio-scanner TG ID:').grid(row=23,column=0,sticky = E)
	RDIO_tg_Entry = Entry(f,width=20,validate='key',validatecommand=vcmd,textvariable = RDIO_tg)
	RDIO_tg_Entry.grid(row = 23, column = 1,sticky=W)
	
	Label(f,text='Save Audio Files:').grid(row=24,column=0,sticky=E)
	Checkbutton(f,text = '',variable = saveaudio).grid(row = 24, column = 1,sticky=W)
	Button(f, text = "Save & Exit",command = saveconfigdata,width=20).grid(row = 25,column = 1,columnspan = 1,sticky=W)
	
	squelchbar = Scale(f,from_ = 100, to = 0,length = 150,sliderlength = 8,showvalue = 0,variable = record_threshold,orient = 'vertical').grid(row = 17,rowspan=8,column = 7,columnspan = 1)
	ttk.Progressbar(f,orient ='vertical',variable = barvar,length = 150).grid(row = 17,rowspan = 8,column = 8,columnspan = 1)
	Label(f,text='Audio\n Squelch').grid(row=25,column=7)
	Label(f,text='Audio\n Level').grid(row=25,column=8)
	

if root != '':
	_thread.start_new_thread(start,())
	root.mainloop()
else:
	start()
