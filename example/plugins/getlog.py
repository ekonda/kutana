from time import sleep #For anti-FloodControl
from kutana import Plugin
plugin = Plugin(name="GetLog", cmds=("getlog - reply with bot logs",)) #Register plugin
@plugin.on_text("/gl", "/getlog", "/logs", "/log", "/droplogs", "/droplog", "/dl")
async def on_gl(mg, ats, env): 
	try: #Try to load kutana.log
		fk_c = open("kutana.log") #Open File
		await env.reply("kutana.log: ") 
		for line in fk_c: #Send every line as message 
			sleep(0.8) #Anti-FloodControl
			await env.reply(line) 
		await env.reply("END")
	except BaseException: #If error, send "Can't load logs."
		await env.reply("Can't load logs.")
