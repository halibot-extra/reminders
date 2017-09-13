import re
from datetime import datetime, timezone, timedelta
from halibot import HalModule, HalConfigurer, Message

class Reminders(HalModule):

	class Configurer(HalConfigurer):
		def configure(self):
			self.optionInt('default-timezone', prompt='Default by UTC offset', default=0)
			self.optionString('empty-reminder', prompt='Empty reminder message', default='poke')

	def init(self):
		pass

	def remind_usage(self, msg):
		self.reply(msg, body='''Usage:
  !remind at [time] [message]
  !remind [who] at [time] [message]
''')

	def remind(self, body, dest, author):
		via = author + ' via !remind'
		msg = Message(body=body, author=via)
		self.send_to(msg, [ dest ])

	def receive(self, msg):
		# TODO support alternate date formats
		# TODO parse timezones as an argument to !remind
		rx = '\\s*!remind(\\s\\S+)?\\s+at(\\s+(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d))?\\s+((\\d\\d):(\\d\\d)(:\\d\\d)?)(\\s+.*)?$'
		m = re.match(rx, msg.body)
		if m:
			# Groups:
			#   0 = who or None
			#   1 = YYYY-MM-DD or None
			#     2 = YYYY
			#     3 = MM
			#     4 = DD
			#   5 = HH:MM or HH:MM:SS
			#     6 = HH
			#     7 = MM
			#     8 = :SS or None
			#   9 = message
			gr = m.groups()

			if gr[0]:
				dest = '/'.join([msg.origin.split('/')[0], gr[0].strip()])
			else:
				dest = msg.origin

			tz = timezone(timedelta(hours=self.config.get('default-timezone', 0)))
			now = datetime.now(tz=tz)

			if gr[1]:
				year  = int(gr[2])
				month = int(gr[3])
				day   = int(gr[4])
			else:
				year  = now.year
				month = now.month
				day   = now.day

			hour   = int(gr[6])
			minute = int(gr[7])
			if gr[8]:
				second = int(gr[8][1:]) # Need to chop off colon
			else:
				second = 0

			try:
				time = datetime(year, month, day, hour=hour, minute=minute, second=second, tzinfo=tz)
			except ValueError as e:
				self.reply(msg, body='Invalid date or time')
				return

			delay = time.timestamp() - now.timestamp()
			rmessage = gr[9].strip() if gr[9] else self.config.get('empty-reminder', 'poke')

			if delay < 0:
				self.reply(msg, body='I cannot change the past')
				return

			self.eventloop.call_later(delay, self.remind, rmessage, dest, msg.author)
			self.log.info('Reminder to '+dest+' scheduled for '+str(time.ctime())+' ('+str(delay)+'s later) by '+msg.author)
			self.reply(msg, body='Reminder set.')
		elif msg.body.strip().startswith('!remind'):
			self.remind_usage(msg)

